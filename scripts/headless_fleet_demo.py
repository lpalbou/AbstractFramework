#!/usr/bin/env python3
"""Fleet demo — 3 headless agents orchestrated by an agora hub, end to end.

The live proof for the hooks-first-class end product (plans/hooks-first-class.md):
three `scripts/headless_steer_repl.py` residents (one process = one agora
identity) collaborate on a tiny project, contacted and orchestrated ONLY
through the hub. The demo exercises the full agora model, not just messaging:

  1:N   kickoff broadcast on the demo channel (status=open, to=[all three])
  N:N   the agents' replies/coordination on the same channel
  1:1   each agent DMs the orchestrator a completion note
  fs    each agent PUBLISHES its deliverable to the per-channel shared
        filesystem (story/part1..3.md) and reads the others' parts
  steer a mid-run message to one agent is folded into its RUNNING turn
        (inject_message — the headless twin of steer_repl's keyboard steer)
  vote  a real agora BLIND vote (ballots DMed to the chair, tally published
        as a resolved reply — the hub's own convention from agora/vote.py)
  stop  a control token stops all three residents cleanly

Everything is verified from artifacts (hub transcript, shared fs, ballots,
driver exit codes) — never from prose claims. Results + evidence land under
plan_proof_out/hooks-fleet/.

The demo boots its OWN hub on a scratch port/db — it never touches the
production hub (:8765) or its channels.

Usage (from the monorepo root):
    .venv/bin/python scripts/headless_fleet_demo.py
    # options: --port 8791 --provider ... --model ... --keep-hub
"""

from __future__ import annotations


# ── UNSUPPORTED SINCE THE RUST MIGRATION ───────────────────────────────────
# This script drives `abstractcode bridge`, a subcommand of the Python client
# that AbstractCode replaced. The Rust client's surface is `exec`, `login` and
# `doctor` — there is no long-lived subprocess protocol to bridge to, so this
# needs porting onto `abstractcode exec` (or onto the gateway API directly)
# before it can run again. Failing at entry is deliberate: the alternative is a
# confusing crash several hundred lines deeper.
def _unsupported() -> None:
    raise SystemExit(
        "headless_fleet_demo.py drives `abstractcode bridge`, which no longer exists.\n"
        "AbstractCode is now a Rust client (cargo install abstractcode) whose\n"
        "subcommands are exec, login and doctor. Port this onto `abstractcode\n"
        "exec` or the gateway API before using it."
    )
# ───────────────────────────────────────────────────────────────────────────


import argparse
import json
import os
import re
import secrets
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "plan_proof_out" / "hooks-fleet"

AGENTS = ("demo-alice", "demo-bob", "demo-carol")
CHAIR = "orchestrator-demo"
CHANNEL = "build-demo"
STOP_TOKEN = "##FLEET-STOP##"

