#!/usr/bin/env python3
"""Headless steering driver — a resident agent driven by the agora hub, not a TTY.

This is scripts/steer_repl.py with the human REPL replaced by the AGORA HUB as
the steering surface. It is the demo vehicle for the hooks-first-class end
product (plans/hooks-first-class.md): a headless agent that

  - LISTENS to its own actions via the react loop's `on_step` (printed with the
    agent's name so a fleet's logs interleave readably),
  - is CONTACTED/ORCHESTRATED by the hub: it long-polls the agora inbox and an
    addressed message becomes the turn's task (idle) or a mid-run STEER
    (`inject_message`, the same durable-inbox seam the gateway uses),
  - COLLABORATES over the FULL agora model: the agent is handed tools for the
    channel (1:N / N:N), DMs (1:1), the per-channel SHARED FILESYSTEM (fs/),
    and the per-channel SHARED STORE (used here as a ballot box for a vote),
    plus a workspace-walled file toolset for its own artifacts,
  - re-PARKS when idle and exits cleanly on a `stop` control.

Identity is per-PROCESS: one driver = one agora agent, its key + URL in the
process env (AGORA_API_KEY / AGORA_URL). Three of these = the fleet. No
gateway, no bridge — the simplest honest shape for a reproducible example
(the gateway-hosted resident + a2a bridge remains the production shape in the
plan).

Usage:
    AGORA_API_KEY=... AGORA_URL=http://127.0.0.1:8791 \
    .venv/bin/python scripts/headless_steer_repl.py \
        --channel build-demo --workspace /tmp/fleet/agent-a --name agent-a \
        --provider endpoint:ovh-provider --model gpt-oss-120b
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent

for rel in ("abstractgateway/src", "abstractruntime/src", "abstractmemory/src",
            "abstractagent/src", "abstractcore"):
    p = str(ROOT / rel)
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    import abstractruntime  # noqa: F401
except ImportError:
    venv_py = ROOT / ".venv" / "bin" / "python"
    if venv_py.exists() and Path(sys.executable).resolve() != venv_py.resolve():
        os.execv(str(venv_py), [str(venv_py), *sys.argv])
    raise

from abstractruntime import RunStatus  # noqa: E402
from abstractruntime.integrations.abstractcore import (  # noqa: E402
    MappingToolExecutor,
    create_local_runtime,
)
from abstractruntime.integrations.abstractcore.agora_tools import (  # noqa: E402
    agora_ack_inbox,
    agora_check_inbox,
    agora_post_message,
    agora_read_channel,
    agora_send_dm,
)
from abstractcore.tools.core import tool  # noqa: E402
from abstractagent import LoopHooks  # noqa: E402  (first-class hooks, agent P0)
from abstractagent.agents.react import ReactAgent  # noqa: E402


# ---------------------------------------------------------------------------
# agora HTTP helper (stdlib only; same contract as agora_tools._request, but
# local so the demo is self-contained and can add the fs/store surfaces the
# shipped runtime toolset doesn't yet expose).
# ---------------------------------------------------------------------------

def _agora_url() -> str:
    return str(os.getenv("AGORA_URL") or "http://127.0.0.1:8765").strip().rstrip("/")


def _agora_key() -> str:
    key = str(os.getenv("AGORA_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("AGORA_API_KEY is not set for this driver process")
    return key


def _agora_request(method: str, path: str, *, payload: Optional[dict] = None,
                   query: Optional[dict] = None, timeout_s: float = 20.0) -> Any:
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
# The shared-filesystem + shared-store tools the demo agent needs (the shipped
# runtime toolset stops at messaging; these expose the channel's fs/ and store,
# scoped to ONE channel bound at driver start so the model can't wander).
# ---------------------------------------------------------------------------

def build_shared_tools(channel: str) -> List[Any]:
    qc = urllib.parse.quote(str(channel), safe="")
    qp = lambda s: urllib.parse.quote(str(s), safe="/")  # fs paths may contain '/'  # noqa: E731

    @tool(name="channel_fs_write",
          description="Write a file to the SHARED channel filesystem (visible to every member).",
          when_to_use="To publish an artifact the whole channel should see/build on.")
    def channel_fs_write(*, path: str, content: str) -> Dict[str, Any]:
        p = str(path or "").strip().lstrip("/")
        if not p:
            raise ValueError("path is required")
        return _agora_request("PUT", f"/channels/{qc}/fs/{qp(p)}",
                              payload={"content": str(content or ""),
                                       "mime": "text/plain"}) or {"ok": True, "path": p}

    @tool(name="channel_fs_read",
          description="Read a file from the SHARED channel filesystem.",
          when_to_use="To read a teammate's published artifact before building on it.")
    def channel_fs_read(*, path: str) -> Dict[str, Any]:
        p = str(path or "").strip().lstrip("/")
        return _agora_request("GET", f"/channels/{qc}/fs/{qp(p)}") or {"path": p, "content": ""}

    @tool(name="channel_fs_list",
          description="List files in the SHARED channel filesystem (paths + versions).",
          when_to_use="To see what teammates have published so far.")
    def channel_fs_list(*, prefix: str = "") -> List[Dict[str, Any]]:
        res = _agora_request("GET", f"/channels/{qc}/fs",
                             query={"prefix": prefix} if prefix else None)
        return res if isinstance(res, list) else []

    @tool(name="channel_store_set",
          description="Set a key in the shared channel STORE (team coordination state / decisions).",
          when_to_use="To record a shared decision or claim a work item (key like 'claim:<item>').")
    def channel_store_set(*, key: str, value: str) -> Dict[str, Any]:
        k = str(key or "").strip()
        if not k:
            raise ValueError("key is required")
        return _agora_request("PUT", f"/channels/{qc}/store/{urllib.parse.quote(k, safe='')}",
                              payload={"value": value}) or {"ok": True, "key": k}

    @tool(name="channel_store_get",
          description="Read a key from the shared channel STORE.",
          when_to_use="To read a shared decision or claim before acting.")
    def channel_store_get(*, key: str) -> Dict[str, Any]:
        k = str(key or "").strip()
        return _agora_request("GET", f"/channels/{qc}/store/{urllib.parse.quote(k, safe='')}") \
            or {"key": k, "value": None}

    return [channel_fs_write, channel_fs_read, channel_fs_list, channel_store_set, channel_store_get]


# ---------------------------------------------------------------------------
# Listen feed: first-class LoopHooks (abstractagent P0 ship) — the CANONICAL
# hook vocabulary (cycle_start / tool_proposed / tool_executed / turn_end /
# message_drained / hook_error), prefixed with the agent name so a 3-driver
# run interleaves readably in one terminal / log. This replaces the raw
# on_step feed: the demo consumes the same capture surface any programmatic
# host (reprompter, reviewer, memory process) would.
# ---------------------------------------------------------------------------

# The turn's final answer, captured from the loop's turn_end hook so the
# DRIVER can deliver it (bridge-owned delivery — the model must never be
# relied on to self-send its reply; see the telegram-bridge lesson). Turns
# are strictly sequential (one Driver at a time, gated by running()), so a
# single holder is safe; the Driver clears it at turn start.
_LAST_ANSWER: Dict[str, str] = {"text": ""}


def make_listen_hooks(name: str) -> LoopHooks:
    tag = f"[{name}]"

    def listener(ev) -> None:  # HookEvent → pure listen (returns nothing)
        d = ev.data or {}
        if ev.name == "cycle_start":
            g = " (+guidance)" if d.get("has_guidance") else ""
            print(f"{tag} ⟲ cycle {d.get('iteration')}/{d.get('max_iterations')}{g}",
                  flush=True)
        elif ev.name == "tool_proposed":
            print(f"{tag}   the model wants {d.get('count')} tool call(s)", flush=True)
        elif ev.name == "tool_executed":
            ok = "ok" if d.get("success") else "ERROR"
            print(f"{tag}   {d.get('tool')} → {ok}", flush=True)
        elif ev.name == "turn_end":
            if d.get("outcome") == "iteration_budget":
                print(f"{tag} ✖ hit max_iterations", flush=True)
            else:
                ans = str(d.get("answer") or "")
                _LAST_ANSWER["text"] = ans  # capture for driver-owned delivery
                print(f"{tag} ✔ done: {ans.strip().replace(chr(10), ' ')[:200]}", flush=True)
        elif ev.name == "message_drained":
            print(f"{tag} ⇣ guidance drained into the reason cycle", flush=True)
        elif ev.name == "hook_error":
            print(f"{tag} ⚠ hook_error: {d.get('error')}", flush=True)

    return LoopHooks(agent=name).add(listener)


# ---------------------------------------------------------------------------
# Provider/model resolution (reused from steer_repl's gateway-baseline logic).
# ---------------------------------------------------------------------------

def _resolve_endpoint_profile(provider: str, llm_kwargs: dict) -> str:
    """endpoint:<name> providers resolve to family + base_url + api_key via the
    gateway's profile store (searched across the known data dirs)."""
    if not provider.startswith("endpoint:"):
        return provider
    from abstractgateway.provider_endpoint_profiles import ProviderEndpointProfileStore
    name = provider.split(":", 1)[1]
    for base in (Path(os.getenv("ABSTRACTGATEWAY_DATA_DIR") or (ROOT / "runtime")),
                 ROOT / "runtime", ROOT / "runtime-data"):
        try:
            profile = ProviderEndpointProfileStore(base_dir=base).get_profile(name)
        except Exception:
            continue
        if profile is None:
            continue
        if profile.base_url:
            llm_kwargs["base_url"] = profile.base_url
        if profile.api_key:
            llm_kwargs["api_key"] = profile.api_key
        return profile.provider_family
    sys.exit(f"error: provider connection {provider!r} not found in any gateway data dir")


