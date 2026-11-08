#!/usr/bin/env python3
"""Run a repository's GitHub Actions jobs on this Mac before a push (docs/ci-local.md).

The workflow files are the only source of truth: this script reads `.github/workflows/*.yml`,
keeps the workflows the event triggers (branch and path filters included), expands each job's
matrix, and runs the job's `run:` steps in a scratch checkout of the commit, with the job's env,
defaults, `if:` conditions, needs, outputs and timeouts. A few actions are emulated with what this
machine already has (checkout, setup-python, setup-node, rust-toolchain); caches and artifact
uploads are no-ops. What cannot run here is SKIPPED with its reason, never passed silently: a
Windows or custom runner, Docker services, secrets, a step that needs root (`sudo`, `apt-get`), a
PowerShell step, a Python/Node/Rust toolchain this machine lacks. An action this script does not
know is an ERROR, so a workflow change the gate does not understand fails it loudly.

By default (`--event auto`) each workflow runs as the push to the base branch when it has one
(the full main matrix and every conditional job, on the merge of the commit into the base: what
main becomes), else as the pull request. Every job runs in a fresh Python environment that
installs exactly the workflow's own `pip install` lines, so sibling packages come from PyPI as
on GitHub, never from the editable checkouts next door.

Exit code (the contract, ADR-bound): 0 when every job that could run passed and none was skipped,
or some were skipped and `--allow-skipped` was given; 1 otherwise; 2 for a usage error.

Run it through scripts/ci_local.sh, which provides PyYAML.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import fcntl
import itertools
import json
import math
import os
import re
import shlex
import shutil
import signal
import socket
import stat
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# --------------------------------------------------------------------------------------------
# GitHub Actions expressions: ${{ ... }}
# https://docs.github.com/actions/learn-github-actions/expressions
# --------------------------------------------------------------------------------------------


class ExprError(Exception):
    pass


_TOKEN = re.compile(
    r"""\s*(?:
      (?P<num>-?(?:0x[0-9a-fA-F]+|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?))
     |(?P<str>'(?:[^']|'')*')
     |(?P<op>&&|\|\||==|!=|<=|>=|[<>!()\[\].,*])
     |(?P<ident>[A-Za-z_][A-Za-z0-9_-]*)
    )""",
    re.X,
)


def _tokenize(text: str) -> list[tuple[str, Any]]:
    out: list[tuple[str, Any]] = []
    pos = 0
    text = text.rstrip()
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            raise ExprError(f"cannot parse expression at {text[pos:]!r}")
        pos = m.end()
        if m.group("num") is not None:
            raw = m.group("num")
            out.append(("lit", int(raw, 16) if raw.lower().startswith(("0x", "-0x")) else float(raw)))
        elif m.group("str") is not None:
            out.append(("lit", m.group("str")[1:-1].replace("''", "'")))
        elif m.group("op") is not None:
            out.append(("op", m.group("op")))
        else:
            word = m.group("ident")
            low = word.lower()
            if low in ("true", "false"):
                out.append(("lit", low == "true"))
            elif low == "null":
                out.append(("lit", None))
            else:
                out.append(("ident", word))
    out.append(("end", None))
    return out


class _Filtered(list):
    """The result of `.*`: property access maps over the items."""


class _Parser:
    def __init__(self, text: str):
        self.toks = _tokenize(text)
        self.i = 0

    def peek(self) -> tuple[str, Any]:
        return self.toks[self.i]

    def take(self, kind: str | None = None, value: Any = None) -> tuple[str, Any]:
        tok = self.toks[self.i]
        if (kind and tok[0] != kind) or (value is not None and tok[1] != value):
            raise ExprError(f"expected {value or kind}, found {tok[1]!r}")
        self.i += 1
        return tok

    def accept(self, value: str) -> bool:
        if self.peek() == ("op", value):
            self.i += 1
            return True
        return False

    def parse(self):
        node = self.or_()
        self.take("end")
        return node

    def or_(self):
        node = self.and_()
        while self.accept("||"):
            node = ("or", node, self.and_())
        return node

    def and_(self):
        node = self.eq()
        while self.accept("&&"):
            node = ("and", node, self.eq())
        return node

    def eq(self):
        node = self.cmp()
        while self.peek()[0] == "op" and self.peek()[1] in ("==", "!="):
            op = self.take()[1]
            node = (op, node, self.cmp())
        return node

    def cmp(self):
        node = self.unary()
        while self.peek()[0] == "op" and self.peek()[1] in ("<", "<=", ">", ">="):
            op = self.take()[1]
            node = (op, node, self.unary())
        return node

    def unary(self):
        if self.accept("!"):
            return ("not", self.unary())
        return self.postfix()

    def postfix(self):
        node = self.primary()
        while True:
            if self.accept("."):
                if self.accept("*"):
                    node = ("star", node)
                else:
                    node = ("prop", node, self.take("ident")[1])
            elif self.accept("["):
                if self.accept("*"):
                    node = ("star", node)
                else:
                    node = ("index", node, self.or_())
                self.take("op", "]")
            else:
                return node

    def primary(self):
        kind, value = self.peek()
        if kind == "lit":
            self.i += 1
            return ("lit", value)
        if self.accept("("):
            node = self.or_()
            self.take("op", ")")
            return node
        if kind == "ident":
            self.i += 1
            if self.accept("("):
                args = []
                if not self.accept(")"):
                    args.append(self.or_())
                    while self.accept(","):
                        args.append(self.or_())
                    self.take("op", ")")
                return ("call", value, args)
            return ("ctx", value)
        raise ExprError(f"unexpected {value!r}")


def _num(v: Any) -> float:
    if v is None:
        return 0.0
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip()
        if s == "":
            return 0.0
        try:
            return float(int(s, 16)) if s.lower().startswith("0x") else float(s)
        except ValueError:
            return math.nan
    return math.nan


def truthy(v: Any) -> bool:
    if v is None or v is False:
        return False
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return v != 0 and not math.isnan(v)
    if isinstance(v, str):
        return v != ""
    return True


def _eq(a: Any, b: Any) -> bool:
    if isinstance(a, str) and isinstance(b, str):
        return a.lower() == b.lower()
    if a is None and b is None:
        return True
    if isinstance(a, (dict, list)) or isinstance(b, (dict, list)):
        return a is b
    return _num(a) == _num(b)


def _cmp(op: str, a: Any, b: Any) -> bool:
    if isinstance(a, str) and isinstance(b, str):
        x, y = a.lower(), b.lower()
    else:
        x, y = _num(a), _num(b)
        if math.isnan(x) or math.isnan(y):
            return False
    return {"<": x < y, "<=": x <= y, ">": x > y, ">=": x >= y}[op]


def to_str(v: Any) -> str:
    if v is None:
        return ""
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else repr(v)
    if isinstance(v, (dict, list)):
        return json.dumps(v, indent=2)
    return str(v)


def _format(fmt: str, *args: Any) -> str:
    out, i = [], 0
    while i < len(fmt):
        c = fmt[i]
        if fmt.startswith("{{", i):
            out.append("{")
            i += 2
        elif fmt.startswith("}}", i):
            out.append("}")
            i += 2
        elif c == "{":
            j = fmt.index("}", i)
            out.append(to_str(args[int(fmt[i + 1 : j])]))
            i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


class Context:
    """The expression contexts (github, env, matrix, needs, steps, ...) plus the status functions."""

    def __init__(self, data: dict[str, Any], status: Callable[[str], bool] | None = None):
        self.data = data
        self.status = status or (lambda name: name in ("success", "always"))
        self.secrets_used: set[str] = set()

    def child(self, **extra: Any) -> "Context":
        ctx = Context({**self.data, **extra}, self.status)
        ctx.secrets_used = self.secrets_used
        return ctx

    def lookup(self, name: str) -> Any:
        key = name.lower()
        for k, v in self.data.items():
            if k.lower() == key:
                return v
        raise ExprError(f"unknown context {name!r}")


def _get(obj: Any, key: Any) -> Any:
    if isinstance(obj, _Filtered):
        return _Filtered(x for x in (_get(o, key) for o in obj) if x is not None)
    if isinstance(obj, dict):
        if isinstance(key, str):
            for k, v in obj.items():
                if str(k).lower() == key.lower():
                    return v
            return None
        return obj.get(key)
    if isinstance(obj, list):
        n = _num(key)
        if not math.isnan(n) and 0 <= int(n) < len(obj):
            return obj[int(n)]
    return None


def _eval(node: tuple, ctx: Context) -> Any:
    kind = node[0]
    if kind == "lit":
        return node[1]
    if kind == "ctx":
        return ctx.lookup(node[1])
    if kind == "prop":
        base = _eval(node[1], ctx)
        if node[1] == ("ctx", "secrets"):
            ctx.secrets_used.add(node[2])
        return _get(base, node[2])
    if kind == "index":
        return _get(_eval(node[1], ctx), _eval(node[2], ctx))
    if kind == "star":
        base = _eval(node[1], ctx)
        if isinstance(base, dict):
            return _Filtered(base.values())
        if isinstance(base, list):
            return _Filtered(base)
        return _Filtered()
    if kind == "not":
        return not truthy(_eval(node[1], ctx))
    if kind == "and":
        left = _eval(node[1], ctx)
        return _eval(node[2], ctx) if truthy(left) else left
    if kind == "or":
        left = _eval(node[1], ctx)
        return left if truthy(left) else _eval(node[2], ctx)
    if kind == "==":
        return _eq(_eval(node[1], ctx), _eval(node[2], ctx))
    if kind == "!=":
        return not _eq(_eval(node[1], ctx), _eval(node[2], ctx))
    if kind in ("<", "<=", ">", ">="):
        return _cmp(kind, _eval(node[1], ctx), _eval(node[2], ctx))
    if kind == "call":
        name = node[1].lower()
        if name in ("success", "failure", "always", "cancelled"):
            return ctx.status(name)
        args = [_eval(a, ctx) for a in node[2]]
        if name == "contains":
            hay, needle = args
            if isinstance(hay, list):
                return any(_eq(x, needle) for x in hay)
            return to_str(needle).lower() in to_str(hay).lower()
        if name == "startswith":
            return to_str(args[0]).lower().startswith(to_str(args[1]).lower())
        if name == "endswith":
            return to_str(args[0]).lower().endswith(to_str(args[1]).lower())
        if name == "format":
            return _format(to_str(args[0]), *args[1:])
        if name == "join":
            sep = to_str(args[1]) if len(args) > 1 else ","
            return sep.join(to_str(x) for x in args[0]) if isinstance(args[0], list) else to_str(args[0])
        if name == "tojson":
            return json.dumps(args[0], indent=2)
        if name == "fromjson":
            return json.loads(to_str(args[0]))
        if name == "hashfiles":
            return ""  # only cache keys use it; caches are no-ops here
        raise ExprError(f"unknown function {node[1]}()")
    raise ExprError(f"bad node {kind}")


def evaluate(text: str, ctx: Context) -> Any:
    return _eval(_Parser(text).parse(), ctx)


_INTERP = re.compile(r"\$\{\{(.*?)\}\}", re.S)


def interpolate(text: Any, ctx: Context) -> Any:
    """`${{ }}` substitution. A string that is exactly one expression keeps the expression's type."""
    if not isinstance(text, str):
        return text
    whole = _INTERP.fullmatch(text.strip())
    if whole and text.strip().count("${{") == 1:
        return evaluate(whole.group(1), ctx)
    return _INTERP.sub(lambda m: to_str(evaluate(m.group(1), ctx)), text)


def condition(cond: Any, ctx: Context, default: str = "success()") -> bool:
    """An `if:` value: an expression with or without the `${{ }}` wrapper."""
    if cond is None:
        cond = default
    if isinstance(cond, bool):
        return cond
    cond = str(cond).strip()
    whole = _INTERP.fullmatch(cond)
    if whole and cond.count("${{") == 1:
        cond = whole.group(1)
    elif "${{" in cond:
        return truthy(interpolate(cond, ctx))
    node = _Parser(cond).parse()
    if not _mentions_status(node):
        node = ("and", ("call", "success", []), node)
    return truthy(_eval(node, ctx))


def _mentions_status(node: Any) -> bool:
    if isinstance(node, tuple):
        if node[0] == "call" and node[1].lower() in ("success", "failure", "always", "cancelled"):
            return True
        return any(_mentions_status(x) for x in node[1:])
    if isinstance(node, list):
        return any(_mentions_status(x) for x in node)
    return False


def secrets_in(obj: Any) -> set[str]:
    """Every `secrets.NAME` an object's expressions read."""
    found: set[str] = set()
    if isinstance(obj, dict):
        for v in obj.values():
            found |= secrets_in(v)
    elif isinstance(obj, list):
        for v in obj:
            found |= secrets_in(v)
    elif isinstance(obj, str):
        for m in _INTERP.finditer(obj):
            found |= set(re.findall(r"\bsecrets\s*\.\s*([A-Za-z_][A-Za-z0-9_]*)", m.group(1)))
    return found


# --------------------------------------------------------------------------------------------
# Triggers: event, branch and path filters
# https://docs.github.com/actions/writing-workflows/workflow-syntax-for-github-actions#filter-pattern-cheat-sheet
# --------------------------------------------------------------------------------------------


def glob_regex(pattern: str) -> re.Pattern[str]:
    out, i = [], 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c in "?+":
            out.append(c)  # zero-or-one / one-or-more of the preceding character
            i += 1
        elif c == "[":
            j = pattern.index("]", i)
            out.append(pattern[i : j + 1])
            i = j + 1
        else:
            out.append(re.escape(c))
            i += 1
    return re.compile("".join(out) + r"\Z")


def filter_matches(patterns: list[str], value: str) -> bool:
    """GitHub's ordered filter: later `!pattern` entries take matches back out."""
    hit = False
    for pat in patterns:
        pat = str(pat)
        if pat.startswith("!"):
            if hit and glob_regex(pat[1:]).match(value):
                hit = False
        elif glob_regex(pat).match(value):
            hit = True
    return hit