# The ballot-line regex is the hub's own convention (agora/vote.py): the DM
# body carries one `vote TAG: choice` line; the last matching line counts.
BALLOT = re.compile(r"^\s*vote\s+(\S+)\s*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)


def _match_ballot_choice(choice: str, options: List[str]) -> Optional[str]:
    """Resolve a ballot's choice text to one of the vote options.

    Accepts the option number, the exact option text, or the natural
    "N. option text" echo — models reliably restate the numbered line
    ("2. Harbor of Echoes"), and a tally that rejects that shape counts
    honest ballots as invalid (live finding: 2/3 ballots lost, 2026-07-13).
    Anything ambiguous stays invalid — a tally guesses nothing.
    """
    norm = choice.strip().strip("\"'`.,;:!?()[]").casefold()
    for i, o in enumerate(options):
        number, text = str(i + 1), o.casefold()
        if norm == text or norm == number:
            return o
        # "N. text" / "N) text" / "N - text" echoes of the option line
        for sep in (".", ")", "-", ":"):
            if norm == f"{number}{sep} {text}" or norm == f"{number}{sep}{text}":
                return o
    return None


# ---------------------------------------------------------------------------
# Minimal hub client (stdlib): one class, one identity per instance.
# ---------------------------------------------------------------------------

class Hub:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def req(self, method: str, path: str, *, payload: Optional[dict] = None,
            query: Optional[dict] = None, timeout_s: float = 30.0) -> Any:
        url = self.base_url + path
        if query:
            clean = {k: v for k, v in query.items() if v is not None}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)
        data = json.dumps(payload).encode() if payload is not None else None
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        return json.loads(body) if body else None

    # -- the surfaces the demo touches ------------------------------------
    def register(self, agent_id: str, about: str) -> str:
        res = self.req("POST", "/agents", payload={"id": agent_id, "about": about})
        return str(res["api_key"])

    def create_channel(self, name: str) -> None:
        self.req("POST", "/channels", payload={"name": name, "private": False})

    def post(self, channel: str, body: str, *, title: str = "", status: str = "fyi",
             to: Optional[List[str]] = None, reply_to: Optional[str] = None,
             data: Optional[dict] = None) -> dict:
        payload: Dict[str, Any] = {"body": body, "title": title, "status": status}
        if to:
            payload["to"] = to
        if reply_to:
            payload["reply_to"] = reply_to
        if data:
            payload["data"] = data
        return self.req("POST", f"/channels/{urllib.parse.quote(channel, safe='')}/messages",
                        payload=payload)

    def messages(self, channel: str, since: int = 0, limit: int = 500) -> List[dict]:
        res = self.req("GET", f"/channels/{urllib.parse.quote(channel, safe='')}/messages",
                       query={"since": since, "limit": limit})
        return res if isinstance(res, list) else []

    def members(self, channel: str) -> List[str]:
        res = self.req("GET", f"/channels/{urllib.parse.quote(channel, safe='')}/members")
        return [str(m.get("agent_id") or m.get("id") or "") for m in (res or [])]

    def fs_list(self, channel: str) -> List[dict]:
        res = self.req("GET", f"/channels/{urllib.parse.quote(channel, safe='')}/fs")
        return res if isinstance(res, list) else []

    def fs_read(self, channel: str, path: str) -> dict:
        return self.req("GET", f"/channels/{urllib.parse.quote(channel, safe='')}/fs/"
                        + urllib.parse.quote(path, safe="/")) or {}

    def inbox(self, wait: float = 0.0) -> List[dict]:
        res = self.req("GET", "/inbox", query={"wait": wait} if wait else None,
                       timeout_s=wait + 15.0)
        return res if isinstance(res, list) else []

    def ack(self, cursors: Dict[str, int]) -> None:
        if cursors:
            self.req("POST", "/inbox/ack", payload={"cursors": cursors})


# ---------------------------------------------------------------------------
# Demo context
# ---------------------------------------------------------------------------

@dataclass
class Ctx:
    args: Any
    base_url: str
    admin: Hub
    chair: Optional[Hub] = None
    keys: Dict[str, str] = field(default_factory=dict)
    hub_proc: Optional[subprocess.Popen] = None
    drivers: Dict[str, subprocess.Popen] = field(default_factory=dict)
    results: List[dict] = field(default_factory=list)
    kickoff_id: str = ""
    vote_tag: str = ""
    vote_msg_id: str = ""
    ballots: Dict[str, str] = field(default_factory=dict)

    def record(self, step: str, status: str, detail: str) -> None:
        row = {"step": step, "status": status, "detail": detail}
        self.results.append(row)
        print(f"  [{status}] {step}: {detail}", flush=True)

    def save(self, name: str, payload: Any) -> None:
        OUT.mkdir(parents=True, exist_ok=True)
        p = OUT / name
        if isinstance(payload, (dict, list)):
            p.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            p.write_text(str(payload))


# ---------------------------------------------------------------------------
# Hub lifecycle (scratch instance — never the production hub)
# ---------------------------------------------------------------------------