def resolve_provider_model(args) -> tuple[str, str, dict]:
    if args.provider and args.model:
        llm_kwargs: dict = {}
        provider = _resolve_endpoint_profile(str(args.provider), llm_kwargs)
        return provider, str(args.model), llm_kwargs
    for base in (Path(os.getenv("ABSTRACTGATEWAY_DATA_DIR") or (ROOT / "runtime")),
                 ROOT / "runtime", ROOT / "runtime-data"):
        cfg = base / "config" / "abstractcore.json"
        if not cfg.is_file():
            continue
        try:
            routes = (json.loads(cfg.read_text()).get("capability_defaults") or {}).get("routes") or {}
            route = routes.get("input.text") or {}
            provider = str(route.get("provider") or "").strip()
            model = str(route.get("model") or "").strip()
        except Exception:
            continue
        if not (provider and model):
            continue
        llm_kwargs = {}
        if isinstance(route.get("base_url"), str) and route["base_url"].strip():
            llm_kwargs["base_url"] = route["base_url"].strip()
        provider = _resolve_endpoint_profile(provider, llm_kwargs)
        return provider, model, llm_kwargs
    sys.exit("error: no provider/model (pass --provider/--model or configure a gateway baseline)")


# ---------------------------------------------------------------------------
# The headless resident loop: park on the inbox, wake on an addressed message,
# run a react turn in a background Driver thread while the MAIN thread keeps
# polling — new addressed traffic during a run becomes a mid-run STEER
# (inject_message), exactly the steer_repl seam without the TTY.
# ---------------------------------------------------------------------------

