#!/usr/bin/env python3
"""Steering REPL — minimal proof that a runtime-hosted agent is observable and steerable.

What it demonstrates, using only existing framework primitives (no patches):
- realtime visibility: the agent's `on_step` callback (semantic: cycle N, observe, done)
  AND the durable ledger subscription (the same channel the gateway streams over SSE).
- mid-run steering: `BaseAgent.inject_message()` -> `_runtime.inbox`, drained at the top
  of the next reason cycle (the in-process twin of the gateway `inject_guidance` command).
- durable controls: `Runtime.pause_run` / `resume_run` / `cancel_run`.

Provider/model resolve from the GATEWAY BASELINE: `<gateway data dir>/config/abstractcore.json`
route `input.text` (the same default shown in the AbstractGateway Console), including
`endpoint:*` provider connections (resolved via the gateway's ProviderEndpointProfileStore).
Override with --provider/--model.

Usage (from the monorepo root):
    .venv/bin/python scripts/steer_repl.py            # or just scripts/steer_repl.py

REPL commands:
    <text>            idle: start a new task | running: steer the agent | ask_user: answer
    /steer <text>     explicitly steer the running agent
    /pause            pause at the next commit point (a blocking LLM call finishes first)
    /resume           resume a paused run
    /cancel           cancel the run (terminal)
    /status           show run status
    /wait             block until the current run finishes (useful for scripting)
    /quit             exit (cancels an active run)
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Local-checkout bootstrap (same set as scripts/lib/apps_common.sh local_pythonpath,
# plus abstractagent which the shell helper doesn't need but we do).
for rel in ("abstractgateway/src", "abstractruntime/src", "abstractmemory/src", "abstractagent/src", "abstractcore"):
    p = str(ROOT / rel)
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    import abstractruntime  # noqa: F401
except ImportError:  # re-exec under the repo venv when run with a bare system python
    venv_py = ROOT / ".venv" / "bin" / "python"
    if venv_py.exists() and Path(sys.executable).resolve() != venv_py.resolve():
        os.execv(str(venv_py), [str(venv_py), *sys.argv])
    raise

from abstractruntime import RunStatus  # noqa: E402
from abstractruntime.integrations.abstractcore import MappingToolExecutor, create_local_runtime  # noqa: E402
from abstractagent.agents.react import ReactAgent  # noqa: E402

try:
    import readline  # enables line editing + lets us repaint the input buffer
except ImportError:  # pragma: no cover
    readline = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Terminal output: colors + an input line that stays separate from the feed.
# Background prints clear the pending input line, emit the event, then repaint
# the prompt with whatever the user had already typed (readline buffer).
# ---------------------------------------------------------------------------

_TTY = sys.stdout.isatty()
_PRINT_LOCK = threading.Lock()
_INPUT_ACTIVE = threading.Event()
PROMPT = "you> "  # keep uncolored: ANSI in input() prompts confuses readline width math


def c(code: str, text: str) -> str:
    return f"\x1b[{code}m{text}\x1b[0m" if _TTY else text


DIM, BOLD = "2", "1"
CYAN, YELLOW, MAGENTA, GREEN, RED, BLUE = "36", "33", "35", "32", "31", "34"


def say(text: str) -> None:
    with _PRINT_LOCK:
        if _TTY and _INPUT_ACTIVE.is_set():
            buf = readline.get_line_buffer() if readline else ""
            sys.stdout.write("\r\x1b[2K" + text + "\n" + PROMPT + buf)
        else:
            sys.stdout.write(text + "\n")
        sys.stdout.flush()


def _trunc(value, n: int = 160) -> str:
    text = str(value or "").strip().replace("\n", " ")
    return text if len(text) <= n else text[: n - 1] + "…"


# ---------------------------------------------------------------------------
# Realtime feed 1: semantic agent steps (in-process on_step callback)
# ---------------------------------------------------------------------------

def on_step(step: str, data: dict) -> None:
    if step == "reason":
        head = c(f"{BOLD};{YELLOW}", f"⟲ cycle {data.get('iteration')}/{data.get('max_iterations')}")
        guided = "  " + c(f"{BOLD};{MAGENTA}", "← guidance folded in") if data.get("has_guidance") else ""
        say("\n" + head + c(DIM, " thinking…") + guided)
    elif step == "parse_tool_calls":
        say(c(DIM, f"  the model wants {data.get('count')} tool call(s)"))
    elif step == "parse":  # memact/codeact vocabulary (codeact's emit carries no tool_calls list)
        if data.get("has_tool_calls"):
            n = len(data.get("tool_calls") or [])
            say(c(DIM, f"  the model wants {n} tool call(s)" if n else "  the model requested tool calls"))
    elif step == "act":
        say(c(DIM, f"  acting: {data.get('tool')}"))
    elif step in ("finalize_request", "finalize"):
        say(c(DIM, f"  {step.replace('_', ' ')}…"))
    elif step == "observe":
        ok = c(GREEN, "ok") if data.get("success") else c(f"{BOLD};{RED}", "ERROR")
        say(f"  {c(BOLD, str(data.get('tool')))} → {ok} {c(DIM, _trunc(data.get('result')))}")
    elif step == "act_blocked":
        say(c(RED, f"  tool blocked by allowlist: {data.get('tool')}"))
    elif step == "ask_user":
        say(c(f"{BOLD};{CYAN}", f"? agent asks: {data.get('question')}") + c(DIM, "  (type your answer)"))
    elif step == "done":
        say("\n" + c(f"{BOLD};{GREEN}", "✔ final answer") + "\n" + str(data.get("answer") or "") + "\n")
    elif step == "max_iterations":
        say("\n" + c(f"{BOLD};{RED}", f"✖ stopped: hit max_iterations={data.get('iterations')}") + "\n")
    elif step.startswith("parse_retry"):
        say(c(DIM, f"  {step}"))


# ---------------------------------------------------------------------------
# Realtime feed 2: durable ledger records (what the gateway streams over SSE)
# ---------------------------------------------------------------------------

def make_ledger_printer(run_id_ref: dict):
    def _led(text: str) -> None:
        say(c(f"{DIM};{BLUE}", f"    · {text}"))

    def _on_record(rec: dict) -> None:
        if rec.get("run_id") != run_id_ref.get("run_id"):
            return
        effect = rec.get("effect") or {}
        etype = str(effect.get("type") or "")
        # StepStatus is a str-subclass enum: it == "started" but str() would give "StepStatus.STARTED".
        raw_status = rec.get("status")
        status = getattr(raw_status, "value", raw_status if isinstance(raw_status, str) else "")
        payload = effect.get("payload") or {}
        if etype == "tool_calls" and status == "started":
            for tc in payload.get("tool_calls") or []:
                if isinstance(tc, dict):
                    _led(f"ledger: tool STARTED {tc.get('name')}({_trunc(tc.get('arguments'), 100)})")
        elif etype == "tool_calls" and status == "completed":
            _led("ledger: tool COMPLETED")
        elif etype == "llm_call" and status == "started":
            _led(f"ledger: llm_call STARTED (node {rec.get('node_id')})")
        elif etype == "emit_event" and payload.get("name") == "abstract.status":
            _led(f"ledger: run status → {(payload.get('payload') or {}).get('text')}")

    return _on_record


# ---------------------------------------------------------------------------
# Driver: ticks the run on a background thread; applies steering between ticks
# (single-writer discipline — the same seam the gateway's tick worker owns).
# ---------------------------------------------------------------------------

class Driver(threading.Thread):
    def __init__(self, agent, steer_q: "queue.Queue[str]"):
        super().__init__(name="agent-driver", daemon=True)
        self.agent = agent
        self.steer_q = steer_q
        self.done = threading.Event()

    def run(self) -> None:
        try:
            while True:
                try:
                    while True:
                        msg = self.steer_q.get_nowait()
                        self.agent.inject_message(msg)
                        say(c(MAGENTA, f"↪ steer queued for the next cycle: {_trunc(msg, 120)}"))
                except queue.Empty:
                    pass

                state = self.agent.step()
                if state.status in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED):
                    if state.status == RunStatus.FAILED:
                        say("\n" + c(f"{BOLD};{RED}", f"✖ run FAILED: {state.error}") + "\n")
                    elif state.status == RunStatus.CANCELLED:
                        say("\n" + c(f"{BOLD};{RED}", "■ run CANCELLED") + "\n")
                    return
                if state.status == RunStatus.WAITING:
                    # paused, ask_user, or another durable wait: step() is a no-op; idle-poll.
                    time.sleep(0.3)
        finally:
            self.done.set()


# ---------------------------------------------------------------------------
# Provider/model resolution — gateway baseline first (what the Console shows).
# ---------------------------------------------------------------------------

def _gateway_data_dir_candidates() -> list[Path]:
    out: list[Path] = []
    env = os.getenv("ABSTRACTGATEWAY_DATA_DIR")
    if env:
        out.append(Path(env).expanduser())
    out += [ROOT / "runtime", ROOT / "runtime-data"]
    return out


def resolve_provider_model(args) -> tuple[str, str, str, dict]:
    """Returns (provider, model, source_label, llm_kwargs)."""
    if args.provider and args.model:
        return args.provider, args.model, "cli", {}

    for base in _gateway_data_dir_candidates():
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

        llm_kwargs: dict = {}
        if isinstance(route.get("base_url"), str) and route["base_url"].strip():
            llm_kwargs["base_url"] = route["base_url"].strip()
        label = f"{provider}/{model}"
        if provider.startswith("endpoint:"):
            from abstractgateway.provider_endpoint_profiles import ProviderEndpointProfileStore

            profile = ProviderEndpointProfileStore(base_dir=base).get_profile(provider.split(":", 1)[1])
            if profile is None:
                sys.exit(f"error: gateway baseline references unknown provider connection {provider!r} ({cfg})")
            if profile.base_url:
                llm_kwargs["base_url"] = profile.base_url
            if profile.api_key:
                llm_kwargs["api_key"] = profile.api_key
            label = (f"{provider} → {profile.provider_family} @ {profile.base_url or '?'} "
                     f"(api key {'set' if profile.api_key else 'NOT set'}) | model {model}")
            provider = profile.provider_family
        return provider, model, f"gateway baseline {cfg} | {label}", llm_kwargs

    # No gateway baseline found: fall back to the shared resolver (abstractcore config).
    from abstractgateway.provider_defaults import resolve_gateway_provider_model

    res = resolve_gateway_provider_model(provider=args.provider, model=args.model, purpose="steering REPL")
    if res.error or not (res.provider and res.model):
        sys.exit(f"error: {res.error or 'no default provider/model configured'}")
    return res.provider, res.model, str(res.source or "default"), {}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--agent", choices=["react", "memact", "codeact"], default="react")
    ap.add_argument("--provider", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-iterations", type=int, default=12)
    args = ap.parse_args()

    provider, model, source, llm_kwargs = resolve_provider_model(args)

    from abstractcore.tools.common_tools import list_files, read_file, search_files

    tools = [list_files, read_file, search_files]
    runtime = create_local_runtime(
        provider=provider,
        model=model,
        llm_kwargs=llm_kwargs or None,
        tool_executor=MappingToolExecutor.from_tools(tools),
    )
    if args.agent == "memact":
        from abstractagent.agents.memact import MemActAgent

        agent = MemActAgent(runtime=runtime, tools=tools, on_step=on_step, max_iterations=args.max_iterations)
    elif args.agent == "codeact":
        from abstractagent.agents.codeact import CodeActAgent

        # review_mode off: keep the steering demo to the plain loop (no verifier rounds).
        agent = CodeActAgent(runtime=runtime, tools=tools, on_step=on_step,
                             max_iterations=args.max_iterations, review_mode=False)
    else:
        agent = ReactAgent(runtime=runtime, tools=tools, on_step=on_step, max_iterations=args.max_iterations)

    run_id_ref: dict = {"run_id": None}
    runtime.subscribe_ledger(make_ledger_printer(run_id_ref))

    say(c(f"{BOLD};{CYAN}", f"steering REPL — {args.agent} agent"))
    say(f"  provider: {c(BOLD, provider)}  model: {c(BOLD, model)}")
    say(c(DIM, f"  source: {source}"))
    say(c(DIM, f"  tools: {', '.join(t.__name__ for t in tools)} | max_iterations: {args.max_iterations}"))
    say(c(DIM, "  type a task to start; while it runs, type to steer. /pause /resume /cancel /status /wait /quit") + "\n")

    steer_q: "queue.Queue[str]" = queue.Queue()
    driver: Driver | None = None

    def running() -> bool:
        return driver is not None and not driver.done.is_set()

    while True:
        try:
            _INPUT_ACTIVE.set()
            line = input(PROMPT).strip()
        except (EOFError, KeyboardInterrupt):
            line = "/quit"
        finally:
            _INPUT_ACTIVE.clear()

        if not line:
            continue

        if line == "/quit":
            if running():
                agent.cancel("operator quit")
                driver.done.wait(timeout=10)
            say("bye")
            return

        if line == "/status":
            state = agent.get_state()
            if state is None:
                say(c(DIM, "no run yet"))
            else:
                waiting = f" waiting={state.waiting.wait_key}" if state.waiting else ""
                say(c(CYAN, f"run {state.run_id} status={state.status.value} node={state.current_node}{waiting}"))
            continue

        if line == "/pause":
            if agent.run_id:
                runtime.pause_run(agent.run_id, reason="operator pause")
                say(c(CYAN, "pause requested — takes effect at the next commit point "
                           "(an in-flight LLM/tool call finishes first)"))
            continue

        if line == "/resume":
            if agent.run_id:
                runtime.resume_run(agent.run_id)
                say(c(CYAN, "resumed"))
            continue

        if line == "/cancel":
            if running():
                agent.cancel("operator cancel")
            continue

        if line == "/wait":
            if driver is not None:
                driver.done.wait()
            continue

        if line.startswith("/steer "):
            if running():
                steer_q.put(line[len("/steer "):].strip())
            else:
                say(c(DIM, "no active run to steer"))
            continue

        # Plain text.
        if running():
            state = agent.get_state()
            waiting = getattr(state, "waiting", None)
            is_pause = bool(waiting and str(getattr(waiting, "wait_key", "")).startswith("pause:"))
            if state is not None and state.status == RunStatus.WAITING and waiting and not is_pause:
                agent.resume(line)  # answer to ask_user
                say(c(CYAN, "answer delivered"))
            else:
                steer_q.put(line)
        else:
            if agent.session_messages:
                say(c(DIM, f"(session carries {len(agent.session_messages)} messages from previous turns)"))
            run_id = agent.start(line)
            run_id_ref["run_id"] = run_id
            say(c(DIM, f"run started: {run_id}"))
            driver = Driver(agent, steer_q)
            driver.start()


if __name__ == "__main__":
    main()