def find_hub_python() -> tuple[str, Dict[str, str]]:
    """(python, extra_env) able to `import agora.hub.main` — probed with the
    SAME env the hub will boot with, so probe success implies boot success."""
    candidates: list[tuple[str, Dict[str, str]]] = []
    if os.environ.get("AGORA_HUB_PYTHON"):
        candidates.append((os.environ["AGORA_HUB_PYTHON"], {}))
    candidates.append(("~/projects/a2a/untracked/stable-hub/.venv/bin/python", {}))
    candidates.append((str(ROOT / ".venv" / "bin" / "python"),
                       {"PYTHONPATH": "~/projects/a2a/src"}))
    for cand, extra in candidates:
        if not Path(cand).exists():
            continue
        probe = subprocess.run([cand, "-c", "import agora.hub.main"],
                               capture_output=True, timeout=30,
                               env={**os.environ, **extra})
        if probe.returncode == 0:
            return cand, extra
    sys.exit("error: no python can import the agora hub "
             "(set AGORA_HUB_PYTHON to a venv with `agoria` installed)")


def boot_hub(ctx: Ctx, admin_key: str, workdir: Path) -> None:
    py, extra_env = find_hub_python()
    env = {**os.environ, **extra_env,
           "AGORA_ADMIN_KEY": admin_key,
           "AGORA_NOTIFY_DIR": ""}
    log = open(workdir / "hub.log", "w")
    ctx.hub_proc = subprocess.Popen(
        [py, "-m", "agora.hub.main", "--host", "127.0.0.1",
         "--port", str(ctx.args.port), "--db", str(workdir / "hub.db")],
        stdout=log, stderr=subprocess.STDOUT, env=env, cwd=str(workdir))
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            urllib.request.urlopen(ctx.base_url + "/channels", timeout=2)
        except urllib.error.HTTPError:
            return  # 401 = hub answering
        except Exception:
            time.sleep(0.5)
            continue
        return
    sys.exit("error: scratch hub did not come up (see hub.log)")


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

def step_register(ctx: Ctx) -> None:
    ctx.keys[CHAIR] = ctx.admin.register(CHAIR, "fleet demo orchestrator (chair)")
    for name in AGENTS:
        ctx.keys[name] = ctx.admin.register(name, "headless fleet demo agent")
    ctx.chair = Hub(ctx.base_url, ctx.keys[CHAIR])
    ctx.chair.create_channel(CHANNEL)
    ctx.record("register", "PASS",
               f"hub registered {CHAIR} + {', '.join(AGENTS)}; channel '{CHANNEL}' created")


def _promoted_cmd(ctx: Ctx, ws: Path, name: str) -> List[str]:
    """Launch line for the PROMOTED `abstractcode bridge` seat.

    Invoked as a module (never a symlink-resolved path — the abstractcode
    symlink lesson) so an editable/uncommitted abstractcode tree is honoured.
    The shipped bridge takes identity + hub from AGORA_API_KEY / AGORA_URL in
    the env, exactly like the prototype, so the demo's per-agent env carries
    the seat identity unchanged.
    """
    cmd = [sys.executable, "-m", "abstractcode.cli", "bridge",
           "--channel", CHANNEL, "--workspace", str(ws), "--name", name,
           "--policy", ctx.args.policy,
           "--max-iterations", str(ctx.args.max_iterations),
           "--poll-wait", "20"]
    if ctx.args.provider:
        cmd += ["--provider", ctx.args.provider]
    if ctx.args.model:
        cmd += ["--model", ctx.args.model]
    if ctx.args.base_url:
        cmd += ["--base-url", ctx.args.base_url]
    for skill in ctx.args.skill:
        cmd += ["--skill", skill]
    return cmd