def _as_list(v: Any) -> list[str]:
    if v is None:
        return []
    return [str(x) for x in (v if isinstance(v, list) else [v])]


def triggered(on: Any, event: str, ref: str, base: str, changed: list[str] | None) -> tuple[bool, str]:
    """Whether a workflow's `on:` runs for this event; the reason when it does not."""
    if isinstance(on, str):
        on = {on: None}
    elif isinstance(on, list):
        on = {e: None for e in on}
    if not isinstance(on, dict) or event not in on:
        return False, f"not on {event}"
    cfg = on.get(event) or {}
    if event == "pull_request":
        if "branches" in cfg and not filter_matches(_as_list(cfg["branches"]), base):
            return False, f"base {base} not in branches"
        if "branches-ignore" in cfg and filter_matches(_as_list(cfg["branches-ignore"]), base):
            return False, f"base {base} in branches-ignore"
    elif event == "push":
        is_tag = ref.startswith("refs/tags/")
        name = ref.split("/", 2)[2] if ref.count("/") >= 2 else ref
        branch_keys = [k for k in ("branches", "branches-ignore") if k in cfg]
        tag_keys = [k for k in ("tags", "tags-ignore") if k in cfg]
        if is_tag:
            if not tag_keys and branch_keys:
                return False, "tag push, only branch filters"
            if "tags" in cfg and not filter_matches(_as_list(cfg["tags"]), name):
                return False, f"tag {name} not in tags"
            if "tags-ignore" in cfg and filter_matches(_as_list(cfg["tags-ignore"]), name):
                return False, f"tag {name} in tags-ignore"
        else:
            if not branch_keys and tag_keys:
                return False, "branch push, only tag filters"
            if "branches" in cfg and not filter_matches(_as_list(cfg["branches"]), name):
                return False, f"branch {name} not in branches"
            if "branches-ignore" in cfg and filter_matches(_as_list(cfg["branches-ignore"]), name):
                return False, f"branch {name} in branches-ignore"
    if ("paths" in cfg or "paths-ignore" in cfg) and not (event == "push" and ref.startswith("refs/tags/")):
        files = changed or []
        if "paths" in cfg and not any(filter_matches(_as_list(cfg["paths"]), f) for f in files):
            return False, "no changed file matches paths"
        if "paths-ignore" in cfg and files and all(filter_matches(_as_list(cfg["paths-ignore"]), f) for f in files):
            return False, "every changed file matches paths-ignore"
    return True, ""


# --------------------------------------------------------------------------------------------
# Matrix
# --------------------------------------------------------------------------------------------


def expand_matrix(strategy: Any, ctx: Context) -> list[dict[str, Any]]:
    if not strategy or "matrix" not in strategy:
        return [{}]
    matrix = interpolate(strategy["matrix"], ctx)
    if not isinstance(matrix, dict):
        raise ExprError("strategy.matrix is not a mapping")
    matrix = dict(matrix)
    include = interpolate(matrix.pop("include", None), ctx) or []
    exclude = interpolate(matrix.pop("exclude", None), ctx) or []
    axes = {}
    for key, values in matrix.items():
        values = interpolate(values, ctx)
        if not isinstance(values, list):
            raise ExprError(f"matrix.{key} is not a list")
        axes[key] = values
    combos = [dict(zip(axes, c)) for c in itertools.product(*axes.values())] if axes else []
    combos = [c for c in combos if not any(all(_eq(c.get(k), v) for k, v in ex.items()) for ex in exclude)]
    for inc in include:
        inc = dict(inc)
        matched = False
        for c in combos:
            if all(_eq(c[k], v) for k, v in inc.items() if k in axes):
                c.update({k: v for k, v in inc.items() if k not in axes})
                matched = True
        if not matched:
            combos.append(inc)
    return combos or [{}]


# --------------------------------------------------------------------------------------------
# Shell steps
# --------------------------------------------------------------------------------------------

_PIP = re.compile(
    r"(?<![\w./$-])(?:python3?(?:\.\d+)?\s+-m\s+pip|pip3?)(?=\s+(?:install|uninstall|freeze|list|show|check)\b)"
)


_PIP_NET_OPTS = re.compile(r"\s--(?:timeout|retries)(?:=\S+|\s+\S+)")


def translate_pip(script: str, uv: str) -> str:
    """`python -m pip <cmd>` / `pip <cmd>` -> `uv pip <cmd>` (the --installer uv mode).

    uv links packages from its cache instead of copying them, so a fresh environment per job
    costs seconds and no disk; `--installer pip` keeps the workflow's pip byte for byte.
    """
    script = _PIP.sub(f"{shlex.quote(uv)} pip", script)
    script = script.replace("--no-cache-dir", "--no-cache")
    # pip's network knobs have no uv spelling (uv: UV_HTTP_TIMEOUT / UV_HTTP_RETRIES, set by the gate's
    # environment): dropped from translated lines only, so a workflow's `pip install --timeout 60 --retries 5`
    # runs instead of failing on "unexpected argument".
    return "\n".join(
        _PIP_NET_OPTS.sub("", line) if f"{shlex.quote(uv)} pip" in line else line for line in script.split("\n")
    )


def shell_command(shell: str | None, script_path: str) -> list[str] | None:
    """The argv GitHub runs for a `shell:` value on Linux/macOS; None for a Windows shell."""
    if shell is None:
        return ["bash", "-e", script_path]
    s = str(shell).strip()
    if s == "bash":
        return ["bash", "--noprofile", "--norc", "-eo", "pipefail", script_path]
    if s == "sh":
        return ["sh", "-e", script_path]
    if s == "python":
        return ["python", script_path]
    if s in ("pwsh", "powershell", "cmd"):
        return None
    if "{0}" in s:
        return [part.replace("{0}", script_path) for part in shlex.split(s)]
    return shlex.split(s) + [script_path]


def parse_env_file(path: Path) -> dict[str, str]:
    """$GITHUB_ENV / $GITHUB_OUTPUT: `KEY=value` lines and `KEY<<DELIM` blocks."""
    out: dict[str, str] = {}
    if not path.exists():
        return out
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if "<<" in line and ("=" not in line or line.index("<<") < line.index("=")):
            key, delim = line.split("<<", 1)
            body = []
            i += 1
            while i < len(lines) and lines[i] != delim:
                body.append(lines[i])
                i += 1
            out[key] = "\n".join(body)
        elif "=" in line:
            key, value = line.split("=", 1)
            out[key] = value
        i += 1
    return out


# --------------------------------------------------------------------------------------------
# Plan
# --------------------------------------------------------------------------------------------

NOOP_ACTIONS = {
    "actions/cache": "cache (this machine keeps its own caches)",
    "actions/upload-artifact": "artifact upload",
    "swatinem/rust-cache": "Rust cache (a persistent target dir per job plays its part)",
}
EMULATED_ACTIONS = {"actions/checkout", "actions/setup-python", "actions/setup-node", "dtolnay/rust-toolchain"}
UNRUNNABLE_ACTIONS = {
    "docker/setup-buildx-action": "Docker build actions",
    "docker/build-push-action": "Docker build actions",
    "docker/login-action": "Docker registry login (secrets)",
    "docker/setup-qemu-action": "Docker build actions",
    "docker/metadata-action": "Docker build actions",
}


@dataclass
class Job:
    workflow: str
    wf_file: str
    wf: dict
    job_id: str
    spec: dict
    matrix: dict
    label: str
    index: int = 0
    result: str = "pending"  # PASS FAIL ERROR SKIPPED SKIPPED-BY-NEEDS NOT-TRIGGERED NOT-SELECTED
    reason: str = ""
    seconds: float = 0.0
    log: Path | None = None
    event: str = "pull_request"
    git_ref: str = ""
    python: str | None = None
    outputs: dict = field(default_factory=dict)
    host_note: str = ""


# Results that make a run red: a job that failed, could not be evaluated, or never started because
# a job it needs failed (on GitHub it would not run either, and what it checks went unchecked).
RED_RESULTS = ("FAIL", "ERROR", "SKIPPED-BY-NEEDS")
SKIPPED_BY_NEEDS = "SKIPPED-BY-NEEDS"

# A release tag's pure checks: a `run:` step named like a validation of the tag, the version or the
# changelog, that writes nothing outside this machine. They run as a "pre-check" job of their own,
# with the steps before them (checkout, setup, tool installs) and without the job's `needs`, so a
# failing test job cannot hide them, and a `--job` selection never drops them.
PURE_CHECK_NAME = re.compile(r"validat|version|changelog", re.I)
PRECHECK_SUFFIX = "--pre-check"


def red_count(counts: dict[str, int]) -> int:
    return sum(counts.get(r, 0) for r in RED_RESULTS)


def pure_check_steps(steps: list) -> list[int]:
    """The indexes of a job's pure-check steps (see PURE_CHECK_NAME)."""
    found = []
    for i, step in enumerate(steps or []):
        run = str(step.get("run") or "")
        if run and PURE_CHECK_NAME.search(str(step.get("name") or "")) and outside_write(run) is None:
            found.append(i)
    return found


_NEEDS_REF = re.compile(r"\$\{\{[^}]*\bneeds\.[^}]*\}\}")


def precheck_spec(spec: dict) -> tuple[dict | None, str]:
    """A job reduced to its pure checks: the steps up to the last one, minus any step that writes
    outside this machine; no needs, no if, no matrix, no outputs, no deployment environment (its
    steps are read-only by rule). (None, "") when the job has no pure check; (None, why) when a kept
    step reads `${{ needs.* }}`: without its needs the expression is empty and the pre-check would be
    red on a healthy release, so none is made (resolving needs from the real jobs is a later item)."""
    steps = spec.get("steps") or []
    checks = pure_check_steps(steps)
    if not checks:
        return None, ""
    kept = [st for st in steps[: checks[-1] + 1] if not (st.get("run") and outside_write(str(st["run"])))]
    reduced = {k: v for k, v in spec.items() if k not in ("needs", "if", "strategy", "outputs", "steps", "environment")}
    for where, part in [("the job's env", reduced.get("env")), ("the job's defaults", reduced.get("defaults"))] + [
            (f"step {st.get('name') or st.get('uses') or st.get('run', '')[:40]!r}", st) for st in kept]:
        m = _NEEDS_REF.search(json.dumps(part)) if part else None
        if m:
            return None, f"{where} reads {m.group(0)}, which only the real job has"
    reduced["steps"] = kept
    return reduced, ""


def action_name(uses: str) -> str:
    return uses.split("@", 1)[0].lower()


def runner_verdict(runs_on: Any, local_labels: list[str] = ()) -> tuple[bool, str]:
    labels = _as_list(runs_on) if not isinstance(runs_on, dict) else ["(runner group)"]
    if labels and all(label in local_labels for label in labels):
        return True, f"{', '.join(labels)} job on this Mac (--runner-label)"
    if len(labels) == 1:
        label = labels[0]
        if label.startswith("ubuntu-"):
            return True, f"{label} job on this Mac"
        if label.startswith("macos-"):
            return True, f"{label} job on this Mac"
        if label.startswith("windows-"):
            return False, f"runs on {label}"
    return False, f"runs on the custom runner {', '.join(labels)!r}, not this Mac"


def static_skip(job: Job) -> tuple[str, str] | None:
    """A reason the job cannot run here, decided before running it: (kind, reason)."""
    spec = job.spec
    if "uses" in spec:
        return "ERROR", f"calls the reusable workflow {spec['uses']}, which ci_local does not run"
    secrets = secrets_in(spec) | secrets_in(job.wf.get("env") or {})
    if secrets:
        return "SKIPPED", "needs secrets " + ", ".join(sorted(secrets))
    if spec.get("environment"):
        env = spec["environment"]
        return "SKIPPED", f"deployment environment {env.get('name') if isinstance(env, dict) else env!r}"
    if spec.get("services"):
        return "SKIPPED", "needs Docker service containers"
    if spec.get("container"):
        return "SKIPPED", "runs in a Docker container"
    for step in spec.get("steps") or []:
        uses = step.get("uses")
        if not uses:
            continue
        name = action_name(uses)
        if uses.startswith(("./", "docker://")):
            return "ERROR", f"uses {uses}, which ci_local does not know: teach scripts/ci_local.py"
        if name in UNRUNNABLE_ACTIONS:
            return "SKIPPED", f"needs {UNRUNNABLE_ACTIONS[name]} ({uses})"
        if name not in NOOP_ACTIONS and name not in EMULATED_ACTIONS:
            return "ERROR", f"uses {uses}, which ci_local does not know: teach scripts/ci_local.py"
    return None


def setup_python_version(job: Job, ctx: Context) -> str | None:
    for step in job.spec.get("steps") or []:
        if action_name(step.get("uses") or "") == "actions/setup-python":
            return to_str(interpolate((step.get("with") or {}).get("python-version"), ctx))
    return None


# --------------------------------------------------------------------------------------------
# Toolchains on this machine
# --------------------------------------------------------------------------------------------


