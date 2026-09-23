#!/usr/bin/env python3
"""Headless fleet bridge — agora hub ⟷ `abstractcode serve` subprocess.

The BRIDGE SWAP of scripts/headless_steer_repl.py (operator directive, fleet
lane A6): the in-process ReactAgent driver is replaced by an `abstractcode
serve` SUBPROCESS speaking its JSONL protocol. The division of labor:

  - abstractcode serve OWNS the agent loop, the toolset (files/web/execute per
    permission mode + the agora comms toolset, auto-registered when
    AGORA_API_KEY is in the child env), approval gates, and steering delivery
    (`{"op":"steer"}` rides its native mid-run guidance seam).
  - THE BRIDGE owns hub reception (inbox long-poll, addressing filter, ack
    cursors), turn dispatch ({"op":"prompt"}), mid-run steering forwarding,
    APPROVAL POLICY (auto-allow in the walled demo workspace, logged), the
    ask_user refusal, STOP control, and driver-owned delivery of the final
    answer back to the origin (channel post or DM) — the model is never
    relied on to self-send its reply (the delivery-gap lesson, 2026-07-13).

One bridge process = one hub seat = one serve child. Three of these = the
fleet. No gateway required — the reproducible-example shape.

Usage:
    AGORA_API_KEY=... AGORA_URL=http://127.0.0.1:8791 \
    python3 scripts/headless_fleet_bridge.py \
        --channel build-demo --workspace /tmp/fleet/agent-a --name agent-a \
        --provider lmstudio --model qwen/qwen3.5-4b
"""

from __future__ import annotations


# ── UNSUPPORTED SINCE THE RUST MIGRATION ───────────────────────────────────
# This script drives `abstractcode serve`, a subcommand of the Python client
# that AbstractCode replaced. The Rust client's surface is `exec`, `login` and
# `doctor` — there is no long-lived subprocess protocol to bridge to, so this
# needs porting onto `abstractcode exec` (or onto the gateway API directly)
# before it can run again. Failing at entry is deliberate: the alternative is a
# confusing crash several hundred lines deeper.
def _unsupported() -> None:
    raise SystemExit(
        "headless_fleet_bridge.py drives `abstractcode serve`, which no longer exists.\n"
        "AbstractCode is now a Rust client (cargo install abstractcode) whose\n"
        "subcommands are exec, login and doctor. Port this onto `abstractcode\n"
        "exec` or the gateway API before using it."
    )
# ───────────────────────────────────────────────────────────────────────────


import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent

STOP_TOKEN = "##FLEET-STOP##"


def _gap_bound_s(env_name: str, default_s: float) -> Optional[float]:
    """A tagged, operator-overridable GAP bound. `0` (or negative) = no bound."""
    raw = str(os.getenv(env_name) or "").strip()
    if raw:
        try:
            default_s = float(raw)
        except ValueError:
            pass
    return None if default_s <= 0 else default_s


# #[WARNING:TIMEOUT] Max GAP between two serve events from a bridged coder
# (ADR-0027 §2/§3/§4). NOT a turn budget: a healthy coder can think, build or
# run a test suite for a long time. 7200s matches ADR-0014's per-effect LLM
# budget; the previous 600s sat BELOW it, so one long local generation killed
# a healthy turn. `0` = wait forever.
SERVE_EVENT_GAP_S = _gap_bound_s("ABSTRACTCODE_BRIDGE_SERVE_EVENT_GAP_S", 7200.0)
# #[WARNING:TIMEOUT] Startup handshake only (spawn + import, never generation).
SERVE_READY_GAP_S = _gap_bound_s("ABSTRACTCODE_BRIDGE_SERVE_READY_S", 120.0)

ASK_USER_NOTE = ("(no human is attached; proceed with your best judgment and "
                 "finish your part.)")


# ---------------------------------------------------------------------------
# agora HTTP (stdlib only — the bridge deliberately imports NO framework
# packages: the agent stack lives entirely in the serve subprocess).
# ---------------------------------------------------------------------------