def step_launch_drivers(ctx: Ctx, workdir: Path) -> None:
    for name in AGENTS:
        ws = workdir / "ws" / name
        ws.mkdir(parents=True, exist_ok=True)
        env = {k: v for k, v in os.environ.items() if not k.startswith("AGORA_")}
        env["AGORA_URL"] = ctx.base_url
        env["AGORA_API_KEY"] = ctx.keys[name]  # one process = one identity
        if ctx.args.promoted:
            cmd = _promoted_cmd(ctx, ws, name)
            if ctx.args.skill and ctx.args.skills_root:
                env["ABSTRACTCODE_SKILLS_ROOTS"] = ctx.args.skills_root
        else:
            driver_script = ("headless_fleet_bridge.py" if ctx.args.bridge
                             else "headless_steer_repl.py")
            cmd = [sys.executable, str(ROOT / "scripts" / driver_script),
                   "--channel", CHANNEL, "--workspace", str(ws), "--name", name,
                   "--max-iterations", str(ctx.args.max_iterations),
                   "--poll-wait", "20"]
            if ctx.args.provider:
                cmd += ["--provider", ctx.args.provider]
            if ctx.args.model:
                cmd += ["--model", ctx.args.model]
        log = open(workdir / f"{name}.log", "w")
        cwd = str(ROOT / "abstractcode") if ctx.args.promoted else str(ws)
        ctx.drivers[name] = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT,
                                             env=env, cwd=cwd)
    # Drivers join the channel at startup; wait until membership shows all 3.
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            members = set(ctx.chair.members(CHANNEL))
        except Exception:
            members = set()
        if all(a in members for a in AGENTS):
            ctx.record("launch", "PASS", f"3 drivers up and joined: members={sorted(members)}")
            break
        if any(p.poll() is not None for p in ctx.drivers.values()):
            dead = [n for n, p in ctx.drivers.items() if p.poll() is not None]
            ctx.record("launch", "FAIL", f"driver(s) died at startup: {dead} (see logs)")
            return
        time.sleep(1.0)
    else:
        ctx.record("launch", "FAIL", "drivers did not all join the channel within 60s")
        return
    # skill's c1818 gate: a NON-ACTIVE skill activation turns the "with-skill"
    # arm into a silent second "without" arm — the bench then measures nothing.
    # Treat a missing/held/blocked outcome as a HARNESS error, never a result.
    if ctx.args.promoted and ctx.args.skill:
        _assert_skills_active(ctx, workdir)


# code's shipped self-attesting activation line (c1820): the bridge emits
#   "skill activated: <name> (tree <full sha256>)"
# on the seat's stderr. One line proves activation AND exact bytes — a wrong-
# bytes root-shadow shows a different hash; a registry-less enable shows a
# requires_review note beside it (activation still happens — code's correction
# to skill's original "with-arm becomes without-arm" claim). The bench asserts
# the line is present and, when a frozen hash is supplied, that it MATCHES.
_SKILL_ACTIVATED = re.compile(r"skill activated:\s*(\S+)\s*\(tree\s+([0-9a-f]+)\)")


def _assert_skills_active(ctx: Ctx, workdir: Path) -> None:
    want = set(ctx.args.skill)
    frozen = (ctx.args.skill_tree_hash or "").strip().lower()
    deadline = time.time() + 30
    per_seat: Dict[str, Dict[str, str]] = {}
    while time.time() < deadline:
        per_seat = {}
        for name in AGENTS:
            log = (workdir / f"{name}.log")
            text = log.read_text(errors="replace") if log.exists() else ""
            per_seat[name] = {n: h for n, h in _SKILL_ACTIVATED.findall(text)}
        if all(want.issubset(per_seat[n].keys()) for n in AGENTS):
            break
        if any(p.poll() is not None for p in ctx.drivers.values()):
            break
        time.sleep(1.5)
    short = {n: sorted(want - set(per_seat.get(n, {}).keys())) for n in AGENTS
             if not want.issubset(per_seat.get(n, {}).keys())}
    if short:
        ctx.record("skill-preflight", "FAIL",
                   f"HARNESS error (skill's c1818 gate, code's c1820 line): no "
                   f"'skill activated: <name> (tree ...)' line per seat={short} — "
                   f"aborting before any trial counts. Check ABSTRACTCODE_SKILLS_ROOTS "
                   f"reaches the serve child (bridge threads its env through).")
        return
    # Bytes gate: when a frozen hash is supplied (the freeze record), every seat
    # must activate EXACTLY those bytes — a mismatch is root-shadowing, a harness
    # error that voids provenance (code's c1820: the hash subsumes both asks).
    if frozen:
        mismatched = {n: per_seat[n] for n in AGENTS
                      if any(not h.startswith(frozen) and not frozen.startswith(h)
                             for s, h in per_seat[n].items() if s in want)}
        if mismatched:
            ctx.record("skill-preflight", "FAIL",
                       f"HARNESS error: activated tree hash != frozen {frozen[:16]}… "
                       f"per seat={ {n: [h[:16] for h in v.values()] for n, v in mismatched.items()} } "
                       f"(root shadowing — the bench would bind to the wrong bytes)")
            return
    attest = {n: [f"{s}@{h[:12]}" for s, h in per_seat[n].items() if s in want]
              for n in AGENTS}
    ctx.record("skill-preflight", "PASS",
               f"every seat self-attests {sorted(want)} active"
               + (f" @ frozen {frozen[:16]}…" if frozen else "")
               + f"; lines={attest}")