def find_python(version: str) -> str | None:
    try:
        out = subprocess.run(
            [UV, "python", "find", "--system", "--no-python-downloads", "--no-project", version],
            capture_output=True, text=True, timeout=60, cwd="/",
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    path = out.stdout.strip()
    return path if out.returncode == 0 and path else None


def _node_version(binary: Path) -> str | None:
    try:
        out = subprocess.run([str(binary), "--version"], capture_output=True, text=True, timeout=30)
    except OSError:
        return None
    return out.stdout.strip().lstrip("v") or None


def find_node(spec: str) -> tuple[Path, str] | None:
    """A node binary whose version starts with the requested one (`24`, `22.11`, `24.x`)."""
    want = [p for p in str(spec).strip().lstrip("v").split(".") if p not in ("x", "*", "")]
    if not want or not all(p.isdigit() for p in want):
        return None
    candidates: list[Path] = []
    nvm = Path.home() / ".nvm" / "versions" / "node"
    if nvm.is_dir():
        candidates += sorted(nvm.glob("v*/bin/node"), reverse=True)
    candidates += sorted(Path("/opt/homebrew/opt").glob("node@*/bin/node"), reverse=True)
    candidates.append(Path("/opt/homebrew/bin/node"))
    for binary in candidates:
        if not binary.exists():
            continue
        version = _node_version(binary)
        if version and version.split(".")[: len(want)] == want:
            return binary.parent, version
    return None


def image_node() -> Path | None:
    """GitHub's ubuntu and macOS images carry a Node; jobs without setup-node get the newest one here."""
    best: tuple[tuple[int, ...], Path] | None = None
    nvm = Path.home() / ".nvm" / "versions" / "node"
    candidates = list(nvm.glob("v*/bin/node")) if nvm.is_dir() else []
    candidates += list(Path("/opt/homebrew/opt").glob("node@*/bin/node")) + [Path("/opt/homebrew/bin/node")]
    for binary in candidates:
        version = _node_version(binary) if binary.exists() else None
        if version and all(p.isdigit() for p in version.split(".")):
            key = tuple(int(p) for p in version.split("."))
            if best is None or key > best[0]:
                best = (key, binary.parent)
    return best[1] if best else None


def rust_toolchain_ok(toolchain: str, components: list[str]) -> str | None:
    """None when the toolchain and components are installed; otherwise what is missing."""
    rustup = shutil.which("rustup") or str(Path.home() / ".cargo" / "bin" / "rustup")
    try:
        listed = subprocess.run([rustup, "toolchain", "list"], capture_output=True, text=True, timeout=60).stdout
    except OSError:
        return "rustup is not installed"
    names = [line.split()[0] for line in listed.splitlines() if line.strip()]
    if not any(n == toolchain or n.startswith(toolchain + "-") for n in names):
        return f"Rust toolchain {toolchain} is not installed (rustup toolchain install {toolchain})"
    if components:
        have = subprocess.run(
            [rustup, "component", "list", "--installed", "--toolchain", toolchain],
            capture_output=True, text=True, timeout=60,
        ).stdout
        for comp in components:
            if not re.search(rf"^{re.escape(comp)}(-|$)", have, re.M):
                return f"Rust component {comp} is not installed for {toolchain}"
    return None


# --------------------------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------------------------

# Outside the workspace on purpose: code that walks up its parents for sibling checkouts
# (abstractcore's theme_sync finds ../abstractuic) must not find the live ones, as on GitHub. And no
# "local" in the path: tests assert on output that contains their tmp paths (AbstractCore's zig
# outline test checks that the word "local" is absent).
SCRATCH = Path.home() / "Library" / "Caches" / "ci-gate"
UV = shutil.which("uv") or str(Path.home() / ".local" / "bin" / "uv")
SYSTEM_PATH = ["/opt/homebrew/bin", "/opt/homebrew/sbin", "/usr/bin", "/bin", "/usr/sbin", "/sbin"]
RUST_TOOLS = ["cargo", "cargo-clippy", "cargo-fmt", "clippy-driver", "rustc", "rustdoc", "rustfmt", "rustup"]
ROOT_SHIM = """#!/bin/sh
# ci_local: a GitHub runner step that needs root. It cannot run on this Mac.
printf '%s\\n' "$(basename "$0") $*" >> "$CI_LOCAL_JOB_DIR/needs-root"
echo "ci_local: '$(basename "$0") $*' needs root on a Linux runner; this job cannot run here" >&2
exit 97
"""


def repo_name_from(origin_url: str, fallback: str) -> str:
    """The repository's name for serial rules, the shared Rust folder, --keep-runs and run folder
    names: the last part of its origin URL without .git, lower case. A worktree at any path
    (untracked/wt-w3-ttl) gets the main checkout's name. `fallback` (the folder name) only when
    there is no origin."""
    base = re.split(r"[/:]", (origin_url or "").strip().rstrip("/"))[-1]
    base = base[:-4] if base.endswith(".git") else base
    if not re.fullmatch(r"[A-Za-z0-9._-]+", base) or base in (".", ".."):
        base = fallback  # `..` would make the shared Rust folder the gate's cache itself
    return base.lower()


def cargo_target_dir(repo_name: str) -> Path:
    """The Rust build folder every run of one repository shares (a job's own CARGO_TARGET_DIR wins):
    a rebuild reuses the previous compilation, as Swatinem/rust-cache does on GitHub. One per
    repository, so crates of different repositories never collide."""
    return SCRATCH / "cargo-target" / repo_name


def rust_target_dirs(root: Path) -> list[Path]:
    """The cargo build folders under `root`: a directory holding the CACHEDIR.TAG cargo writes, or
    its .rustc_info.json. Symlinks are not followed; a found folder is not searched further."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        tag = here / "CACHEDIR.TAG"
        is_cargo = ".rustc_info.json" in filenames or (
            "CACHEDIR.TAG" in filenames and "cargo" in tag.read_text(encoding="utf-8", errors="replace").lower())
        if is_cargo:
            found.append(here)
            dirnames[:] = []
        else:
            dirnames[:] = [d for d in dirnames if d != ".git"]
    return found


def _remove_tree(path: Path) -> None:
    """shutil.rmtree of a real directory, read-only folders included (Go's module cache makes its
    folders read-only). First every real directory in the tree gets u+rwx, so its entries can be
    listed and unlinked; a symlink is never chmod-ed or followed (only the link itself is removed),
    so nothing outside `path` changes mode. Raises OSError when `path` is a symlink."""
    if path.is_symlink():
        raise OSError(f"refusing to remove a symlink as a tree: {path}")
    stack = [str(path)]
    while stack:
        d = stack.pop()
        try:
            mode = os.lstat(d).st_mode
        except OSError:
            continue
        if not stat.S_ISDIR(mode):  # a symlink (to a folder or not) is S_ISLNK under lstat
            continue
        if mode & 0o700 != 0o700:
            os.chmod(d, stat.S_IMODE(mode) | 0o700)
        with os.scandir(d) as entries:
            stack.extend(e.path for e in entries if e.is_dir(follow_symlinks=False))
    shutil.rmtree(path)


def clean_rust_builds(jobdir: Path, run_dir: Path) -> list[str]:
    """Remove the Rust build folders a finished job left inside its run directory (a workflow that
    set its own CARGO_TARGET_DIR, or a tool that ignores it), keeping the executables cargo placed
    at the top of each profile folder (`release/<bin>`) in `<job>/rust-binaries/`. Never touches
    anything outside `run_dir`. Returns one line per folder for the job log."""
    notes = []
    inside = run_dir.resolve()
    for target in rust_target_dirs(jobdir):
        real = target.resolve()
        if target.is_symlink() or inside not in real.parents:
            notes.append(f"ci_local: kept Rust build folder {target}: not inside the run directory")
            continue
        kept = 0
        # <target>/<profile>/<bin>, and <target>/<triple>/<profile>/<bin> for a cross build
        tops = [d for d in target.iterdir() if d.is_dir() and not d.is_symlink()]
        profiles = tops + [t / q for t in tops for q in ("debug", "release") if (t / q).is_dir()]
        for profile in profiles:
            for f in profile.iterdir():
                if f.is_file() and not f.is_symlink() and os.access(f, os.X_OK) and f.suffix not in (".d", ".rlib", ".rmeta"):
                    dest = jobdir / "rust-binaries" / f.relative_to(target)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dest)
                    kept += 1
        _remove_tree(target)
        notes.append(f"ci_local: removed the Rust build folder {target}"
                     + (f"; kept {kept} executable(s) in {jobdir / 'rust-binaries'}" if kept else ""))
    return notes


RUN_DIR_NAME = r"-\d{8}-\d{6}-[0-9a-f]{8}"  # <repo>-<YYYYmmdd>-<HHMMSS>-<sha8>, as prepare_source names it
RUN_LOCK = ".ci-local-running"
LEGACY_QUIET_SECONDS = 30 * 60  # a run folder without a lock (an older gate) counts as running this long


def parse_keep_runs(text: str) -> int:
    """--keep-runs: a count of run folders, or `all` (0) to keep every one."""
    if text.strip().lower() == "all":
        return 0
    try:
        n = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"--keep-runs takes a number or 'all', not {text!r}") from None
    if n < 0:
        raise argparse.ArgumentTypeError("--keep-runs takes 0 or more (0 or 'all' keeps every run folder)")
    return n


def _run_busy(run: Path, now: float) -> bool:
    """A run folder still in use: its lock is held, or (no lock: a gate older than the lock) a job log
    changed in the last LEGACY_QUIET_SECONDS."""
    lock = run / RUN_LOCK
    if lock.exists():
        try:
            with open(lock, "a", encoding="utf-8") as f:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(f, fcntl.LOCK_UN)
            return False
        except OSError:
            return True
    stamps = [run.stat().st_mtime] + [p.stat().st_mtime for p in run.glob("jobs/*/log.txt")]
    return now - max(stamps) < LEGACY_QUIET_SECONDS


def prune_runs(runs_root: Path, repo_name: str, current: Path, keep: int, allowed_root: Path) -> tuple[list[Path], str]:
    """Delete the oldest run folders of `repo_name` directly under `runs_root` so at most `keep`
    remain, `current` included and never deleted. keep 0 keeps everything. Refused (nothing
    deleted, the reason returned) when `runs_root` is not under `allowed_root`. A folder another
    gate is still running in is skipped. Returns (deleted folders, note)."""
    if keep <= 0:
        return [], ""
    root, allowed = runs_root.resolve(), allowed_root.resolve()
    if root != allowed and allowed not in root.parents:
        return [], f"not deleting old run folders: {root} is not under {allowed}"
    name = re.compile(re.escape(repo_name) + RUN_DIR_NAME)
    current = current.resolve()
    others = sorted((d for d in root.iterdir()
                     if d.is_dir() and not d.is_symlink() and name.fullmatch(d.name) and d.resolve() != current),
                    key=lambda d: d.name[len(repo_name) + 1:])  # the time stamp sorts oldest first
    excess = others[:max(0, len(others) - (keep - 1))]
    deleted, busy = [], []
    now = time.time()
    for d in excess:
        if d.resolve().parent != root:
            continue
        if _run_busy(d, now):
            busy.append(d.name)
            continue
        _remove_tree(d)
        deleted.append(d)
    note = f"still in use, kept: {', '.join(busy)}" if busy else ""
    return deleted, note


# A step that writes outside this machine (pushes, publishes, releases, posts to GitHub or a
# registry) never runs here: GitHub runs it. The job stops at that step as SKIPPED ("could not run
# here"). Credentials are stripped from every job as well (credential_free_env), so a command these
# patterns miss still has nothing to publish with.
_HOSTS = r"(?:api\.github\.com|uploads\.github\.com|github\.com|upload\.pypi\.org|pypi\.org|test\.pypi\.org|registry\.npmjs\.org|crates\.io)"
OUTSIDE_WRITES = [
    ("git push", r"\bgit(?:\s+-[Cc]\s+\S+|\s+-\S+)*\s+push\b"),
    ("gh release", r"\bgh\s+release\s+(?:create|upload|edit|delete)\b"),
    ("gh api write", r"\bgh\s+api\b[^\n;|&]*(?:\s(?:-X|--method)\s*(?:POST|PUT|PATCH|DELETE)\b|\s(?:-f|-F|--field|--raw-field|--input)\b)"),
    ("gh write", r"\bgh\s+(?:pr\s+(?:create|merge|comment|edit|close|review)|issue\s+(?:create|comment|edit|close)|workflow\s+run|repo\s+(?:create|edit|delete)|secret\s+set|variable\s+set)\b"),
    ("twine upload", r"\btwine\s+upload\b"),
    ("npm publish", r"\b(?:npm|pnpm|yarn)\s+(?:\S+\s+)*?publish\b"),
    ("cargo publish", r"\bcargo\s+(?:\+\S+\s+)?publish\b"),
    ("uv publish", r"\b(?:uv|poetry|maturin|flit|hatch)\s+publish\b"),
    ("docker push", r"\b(?:docker|podman)\s+(?:image\s+)?push\b"),
    ("curl write", r"\bcurl\b[^\n;|&]*(?:\s(?:-X|--request)\s*(?:POST|PUT|PATCH|DELETE)\b|\s(?:-d|--data\S*|-F|--form|-T|--upload-file)\s)[^\n;|&]*" + _HOSTS),
]
# Never passed to a step, whatever the workflow, $GITHUB_ENV or your shell says.
CREDENTIAL_ENV = {"GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN", "NPM_TOKEN",
                  "NODE_AUTH_TOKEN", "CARGO_REGISTRY_TOKEN", "UV_PUBLISH_TOKEN", "UV_PUBLISH_PASSWORD",
                  "PYPI_TOKEN", "PYPI_API_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_URL",
                  "ACTIONS_RUNTIME_TOKEN", "DOCKER_PASSWORD", "SSH_AUTH_SOCK"}
SSH_REFUSED = """#!/bin/sh
echo "ci_local: ssh is refused in a job here (nothing leaves this machine with your keys)" >&2
exit 1
"""


def outside_write(script: str) -> str | None:
    """The kind of write outside this machine a step's script makes (`git push`, `npm publish`, ...),
    or None."""
    for kind, pattern in OUTSIDE_WRITES:
        if re.search(pattern, script):
            return kind
    return None


def _npm_auth(key: str, value: str) -> bool:
    """npm's env-style auth: an npm_config_* / NPM_CONFIG_* key whose name or value carries `_auth`
    or `authToken` (`NPM_CONFIG__AUTH`, `npm_config_//registry.npmjs.org/:_authToken`)."""
    k = key.lower()
    return k.startswith("npm_config_") and any(m in text for text in (k, value.lower()) for m in ("_auth", "authtoken"))


def credential_free_env(env: dict[str, str]) -> dict[str, str]:
    """`env` without a publishing credential: the names in CREDENTIAL_ENV, TWINE_*, the
    per-registry cargo tokens, and npm's env-style auth."""
    return {k: v for k, v in env.items()
            if k not in CREDENTIAL_ENV and not k.startswith("TWINE_")
            and not (k.startswith("CARGO_REGISTRIES_") and k.endswith("_TOKEN")) and not _npm_auth(k, v)}


def git(*args: str, cwd: Path | None = None, check: bool = True, quiet: bool = False) -> str:
    cmd = ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
           "-c", "user.name=ci-local", "-c", "user.email=ci-local@localhost", *args]
    out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and out.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {(out.stderr or out.stdout).strip()}")
    return out.stdout.strip()


