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
import itertools
import json
import math
import os
import re
import shlex
import shutil
import signal
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


def translate_pip(script: str, uv: str) -> str:
    """`python -m pip <cmd>` / `pip <cmd>` -> `uv pip <cmd>` (the --installer uv mode).

    uv links packages from its cache instead of copying them, so a fresh environment per job
    costs seconds and no disk; `--installer pip` keeps the workflow's pip byte for byte.
    """
    script = _PIP.sub(f"{shlex.quote(uv)} pip", script)
    return script.replace("--no-cache-dir", "--no-cache")


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
    result: str = "pending"  # PASS FAIL ERROR SKIPPED NOT-TRIGGERED
    reason: str = ""
    seconds: float = 0.0
    log: Path | None = None
    event: str = "pull_request"
    git_ref: str = ""
    outputs: dict = field(default_factory=dict)
    host_note: str = ""


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

UV = shutil.which("uv") or str(Path.home() / ".local" / "bin" / "uv")
SYSTEM_PATH = ["/opt/homebrew/bin", "/opt/homebrew/sbin", "/usr/bin", "/bin", "/usr/sbin", "/sbin"]
RUST_TOOLS = ["cargo", "cargo-clippy", "cargo-fmt", "clippy-driver", "rustc", "rustdoc", "rustfmt", "rustup"]
ROOT_SHIM = """#!/bin/sh
# ci_local: a GitHub runner step that needs root. It cannot run on this Mac.
printf '%s\\n' "$(basename "$0") $*" >> "$CI_LOCAL_JOB_DIR/needs-root"
echo "ci_local: '$(basename "$0") $*' needs root on a Linux runner; this job cannot run here" >&2
exit 97
"""


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
    ]
    lines += [f"(allow file-write* (subpath {q(p)}))" for p in allow_write]
    lines += [f"(deny file-read* file-write* (subpath {q(p)}))" for p in deny]
    return "\n".join(lines) + "\n"