def step_kickoff(ctx: Ctx) -> None:
    parts = {
        "demo-alice": "story/part1.md (the OPENING)",
        "demo-bob": "story/part2.md (the MIDDLE)",
        "demo-carol": "story/part3.md (the ENDING)",
    }
    lines = "\n".join(f"- {n}: write {p}" for n, p in parts.items())
    if ctx.args.bridge or ctx.args.promoted:
        # serve-subprocess agents have the shipped agora MESSAGING toolset +
        # their own file tools; the bridge mirrors workspace changes to the
        # channel fs, so publication is automatic (bridge-owned, like delivery).
        rules = (
            "Rules for EACH agent:\n"
            "1. Write YOUR part only: 4-8 lines of story prose. Save it at EXACTLY "
            "your assigned relative path (e.g. story/part1.md) in your workspace "
            "with write_file — publication to the shared channel filesystem is "
            "automatic when you finish.\n"
            "2. Post ONE short status='reply' to this message on this channel "
            "(agora_post_message) when your part is written (say the path).\n"
            "3. DM the orchestrator (agora_send_dm, peer='orchestrator-demo') one "
            "line: done: <your path>.\n"
            "4. You may read the channel (agora_read_channel) for continuity with "
            "the others' announced parts, but write only your own file.\n"
        )
    else:
        rules = (
            "Rules for EACH agent:\n"
            "1. Write YOUR part only: 4-8 lines of story prose, publish it to the SHARED "
            "channel filesystem with channel_fs_write at your assigned path.\n"
            "2. Also save a working copy in your own workspace with write_file.\n"
            "3. Post ONE short status='reply' to this message on this channel when your "
            "part is published (say the fs path).\n"
            "4. DM the orchestrator (agora_send_dm, peer='orchestrator-demo') one line: "
            "done: <your fs path>.\n"
            "5. You may read the others' parts with channel_fs_list / channel_fs_read "
            "for continuity, but do not edit anyone else's file.\n"
        )
    body = (
        "PROJECT KICKOFF — 'the fleet fable' (a 3-part micro-story, theme: a small "
        "harbor town at dawn).\n\n"
        f"Assignments:\n{lines}\n\n" + rules
    )
    res = ctx.chair.post(CHANNEL, body, title="KICKOFF: the fleet fable",
                         status="open", to=list(AGENTS))
    ctx.kickoff_id = str(res.get("id") or "")
    ctx.record("kickoff", "PASS", f"broadcast posted (1:N, to=3 agents), id={ctx.kickoff_id}")