def sandbox_profile(home: Path, allow_write: list[Path], deny: list[Path]) -> str:
    def q(p: Path) -> str:
        return json.dumps(str(p))
    lines = [
        "(version 1)",
        "(allow default)",
        '(deny network-outbound (remote ip "localhost:8080"))',
        f"(deny file-write* (subpath {q(home)}))",
        # A sandboxed process cannot exec a setuid binary. The two read-only process inspectors run
        # outside the sandbox; the other setuid tools (su, login, crontab, at) stay refused.
        '(allow process-exec (literal "/bin/ps") (with no-sandbox))',
        '(allow process-exec (literal "/usr/bin/top") (with no-sandbox))',
    ]
    lines += [f"(allow file-write* (subpath {q(p)}))" for p in allow_write]
    lines += [f"(deny file-read* file-write* (subpath {q(p)}))" for p in deny]
    return "\n".join(lines) + "\n"


# ---- tier light (ADR 0051): docs, copy, CSS, a catalog entry, a pin bump
PRIMARY_PYTHON = "3.12"  # every repository's single-version jobs (build, docs, changelog) use it
LIGHT_DROPPED = "tier light: one Python per matrix"
_WHOLE_SUITE = {"conftest.py", "pyproject.toml", "setup.py", "setup.cfg", "pytest.ini", "tox.ini"}


def module_name(path: str) -> str | None:
    """`src/pkg/sub/mod.py` and `pkg/sub/mod.py` -> `pkg.sub.mod`; a package's `__init__.py` -> `pkg.sub`."""
    parts = Path(path).with_suffix("").parts
    if parts and parts[0] == "src":
        parts = parts[1:]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts or not all(p.isidentifier() for p in parts):
        return None
    return ".".join(parts)


def is_test_file(path: str) -> bool:
    return bool(re.search(r"(^|/)test_[^/]*\.py$", path))


TEST_DIRS = {"tests", "test", "__tests__", "__fixtures__", "fixtures"}


def is_test_material(path: str) -> bool:
    """A file under a test directory (tests/, test/, __tests__/, __fixtures__/, fixtures/) or named
    *.fixture.*: saved answers, fixtures, helpers. Tier light never asks a test to be named after it."""
    p = Path(path)
    return any(part in TEST_DIRS for part in p.parts[:-1]) or ".fixture." in p.name


def material_home(path: str, all_files: list[str]) -> str:
    """Whose suite a piece of test material belongs to, by location: the nearest folder holding a
    package manifest decides (`python` for pyproject.toml/setup.py/setup.cfg or none at all, `npm`
    for package.json, `cargo` for Cargo.toml; Python first when one folder holds several)."""
    kinds_at: dict[str, set[str]] = {}
    for f in all_files:
        q = Path(f)
        kind = {"pyproject.toml": "python", "setup.py": "python", "setup.cfg": "python",
                "package.json": "npm", "Cargo.toml": "cargo"}.get(q.name)
        if kind:
            kinds_at.setdefault(str(q.parent), set()).add(kind)
    for parent in Path(path).parents:
        kinds = kinds_at.get(str(parent))
        if kinds:
            return next(k for k in ("python", "npm", "cargo") if k in kinds)
    return "python"


def imports_module(text: str, module: str) -> bool:
    """`import pkg.mod`, `from pkg.mod import x`, `from pkg import mod` (also in parentheses)."""
    if re.search(rf"^\s*(?:import|from)\s+{re.escape(module)}(?![\w])", text, re.M):
        return True
    parent, _, leaf = module.rpartition(".")
    if not parent:
        return False
    for m in re.finditer(rf"^\s*from\s+{re.escape(parent)}\s+import\s+(\([^)]*\)|[^\n]*)", text, re.M):
        if re.search(rf"\b{re.escape(leaf)}\b", m.group(1)):
            return True
    return False


DOC_SUFFIXES = (".md", ".txt")  # README, CHANGELOG, llms*.txt: they neither select nor force tests


RUST_FILES = ((".rs",), ("Cargo.toml", "Cargo.lock"))
JS_FILES = ((".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts", ".css", ".scss", ".sass", ".less",
             ".vue", ".svelte"), ("package.json", "package-lock.json", "npm-shrinkwrap.json"))


def owner_dir(path: str, all_files: list[str]) -> str | None:
    """The crate or npm package whose own test step covers `path`, decided by the file's type: a Rust
    file (`.rs`, Cargo.toml/lock) belongs to the nearest directory holding a Cargo.toml, a JS/TS/CSS
    file (or package.json, a lockfile, tsconfig*.json) to the nearest one holding a package.json.
    Any other file (Python, YAML, JSON, shell, templates) is never owned, so a Cargo.toml or a
    package.json at the repository root cannot excuse a Python change from its pytest tests."""
    p = Path(path)
    if p.suffix in RUST_FILES[0] or p.name in RUST_FILES[1]:
        manifest = "Cargo.toml"
    elif p.suffix in JS_FILES[0] or p.name in JS_FILES[1] or re.fullmatch(r"tsconfig.*\.json", p.name):
        manifest = "package.json"
    else:
        return None
    markers = {str(Path(f).parent) for f in all_files if Path(f).name == manifest}
    for parent in p.parents:
        if str(parent) in markers:
            return str(parent)
    return None


def _name_key(text: str) -> str:
    """A file stem as the light name rule compares it: `-` and `.` read as `_` (test files are Python
    modules and cannot hold either), so `select-xcode.sh` keeps `test_select_xcode.py`."""
    return re.sub(r"[-.]", "_", text)


def light_tests(changed: list[str], all_files: list[str], read: Callable[[str], str]
                ) -> tuple[dict[str, list[str]] | None, list[str], list[str]]:
    """Tier light's pytest selection: (test file -> why, changed files no test covers, changed files
    an npm package or a crate owns).

    A test file is kept when it changed, when its name holds the name of a changed file
    (a substring match on the stem, `-` and `.` read as `_`: `model_host.py` keeps
    `test_model_host_portable.py`, `catalog.yaml` keeps `test_model_catalog.py`, `select-xcode.sh`
    keeps `test_select_xcode.py`), or, for a changed module, when it imports it.
    Every changed file that is not documentation and not owned by an npm package or a crate (see
    owner_dir: by file type, never Python) must
    keep at least one test, or it is listed as uncovered (a red light run). None instead of the
    mapping = the whole suite: a conftest.py or the package configuration changed, or test material
    (is_test_material: a fixture, a saved answer, a helper no test imports) of a Python package
    changed. Test material of an npm package or a crate is owned: its own test step runs whole.
    Test material is never uncovered. `read(path)` returns a file's text at the tested commit.
    """
    present = set(all_files)
    live = [f for f in changed if f in present and not f.endswith(DOC_SUFFIXES)]
    if any(Path(f).name in _WHOLE_SUITE for f in changed):
        return None, [], []
    tests = [f for f in all_files if is_test_file(f)]
    keep: dict[str, list[str]] = {}
    for f in live:
        if f in tests:
            keep.setdefault(f, []).append("changed")
    texts: dict[str, str] = {}
    uncovered, owned = [], []
    whole = False
    for f in live:
        if is_test_file(f):
            continue
        material = is_test_material(f)
        if material and material_home(f, all_files) != "python":
            owned.append(f)
            continue
        if material and not f.endswith(".py"):
            whole = True  # like a changed test file: its package's suite runs
            continue
        if not material and owner_dir(f, all_files) is not None:
            owned.append(f)
            continue
        stem = Path(f).stem if Path(f).stem != "__init__" else Path(f).parent.name
        module = module_name(f) if f.endswith(".py") else None
        hits = []
        for t in tests:
            if stem and _name_key(stem) in _name_key(Path(t).stem):
                hits.append((t, f"named after {f}"))
            elif module:
                if t not in texts:
                    texts[t] = read(t)
                bare = stem if "tests" in Path(f).parts else None  # a test helper, imported by its name
                if imports_module(texts[t], module) or (bare and imports_module(texts[t], bare)):
                    hits.append((t, f"imports {module}"))
        for t, why in hits:
            keep.setdefault(t, []).append(why)
        if not hits and material:
            whole = True  # a test helper no test imports by name: the whole suite, never uncovered
        elif not hits:
            uncovered.append(f)
    if whole:
        return None, [], owned
    return keep, uncovered, owned


def docs_only(changed: list[str]) -> bool:
    """A change made of documentation alone (`.md`, `.txt`): tier light runs no test for it and says so."""
    return bool(changed) and all(f.endswith(DOC_SUFFIXES) for f in changed)


def light_executed(counts_file: Path) -> int:
    """How many tests a light run executed: the pytest plugin writes each run's kept count, a
    narrowed npm / cargo test step writes 1. Zero makes a light run red, never green."""
    if not counts_file.exists():
        return 0
    return sum(int(x) for x in counts_file.read_text(encoding="utf-8").split() if x.isdigit())


def light_matrix(group: list["Job"]) -> list["Job"]:
    """The matrix entries a light run drops: all but the PRIMARY_PYTHON ones (all but the first
    when no entry uses it)."""
    if len(group) < 2:
        return []
    keep = [j for j in group if j.python == PRIMARY_PYTHON] or group[:1]
    return [j for j in group if j not in keep]