STOP_TOKEN = "##FLEET-STOP##"


class Driver(threading.Thread):
    """Ticks one react turn to terminal (steer_repl's Driver, headless: an
    ask_user wait is auto-answered once so the turn never wedges on a dead
    stdin). Steers queued by the main thread are injected at tick boundaries
    (single-writer discipline: only this thread touches the run)."""

    def __init__(self, agent, task: str, log_tag: str, *,
                 origin_channel: str = "", origin_sender: str = "", self_name: str = ""):
        super().__init__(name="agent-driver", daemon=True)
        self.agent = agent
        self.task = task
        self.log_tag = log_tag
        # Delivery target: where the reply must be SENT by the driver (never
        # left to the model to self-send — the delivery-gap bug, 2026-07-13).
        self.origin_channel = origin_channel
        self.origin_sender = origin_sender
        self.self_name = self_name
        self.steer_q: "queue.Queue[str]" = queue.Queue()
        self.done = threading.Event()

    def run(self) -> None:
        _LAST_ANSWER["text"] = ""  # clear so a mute turn can't deliver a stale answer
        try:
            self.agent.start(self.task)
            while True:
                try:
                    while True:
                        msg = self.steer_q.get_nowait()
                        self.agent.inject_message(msg)
                        print(f"{self.log_tag} ↪ steer folded into next cycle: "
                              f"{msg[:120]}", flush=True)
                except queue.Empty:
                    pass
                state = self.agent.step()
                st = state.status
                if st in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED):
                    if st == RunStatus.FAILED:
                        print(f"{self.log_tag} run FAILED: {state.error}", flush=True)
                    else:
                        self._deliver()
                    return
                if st == RunStatus.WAITING:
                    w = getattr(state, "waiting", None)
                    if w and not str(getattr(w, "wait_key", "")).startswith("pause:"):
                        self.agent.resume("(no human is attached; proceed with your "
                                          "best judgment and finish your part.)")
                    else:
                        time.sleep(0.2)
        except Exception as e:  # never let a turn error kill the resident
            print(f"{self.log_tag} turn error: {e}", flush=True)
        finally:
            self.done.set()

    def _deliver(self) -> None:
        """Driver-owned delivery: SEND the turn's final answer back to the
        message's origin. The model produces the answer; the driver guarantees
        it reaches the asker — the bug this fixes is a model that ends a turn
        with `done` but never calls a send tool, so the reply died in the log
        (laurent's 2nd DM, 2026-07-13). DM origin → send_dm to the sender;
        channel origin → post a reply. No origin (fleet-internal turns) →
        nothing, the model's own channel posts stand."""
        answer = (_LAST_ANSWER.get("text") or "").strip()
        if not answer or not self.origin_channel:
            return
        try:
            if self.origin_channel.startswith("dm:"):
                if self.origin_sender and self.origin_sender != self.self_name:
                    agora_send_dm(peer=self.origin_sender, body=answer, status="reply")
                    print(f"{self.log_tag} → delivered reply to {self.origin_sender} (dm)",
                          flush=True)
            else:
                agora_post_message(channel=self.origin_channel, body=answer, status="reply")
                print(f"{self.log_tag} → delivered reply to #{self.origin_channel}", flush=True)
        except Exception as e:
            print(f"{self.log_tag} delivery error (answer preserved in log): {e}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--channel", required=True, help="the agora channel the fleet collaborates on")
    ap.add_argument("--workspace", required=True, help="this agent's own file workspace (walled)")
    ap.add_argument("--name", required=True, help="this agent's agora id (for log prefixing)")
    ap.add_argument("--provider", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-iterations", type=int, default=16)
    ap.add_argument("--idle-polls-before-exit", type=int, default=0,
                    help="exit after N consecutive empty long-polls (0 = run until stopped)")
    ap.add_argument("--poll-wait", type=float, default=25.0)
    args = ap.parse_args()

    name = args.name
    tag = f"[{name}]"
    workspace = Path(args.workspace).expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    provider, model, llm_kwargs = resolve_provider_model(args)

    # File tools + the agora collaboration tools. The file tools resolve
    # relative paths against CWD, so the driver chdirs into its workspace
    # (the task text also names it); real walling is a runtime/gateway
    # concern, out of scope for this in-process demo driver.
    from abstractcore.tools.common_tools import (
        fetch_url, list_files, read_file, web_search, write_file,
    )
    os.chdir(workspace)
    workspace_tools = [write_file, read_file, list_files]
    web_tools = [web_search, fetch_url]  # laurent 2026-07-13: give residents the web lane
    agora_msg_tools = [agora_post_message, agora_send_dm, agora_read_channel, agora_check_inbox]
    shared_tools = build_shared_tools(args.channel)
    tools = workspace_tools + web_tools + agora_msg_tools + shared_tools

    runtime = create_local_runtime(
        provider=provider, model=model, llm_kwargs=llm_kwargs or None,
        tool_executor=MappingToolExecutor.from_tools(tools),
    )
    agent = ReactAgent(runtime=runtime, tools=tools, hooks=make_listen_hooks(name),
                       max_iterations=args.max_iterations)

    # Join the channel (idempotent) so inbox long-poll delivers its traffic.
    try:
        _agora_request("POST", f"/channels/{urllib.parse.quote(args.channel, safe='')}/join",
                      payload={})
    except Exception as e:
        print(f"{tag} join note: {e}", flush=True)

    print(f"{tag} resident up — channel={args.channel} workspace={workspace} "
          f"provider={provider} model={model}", flush=True)

    seen_seq: Dict[str, int] = {}
    empty_polls = 0
    driver: Optional[Driver] = None
    # OPEN obligations steered into a running turn may land after the last
    # reason-cycle drain and die with the run (observed live: a VOTE folded in
    # at the final cycle was never acted on). They stay pending until a turn
    # BEGUN after their arrival completes — then one follow-up verification
    # turn handles any that were missed. fyi steers are advisory: no follow-up.
    pending_obligations: List[str] = []

    def running() -> bool:
        return driver is not None and not driver.done.is_set()

    while True:
        if not running() and pending_obligations:
            items = "\n\n".join(f"--- item {i + 1} ---\n{b}"
                                for i, b in enumerate(pending_obligations))
            pending_obligations.clear()
            task = (
                f"You are '{name}' on the agora channel '{args.channel}'. While you were "
                f"working, the following message(s) arrived and were folded into your turn "
                f"as guidance. For EACH item, verify honestly whether you actually completed "
                f"what it asks; complete anything you did not (e.g. a VOTE means DM the "
                f"chair your ballot line EXACTLY as instructed — do it now if you have not). "
                f"If everything was already handled, do nothing further and finish with a "
                f"one-line confirmation.\n\n{items}"
            )
            print(f"{tag} follow-up turn for steered-in obligation(s)", flush=True)
            driver = Driver(agent, task, tag)
            driver.start()
            continue

        try:
            envelopes = agora_check_inbox(wait_seconds=args.poll_wait)
        except Exception as e:
            print(f"{tag} inbox poll error: {e}", flush=True)
            time.sleep(5)
            continue

        # Only act on genuinely-new, addressed traffic on our channel/DMs; never
        # on our own posts. Envelope truth (agora models.Envelope): to_me /
        # reply_to_me are hub-computed booleans; status open/blocked is an
        # obligation; DM channels are addressed by construction.
        fresh: List[Dict[str, Any]] = []
        cursor_moved = False
        for env in envelopes:
            ch = str(env.get("channel") or "")
            seq = int(env.get("seq") or 0)
            sender = str(env.get("sender") or env.get("from") or "")
            if not ch:
                continue
            if seq <= seen_seq.get(ch, 0):
                continue
            seen_seq[ch] = seq
            cursor_moved = True
            # Never treat our own posts or HUB SYSTEM notices (channel-created,
            # "direct channel between X and Y", joined) as tasks — the hub is
            # not a peer asking for work (fix: athena ran a turn on the DM
            # channel-creation notice, 2026-07-13).
            if sender == name or sender == "hub":
                continue
            status = str(env.get("status") or "")
            addressed = (bool(env.get("to_me")) or bool(env.get("reply_to_me"))
                         or ch.startswith("dm:") or status in ("open", "blocked"))
            if addressed:
                fresh.append(env)

        # Ack everything we saw (fresh or not) so the hub stops re-delivering.
        if cursor_moved:
            try:
                agora_ack_inbox(cursors=dict(seen_seq))
            except Exception:
                pass
        else:
            # Undischarged open/blocked messages are STICKY in the hub inbox
            # (deliberate: obligations cannot rot away behind an ack) — the
            # long-poll returns them instantly, which would spin this loop.
            # Nothing new ⇒ floor sleep; fresh traffic still lands within it.
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
            if not body:  # large/low-urgency bodies arrive envelope-only: fetch
                try:
                    msgs = _agora_request(
                        "GET",
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
                    agent.cancel("fleet stop")
                    driver.done.wait(timeout=15)
                return 0

            if running():
                # Mid-run steering FROM THE HUB — the headless twin of the
                # steer_repl keyboard path (inject_message at the next cycle).
                driver.steer_q.put(
                    f"New hub message from '{sender}' on '{ch}' while you work:\n{body}\n"
                    f"Fold it into your current work if relevant (a VOTE message means: "
                    f"cast your ballot as instructed before finishing); otherwise finish "
                    f"your task first."
                )
                if str(env.get("status") or "") in ("open", "blocked"):
                    # An obligation: keep it until a post-arrival turn confirms it.
                    pending_obligations.append(body)
                continue

            is_dm = ch.startswith("dm:")
            reply_route = (f"a direct message back to '{sender}'" if is_dm
                           else f"a reply in '{ch}'")
            task = (
                f"You are '{name}', a headless agent on the agora hub. A message arrived "
                f"from '{sender}' via {'a direct message' if is_dm else f'channel {ch}'}:\n\n"
                f"{body}\n\n"
                f"Answer it / do the work autonomously, then STOP with your reply as your "
                f"final answer. Delivery is automatic: your final answer is sent as "
                f"{reply_route} by the runtime — do NOT call agora_send_dm or "
                f"agora_post_message just to reply to '{sender}' (that would double-send). "
                f"Use tools for the WORK, not for the reply:\n"
                f"- web_search / fetch_url for live information from the internet.\n"
                f"- write_file / read_file / list_files for your own files (under {workspace}).\n"
                f"- agora_read_channel, channel_fs_list/read/write, channel_store_* for "
                f"collaboration WITH PEERS on '{args.channel}' (publish shared artifacts, cast "
                f"votes) — this is separate from replying to the asker.\n"
                f"- If a VOTE with a blind-ballot contract is in play, follow it EXACTLY "
                f"(DM the chair your ballot line).\n"
                f"If you cannot do something (e.g. a missing capability), say so plainly in "
                f"your final answer — that IS the reply. Keep it tight; do not loop."
            )
            print(f"{tag} ← task from {sender} on {ch}: {body[:120].strip()}", flush=True)
            driver = Driver(agent, task, tag, origin_channel=ch,
                            origin_sender=sender, self_name=name)
            driver.start()


if __name__ == "__main__":
    raise SystemExit(main())