def step_steer_alice(ctx: Ctx) -> None:
    """A second addressed message while alice is (likely) mid-run: the driver
    folds it into the RUNNING turn via inject_message — hub-driven steering."""
    time.sleep(ctx.args.steer_delay)
    # status=fyi + to=[alice]: to_me makes it addressed FOR ALICE ONLY — an
    # `open` here would read as an obligation to bob/carol too (triage rule).
    fix_hint = ("update your workspace story/part1.md with write_file so it includes "
                "'lighthouse' (re-publication is automatic)"
                if (ctx.args.bridge or ctx.args.promoted) else
                "update it with channel_fs_write so it includes 'lighthouse'")
    ctx.chair.post(
        CHANNEL,
        "demo-alice — steering note for your CURRENT work: your part must include "
        f"the word 'lighthouse'. If you already published part1, {fix_hint}.",
        title="steer: lighthouse", status="fyi", to=["demo-alice"])
    ctx.record("steer-sent", "PASS",
               f"mid-run steer posted to demo-alice {ctx.args.steer_delay}s after kickoff")


def wait_for_parts(ctx: Ctx) -> None:
    want = {"story/part1.md", "story/part2.md", "story/part3.md"}
    deadline = time.time() + ctx.args.build_timeout
    have: Dict[str, str] = {}
    while time.time() < deadline:
        try:
            listing = ctx.chair.fs_list(CHANNEL)
        except Exception:
            listing = []
        have = {str(f.get("path") or f.get("key") or ""): str(f.get("updated_by") or "")
                for f in listing}
        if want.issubset(have.keys()):
            break
        time.sleep(5)
    ctx.save("fs_listing.json", have)
    missing = want - set(have.keys())
    if missing:
        ctx.record("build", "FAIL", f"shared-fs parts missing after "
                    f"{ctx.args.build_timeout}s: {sorted(missing)}; have={sorted(have)}")
        return
    authors = {p: have.get(p, "") for p in sorted(want)}
    distinct = len({a for a in authors.values() if a})
    contents = {}
    for p in sorted(want):
        row = ctx.chair.fs_read(CHANNEL, p)
        contents[p] = str(row.get("content") or "")
    ctx.save("fs_contents.json", contents)
    ok = distinct >= 3 and all(len(c.strip()) > 40 for c in contents.values())
    ctx.record("build", "PASS" if ok else "PARTIAL",
               f"all 3 parts published to the shared fs; authors={authors}; "
               f"sizes={[len(c) for c in contents.values()]}")


def step_vote(ctx: Ctx) -> None:
    """The hub's real blind-vote convention: open message + data.vote payload,
    ballots DMed to the chair, chair tallies + publishes resolved."""
    ctx.vote_tag = "v-" + secrets.token_hex(3)
    options = ["The Last Signal", "Harbor of Echoes"]
    opts = "\n".join(f"  {i+1}. {o}" for i, o in enumerate(options))
    body = (
        f"VOTE — pick the story's title\n\nOptions:\n{opts}\n\n"
        "BLIND VOTE — do NOT post your choice in this channel.\n"
        f"DM your ballot to {CHAIR} (agora_send_dm) as ONE line, exactly:\n"
        f"  vote {ctx.vote_tag}: <option number or exact option text>\n"
        "Your latest ballot line counts. The result (counts and roll call) will be "
        "published here when everyone has voted."
    )
    res = ctx.chair.post(
        CHANNEL, body, title="VOTE: story title", status="open", to=list(AGENTS),
        data={"vote": {"topic": "story title", "options": options,
                        "tag": ctx.vote_tag, "ballots": "dm",
                        "closes_at": time.time() + ctx.args.vote_timeout}})
    ctx.vote_msg_id = str(res.get("id") or "")

    # Chair duty: collect DM ballots from the inbox until all voted or timeout.
    cursors: Dict[str, int] = {}
    deadline = time.time() + ctx.args.vote_timeout
    while time.time() < deadline and len(ctx.ballots) < len(AGENTS):
        try:
            envs = ctx.chair.inbox(wait=10)
        except Exception:
            time.sleep(3)
            continue
        for env in envs:
            ch = str(env.get("channel") or "")
            seq = int(env.get("seq") or 0)
            cursors[ch] = max(cursors.get(ch, 0), seq)
            if not ch.startswith("dm:"):
                continue
            sender = str(env.get("sender") or "")
            body_txt = str(env.get("body") or "")
            for tag, choice in BALLOT.findall(body_txt):
                if tag.lstrip("#").casefold() != ctx.vote_tag.casefold():
                    continue
                picked = _match_ballot_choice(choice, options)
                if picked and sender in AGENTS:
                    ctx.ballots[sender] = picked
        try:
            ctx.chair.ack(cursors)
        except Exception:
            pass

    ctx.save("ballots.json", ctx.ballots)
    counts: Dict[str, int] = {}
    for choice in ctx.ballots.values():
        counts[choice] = counts.get(choice, 0) + 1
    winner = max(counts, key=counts.get) if counts else "(no valid ballots)"
    roll = ", ".join(f"{a}→{c}" for a, c in sorted(ctx.ballots.items()))
    ctx.chair.post(
        CHANNEL,
        f"VOTE RESULT — story title: {winner}\ncounts: {counts}\nroll call: {roll}",
        title=f"RESOLVED: story title = {winner}", status="resolved",
        reply_to=ctx.vote_msg_id or None,
        data={"vote_result": {"tag": ctx.vote_tag, "counts": counts,
                               "ballots": ctx.ballots, "winner": winner}})
    n = len(ctx.ballots)
    ctx.record("vote", "PASS" if n >= 2 else ("PARTIAL" if n == 1 else "FAIL"),
               f"{n}/3 valid blind ballots via DM (tag {ctx.vote_tag}); "
               f"winner: {winner}; result published as resolved reply")