class Runner:
    def __init__(self, args: argparse.Namespace, repo: Path, workspace: Path):
        self.args = args
        self.repo = repo
        self.workspace = workspace
        self.lock = threading.Lock()
        self.uv = UV
        self.real_home = Path.home()
        self.job_counter = 0
        self.inputs: dict[str, Any] = {}
        for item in args.input or []:
            key, _, value = item.partition("=")
            self.inputs[key] = {"true": True, "false": False}.get(value.lower(), value)

    def say(self, text: str) -> None:
        with self.lock:
            print(text, flush=True)

    @property
    def repo_name(self) -> str:
        return self.repo.name.lower() if self.repo != self.workspace else "abstractframework"

    # ---- the commit under test: the head, merged into the base the way GitHub merges a pull request
    def prepare_source(self) -> None:
        a = self.args
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.head = git("rev-parse", "--verify", f"{a.ref}^{{commit}}", cwd=self.repo)
        self.run_dir = Path(a.work or self.workspace / "untracked" / "ci-local" / "runs").resolve() / (
            f"{self.repo_name}-{stamp}-{self.head[:8]}"
        )
        self.run_dir.mkdir(parents=True, exist_ok=False)
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
                        group.append(Job(name, path.name, wf, job_id, spec, combo, f"{prefix}/{label}", i,
                                         event=event_name, git_ref=ref))
                    groups.append(group)
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
        selected = self._selection(groups)
        by_key = {self._key(g[0]): g for g in groups}
        done = {k: threading.Event() for k in by_key}

        def run_group(g: list[Job]) -> None:
            key = self._key(g[0])
            try:
                for n in _as_list(g[0].spec.get("needs")):
                    done[self._key(g[0], n)].wait()
                for job in g:
                    if key not in selected:
                        job.result = "NOT-SELECTED"
                        continue
                    self.run_job(job, by_key)
            finally:
                done[key].set()

        if self.args.parallel <= 1:
            for g in groups:
                run_group(g)
        else:
            with ThreadPoolExecutor(max_workers=self.args.parallel) as pool:
                for f in [pool.submit(run_group, g) for g in groups]:
                    f.result()
        return [j for g in groups for j in g]

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
        results = [j.result for j in g]
        if any(r in ("FAIL", "ERROR") for r in results):
            return "failure"
        if any(r in ("SKIPPED", "NOT-SELECTED") for r in results):
            return "unrunnable"
        if all(r == "NOT-TRIGGERED" for r in results):
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
        jobdir = self.run_dir / "jobs" / f"{number:02d}-{_slug(job.label)}"
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
            return self.finish(job, "NOT-TRIGGERED", f"if: {job.spec.get('if') or 'success()'} is false")

        can_run, note = runner_verdict(interpolate(job.spec.get("runs-on"), ctx), a.runner_label or [])
        if not can_run:
            return self.finish(job, "SKIPPED", note)
        job.host_note = note
        skip = static_skip(job)
        if skip:
            return self.finish(job, *skip)
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
            "CARGO_HOME": str(rh / ".cargo"), "RUSTUP_HOME": str(rh / ".rustup"), "CARGO_TARGET_DIR": str(target),
            # uv pip as pip: best match across indexes, and pip's tolerance of wheels whose zip headers
            # disagree with their contents (llama.cpp's macOS CPU wheel; pip installs it, uv refuses).
            "UV_LINK_MODE": "clone", "UV_PYTHON_DOWNLOADS": "never", "UV_INDEX_STRATEGY": "unsafe-best-match",
            "UV_INSECURE_NO_ZIP_VALIDATION": "1",
            "CI_LOCAL_JOB_DIR": str(jobdir),
        }
        (jobdir / "event.json").write_text(json.dumps(github["event"], indent=2), encoding="utf-8")
        return env

    def _steps(self, job: Job, ctx: Context, jobdir: Path, workspace: Path, home: Path, tmp: Path, rtemp: Path) -> tuple[str, str]:
        a = self.args
        rh = self.real_home
        target = self.workspace / "untracked" / "ci-local" / "cargo-target" / self.repo_name / _slug(f"{job.wf_file}-{job.job_id}")
        target.mkdir(parents=True, exist_ok=True)
        env = self._base_env(job, jobdir, workspace, home, tmp, rtemp, ctx.data["github"], target)
        shims = jobdir / "shims"
        for tool in ("sudo", "apt-get", "apt"):
            (shims / tool).write_text(ROOT_SHIM, encoding="utf-8")
            (shims / tool).chmod(0o755)
        rust_bin = jobdir / "rust-bin"
        rust_bin.mkdir()
        for tool in RUST_TOOLS:
            real = rh / ".cargo" / "bin" / tool
            if real.exists():
                (rust_bin / tool).symlink_to(real)
        prefix_path: list[str] = []  # setup-python / setup-node / $GITHUB_PATH
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
                    step_env[k] = to_str(interpolate(v, senv))
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
                    script = to_str(interpolate(step.get("run") or "", senv))
                    if a.installer == "uv":
                        script = translate_pip(script, self.uv)
                    script_path = jobdir / "steps" / f"{n:02d}.sh"
                    script_path.write_text(script + "\n", encoding="utf-8")
                    argv = shell_command(shell, str(script_path))
                    if argv is None:
                        return "SKIPPED", f"step {name!r} needs {shell} (a Windows shell)"
                    wd = step.get("working-directory") or defaults.get("working-directory")
                    cwd = workspace / to_str(interpolate(wd, senv)) if wd else workspace
                    files = {k: jobdir / "steps" / f"{n:02d}.{k.lower()}"
                             for k in ("GITHUB_ENV", "GITHUB_OUTPUT", "GITHUB_PATH", "GITHUB_STEP_SUMMARY")}
                    for f in files.values():
                        f.touch()
                    step_env.update({k: str(v) for k, v in files.items()})
                    step_env["PATH"] = ":".join([str(shims)] + prefix_path + [str(rust_bin)] + SYSTEM_PATH)
                    limit = job_deadline - time.monotonic()
                    if step.get("timeout-minutes"):
                        limit = min(limit, 60 * _num(interpolate(step.get("timeout-minutes"), senv)))
                    code, why = self._exec(["sandbox-exec", "-f", str(profile), *argv], cwd, step_env, log, limit, pgids)
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


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-")[:80] or "job"


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
    p.add_argument("--allow-skipped", action="store_true", help="exit 0 even when some jobs could not run here")
    p.add_argument("--parallel", type=int, default=1, help="jobs to run at once (default 1)")
    p.add_argument("--tail", type=int, default=40, help="log lines to print for a failed job (default 40)")
    p.add_argument("--workspace", help="the AbstractFramework workspace (default: this checkout's main worktree)")
    p.add_argument("--work", help="where run directories go (default <workspace>/untracked/ci-local/runs)")
    p.add_argument("--list", action="store_true", help="print the jobs that would run, and exit")
    return p


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    if sys.platform != "darwin":
        print("ci_local: this gate runs on macOS (every step runs under sandbox-exec)", file=sys.stderr)
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
    what = f"{r.head[:12]} merged into {a.base} {r.base_sha[:12]}" if r.merged else r.head[:12]
    print(f"ci_local: {r.repo_name} @ {what}; {len(r.changed)} changed files; run dir {r.run_dir}", flush=True)
    try:
        groups = r.plan()
    except (ExprError, RuntimeError) as exc:
        print(f"ci_local: RED reading the workflows: {exc}", file=sys.stderr)
        return 1
    print("ci_local: runs " + "; ".join(r.triggered) + ("" if not r.untriggered else
          "; not triggered: " + ", ".join(r.untriggered)), flush=True)
    if a.list:
        for g in groups:
            for j in g:
                print(f"    {Path(j.wf_file).stem}:{j.job_id}  {j.label}  [{j.event} {j.git_ref}]")
        return 0
    if not groups:
        print("ci_local: GREEN, no workflow runs for this push")
        return 0
    jobs = r.run_all(groups)
    counts: dict[str, int] = {}
    for j in jobs:
        counts[j.result] = counts.get(j.result, 0) + 1
    bad = counts.get("FAIL", 0) + counts.get("ERROR", 0)
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