def light_step(script: str, cwd_rel: str, cwd: Path, changed: list[str]) -> tuple[str | None, str]:
    """Tier light's narrowing of one `npm test` or `cargo test` step: (new script or None to skip it,
    what was decided). Any other step is returned unchanged with an empty note."""
    line = script.strip()
    prefix = (cwd_rel.rstrip("/") + "/") if cwd_rel not in ("", ".") else ""
    # Documentation (README, CHANGELOG, llms*.txt) neither selects tests nor forces the whole run.
    here = [f for f in changed if f.startswith(prefix) and not f.endswith(DOC_SUFFIXES)]
    if line in ("npm test", "npm run test", "npm t"):
        try:
            pkg = json.loads((cwd / "package.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return script, "no package.json: npm test runs whole"
        test = str((pkg.get("scripts") or {}).get("test") or "")
        if not here:
            return None, f"npm test skipped: no change under {prefix or 'the repository'}"
        material = [f for f in here if is_test_material(f) and not f.endswith(JS_FILES[0])]
        if material:  # a fixture no import graph reaches: the package's whole suite
            return script, f"npm test runs whole: test material changed ({material[0]})"
        if re.fullmatch(r"vitest run(\s+--?[\w-]+)*", test):
            files = " ".join(shlex.quote(str(cwd / f[len(prefix):])) for f in here if (cwd / f[len(prefix):]).exists())
            if not files:
                return None, "npm test skipped: the changed files were removed"
            return f"npx vitest related --run {files}", f"vitest related to {len(here)} changed file(s)"
        workspaces = pkg.get("workspaces")
        if isinstance(workspaces, dict):
            workspaces = workspaces.get("packages")
        if isinstance(workspaces, list) and workspaces:
            dirs = [str(w).rstrip("/") for w in workspaces]
            touched = sorted({d for d in dirs for f in here if f[len(prefix):].startswith(d + "/")})
            outside = [f for f in here if not any(f[len(prefix):].startswith(d + "/") for d in dirs)]
            if outside:
                return script, f"npm test runs whole: {outside[0]} is outside every workspace"
            flags = " ".join(f"--workspace {shlex.quote(d)}" for d in touched)
            return f"npm {flags} --if-present run test", "the workspaces with changed files: " + ", ".join(touched)
        return script, "npm test runs whole (its test script is not vitest run)"
    if line.startswith("cargo test"):
        if not here:
            return None, f"cargo test skipped: no change under {prefix or 'the repository'}"
        manifest = cwd / "Cargo.toml"
        try:
            import tomllib

            cargo = tomllib.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError, ImportError):
            return script, "cargo test runs whole (Cargo.toml unreadable)"
        members = (cargo.get("workspace") or {}).get("members") or []
        if not members:
            return script, "cargo test: the crate changed"
        crates = []
        for member in members:
            mdir = str(member).rstrip("/")
            if any(f[len(prefix):].startswith(mdir + "/") for f in here):
                try:
                    crates.append(tomllib.loads((cwd / mdir / "Cargo.toml").read_text(encoding="utf-8"))["package"]["name"])
                except (OSError, ValueError, KeyError):
                    return script, f"cargo test runs whole ({mdir}/Cargo.toml unreadable)"
        if not crates:
            return script, "cargo test runs whole: a change outside every workspace member"
        args = [a for a in shlex.split(line)[2:] if a not in ("--workspace", "--all")]
        return " ".join(["cargo", "test"] + [f"-p {c}" for c in crates] + args), "cargo test -p " + ", ".join(crates)
    return script, ""


# pytest plugin for tier light: keeps the selected files' tests in the top-level pytest only (it
# takes the list out of the environment, so a nested pytest runs whole), and a run with nothing
# selected exits 0 instead of 5.
LIGHT_PLUGIN = """import json, os
_SELECTED = None
_ROOT = None


def pytest_configure(config):
    global _SELECTED, _ROOT
    raw = os.environ.pop("CI_LOCAL_LIGHT_TESTS", None)
    if raw is not None:
        _SELECTED, _ROOT = set(json.loads(raw)), os.environ.get("CI_LOCAL_LIGHT_ROOT", os.getcwd())


def pytest_collection_modifyitems(config, items):
    if _SELECTED is None:
        return
    keep, drop = [], []
    for item in items:
        rel = os.path.relpath(str(getattr(item, "path", None) or item.fspath), _ROOT)
        (keep if rel in _SELECTED else drop).append(item)
    if drop:
        config.hook.pytest_deselected(items=drop)
        items[:] = keep
    counts = os.environ.get("CI_LOCAL_LIGHT_COUNTS")
    if counts:
        with open(counts, "a", encoding="utf-8") as f:
            f.write(str(len(keep)) + "\\n")


def pytest_sessionfinish(session, exitstatus):
    if _SELECTED is not None and exitstatus == 5:
        session.exitstatus = 0
"""


# Jobs that must run alone, after everything else (the operator's one-model-at-a-time GPU rule, and
# gates that measure latency). Keyed by repository and job id; the reason is printed.
SERIAL_JOBS = {
    ("abstractcore", "local-models"): "loads local model engines (one model process at a time)",
    ("abstractgateway", "perf"): "its p99 latency gates need a quiet machine",
    # Each matrix entry installs and starts a whole gateway: separate machines on GitHub, one Mac here.
    ("abstractframework", "bootstrap-smoke"): "installs and starts a whole gateway",
}
# The fixed ports a job binds, written as literals in its steps and env (`--port 18080`,
# `http://127.0.0.1:18080`). On GitHub every job has a machine of its own; here every such job
# leases a free port of its own and the literal is rewritten in its scripts and env, so two gates
# (or two jobs) never fight over one port.
JOB_PORTS = {
    ("abstractframework", "bootstrap-smoke"): (18080,),
}
PORT_RANGE = range(28000, 29000)  # clear of the live gateway (8080) and the scratch deploys (18080, 18850)


def lease_port(lock_dir: Path, ports: range = PORT_RANGE):
    """A free TCP port on 127.0.0.1, reserved for as long as the returned file stays open: its lock
    (flock on <lock_dir>/<port>.lock) keeps every other gate and job off it, and the OS releases it
    when this process ends. A port something already listens on is skipped. Returns (port, file)."""
    lock_dir.mkdir(parents=True, exist_ok=True)
    for port in ports:
        f = open(lock_dir / f"{port}.lock", "a", encoding="utf-8")
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            f.close()
            continue
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                f.close()
                continue
        return port, f
    raise RuntimeError(f"no free port in {ports.start}-{ports.stop - 1}")


def rewrite_ports(text: str, ports: dict[int, int]) -> str:
    """The job's fixed ports replaced by its leased ones, as whole numbers only (18080, not 180800)."""
    for fixed, leased in ports.items():
        text = re.sub(rf"(?<!\d){fixed}(?!\d)", str(leased), text)
    return text
MEMORY_PER_JOB = 4 * 1024**3  # what one job may hold (a test suite with torch imported, a cargo build)


def runs_cargo(job: "Job") -> bool:
    """A job whose steps run cargo or install a Rust toolchain (dtolnay/rust-toolchain)."""
    steps = job.spec.get("steps")
    for step in (steps if isinstance(steps, list) else []):
        if not isinstance(step, dict):
            continue
        if "rust-toolchain" in str(step.get("uses") or ""):
            return True
        if re.search(r"(?<![\w-])cargo\s", str(step.get("run") or "")):
            return True
    return False


def serial_reason(repo_name: str, job: "Job") -> str | None:
    listed = SERIAL_JOBS.get((repo_name, job.job_id))
    if listed:
        return listed
    if runs_cargo(job):
        # Every job of a repository builds into ONE Rust folder (cargo_target_dir): two cargo jobs at once
        # made rustdoc lose its dependency rlibs ("can't find crate" in doctests) and once got a test
        # process killed (2026-11-07, abstractgateway console-tui).
        return "runs cargo in the repository's shared Rust build folder"
    return None


def run_scheduled(items: list, key_of: Callable, needs_of: Callable, serial_of: Callable, workers: int,
                  fn: Callable) -> None:
    """Run fn(item) for every item, each after every item of the keys it needs.

    Phase 1: the items outside any serial chain, on a pool of `workers`, queued by depth in the needs
    graph (a waiting item holds a worker; FIFO by depth means what it waits for has already started,
    so the pool cannot deadlock). Phase 2: the serial items and everything that needs them, one at a
    time, alone, in needs order.
    """
    keys = list(dict.fromkeys(key_of(i) for i in items))
    needs = {}
    for i in items:
        needs.setdefault(key_of(i), needs_of(i))
    late = {key_of(i) for i in items if serial_of(i)}
    grew = True
    while grew:
        grew = False
        for k in keys:
            if k not in late and any(n in late for n in needs[k]):
                late.add(k)
                grew = True
    depth: dict = {}

    def depth_of(k, seen=()):
        if k not in depth:
            if k in seen:
                raise RuntimeError(f"needs cycle at {k}")
            depth[k] = 1 + max((depth_of(n, seen + (k,)) for n in needs.get(k, [])), default=-1)
        return depth[k]

    left = {k: 0 for k in keys}
    for i in items:
        left[key_of(i)] += 1
    done = {k: threading.Event() for k in keys}
    lock = threading.Lock()

    def one(item) -> None:
        k = key_of(item)
        try:
            for n in needs[k]:
                done[n].wait()
            fn(item)
        finally:
            with lock:
                left[k] -= 1
                if left[k] == 0:
                    done[k].set()

    early = sorted((i for i in items if key_of(i) not in late), key=lambda i: depth_of(key_of(i)))
    if workers <= 1:
        for i in early:
            one(i)
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for f in [pool.submit(one, i) for i in early]:
                f.result()
    for i in sorted((i for i in items if key_of(i) in late), key=lambda i: depth_of(key_of(i))):
        one(i)


def available_memory() -> int | None:
    """Free + inactive + speculative pages (what macOS can hand out without swapping)."""
    try:
        out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=10).stdout
    except OSError:
        return None
    m = re.search(r"page size of (\d+) bytes", out)
    page = int(m.group(1)) if m else 16384
    pages = 0
    for name in ("Pages free", "Pages inactive", "Pages speculative"):
        m = re.search(rf"{name}:\s+(\d+)", out)
        pages += int(m.group(1)) if m else 0
    return pages * page if pages else None