def step_stop(ctx: Ctx) -> None:
    ctx.chair.post(CHANNEL, f"{STOP_TOKEN} — demo complete, thank you all.",
                   title="fleet stop", status="fyi", to=list(AGENTS))
    deadline = time.time() + 120
    while time.time() < deadline:
        if all(p.poll() is not None for p in ctx.drivers.values()):
            break
        time.sleep(2)
    codes = {n: p.poll() for n, p in ctx.drivers.items()}
    for n, p in ctx.drivers.items():
        if p.poll() is None:
            p.send_signal(signal.SIGTERM)
    clean = all(c == 0 for c in codes.values())
    ctx.record("stop", "PASS" if clean else "PARTIAL",
               f"stop token broadcast; driver exits={codes}"
               + ("" if clean else " (non-zero/None = forced SIGTERM after timeout)"))


def step_verify_transcript(ctx: Ctx) -> None:
    msgs = ctx.chair.messages(CHANNEL)
    ctx.save("channel_transcript.json", msgs)
    by_sender: Dict[str, int] = {}
    replies_to_kickoff = 0
    for m in msgs:
        s = str(m.get("sender") or "")
        by_sender[s] = by_sender.get(s, 0) + 1
        if str(m.get("reply_to") or "") == ctx.kickoff_id:
            replies_to_kickoff += 1
    spoke = [a for a in AGENTS if by_sender.get(a, 0) >= 1]
    ok = len(spoke) == 3
    ctx.record("transcript", "PASS" if ok else "PARTIAL",
               f"channel N:N traffic by sender={by_sender}; "
               f"{replies_to_kickoff} direct replies to kickoff; all 3 spoke={ok}")

    # Steer effect on the FINAL shared-fs state (the steer may legitimately be
    # applied in a follow-up turn — judge the outcome, not the timing).
    final_part1 = ""
    try:
        final_part1 = str(ctx.chair.fs_read(CHANNEL, "story/part1.md").get("content") or "")
    except Exception:
        pass
    ctx.save("final_part1.md", final_part1)
    lit = "lighthouse" in final_part1.lower()
    ctx.record("steer-effect", "PASS" if lit else "DEGRADED-HONEST",
               "final part1 contains 'lighthouse' — the hub-sent steer changed the work"
               if lit else
               "final part1 lacks 'lighthouse' (election is probabilistic; steer DELIVERY "
               "is proven by the driver log '↪ steer folded into next cycle')")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8791)
    ap.add_argument("--provider", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--base-url", default=None,
                    help="provider base URL for promoted seats (e.g. a local "
                         "LMStudio endpoint) — free-substrate benching")
    ap.add_argument("--max-iterations", type=int, default=16)
    ap.add_argument("--build-timeout", type=float, default=420.0)
    ap.add_argument("--vote-timeout", type=float, default=300.0)
    ap.add_argument("--steer-delay", type=float, default=8.0)
    ap.add_argument("--keep-hub", action="store_true")
    ap.add_argument("--workdir", default=None)
    ap.add_argument("--bridge", action="store_true",
                    help="drive agents through the agency PROTOTYPE bridge "
                         "(headless_fleet_bridge.py) instead of the in-process driver")
    ap.add_argument("--promoted", action="store_true",
                    help="drive agents through the PROMOTED `abstractcode bridge` "
                         "subcommand (the shipped fleet seat) — the step-4 acceptance "
                         "bench for the swarm-promotion wave")
    ap.add_argument("--policy", default="worker",
                    choices=["reader", "worker", "builder", "full-auto"],
                    help="fleet permission preset for --promoted seats (default worker)")
    ap.add_argument("--skill", action="append", default=[],
                    help="Agent Skill name to charge into each promoted seat "
                         "(repeatable). NON-ACTIVE activation is a HARNESS error, "
                         "never a skill result (skill's c1818 gate): the launch "
                         "pre-flight aborts unless every seat's stderr reports the "
                         "skill active.")
    ap.add_argument("--skills-root", default=None,
                    help="ABSTRACTCODE_SKILLS_ROOTS for promoted seats when using "
                         "--skill (points at the registry/drafts dir for a not-yet-"
                         "shelved skill; the bridge threads its env to the serve "
                         "child, so this reaches the seat — code c1820).")
    ap.add_argument("--skill-tree-hash", default=None,
                    help="frozen tree sha256 for the charged skill (the freeze "
                         "record). When set, the pre-flight asserts every seat "
                         "self-attests EXACTLY these bytes — a mismatch is root-"
                         "shadowing and voids the trial (code c1820).")
    args = ap.parse_args()
    if args.bridge and args.promoted:
        sys.exit("error: --bridge (prototype) and --promoted (shipped) are mutually exclusive")

    workdir = Path(args.workdir) if args.workdir else (OUT / "run")
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    admin_key = "demo-admin-" + secrets.token_hex(8)
    base_url = f"http://127.0.0.1:{args.port}"
    ctx = Ctx(args=args, base_url=base_url, admin=Hub(base_url, admin_key))

    print(f"fleet demo — scratch hub {base_url}, workdir {workdir}", flush=True)
    boot_hub(ctx, admin_key, workdir)
    try:
        step_register(ctx)
        step_launch_drivers(ctx, workdir)
        if not any(r["status"] == "FAIL" for r in ctx.results):
            step_kickoff(ctx)
            step_steer_alice(ctx)
            wait_for_parts(ctx)
            step_vote(ctx)
            step_stop(ctx)
            step_verify_transcript(ctx)
    except Exception as e:
        ctx.record("harness", "ERROR", f"{type(e).__name__}: {e}")
    finally:
        code = finish(ctx, workdir)
    return code


def finish(ctx: Ctx, workdir: Path) -> int:
    for n, p in ctx.drivers.items():
        if p.poll() is None:
            p.send_signal(signal.SIGTERM)
    if ctx.hub_proc and not ctx.args.keep_hub:
        ctx.hub_proc.send_signal(signal.SIGTERM)
    ctx.save("results.json", ctx.results)
    print("\n=== fleet demo results ===", flush=True)
    for r in ctx.results:
        print(f"  {r['status']:>16}  {r['step']}: {r['detail'][:160]}", flush=True)
    bad = [r for r in ctx.results if r["status"] in ("FAIL", "ERROR")]
    print(f"\nevidence: {OUT} (transcript, fs contents, ballots, driver logs in {workdir})",
          flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    _unsupported()
    raise SystemExit(main())