def _agora_url() -> str:
    return str(os.getenv("AGORA_URL") or "http://127.0.0.1:8765").strip().rstrip("/")


def _agora_key() -> str:
    key = str(os.getenv("AGORA_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("AGORA_API_KEY is not set for this bridge process")
    return key


def _agora(method: str, path: str, *, payload: Optional[dict] = None,
           query: Optional[dict] = None, timeout_s: float = 35.0) -> Any:
    url = _agora_url() + path
    if query:
        clean = {k: v for k, v in query.items() if v is not None}
        if clean:
            url += "?" + urllib.parse.urlencode(clean)
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Authorization": f"Bearer {_agora_key()}"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        raise RuntimeError(f"agora HTTP {e.code} for {method} {path}: {detail}") from e
    if not body:
        return None
    try:
        return json.loads(body)
    except Exception:
        return body


# ---------------------------------------------------------------------------
# The serve child: spawn + JSONL in/out. A reader thread pumps stdout events
# into a queue; the bridge's turn loop consumes them and answers waits.
# ---------------------------------------------------------------------------

class ServeChild:
    """One `abstractcode serve` subprocess and its JSONL protocol."""

    def __init__(self, args: argparse.Namespace, workspace: Path, tag: str):
        self.tag = tag
        self.events: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        cmd = [
            args.abstractcode, "serve",
            "--agent", args.agent,
            "--provider", args.provider,
            "--model", args.model,
            "--permission-mode", "write",   # gates emit approval_required → bridge policy
            "--max-iterations", str(args.max_iterations),
            "--no-review",                  # fleet demo: no verifier round (cost discipline)
        ]
        if args.base_url:
            cmd += ["--base-url", args.base_url]
        env = dict(os.environ)  # carries AGORA_API_KEY/AGORA_URL → child auto-registers agora tools
        self.proc = subprocess.Popen(
            cmd, cwd=str(workspace), env=env, text=True, bufsize=1,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        threading.Thread(target=self._pump_stdout, name="serve-out", daemon=True).start()
        threading.Thread(target=self._pump_stderr, name="serve-err", daemon=True).start()

    def _pump_stdout(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            raw = line.strip()
            if not raw:
                continue
            try:
                self.events.put(json.loads(raw))
            except Exception:
                print(f"{self.tag} [serve stdout] {raw[:200]}", flush=True)
        self.events.put({"event": "_eof"})

    def _pump_stderr(self) -> None:
        assert self.proc.stderr is not None
        for line in self.proc.stderr:
            text = line.rstrip()
            if text:
                print(f"{self.tag} [serve] {text[:220]}", flush=True)

    def send(self, op: Dict[str, Any]) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(op) + "\n")
        self.proc.stdin.flush()

    def alive(self) -> bool:
        return self.proc.poll() is None

    def shutdown(self) -> None:
        try:
            if self.alive():
                self.send({"op": "quit"})
                self.proc.wait(timeout=10)
        except Exception:
            pass
        if self.alive():
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()


# ---------------------------------------------------------------------------
# One turn through the child: prompt in, events out until `final`. Steers
# arriving from the hub are forwarded live via {"op":"steer"} — abstractcode's
# own mid-run seam (no bridge-side buffering games).
# ---------------------------------------------------------------------------

class Turn(threading.Thread):
    def __init__(self, child: ServeChild, task: str, tag: str, *,
                 origin_channel: str = "", origin_sender: str = "", self_name: str = "",
                 workspace: Optional[Path] = None, publish_channel: str = ""):
        super().__init__(name="bridge-turn", daemon=True)
        self.child = child
        self.task = task
        self.tag = tag
        self.origin_channel = origin_channel
        self.origin_sender = origin_sender
        self.self_name = self_name
        # Artifact publication: the serve child has NO channel-fs tools (the
        # shipped agora toolset stops at messaging), so the BRIDGE mirrors
        # workspace files changed during the turn to the channel's shared fs
        # — same ownership rule as delivery: the model does the work, the
        # bridge guarantees it reaches the shared surface.
        self.workspace = workspace
        self.publish_channel = publish_channel
        self._pre_snapshot: Dict[str, float] = self._snapshot() if workspace else {}
        self.answer: str = ""
        self.status: str = ""
        self.done = threading.Event()

    def _snapshot(self) -> Dict[str, float]:
        out: Dict[str, float] = {}
        if not self.workspace:
            return out
        for p in self.workspace.rglob("*"):
            if p.is_file() and not any(part.startswith(".") for part in p.parts):
                try:
                    out[str(p.relative_to(self.workspace))] = p.stat().st_mtime
                except OSError:
                    pass
        return out

    def _publish_changed(self) -> None:
        if not (self.workspace and self.publish_channel):
            return
        post = self._snapshot()
        changed = [rel for rel, m in post.items()
                   if m > self._pre_snapshot.get(rel, 0.0)]
        for rel in sorted(changed):
            try:
                content = (self.workspace / rel).read_text(errors="replace")
            except OSError:
                continue
            if len(content) > 200_000:
                continue  # demo artifacts are small; skip anything huge
            try:
                _agora("PUT",
                       f"/channels/{urllib.parse.quote(self.publish_channel, safe='')}/fs/"
                       + urllib.parse.quote(rel, safe="/"),
                       payload={"content": content, "mime": "text/plain"})
                print(f"{self.tag} ⇧ published {rel} to #{self.publish_channel} fs", flush=True)
            except Exception as e:
                print(f"{self.tag} publish error for {rel}: {e}", flush=True)

    def steer(self, text: str) -> None:
        try:
            self.child.send({"op": "steer", "text": text})
            print(f"{self.tag} ↪ steer forwarded to serve child: {text[:120]}", flush=True)
        except Exception as e:
            print(f"{self.tag} steer forward error: {e}", flush=True)

    def run(self) -> None:
        try:
            self.child.send({"op": "prompt", "text": self.task, "id": f"t-{int(time.time())}"})
            while True:
                try:
                    ev = self.child.events.get(timeout=SERVE_EVENT_GAP_S)
                except queue.Empty:
                    # #[WARNING:TIMEOUT] ADR-0027 §1 — duration + component + knob.
                    print(
                        f"{self.tag} #[WARNING:TIMEOUT] headless_fleet_bridge gave up after "
                        f"{SERVE_EVENT_GAP_S}s with NO serve event (gap bound between events, "
                        f"not a turn budget; ABSTRACTCODE_BRIDGE_SERVE_EVENT_GAP_S, "
                        f"0 = wait forever)",
                        flush=True,
                    )
                    self.status = "timeout"
                    return
                name = str(ev.get("event") or "")
                if name == "_eof":
                    print(f"{self.tag} serve child exited mid-turn", flush=True)
                    self.status = "child_exit"
                    return
                if name == "cycle":
                    print(f"{self.tag} ⟲ cycle {ev.get('iteration')}", flush=True)
                elif name == "tool_call":
                    print(f"{self.tag}   → {ev.get('tool')}", flush=True)
                elif name == "tool_result":
                    ok = "ok" if ev.get("success", True) else "ERROR"
                    print(f"{self.tag}   ← {ev.get('tool')} {ok}", flush=True)
                elif name == "approval_required":
                    # Bridge policy: auto-allow inside the walled demo workspace,
                    # visibly. (The seam a production controller would gate.)
                    call_id = ev.get("call_id") or ""
                    print(f"{self.tag} ✋ approval: {ev.get('tool')} → auto-allow (demo policy)",
                          flush=True)
                    self.child.send({"op": "approve", "call_id": call_id, "decision": "allow"})
                elif name == "ask_user":
                    self.child.send({"op": "answer", "text": ASK_USER_NOTE})
                elif name == "final":
                    self.status = str(ev.get("status") or "")
                    self.answer = str(ev.get("answer") or "")
                    err = ev.get("error")
                    if err:
                        print(f"{self.tag} turn ended {self.status}: {str(err)[:200]}", flush=True)
                    self._publish_changed()
                    self._deliver()
                    return
        finally:
            self.done.set()

    def _deliver(self) -> None:
        """Bridge-owned delivery of the final answer to the origin."""
        answer = self.answer.strip()
        if not answer or not self.origin_channel:
            return
        try:
            if self.origin_channel.startswith("dm:"):
                if self.origin_sender and self.origin_sender != self.self_name:
                    _agora("POST",
                           f"/dms/{urllib.parse.quote(self.origin_sender, safe='')}/messages",
                           payload={"body": answer, "status": "reply"})
                    print(f"{self.tag} → delivered reply to {self.origin_sender} (dm)", flush=True)
            else:
                _agora("POST", f"/channels/{urllib.parse.quote(self.origin_channel, safe='')}/messages",
                       payload={"body": answer, "status": "reply"})
                print(f"{self.tag} → delivered reply to #{self.origin_channel}", flush=True)
        except Exception as e:
            print(f"{self.tag} delivery error (answer preserved in log): {e}", flush=True)


# ---------------------------------------------------------------------------
# Bridge main loop: identical hub semantics to headless_steer_repl (filter,
# ack, stop token, pending obligations), turns dispatched to the serve child.
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--channel", required=True)
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--name", required=True, help="this agent's agora id")
    ap.add_argument("--provider", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--agent", default="react", help="react | codeact | memact")
    ap.add_argument("--abstractcode", default=str(ROOT / ".venv" / "bin" / "abstractcode"),
                    help="abstractcode executable (default: workspace venv)")
    ap.add_argument("--max-iterations", type=int, default=16)
    ap.add_argument("--poll-wait", type=float, default=25.0)
    ap.add_argument("--idle-polls-before-exit", type=int, default=0)
    args = ap.parse_args()

    name, tag = args.name, f"[{args.name}]"
    workspace = Path(args.workspace).expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    child = ServeChild(args, workspace, tag)
    # Wait for the child's ready line before touching the hub.
    try:
        ev = child.events.get(timeout=SERVE_READY_GAP_S)
        if str(ev.get("event")) != "ready":
            print(f"{tag} unexpected first serve event: {ev}", flush=True)
    except queue.Empty:
        # #[WARNING:TIMEOUT] ADR-0027 §1 — duration + component + knob.
        print(
            f"{tag} #[WARNING:TIMEOUT] headless_fleet_bridge: serve child never became "
            f"ready within {SERVE_READY_GAP_S}s (startup handshake only; "
            f"ABSTRACTCODE_BRIDGE_SERVE_READY_S, 0 = wait forever)",
            flush=True,
        )
        child.shutdown()
        return 1
    print(f"{tag} bridge up — serve pid {child.proc.pid}, channel={args.channel}, "
          f"workspace={workspace}, {args.provider}:{args.model}", flush=True)

    try:
        _agora("POST", f"/channels/{urllib.parse.quote(args.channel, safe='')}/join", payload={})
    except Exception as e:
        print(f"{tag} join note: {e}", flush=True)

    seen_seq: Dict[str, int] = {}
    empty_polls = 0
    turn: Optional[Turn] = None
    pending_obligations: List[str] = []

    def running() -> bool:
        return turn is not None and not turn.done.is_set()

    try:
        while True:
            if not child.alive():
                print(f"{tag} serve child died (exit {child.proc.poll()}) — bridge exiting",
                      flush=True)
                return 1

            if not running() and pending_obligations:
                items = "\n\n".join(f"--- item {i+1} ---\n{b}"
                                    for i, b in enumerate(pending_obligations))
                pending_obligations.clear()
                task = (f"You are '{name}' on the agora channel '{args.channel}'. While you "
                        f"were working, these message(s) were folded into your turn as "
                        f"guidance. For EACH, verify honestly whether you completed what it "
                        f"asks; complete anything missed (a VOTE means DM the chair your "
                        f"ballot EXACTLY as instructed). If all handled, finish with one "
                        f"line.\n\n{items}")
                print(f"{tag} follow-up turn for steered-in obligation(s)", flush=True)
                turn = Turn(child, task, tag, workspace=workspace,
                            publish_channel=args.channel)
                turn.start()
                continue

            try:
                envelopes = _agora("GET", "/inbox", query={"wait": args.poll_wait}) or []
            except Exception as e:
                print(f"{tag} inbox poll error: {e}", flush=True)
                time.sleep(5)
                continue

            fresh: List[Dict[str, Any]] = []
            cursor_moved = False
            for env in envelopes if isinstance(envelopes, list) else []:
                ch = str(env.get("channel") or "")
                seq = int(env.get("seq") or 0)
                sender = str(env.get("sender") or env.get("from") or "")
                if not ch or seq <= seen_seq.get(ch, 0):
                    continue
                seen_seq[ch] = seq
                cursor_moved = True
                if sender in (name, "hub"):
                    continue
                status = str(env.get("status") or "")
                addressed = (bool(env.get("to_me")) or bool(env.get("reply_to_me"))
                             or ch.startswith("dm:") or status in ("open", "blocked"))
                if addressed:
                    fresh.append(env)

            if cursor_moved:
                try:
                    _agora("POST", "/inbox/ack", payload={"cursors": dict(seen_seq)})
                except Exception:
                    pass
            else:
                time.sleep(min(5.0, args.poll_wait))

            if not fresh:
                if not running():
                    empty_polls += 1
                    if args.idle_polls_before_exit and empty_polls >= args.idle_polls_before_exit:
                        print(f"{tag} idle exit after {empty_polls} empty polls", flush=True)
                        return 0
                continue
            empty_polls = 0

            for env in fresh:
                sender = str(env.get("sender") or env.get("from") or "?")
                ch = str(env.get("channel") or args.channel)
                body = env.get("body")
                if not body:
                    try:
                        msgs = _agora("GET",
                                      f"/channels/{urllib.parse.quote(ch, safe='')}/messages/"
                                      f"{urllib.parse.quote(str(env.get('id') or ''), safe='')}")
                        if isinstance(msgs, list) and msgs:
                            body = str(msgs[-1].get("body") or "")
                    except Exception:
                        body = ""
                body = str(body or env.get("title") or "")

                if STOP_TOKEN in body:
                    print(f"{tag} stop signal received — exiting", flush=True)
                    if running():
                        child.send({"op": "cancel"})
                        turn.done.wait(timeout=20)
                    return 0

                if running():
                    turn.steer(
                        f"New hub message from '{sender}' on '{ch}' while you work:\n{body}\n"
                        f"Fold it into your current work if relevant (a VOTE means: cast "
                        f"your ballot as instructed before finishing); otherwise finish "
                        f"your task first.")
                    if str(env.get("status") or "") in ("open", "blocked"):
                        pending_obligations.append(body)
                    continue

                is_dm = ch.startswith("dm:")
                reply_route = (f"a direct message back to '{sender}'" if is_dm
                               else f"a reply in '{ch}'")
                task = (
                    f"You are '{name}', a headless agent on the agora hub. A message "
                    f"arrived from '{sender}' via "
                    f"{'a direct message' if is_dm else f'channel {ch}'}:\n\n{body}\n\n"
                    f"Answer it / do the work autonomously, then STOP with your reply as "
                    f"your final answer. Delivery is automatic: your final answer is sent "
                    f"as {reply_route} by the bridge — do NOT call agora_send_dm or "
                    f"agora_post_message just to reply to '{sender}' (double-send). Use "
                    f"tools for the WORK: files under {workspace}; web_search/fetch_url "
                    f"for live info; agora tools for collaboration WITH PEERS on "
                    f"'{args.channel}' (separate from replying). If you cannot do "
                    f"something, say so plainly — that IS the reply. Keep it tight.")
                print(f"{tag} ← task from {sender} on {ch}: {body[:120].strip()}", flush=True)
                turn = Turn(child, task, tag, origin_channel=ch,
                            origin_sender=sender, self_name=name,
                            workspace=workspace, publish_channel=args.channel)
                turn.start()
    finally:
        child.shutdown()


if __name__ == "__main__":
    _unsupported()
    raise SystemExit(main())