def default_jobs(runnable: int, physical_cores: int | None, memory: int | None) -> tuple[int, str]:
    """min(runnable jobs, max(1, physical cores // 4)), capped by free memory / MEMORY_PER_JOB."""
    by_cores = max(1, (physical_cores or 4) // 4)
    n = min(max(1, runnable), by_cores)
    why = f"{physical_cores} physical cores // 4 = {by_cores}, {runnable} jobs"
    if memory is not None:
        by_memory = max(1, memory // MEMORY_PER_JOB)
        n = min(n, by_memory)
        why += f", {memory / 1024**3:.0f} GiB free / {MEMORY_PER_JOB // 1024**3} GiB per job = {by_memory}"
    return n, why


def physical_cores() -> int | None:
    try:
        return int(subprocess.run(["sysctl", "-n", "hw.physicalcpu"], capture_output=True, text=True).stdout.strip())
    except (OSError, ValueError):
        return None


class Runner:
    def __init__(self, args: argparse.Namespace, repo: Path, workspace: Path):
        self.args = args
        self.repo = repo
        self.workspace = workspace
        self.lock = threading.Lock()
        self.uv = UV
        self.real_home = Path.home()
        self.job_counter = 0
        self.jobs_completed = False  # set once run_all returns: the one point --keep-runs may delete
        self.inputs: dict[str, Any] = {}
        for item in args.input or []:
            key, _, value = item.partition("=")
            self.inputs[key] = {"true": True, "false": False}.get(value.lower(), value)

    def say(self, text: str) -> None:
        with self.lock:
            print(text, flush=True)

    def read_file(self, path: str) -> str:
        return git("show", f"{self.tested}:{path}", cwd=self.src, check=False)

    @property
    def repo_name(self) -> str:
        if not hasattr(self, "_repo_name"):
            origin = git("remote", "get-url", "origin", cwd=self.repo, check=False)
            fallback = self.repo.name if self.repo != self.workspace else "abstractframework"
            self._repo_name = repo_name_from(origin, fallback)
        return self._repo_name

    # ---- the commit under test: the head, merged into the base the way GitHub merges a pull request
    def prepare_source(self) -> None:
        a = self.args
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.head = git("rev-parse", "--verify", f"{a.ref}^{{commit}}", cwd=self.repo)
        self.run_dir = Path(a.work or SCRATCH / "runs").expanduser().resolve() / (
            f"{self.repo_name}-{stamp}-{self.head[:8]}"
        )
        self.run_dir.mkdir(parents=True, exist_ok=False)
        # Held while this gate runs: --keep-runs in another gate never deletes a run in progress.
        self._run_lock = open(self.run_dir / RUN_LOCK, "w", encoding="utf-8")
        fcntl.flock(self._run_lock, fcntl.LOCK_EX)
        self.origin_url = git("remote", "get-url", "origin", cwd=self.repo, check=False)
        m = re.search(r"github\.com[:/]+([^/]+/[^/]+?)(?:\.git)?/?$", self.origin_url or "")
        self.repository = m.group(1) if m else f"local/{self.repo_name}"
        src = self.run_dir / "src.git"
        git("clone", "-q", "--bare", "--shared", str(self.repo), str(src))
        if a.base_sha:
            self.base_sha = git("rev-parse", "--verify", f"{a.base_sha}^{{commit}}", cwd=src)
        else:
            if not self.origin_url:
                raise RuntimeError("the repository has no origin remote; pass --base-sha")
            git("fetch", "-q", "--no-tags", self.origin_url, f"+refs/heads/{a.base}:refs/ci-local/base", cwd=src)
            self.base_sha = git("rev-parse", "refs/ci-local/base", cwd=src)
        git("update-ref", f"refs/heads/{a.base}", self.base_sha, cwd=src)
        self.tested, self.merged = self.head, False
        head_in_base = subprocess.run(["git", "merge-base", "--is-ancestor", self.head, self.base_sha], cwd=src).returncode == 0
        if head_in_base and not a.no_merge and a.event != "push":
            self.tested = self.base_sha  # already in the base: merging it changes nothing
        elif not a.no_merge and a.event != "push":
            # GitHub tests a pull request on refs/pull/N/merge (the head merged into the base), and
            # merging the branch puts that same tree on the base branch.
            out = subprocess.run(["git", "merge-tree", "--write-tree", self.base_sha, self.head],
                                 cwd=src, capture_output=True, text=True)
            if out.returncode != 0:
                raise RuntimeError(
                    f"{self.head[:12]} does not merge cleanly into {a.base} ({self.base_sha[:12]}); "
                    "GitHub runs no pull-request CI on a conflicting branch: merge the base in first"
                )
            tree = out.stdout.split()[0]
            self.tested = git("commit-tree", tree, "-p", self.base_sha, "-p", self.head,
                              "-m", f"Merge {self.head[:12]} into {a.base}", cwd=src)
            self.merged = True
        git("update-ref", "refs/heads/ci-local-head", self.tested, cwd=src)
        self.src = src
        diff_from = a.before or git("merge-base", self.base_sha, self.head, cwd=src)
        self.changed = git("diff", "--name-only", diff_from, self.head, cwd=src).splitlines()
        self.all_files = git("ls-tree", "-r", "--name-only", self.tested, cwd=src).splitlines()
        wf_dir = self.run_dir / "workflows"
        wf_dir.mkdir()
        listing = git("ls-tree", "--name-only", f"{self.tested}:.github/workflows", cwd=src, check=False)
        self.workflow_files = []
        for name in sorted(listing.splitlines()):
            if name.endswith((".yml", ".yaml")):
                text = git("show", f"{self.tested}:.github/workflows/{name}", cwd=src)
                (wf_dir / name).write_text(text + "\n", encoding="utf-8")
                self.workflow_files.append(wf_dir / name)

    # ---- contexts
    def github_ctx(self, wf_name: str, job_id: str, workspace: Path, event_name: str, ref: str) -> dict:
        a = self.args
        owner = self.repository.split("/")[0]
        event: dict[str, Any] = {"inputs": {k: to_str(v) for k, v in self.inputs.items()} or None}
        if event_name == "pull_request":
            event["pull_request"] = {
                "number": 0,
                "base": {"ref": a.base, "sha": self.base_sha},
                "head": {"ref": a.branch or "ci-local", "sha": self.head},
            }
        else:
            event.update({"before": a.before or self.base_sha, "after": self.tested, "ref": ref})
        return {
            "event_name": event_name,
            "event": event,
            "ref": ref,
            "ref_name": "0/merge" if event_name == "pull_request" else ref.split("/", 2)[-1],
            "ref_type": "tag" if ref.startswith("refs/tags/") else "branch",
            "head_ref": (a.branch or "ci-local") if event_name == "pull_request" else "",
            "base_ref": a.base if event_name == "pull_request" else "",
            "sha": self.tested,
            "repository": self.repository,
            "repository_owner": owner,
            "actor": owner,
            "triggering_actor": owner,
            "workflow": wf_name,
            "job": job_id,
            "run_id": "0",
            "run_number": "1",
            "run_attempt": "1",
            "server_url": "https://github.com",
            "api_url": "https://api.github.com",
            "workspace": str(workspace),
            "token": "",
            "action": "",
        }

    def runs_for(self, on: Any) -> list[tuple[str, str]]:
        """The (event, github.ref) runs of one workflow; empty when nothing triggers it."""
        a = self.args
        main_ref = f"refs/heads/{a.base}"
        pr_ref = "refs/pull/0/merge"
        runs: list[tuple[str, str]] = []
        if a.event == "auto":
            if triggered(on, "push", main_ref, a.base, self.changed)[0]:
                runs.append(("push", main_ref))
            elif triggered(on, "pull_request", pr_ref, a.base, self.changed)[0]:
                runs.append(("pull_request", pr_ref))
        elif a.event == "pull_request":
            if triggered(on, "pull_request", pr_ref, a.base, self.changed)[0]:
                runs.append(("pull_request", pr_ref))
        else:
            ref = a.git_ref or f"refs/heads/{a.branch or a.base}"
            if triggered(on, "push", ref, a.base, self.changed)[0]:
                runs.append(("push", ref))
        for tag in a.release_tag or []:
            ref = f"refs/tags/{tag}"
            if triggered(on, "push", ref, a.base, self.changed)[0]:
                runs.append(("push", ref))
        return runs

    # ---- planning
    def plan(self) -> list[list[Job]]:
        import yaml  # provided by scripts/ci_local.sh

        groups: list[list[Job]] = []
        self.untriggered: list[str] = []
        self.triggered: list[str] = []
        self.prechecks, self.precheck_notes = 0, []
        for path in self.workflow_files:
            wf = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if True in wf and "on" not in wf:  # YAML 1.1 reads `on:` as true
                wf["on"] = wf.pop(True)
            name = str(wf.get("name") or path.name)
            runs = self.runs_for(wf.get("on"))
            if not runs:
                self.untriggered.append(path.name)
                continue
            jobs = wf.get("jobs") or {}
            for event_name, ref in runs:
                tag = ref.split("/", 2)[2] if ref.startswith("refs/tags/") else ""
                self.triggered.append(f"{path.name} as {'tag ' + tag if tag else event_name + (' to ' + self.args.base if event_name == 'push' else '')}")
                for job_id in self._order(jobs):
                    spec = jobs[job_id] or {}
                    base_ctx = Context({
                        "github": self.github_ctx(name, job_id, Path("/"), event_name, ref),
                        "env": dict(wf.get("env") or {}), "inputs": dict(self.inputs), "vars": {}, "secrets": {},
                        "needs": {}, "strategy": {}, "matrix": {},
                        "runner": {"os": "macOS", "arch": "ARM64", "name": "ci-local", "temp": "", "tool_cache": ""},
                    })
                    group = []
                    for i, combo in enumerate(expand_matrix(spec.get("strategy"), base_ctx)):
                        ctx = base_ctx.child(matrix=combo)
                        label = to_str(interpolate(spec.get("name"), ctx)) if spec.get("name") else job_id
                        if not spec.get("name") and combo:
                            label += " (" + ", ".join(to_str(v) for v in combo.values()) + ")"
                        prefix = f"{path.stem}@{tag}" if tag else path.stem
                        job = Job(name, path.name, wf, job_id, spec, combo, f"{prefix}/{label}", i,
                                  event=event_name, git_ref=ref)
                        job.python = setup_python_version(job, ctx)
                        group.append(job)
                    groups.append(group)
                    reduced, refused = precheck_spec(spec) if tag else (None, "")
                    if refused:
                        self.precheck_notes.append(f"no pre-check for {group[0].label}: {refused}")
                    if reduced is not None:
                        self.prechecks += 1
                        first = group[0]
                        pre = Job(name, path.name, wf, job_id + PRECHECK_SUFFIX, reduced, first.matrix,
                                  f"{first.label.split('/', 1)[0]}/pre-check: {first.label.split('/', 1)[-1]}", 0,
                                  event=event_name, git_ref=ref)
                        pre.python = first.python
                        groups.append([pre])
        return groups

    @staticmethod
    def _order(jobs: dict) -> list[str]:
        done: list[str] = []
        visiting: set[str] = set()

        def visit(j: str) -> None:
            if j in done:
                return
            if j in visiting:
                raise RuntimeError(f"needs cycle at {j}")
            visiting.add(j)
            for n in _as_list((jobs[j] or {}).get("needs")):
                if n not in jobs:
                    raise RuntimeError(f"job {j} needs unknown job {n}")
                visit(n)
            visiting.discard(j)
            done.append(j)

        for j in jobs:
            visit(j)
        return done

    @staticmethod
    def _key(job: Job, job_id: str | None = None) -> tuple[str, str, str]:
        return (job.wf_file, job.git_ref, job_id or job.job_id)

    # ---- execution
    def run_all(self, groups: list[list[Job]]) -> list[Job]:
        """Every job instance (each matrix entry) is one task; see run_scheduled."""
        selected = self._selection(groups)
        by_key = {self._key(g[0]): g for g in groups}
        items = [j for g in groups for j in g]
        workers = self.args.parallel

        def run(job: Job) -> None:
            if self._key(job) not in selected:
                job.result = "NOT-SELECTED"
            else:
                self.run_job(job, by_key)

        run_scheduled(
            items,
            key_of=self._key,
            needs_of=lambda j: [self._key(j, n) for n in _as_list(j.spec.get("needs"))],
            serial_of=lambda j: serial_reason(self.repo_name, j) is not None,
            workers=workers,
            fn=run,
        )
        return items

    def _selection(self, groups: list[list[Job]]) -> set[tuple[str, str, str]]:
        keys = {self._key(g[0]) for g in groups}
        if not self.args.job:
            return keys
        chosen: set[tuple[str, str, str]] = set()
        for want in self.args.job:
            hits = [k for k in keys if want in (k[2], f"{Path(k[0]).stem}:{k[2]}")]
            if not hits:
                raise SystemExit(f"ci_local: no triggered job named {want!r}; jobs: "
                                 + ", ".join(sorted({f"{Path(k[0]).stem}:{k[2]}" for k in keys})))
            chosen |= set(hits)
        # A release tag's pure checks always run, whatever --job selects.
        chosen |= {k for k in keys if k[2].endswith(PRECHECK_SUFFIX)}
        spec = {self._key(g[0]): g[0].spec for g in groups}
        stack = list(chosen)
        while stack:
            wf, ref, j = stack.pop()
            for n in _as_list(spec[(wf, ref, j)].get("needs")):
                if (wf, ref, n) not in chosen:
                    chosen.add((wf, ref, n))
                    stack.append((wf, ref, n))
        return chosen

    @staticmethod
    def _aggregate(g: list[Job]) -> str:
        results = [j.result for j in g if j.reason != LIGHT_DROPPED]
        if any(r in ("FAIL", "ERROR") for r in results):
            return "failure"
        if any(r in ("SKIPPED", "NOT-SELECTED") for r in results):
            return "unrunnable"
        if all(r in ("NOT-TRIGGERED", SKIPPED_BY_NEEDS) for r in results):
            return "skipped"
        return "success"

    def finish(self, job: Job, result: str, reason: str = "", started: float | None = None) -> None:
        job.result, job.reason = result, reason
        if started is not None:
            job.seconds = time.monotonic() - started
        text = verdict_line(job)
        if result in ("FAIL", "ERROR") and job.log and job.log.exists():
            tail = job.log.read_text(encoding="utf-8", errors="replace").splitlines()[-self.args.tail:]
            text += "\n" + "\n".join("    | " + line for line in tail)
        self.say(text)

    def run_job(self, job: Job, by_key: dict) -> None:
        a = self.args
        needs_ctx = {}
        for n in _as_list(job.spec.get("needs")):
            g = by_key[self._key(job, n)]
            agg = self._aggregate(g)
            if agg == "unrunnable":
                return self.finish(job, "SKIPPED", f"needs {n}, which did not run in full here")
            outputs: dict = {}
            for j in g:
                outputs.update(j.outputs)
            needs_ctx[n] = {"result": agg, "outputs": outputs}

        def job_status(name: str) -> bool:
            results = [v["result"] for v in needs_ctx.values()]
            if name == "always":
                return True
            if name == "cancelled":
                return False
            if name == "failure":
                return "failure" in results
            return all(r == "success" for r in results)

        with self.lock:
            self.job_counter += 1
            number = self.job_counter
        jobdir = self.run_dir / "jobs" / job_dir_name(number, job.label)
        jobdir.mkdir(parents=True)
        job.log = jobdir / "log.txt"
        home, tmp, rtemp = jobdir / "home", jobdir / "tmp", jobdir / "runner-temp"
        for d in (home, tmp, rtemp, jobdir / "steps", jobdir / "shims"):
            d.mkdir()
        workspace = jobdir / "work" / self.repo_name
        workspace.mkdir(parents=True)

        github = self.github_ctx(job.workflow, job.job_id, workspace, job.event, job.git_ref)
        runner = {"os": "macOS", "arch": "ARM64", "name": "ci-local", "temp": str(rtemp), "tool_cache": str(jobdir / "toolcache")}
        ctx = Context(
            {"github": github, "env": {}, "inputs": dict(self.inputs), "vars": {}, "secrets": {}, "matrix": job.matrix,
             "needs": needs_ctx, "strategy": {"fail-fast": True, "job-index": job.index}, "runner": runner,
             "steps": {}, "job": {"status": "success"}},
            job_status,
        )
        try:
            ok = condition(job.spec.get("if"), ctx)
        except ExprError as exc:
            return self.finish(job, "ERROR", f"if: {exc}")
        if not ok:
            blocked = [n for n in _as_list(job.spec.get("needs"))
                       if any(j.result in RED_RESULTS for j in by_key[self._key(job, n)])]
            if blocked:  # never silently absent: what this job checks went unchecked
                return self.finish(job, SKIPPED_BY_NEEDS, "did not run: its needs failed (" + ", ".join(blocked) + ")")
            return self.finish(job, "NOT-TRIGGERED", f"if: {job.spec.get('if') or 'success()'} is false")

        can_run, note = runner_verdict(interpolate(job.spec.get("runs-on"), ctx), a.runner_label or [])
        if not can_run:
            return self.finish(job, "SKIPPED", note)
        job.host_note = note
        skip = static_skip(job)
        if skip:
            return self.finish(job, *skip)
        if job.reason == LIGHT_DROPPED:
            return self.finish(job, "NOT-SELECTED", LIGHT_DROPPED)
        if a.python:
            want = setup_python_version(job, ctx)
            if want is not None and want not in a.python:
                return self.finish(job, "NOT-SELECTED", f"Python {want} is not in --python")

        self.say(f"{'..':<13} {'':>7}  {job.label}  [{note}]")
        started = time.monotonic()
        try:
            result, reason = self._steps(job, ctx, jobdir, workspace, home, tmp, rtemp)
        except (ExprError, RuntimeError, OSError) as exc:
            result, reason = "ERROR", f"{type(exc).__name__}: {exc}"
        try:  # a finished job keeps its logs and executables, not its Rust build output
            notes = clean_rust_builds(jobdir, self.run_dir)
        except OSError as exc:
            notes = [f"ci_local: could not remove a Rust build folder: {exc}"]
        if notes:
            with open(job.log, "a", encoding="utf-8") as log:
                log.write("\n" + "\n".join(notes) + "\n")
        self.finish(job, result, reason, started)

    def _base_env(self, job: Job, jobdir: Path, workspace: Path, home: Path, tmp: Path, rtemp: Path,
                  github: dict, target: Path) -> dict[str, str]:
        rh = self.real_home
        env = {
            "HOME": str(home), "TMPDIR": str(tmp) + "/", "USER": os.environ.get("USER", "runner"),
            "LOGNAME": os.environ.get("LOGNAME", "runner"), "LANG": "en_US.UTF-8", "TERM": "dumb", "SHELL": "/bin/bash",
            "CI": "true", "GITHUB_ACTIONS": "true", "RUNNER_OS": "macOS", "RUNNER_ARCH": "ARM64",
            "RUNNER_NAME": "ci-local", "RUNNER_TEMP": str(rtemp), "RUNNER_TOOL_CACHE": str(jobdir / "toolcache"),
            "GITHUB_WORKSPACE": str(workspace), "GITHUB_EVENT_NAME": github["event_name"], "GITHUB_SHA": github["sha"],
            "GITHUB_REF": github["ref"], "GITHUB_REF_NAME": github["ref_name"], "GITHUB_REF_TYPE": github["ref_type"],
            "GITHUB_HEAD_REF": github["head_ref"], "GITHUB_BASE_REF": github["base_ref"],
            "GITHUB_REPOSITORY": github["repository"], "GITHUB_REPOSITORY_OWNER": github["repository_owner"],
            "GITHUB_ACTOR": github["actor"], "GITHUB_WORKFLOW": github["workflow"], "GITHUB_JOB": github["job"],
            "GITHUB_RUN_ID": "0", "GITHUB_RUN_NUMBER": "1", "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_SERVER_URL": "https://github.com", "GITHUB_API_URL": "https://api.github.com",
            "GITHUB_EVENT_PATH": str(jobdir / "event.json"),
            # Download caches shared across runs (actions/cache plays this part on GitHub).
            "UV_CACHE_DIR": str(rh / ".cache" / "uv"), "PIP_CACHE_DIR": str(rh / "Library" / "Caches" / "pip"),
            "npm_config_cache": str(rh / ".npm"), "PLAYWRIGHT_BROWSERS_PATH": str(rh / "Library" / "Caches" / "ms-playwright"),
            # A CARGO_HOME of the job's own: the download caches are linked in, ~/.cargo/credentials.toml is not.
            "CARGO_HOME": str(jobdir / "cargo-home"), "RUSTUP_HOME": str(rh / ".rustup"), "CARGO_TARGET_DIR": str(target),
            # No credential reaches a step: HOME is the job's own (no ~/.netrc, ~/.config/gh, ~/.npmrc,
            # ~/.pypirc, ~/.docker); git reads no system config (Xcode's osxkeychain helper) and asks no
            # helper or terminal; ssh is refused (it reads your real ~/.ssh whatever HOME says);
            # Python's keyring (twine) sees no Keychain.
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "credential.helper",
            "GIT_CONFIG_VALUE_0": "", "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never",
            "GIT_SSH_COMMAND": str(jobdir / "shims" / "ssh-refused"),
            "PYTHON_KEYRING_BACKEND": "keyring.backends.null.Keyring",
            # uv pip as pip: best match across indexes, and pip's tolerance of wheels whose zip headers
            # disagree with their contents (llama.cpp's macOS CPU wheel; pip installs it, uv refuses).
            # manual: uv never fetches a Python on its own, but an explicit `uv python install` (the
            # one-line installer's own step, which bootstrap-smoke runs) works as on a GitHub runner.
            "UV_LINK_MODE": "clone", "UV_PYTHON_DOWNLOADS": "manual", "UV_INDEX_STRATEGY": "unsafe-best-match",
            "UV_INSECURE_NO_ZIP_VALIDATION": "1",
            "CI_LOCAL_JOB_DIR": str(jobdir),
        }
        (jobdir / "event.json").write_text(json.dumps(github["event"], indent=2), encoding="utf-8")
        return env

    def _steps(self, job: Job, ctx: Context, jobdir: Path, workspace: Path, home: Path, tmp: Path, rtemp: Path) -> tuple[str, str]:
        a = self.args
        rh = self.real_home
        target = cargo_target_dir(self.repo_name)
        target.mkdir(parents=True, exist_ok=True)
        env = self._base_env(job, jobdir, workspace, home, tmp, rtemp, ctx.data["github"], target)
        shims = jobdir / "shims"
        for tool in ("sudo", "apt-get", "apt"):
            (shims / tool).write_text(ROOT_SHIM, encoding="utf-8")
            (shims / tool).chmod(0o755)
        for tool in ("ssh", "ssh-refused"):
            (shims / tool).write_text(SSH_REFUSED, encoding="utf-8")
            (shims / tool).chmod(0o755)
        cargo_home = jobdir / "cargo-home"
        cargo_home.mkdir()
        for part in ("registry", "git", "bin"):  # caches and installed tools; never credentials or config
            (rh / ".cargo" / part).mkdir(parents=True, exist_ok=True)
            (cargo_home / part).symlink_to(rh / ".cargo" / part)
        rust_bin = jobdir / "rust-bin"
        rust_bin.mkdir()
        for tool in RUST_TOOLS:
            real = rh / ".cargo" / "bin" / tool
            if real.exists():
                (rust_bin / tool).symlink_to(real)
        prefix_path: list[str] = []  # setup-python / setup-node / $GITHUB_PATH
        node_dir = image_node()
        image_bin = [str(node_dir)] if node_dir else []
        allow = [self.run_dir, target, rh / ".cache" / "uv", rh / "Library" / "Caches" / "pip", rh / ".npm",
                 rh / ".cargo" / "registry", rh / ".cargo" / "git", rh / ".rustup" / "tmp",
                 rh / "Library" / "Caches" / "ms-playwright"]
        deny = [rh / ".abstractcore", self.workspace / "runtime"]
        profile = jobdir / "sandbox.sb"
        profile.write_text(sandbox_profile(rh, allow, deny), encoding="utf-8")

        defaults = dict(((job.wf.get("defaults") or {}).get("run") or {}))
        defaults.update(((job.spec.get("defaults") or {}).get("run") or {}))
        wf_env = {k: to_str(interpolate(v, ctx)) for k, v in (job.wf.get("env") or {}).items()}
        env.update(wf_env)
        ctx.data["env"] = dict(wf_env)
        job_env = {k: to_str(interpolate(v, ctx)) for k, v in (job.spec.get("env") or {}).items()}
        env.update(job_env)
        ctx.data["env"].update(job_env)
        leases, ports = [], {}
        for fixed in JOB_PORTS.get((self.repo_name, job.job_id), ()):
            port, lease = lease_port(SCRATCH / "ports")
            leases.append(lease)
            ports[fixed] = port
        if ports:  # the workflow's and the job's env only: the gate's own (GITHUB_SHA, HOME, ...) never
            for k in {**wf_env, **job_env}:
                env[k] = rewrite_ports(env[k], ports)
            ctx.data["env"] = {k: rewrite_ports(v, ports) for k, v in ctx.data["env"].items()}
        steps_ctx: dict[str, dict] = {}
        ctx.data["steps"] = steps_ctx
        failed = [False]

        def step_status(name: str) -> bool:
            if name == "always":
                return True
            if name == "cancelled":
                return False
            if name == "failure":
                return failed[0]
            return not failed[0]

        sctx = Context(ctx.data, step_status)
        pgids: list[int] = []
        job_deadline = time.monotonic() + 60 * float(_num(interpolate(job.spec.get("timeout-minutes"), sctx)) or 360)
        first_failure = ""
        log = open(job.log, "w", encoding="utf-8")
        log.write(f"ci_local: job {job.label} ({Path(job.wf_file).name}: {job.job_id}); folder {jobdir}\n")
        for fixed, port in ports.items():
            log.write(f"ci_local: port {fixed} is {port} in this job (its own, as on a GitHub machine)\n")
        try:
            for n, step in enumerate(job.spec.get("steps") or [], 1):
                name = step.get("name") or (f"Run {step['uses']}" if step.get("uses") else
                                            "Run " + (str(step.get("run") or "").strip().splitlines() or [""])[0])
                name = to_str(interpolate(name, sctx))
                sid = str(step.get("id") or f"__step{n}")
                if not condition(step.get("if"), sctx):
                    steps_ctx[sid] = {"outcome": "skipped", "conclusion": "skipped", "outputs": {}}
                    log.write(f"\n=== step {n}: {name} (skipped: if)\n")
                    continue
                senv = sctx.child(env=dict(ctx.data["env"]))
                step_env = dict(env)
                for k, v in (step.get("env") or {}).items():
                    step_env[k] = rewrite_ports(to_str(interpolate(v, senv)), ports)
                    senv.data["env"][k] = step_env[k]
                log.write(f"\n=== step {n}: {name}\n")
                log.flush()
                outcome, outputs = "success", {}
                if step.get("uses"):
                    res = self._action(step, senv, workspace, env, prefix_path, log, jobdir)
                    if res[0] == "SKIPPED":
                        return res
                    if res[0] == "FAIL":
                        outcome = "failure"
                        first_failure = first_failure or f"step {name!r}: {res[1]}"
                else:
                    shell = step.get("shell") or defaults.get("shell")
                    script = rewrite_ports(to_str(interpolate(step.get("run") or "", senv)), ports)
                    wd = step.get("working-directory") or defaults.get("working-directory")
                    cwd_rel = to_str(interpolate(wd, senv)) if wd else ""
                    if a.tier == "light":
                        here = (workspace / cwd_rel).resolve()
                        root = next((d for d in [here, *here.parents] if (d / ".git").exists()), workspace)
                        narrowed, note = light_step(script, os.path.relpath(here, root), here, self.changed)
                        if note:
                            log.write(f"ci_local: tier light: {note}\n")
                            self.say(f"{'':<13} {'':>7}  {job.label}: tier light: {note}")
                        if narrowed is None:
                            steps_ctx[sid] = {"outcome": "skipped", "conclusion": "skipped", "outputs": {}}
                            continue
                        if note:  # an npm / cargo test step that runs
                            with self.lock, open(self.run_dir / "light-counts", "a", encoding="utf-8") as f:
                                f.write("1\n")
                        script = narrowed
                    write = outside_write(script)
                    if write:
                        log.write(f"ci_local: not run: the step writes outside this machine ({write})\n")
                        return "SKIPPED", f"step {name!r} writes outside this machine ({write}); GitHub runs it"
                    if a.installer == "uv":
                        script = translate_pip(script, self.uv)
                    script_path = jobdir / "steps" / f"{n:02d}.sh"
                    script_path.write_text(script + "\n", encoding="utf-8")
                    argv = shell_command(shell, str(script_path))
                    if argv is None:
                        return "SKIPPED", f"step {name!r} needs {shell} (a Windows shell)"
                    cwd = workspace / cwd_rel if cwd_rel else workspace
                    files = {k: jobdir / "steps" / f"{n:02d}.{k.lower()}"
                             for k in ("GITHUB_ENV", "GITHUB_OUTPUT", "GITHUB_PATH", "GITHUB_STEP_SUMMARY")}
                    for f in files.values():
                        f.touch()
                    step_env.update({k: str(v) for k, v in files.items()})
                    step_env["PATH"] = ":".join([str(shims)] + prefix_path + [str(rust_bin)] + image_bin + SYSTEM_PATH)
                    if a.tier == "light" and self.light_tests is not None:
                        plugin_dir = jobdir / "light-plugin"
                        plugin_dir.mkdir(exist_ok=True)
                        (plugin_dir / "ci_local_light.py").write_text(LIGHT_PLUGIN, encoding="utf-8")
                        step_env["PYTHONPATH"] = ":".join(x for x in (str(plugin_dir), step_env.get("PYTHONPATH", "")) if x)
                        step_env["PYTEST_ADDOPTS"] = " ".join(x for x in ("-p ci_local_light", step_env.get("PYTEST_ADDOPTS", "")) if x)
                        step_env["CI_LOCAL_LIGHT_TESTS"] = json.dumps(self.light_tests)
                        step_env["CI_LOCAL_LIGHT_ROOT"] = str(workspace)
                        step_env["CI_LOCAL_LIGHT_COUNTS"] = str(self.run_dir / "light-counts")
                    limit = job_deadline - time.monotonic()
                    if step.get("timeout-minutes"):
                        limit = min(limit, 60 * _num(interpolate(step.get("timeout-minutes"), senv)))
                    wrap = ["sandbox-exec", "-f", str(profile)] if a.sandbox else []
                    code, why = self._exec([*wrap, *argv], cwd, credential_free_env(step_env), log, limit, pgids)
                    if (jobdir / "needs-root").exists():
                        cmd = (jobdir / "needs-root").read_text(encoding="utf-8").splitlines()[0]
                        return "SKIPPED", f"step {name!r} needs root on a Linux runner ({cmd})"
                    if code != 0:
                        outcome = "failure"
                        first_failure = first_failure or f"step {name!r} {why or f'exited {code}'}"
                    for k, v in parse_env_file(files["GITHUB_ENV"]).items():
                        env[k] = v
                        ctx.data["env"][k] = v
                    for line in files["GITHUB_PATH"].read_text(encoding="utf-8").splitlines():
                        if line.strip():
                            prefix_path.insert(0, line.strip())
                    outputs = parse_env_file(files["GITHUB_OUTPUT"])
                coe = truthy(interpolate(step.get("continue-on-error"), senv)) if step.get("continue-on-error") else False
                conclusion = "success" if outcome == "success" or coe else "failure"
                steps_ctx[sid] = {"outcome": outcome, "conclusion": conclusion, "outputs": outputs}
                if conclusion == "failure":
                    failed[0] = True
                    ctx.data["job"]["status"] = "failure"
        finally:
            for pg in pgids:  # GitHub ends a job's leftover processes when the job ends
                try:
                    os.killpg(pg, signal.SIGTERM)
                except (ProcessLookupError, PermissionError):
                    pass
            for lease in leases:  # the job's ports go back to the pool
                lease.close()
            log.close()
        for k, v in (job.spec.get("outputs") or {}).items():
            job.outputs[k] = to_str(interpolate(v, sctx))
        if failed[0]:
            return "FAIL", first_failure
        return "PASS", ""

    def _exec(self, argv: list[str], cwd: Path, env: dict, log, limit: float, pgids: list[int]) -> tuple[int, str]:
        if not cwd.is_dir():
            log.write(f"ci_local: working directory {cwd} does not exist\n")
            return 1, f"(working-directory {cwd.name} does not exist)"
        if limit <= 0:
            return 1, "timed out (job timeout-minutes)"
        log.flush()
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=log,
                                stderr=subprocess.STDOUT, start_new_session=True)
        pgids.append(proc.pid)
        try:
            return proc.wait(timeout=limit), ""
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            return 124, f"timed out after {limit / 60:.0f} min"

    def _action(self, step: dict, ctx: Context, workspace: Path, env: dict, prefix_path: list[str], log,
                jobdir: Path) -> tuple[str, str]:
        uses = step["uses"]
        name = action_name(uses)
        rev = uses.split("@", 1)[1] if "@" in uses else ""
        with_ = {k: interpolate(v, ctx) for k, v in (step.get("with") or {}).items()}
        if name in NOOP_ACTIONS:
            log.write(f"ci_local: {uses} is a no-op here ({NOOP_ACTIONS[name]})\n")
            return "PASS", ""
        if name == "actions/checkout":
            return self._checkout(with_, workspace, log)
        if name == "actions/setup-python":
            version = to_str(with_.get("python-version") or "")
            if not version and with_.get("python-version-file"):
                version = (workspace / to_str(with_["python-version-file"])).read_text(encoding="utf-8").strip()
            interp = find_python(version)
            if not interp:
                return "SKIPPED", f"Python {version} is not installed here (uv python install {version})"
            venv = jobdir / f"python-{version}"
            out = subprocess.run([self.uv, "venv", "-q", "--seed", "--python", interp, str(venv)],
                                 capture_output=True, text=True,
                                 env={**os.environ, "UV_PYTHON_DOWNLOADS": "never", "UV_LINK_MODE": "clone"})
            log.write(out.stdout + out.stderr)
            if out.returncode != 0:
                return "FAIL", f"could not create a Python {version} environment"
            prefix_path.insert(0, str(venv / "bin"))
            env["VIRTUAL_ENV"] = str(venv)
            env["pythonLocation"] = str(venv)
            log.write(f"ci_local: a fresh Python {version} environment from {interp} in {venv}\n")
            return "PASS", ""
        if name == "actions/setup-node":
            spec = to_str(with_.get("node-version") or "")
            if not spec and with_.get("node-version-file"):
                spec = (workspace / to_str(with_["node-version-file"])).read_text(encoding="utf-8").strip()
            found = find_node(spec)
            if not found:
                return "SKIPPED", f"Node {spec} is not installed here (nvm install {spec})"
            prefix_path.insert(0, str(found[0]))
            log.write(f"ci_local: Node {found[1]} from {found[0]}\n")
            return "PASS", ""
        if name == "dtolnay/rust-toolchain":
            toolchain = to_str(with_.get("toolchain") or rev)
            components = [c.strip() for c in to_str(with_.get("components") or "").split(",") if c.strip()]
            missing = rust_toolchain_ok(toolchain, components)
            if missing:
                return "SKIPPED", missing
            env["RUSTUP_TOOLCHAIN"] = toolchain  # the action makes it the default for later steps
            ver = subprocess.run([str(self.real_home / ".cargo" / "bin" / "rustc"), f"+{toolchain}", "--version"],
                                 capture_output=True, text=True).stdout.strip()
            log.write(f"ci_local: Rust {toolchain}: {ver}\n")
            return "PASS", ""
        return "FAIL", f"{uses} is not emulated"

    def _checkout(self, with_: dict, workspace: Path, log) -> tuple[str, str]:
        dest = (workspace / to_str(with_["path"])) if with_.get("path") else workspace
        depth = int(_num(with_.get("fetch-depth", 1)))
        repository = to_str(with_.get("repository") or "")
        if repository and repository.lower() != self.repository.lower():
            ref = to_str(with_.get("ref") or "")
            url = f"https://github.com/{repository}.git"
            cmd = ["clone", "-q"] + (["--depth", str(depth)] if depth > 0 else []) + (["--branch", ref] if ref else [])
            try:
                git(*cmd, url, str(dest))
            except RuntimeError as exc:
                log.write(f"{exc}\n")
                return "FAIL", f"could not clone {repository}@{ref or 'default'}"
            log.write(f"ci_local: cloned {repository}@{ref or 'default'} into {dest}\n")
            return "PASS", ""
        if dest.exists() and any(dest.iterdir()):
            return "FAIL", f"checkout path {dest} is not empty"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if depth > 0:
            git("clone", "-q", "--no-local", "--depth", str(depth), "--branch", "ci-local-head", f"file://{self.src}", str(dest))
        else:
            git("clone", "-q", "--shared", "--branch", "ci-local-head", str(self.src), str(dest))
        git("checkout", "-q", "--detach", self.tested, cwd=dest)
        if self.origin_url:
            git("remote", "set-url", "origin", self.origin_url, cwd=dest)
        log.write(f"ci_local: checked out {self.tested[:12]} (fetch-depth {depth}) into {dest}\n")
        return "PASS", ""


# A job folder's name stays short: tests build cache file names out of their paths (Hugging Face's
# hub cache), and macOS refuses a file name over 255 bytes (Errno 63). The full job name heads the
# job's log and the summary.
JOB_DIR_MAX = 40


def job_dir_name(number: int, label: str) -> str:
    """`NN-<the job's name, made safe>`, at most JOB_DIR_MAX characters; the number keeps it unique."""
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", label).strip("-") or "job"
    return f"{number:02d}-{slug}"[:JOB_DIR_MAX].rstrip("-")


def _fmt_seconds(s: float) -> str:
    m, sec = divmod(int(round(s)), 60)
    return f"{m}m{sec:02d}s"


def verdict_line(job: Job) -> str:
    timing = _fmt_seconds(job.seconds) if job.seconds else ""
    tail = f"  {job.reason}" if job.reason else ""
    if job.result in ("FAIL", "ERROR") and job.log:
        tail += f"  (log: {job.log})"
    return f"{job.result:<13} {timing:>7}  {job.label}{tail}"


def resolve_repo(name: str, workspace: Path) -> Path:
    if name.lower() in (".", "root", "abstractframework"):
        return workspace
    if os.sep in name:  # a path, as the pre-push hook passes it
        path = Path(name).expanduser().resolve()
        if not (path / ".git").exists():
            raise SystemExit(f"ci_local: {path} is not a git checkout")
        return path
    for child in sorted(workspace.iterdir()):
        if child.is_dir() and child.name.lower() == name.lower() and (child / ".git").exists():
            return child
    raise SystemExit(f"ci_local: no repository {name!r} under {workspace}")


def default_workspace() -> Path:
    """The workspace holding the sibling checkouts: this script's main worktree (not a linked one)."""
    here = Path(__file__).resolve().parent
    common = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                            cwd=here, capture_output=True, text=True).stdout.strip()
    return Path(common).parent if common else here.parent


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ci_local.sh",
        description="Run a repository's GitHub Actions jobs for a commit on this Mac (docs/ci-local.md).",
    )
    p.add_argument("repo", help="repository directory under the workspace (abstractcore, AbstractGateway, ...) or 'root'")
    p.add_argument("--job", action="append", help="run only this job id (or workflow:job) and the jobs it needs; repeatable")
    p.add_argument("--ref", default="HEAD", help="the commit to test (default HEAD; uncommitted changes are never tested)")
    p.add_argument("--event", choices=["auto", "pull_request", "push"], default="auto",
                   help="auto (default): each workflow's push-to-base run when it has one (the full main matrix), "
                        "else its pull-request run; pull_request or push: only that event")
    p.add_argument("--base", default="main", help="the base branch, fetched from origin (default main)")
    p.add_argument("--base-sha", help="use this base commit instead of fetching the base branch (replays an old pull request)")
    p.add_argument("--branch", help="the head branch name (github.head_ref; with --event push, refs/heads/<branch>)")
    p.add_argument("--git-ref", help="github.ref for --event push (refs/heads/main, refs/tags/v1.2.3)")
    p.add_argument("--before", help="the remote commit before the push (path filters diff from it)")
    p.add_argument("--release-tag", action="append",
                   help="also run the workflows a push of this tag triggers (release.yml's build and verify jobs); repeatable")
    p.add_argument("--input", action="append", metavar="NAME=VALUE",
                   help="set a workflow_dispatch input (inputs.NAME) for every workflow, e.g. full_ui_suite=true; repeatable")
    p.add_argument("--runner-label", action="append", metavar="LABEL",
                   help="run jobs on this custom runner label here (e.g. xcode-27); repeatable")
    p.add_argument("--no-merge", action="store_true",
                   help="test the commit itself, not its merge into the base (what GitHub tests and merging produces)")
    p.add_argument("--python", action="append", help="run only the matrix entries for this Python (repeatable)")
    p.add_argument("--installer", choices=["uv", "pip"], default="uv",
                   help="run the workflow's pip commands as uv pip (default: linked from the uv cache) or as pip")
    p.add_argument("--tier", choices=["light", "full"], default="full",
                   help="full (default): every job and matrix entry. light (ADR 0051: docs, copy, a catalog entry, a "
                        "pin bump): one Python per matrix, pytest narrowed to the changed files' tests; lint, "
                        "type-check, build and the npm/cargo jobs still run whole. Never with --release-tag")
    p.add_argument("--allow-skipped", action="store_true", help="exit 0 even when some jobs could not run here")
    p.add_argument("--sandbox", action="store_true",
                   help="run every step under sandbox-exec (refuses localhost:8080, ~/.abstractcore, writes under your "
                        "home outside the run); off by default: macOS cannot nest it, so tests that sandbox commands "
                        "themselves (AbstractCore's macOS sandbox) fail under it")
    p.add_argument("--jobs", "--parallel", dest="parallel", type=int, default=None, metavar="N",
                   help="jobs to run at once (default: min(jobs, physical cores // 4), capped by free memory at "
                        "4 GiB a job; the serial jobs, such as Core's local-model tests, always run alone at the end)")
    p.add_argument("--tail", type=int, default=40, help="log lines to print for a failed job (default 40)")
    p.add_argument("--workspace", help="the AbstractFramework workspace (default: this checkout's main worktree)")
    p.add_argument("--work", help="where run directories go (default ~/Library/Caches/ci-gate/runs, outside the workspace)")
    p.add_argument("--list", action="store_true", help="print the jobs that would run, and exit")
    p.add_argument("--keep-runs", type=parse_keep_runs, default=3, metavar="N",
                   help="after the run, delete this repository's oldest run folders under "
                        "~/Library/Caches/ci-gate/runs so at most N remain, this run included (default 3; "
                        "0 or 'all' keeps every one; refused when --work is outside ~/Library/Caches/ci-gate)")
    return p


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    if sys.platform != "darwin":
        print("ci_local: this gate runs on macOS (the workflows' Linux jobs run on this Mac)", file=sys.stderr)
        return 2
    if a.tier == "light" and a.release_tag:
        print("ci_local: a release is always --tier full (ADR 0051); drop --tier light", file=sys.stderr)
        return 2
    workspace = Path(a.workspace).resolve() if a.workspace else default_workspace()
    repo = resolve_repo(a.repo, workspace)
    r = Runner(a, repo, workspace)
    t0 = time.monotonic()
    try:
        r.prepare_source()
    except RuntimeError as exc:
        print(f"ci_local: RED {exc}", file=sys.stderr)
        return 1
    try:
        return run_prepared(r, a, t0)
    finally:
        # Only after the jobs ran to the end: --list, a push with no workflow run, a light run refused
        # before it starts, or an interrupted run never delete anyone's run folders.
        if r.jobs_completed:
            prune_after_run(r, a)


def prune_after_run(r: "Runner", a: argparse.Namespace) -> None:
    """--keep-runs: delete this repository's oldest run folders once a run has completed."""
    runs_root = Path(a.work or SCRATCH / "runs").expanduser()
    try:
        deleted, note = prune_runs(runs_root, r.repo_name, r.run_dir, a.keep_runs, SCRATCH)
    except OSError as exc:
        deleted, note = [], f"could not delete an old run folder: {exc}"
    if deleted:
        print(f"ci_local: --keep-runs {a.keep_runs}: deleted {len(deleted)} older run folder(s) of "
              f"{r.repo_name}: " + ", ".join(d.name for d in deleted), flush=True)
    if note:
        print(f"ci_local: --keep-runs {a.keep_runs}: {note}", flush=True)


def run_prepared(r: "Runner", a: argparse.Namespace, t0: float) -> int:
    """Everything after the tested commit is prepared: plan, select, run, report."""
    what = f"{r.head[:12]} merged into {a.base} {r.base_sha[:12]}" if r.merged else r.head[:12]
    print(f"ci_local: {r.repo_name} @ {what}; {len(r.changed)} changed files; run dir {r.run_dir}", flush=True)
    try:
        groups = r.plan()
    except (ExprError, RuntimeError) as exc:
        print(f"ci_local: RED reading the workflows: {exc}", file=sys.stderr)
        return 1
    print("ci_local: runs " + "; ".join(r.triggered) + ("" if not r.untriggered else
          "; not triggered: " + ", ".join(r.untriggered)), flush=True)
    for note in r.precheck_notes:
        print(f"ci_local: --release-tag: {note}", flush=True)
    if a.release_tag and not r.prechecks and not r.precheck_notes:
        print("ci_local: --release-tag: no pre-checks: no release job has a validation step (tag, version or "
              "changelog); the version check is not covered unless the release jobs run in full", flush=True)
    if a.list:
        for g in groups:
            for j in g:
                print(f"    {Path(j.wf_file).stem}:{j.job_id}  {j.label}  [{j.event} {j.git_ref}]")
        return 0
    if not groups:
        print("ci_local: GREEN, no workflow runs for this push")
        return 0
    r.light_tests = None
    if a.tier == "light":
        dropped = [j for g in groups for j in light_matrix(g)]
        for j in dropped:
            j.reason = LIGHT_DROPPED
        print("ci_local: tier light: skipped jobs " + (", ".join(j.label for j in dropped) or "none"), flush=True)
        selection, uncovered, owned = light_tests(r.changed, r.all_files, r.read_file)
        if owned:
            print(f"ci_local: tier light: {len(owned)} changed file(s) belong to an npm package or a crate; "
                  "their test steps are narrowed", flush=True)
        if docs_only(r.changed):
            print(f"ci_local: tier light: documentation only ({len(r.changed)} file(s)): no test runs, "
                  "every other step still runs", flush=True)
        if selection is None:
            print("ci_local: tier light: pytest runs whole (a conftest.py or the package configuration changed)")
        else:
            r.light_tests = sorted(selection)
            print(f"ci_local: tier light: pytest keeps {len(selection)} test file(s)", flush=True)
            for t, why in sorted(selection.items()):
                print(f"    {t}: {'; '.join(why)}")
        if uncovered:
            for f in uncovered:
                print(f"ci_local: RED tier light: no test covers {f}; use --tier full or add a test", flush=True)
            return 1
    count = sum(len(g) for g in groups)
    if a.parallel is None:
        a.parallel, why = default_jobs(count, physical_cores(), available_memory())
        print(f"ci_local: --jobs {a.parallel} ({why})", flush=True)
    else:
        print(f"ci_local: --jobs {a.parallel}", flush=True)
    serial = sorted({f"{j.label}: {serial_reason(r.repo_name, j)}" for g in groups for j in g if serial_reason(r.repo_name, j)})
    if serial:
        print("ci_local: alone at the end: " + "; ".join(serial), flush=True)
    jobs = r.run_all(groups)
    r.jobs_completed = True
    print("ci_local: summary")
    for j in jobs:
        if j.result != "NOT-SELECTED":
            print("  " + verdict_line(j))
    counts: dict[str, int] = {}
    for j in jobs:
        counts[j.result] = counts.get(j.result, 0) + 1
    bad = red_count(counts)
    if (a.tier == "light" and r.light_tests is not None and not docs_only(r.changed)
            and light_executed(r.run_dir / "light-counts") == 0):
        print("ci_local: RED tier light: the run executed no test; a light run may select few tests, never none "
              "(use --tier full)")
        bad += 1
    skipped = [j for j in jobs if j.result == "SKIPPED"]
    green = bad == 0 and (not skipped or a.allow_skipped)
    if skipped:
        print("ci_local: could not run here (GitHub still runs them): "
              + "; ".join(f"{j.label}: {j.reason}" for j in skipped))
    summary = ", ".join(f"{v} {k.lower()}" for k, v in sorted(counts.items()))
    if green:
        verdict = "GREEN" + (" (skipped jobs accepted by --allow-skipped)" if skipped else "")
    elif bad:
        verdict = "RED"
    else:
        verdict = "RED (jobs could not run here; --allow-skipped accepts that)"
    print(f"ci_local: {r.repo_name} {verdict} in {_fmt_seconds(time.monotonic() - t0)}: {summary}; run dir {r.run_dir}")
    return 0 if green else 1


if __name__ == "__main__":
    sys.exit(main())
