#!/usr/bin/env python3
"""Cache-aware steering REPL — steer_repl.py + prompt-cache leverage, made visible.

What this adds over scripts/steer_repl.py (same skeleton, same primitives):

- EXPLICIT cache identity: every LLM call in the session shares ONE
  `prompt_cache_key` (set via the documented `_runtime.prompt_cache` run-var
  config; the runtime would otherwise derive a session-scoped key by default —
  backlog 0212). The key is printed so you can see what rides the wire.
- CACHE INSTRUMENTATION (ledger-driven, zero monkeypatching): every `llm_call`
  ledger record is measured — wall time, prompt/completion tokens, decode-rate,
  and a PREFIX-REUSE meter: the rendered (system_prompt + messages) bytes of
  consecutive calls are compared so you SEE the append-only transcript sharing
  its prefix cycle over cycle (the property server-side prefix caches key on).
- A/B PROOF: `/bust on` (or --cache-bust) prepends a fresh nonce line to the
  system prompt before every cycle, deliberately destroying the shared prefix.
  Same model, same task: watch per-cycle latency jump to cold-prefill levels.
- `/cache` shows the provider's prompt-cache capability profile, the active
  key, and the per-call latency/token table.
- `--bench` runs a scripted tool-using task non-interactively and prints the
  per-call table (run once plain and once with --cache-bust to A/B).

Why this matters for ReAct: each cycle re-sends the whole growing transcript.
With a byte-stable prefix (stable system prompt, append-only messages — which
the ReAct adapter guarantees by design, see abstractagent react_runtime.py
0212 notes), a local server (LM Studio llama.cpp/MLX slot cache, vLLM APC)
only prefills the NEW tail tokens. Measured on this box (qwen3-4b @ 4bit,
4.4k-token prefix): cold 26.6s -> warm 1.6-3.5s per call.

Usage (from the monorepo root):
    .venv/bin/python scripts/cache_steer_repl.py
    .venv/bin/python scripts/cache_steer_repl.py --bench
    .venv/bin/python scripts/cache_steer_repl.py --bench --cache-bust   # A/B arm

Defaults to LM Studio + a <=4B 4-bit local model (see --model). REPL commands:
    <text>            idle: start a task | running: steer | ask_user: answer
    /steer <text>     explicitly steer the running agent
    /bust on|off      toggle per-cycle prefix busting (A/B lever)
    /cache            cache capabilities + per-call measurements
    /pause /resume /cancel /status /wait /quit   as in steer_repl.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

for rel in ("abstractgateway/src", "abstractruntime/src", "abstractmemory/src", "abstractagent/src", "abstractcore"):
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
from abstractruntime.integrations.abstractcore import MappingToolExecutor, create_local_runtime  # noqa: E402
from abstractagent.agents.react import ReactAgent  # noqa: E402

try:
    import readline
except ImportError:  # pragma: no cover
    readline = None  # type: ignore[assignment]


_TTY = sys.stdout.isatty()
_PRINT_LOCK = threading.Lock()
_INPUT_ACTIVE = threading.Event()
PROMPT = "you> "


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
# The A/B system prompt. BOTH arms use this same override so the only
# difference between plain and --cache-bust runs is the per-cycle nonce line.
# It restates the ReAct loop contract (short form of the built-in prompt).
# ---------------------------------------------------------------------------

SCRIPT_SYSTEM_PROMPT = (
    "You are an autonomous ReAct agent (Reason -> Act -> Observe).\n"
    "- If you need to act, CALL one or more tools (function calls).\n"
    "- If you are done, respond with the final answer and NO tool calls.\n"
    "- Choose tools yourself; batch independent read-only calls.\n"
    "- Use tool outputs as evidence; never claim actions without them.\n"
    "- Keep non-final responses short. Continue until the task is complete."
)


# ---------------------------------------------------------------------------
# Cache instrumentation: fed by the durable ledger (the same channel the
# gateway streams over SSE) — llm_call records carry the effect payload
# (system_prompt + messages, exactly what the provider will render) and, when
# completed, the result usage. No provider monkeypatching needed.
# ---------------------------------------------------------------------------

def _parse_iso(ts: str | None) -> float | None:
    if not isinstance(ts, str) or not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


import re as _re

_ENVELOPE_ONLY_RE = _re.compile(r"^\s*<runtime_metadata>.*</runtime_metadata>\s*$", _re.DOTALL)


def _is_envelope_only(msg: dict) -> bool:
    """The runtime grounding envelope is a fresh-timestamp user message appended
    per call BY DESIGN (volatile tail, never the prefix). Exclude it from the
    stability measurement so designed volatility doesn't read as instability."""
    return (
        msg.get("role") == "user"
        and isinstance(msg.get("content"), str)
        and bool(_ENVELOPE_ONLY_RE.match(msg["content"]))
    )


def _render_llm_input(payload: dict) -> bytes:
    """Approximate the provider's TEMPLATED prompt bytes, in template order.

    Order matters: chat templates render system (+ tool schemas) FIRST, then
    the messages in list order — so the measurement must too, or a tail-only
    change would falsely register as a head change. Envelope-only grounding
    messages are excluded (designed per-call volatility). This is a
    MEASUREMENT rendering, not the provider's exact template bytes, but
    prefix-share of this rendering tracks prefix-share of the templated
    prompt, which is what server-side prefix caches (llama.cpp slot reuse /
    MLX cache / vLLM APC) match on.
    """
    parts: list[str] = []
    parts.append("[system]\n" + str(payload.get("system_prompt") or ""))
    tools = payload.get("tools")
    if tools:
        parts.append("[tools]\n" + json.dumps(tools, sort_keys=True, ensure_ascii=False))
    for msg in payload.get("messages") or []:
        if isinstance(msg, dict):
            if _is_envelope_only(msg):
                continue
            parts.append(json.dumps(msg, sort_keys=True, ensure_ascii=False))
        else:
            parts.append(str(msg))
    return "\n\x00\n".join(parts).encode("utf-8")


def _common_prefix_len(a: bytes, b: bytes) -> int:
    n = min(len(a), len(b))
    lo = 0
    while lo < n and a[lo] == b[lo]:
        lo += 1
    return lo


class CacheMeter:
    """Collects per-llm_call measurements from ledger records.

    Prefix reuse compares consecutive calls OF THE SAME NODE (the conclusion/
    review nodes issue differently-shaped payloads; cross-node comparison
    would falsely tank the number). Retried attempts are flagged, not
    silently averaged. Prefill is estimated by subtracting decode time at a
    self-calibrated rate (the fastest observed decode across calls), so a
    long final answer doesn't masquerade as a cache miss.
    """

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.calls: list[dict] = []
        self._open: dict[str, dict] = {}          # step_id -> partial entry
        self._prev_render: dict[str, bytes] = {}  # node_id -> last render

    def on_record(self, rec: dict) -> None:
        effect = rec.get("effect") or {}
        if str(effect.get("type") or "") != "llm_call":
            return
        raw_status = rec.get("status")
        status = getattr(raw_status, "value", raw_status if isinstance(raw_status, str) else "")
        step_id = str(rec.get("step_id") or "")
        node_id = str(rec.get("node_id") or "?")
        if status == "started":
            payload = effect.get("payload") or {}
            render = _render_llm_input(payload)
            with self.lock:
                prev = self._prev_render.get(node_id)
                reuse_pct = None
                if prev:
                    reuse_pct = 100.0 * _common_prefix_len(prev, render) / max(1, len(prev))
                self._open[step_id] = {
                    "node": node_id,
                    "t0": _parse_iso(rec.get("started_at")) or time.time(),
                    "bytes": len(render),
                    "prefix_reuse_pct": reuse_pct,
                    "cache_key": (payload.get("params") or {}).get("prompt_cache_key"),
                    "attempt": rec.get("attempt") or 1,
                }
                self._prev_render[node_id] = render
        elif status in ("completed", "failed"):
            with self.lock:
                entry = self._open.pop(step_id, None)
                if entry is None:
                    return
                t1 = _parse_iso(rec.get("ended_at")) or time.time()
                wall = max(0.0, t1 - entry["t0"])
                usage = ((rec.get("result") or {}).get("usage") or {}) if isinstance(rec.get("result"), dict) else {}
                prompt_tk = usage.get("prompt_tokens") or usage.get("input_tokens")
                completion_tk = usage.get("completion_tokens") or usage.get("output_tokens")
                # Server-reported cache hits, when the backend exposes them
                # (OpenAI prompt_tokens_details.cached_tokens, Anthropic
                # cached_input_tokens; LM Studio reports none as of 2026-07).
                details = usage.get("prompt_tokens_details") or {}
                cached_tk = (
                    usage.get("cached_input_tokens")
                    or (details.get("cached_tokens") if isinstance(details, dict) else None)
                )
                entry.update({
                    "wall_s": wall,
                    "prompt_tokens": prompt_tk,
                    "completion_tokens": completion_tk,
                    "cached_tokens": cached_tk,
                    "failed": status == "failed",
                })
                self.calls.append(entry)
            self._announce(entry)

    def _decode_rate(self, calls: list[dict]) -> float | None:
        """Self-calibrated decode tokens/s: the fastest observed decode.

        An upper-bound rate makes the prefill estimate CONSERVATIVE (prefill
        is under- rather than over-attributed)."""
        best = None
        for e in calls:
            ctk, wall = e.get("completion_tokens"), e.get("wall_s")
            if isinstance(ctk, int) and ctk >= 8 and isinstance(wall, float) and wall > 0:
                rate = ctk / wall
                best = rate if best is None or rate > best else best
        return best

    def _announce(self, e: dict) -> None:
        reuse = e.get("prefix_reuse_pct")
        reuse_s = f"prefix reuse {reuse:5.1f}%" if isinstance(reuse, float) else "prefix reuse   n/a"
        ptk = e.get("prompt_tokens")
        ctk = e.get("completion_tokens")
        cache_s = f" cached={e['cached_tokens']}" if e.get("cached_tokens") is not None else ""
        retry_s = f" (attempt {e['attempt']})" if (e.get("attempt") or 1) > 1 else ""
        color = GREEN if (isinstance(reuse, float) and reuse >= 90.0) else YELLOW
        say(c(f"{DIM};{color}",
              f"    ⚡ llm_call[{e.get('node')}] {e['wall_s']:6.2f}s  prompt={ptk} tk  out={ctk} tk  {reuse_s}{cache_s}{retry_s}"))

    def table(self) -> str:
        with self.lock:
            calls = list(self.calls)
        if not calls:
            return "  (no llm calls measured yet)"
        rate = self._decode_rate(calls)
        lines = [f"  {'#':>2} {'node':<8} {'wall s':>8} {'~prefill s':>10} {'prompt tk':>10} {'out tk':>7} {'prefix reuse':>13} {'cached tk':>10}"]
        for i, e in enumerate(calls, 1):
            reuse = e.get("prefix_reuse_pct")
            reuse_s = f"{reuse:6.1f}%" if isinstance(reuse, float) else "   n/a"
            cached = e.get("cached_tokens")
            ctk = e.get("completion_tokens")
            prefill_s = "-"
            if rate and isinstance(ctk, int):
                prefill_s = f"{max(0.0, e.get('wall_s', 0.0) - ctk / rate):8.2f}"
            flag = "*" if (e.get("attempt") or 1) > 1 else " "
            lines.append(
                f"  {i:>2}{flag}{str(e.get('node')):<8}{e.get('wall_s', 0):8.2f} {prefill_s:>10} "
                f"{str(e.get('prompt_tokens')):>10} {str(ctk):>7} {reuse_s:>13} "
                f"{str(cached if cached is not None else '-'):>10}"
            )
        if rate:
            lines.append(f"  (~prefill = wall − out/decode_rate; decode_rate self-calibrated at {rate:.0f} tk/s; * = retried attempt)")
        walls = [e.get("wall_s", 0.0) for e in calls if not e.get("failed")]
        if len(walls) >= 2:
            lines.append(f"  first call {walls[0]:.2f}s vs later avg {sum(walls[1:]) / len(walls[1:]):.2f}s")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Run-var seam: set the cache identity (and bust nonces) on the durable run.
# Same single-writer discipline as BaseAgent.inject_message: mutate vars and
# save through the run store — from the tick thread or before it starts.
# ---------------------------------------------------------------------------

def _mutate_runtime_ns(runtime, run_id: str, **updates) -> None:
    state = runtime.get_state(run_id)
    ns = state.vars.get("_runtime")
    if not isinstance(ns, dict):
        ns = {}
        state.vars["_runtime"] = ns
    ns.update(updates)
    runtime._run_store.save(state)


def apply_cache_identity(runtime, run_id: str, key: str) -> None:
    """Pin ONE explicit prompt_cache_key for every LLM call of this run.

    Two lanes, deliberately both:
    - `_runtime.prompt_cache_key` rides the agent adapter's params builder
      (generation_params.runtime_llm_params) so the key is LEDGER-VISIBLE in
      every llm_call payload — the handler-derived default key is injected
      after the ledger record and never shows up there.
    - `_runtime.prompt_cache` is the runtime LLM-handler config (backlog
      0212); explicit here for clarity. Without EITHER, a session-scoped key
      is derived by default — caching is on regardless; explicitness buys
      observability and a human-readable key.
    """
    _mutate_runtime_ns(
        runtime, run_id,
        prompt_cache_key=key,
        prompt_cache={"enabled": True, "namespace": "steer", "key": key},
    )


def apply_system_prompt(runtime, run_id: str, *, bust: bool) -> None:
    """Set the run's system prompt override; bust=True prepends a fresh nonce.

    The nonce line changes the FIRST bytes of the rendered prompt, so every
    server-side prefix cache misses — the A/B lever. Called between ticks
    (single-writer: only the driver thread calls this while running).
    """
    prompt = SCRIPT_SYSTEM_PROMPT
    if bust:
        prompt = f"[cache-bust {uuid.uuid4().hex}]\n\n{prompt}"
    _mutate_runtime_ns(runtime, run_id, system_prompt=prompt)


# ---------------------------------------------------------------------------
# Driver: same as steer_repl.py + optional per-cycle prefix busting.
# ---------------------------------------------------------------------------

BENCH_AUTO_ANSWER = (
    "This is a non-interactive benchmark; no user is available to answer. "
    "Do not ask again — proceed with the available tools and give your final answer."
)
BENCH_MAX_AUTO_ANSWERS = 3


class Driver(threading.Thread):
    def __init__(self, agent, steer_q: "queue.Queue[str]", bust_flag: threading.Event,
                 *, bench_mode: bool = False):
        super().__init__(name="agent-driver", daemon=True)
        self.agent = agent
        self.steer_q = steer_q
        self.bust_flag = bust_flag
        self.bench_mode = bench_mode
        self._auto_answers = 0
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

                if self.bust_flag.is_set() and self.agent.run_id:
                    apply_system_prompt(self.agent.runtime, self.agent.run_id, bust=True)

                try:
                    state = self.agent.step()
                except Exception as e:
                    say("\n" + c(f"{BOLD};{RED}", f"✖ driver error: {e}") + "\n")
                    return
                if state.status in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED):
                    if state.status == RunStatus.FAILED:
                        say("\n" + c(f"{BOLD};{RED}", f"✖ run FAILED: {state.error}") + "\n")
                    elif state.status == RunStatus.CANCELLED:
                        say("\n" + c(f"{BOLD};{RED}", "■ run CANCELLED") + "\n")
                    return
                if state.status == RunStatus.WAITING:
                    if self.bench_mode:
                        # Non-interactive: a WAITING run (ask_user) would hang
                        # forever on /dev/null stdin. Auto-answer with a canned
                        # refusal, capped — a model that keeps asking fails the
                        # bench loudly instead of wedging the harness.
                        self._auto_answers += 1
                        if self._auto_answers > BENCH_MAX_AUTO_ANSWERS:
                            say("\n" + c(f"{BOLD};{RED}",
                                         f"✖ bench: model kept asking after {BENCH_MAX_AUTO_ANSWERS} "
                                         f"auto-answers — cancelling run") + "\n")
                            self.agent.cancel("bench: ask_user loop")
                            continue
                        say(c(MAGENTA, f"↪ bench auto-answer {self._auto_answers}/{BENCH_MAX_AUTO_ANSWERS} "
                                       f"(non-interactive; canned refusal)"))
                        try:
                            self.agent.resume(BENCH_AUTO_ANSWER)
                        except Exception as e:
                            say(c(f"{BOLD};{RED}", f"✖ bench auto-answer failed: {e} — cancelling"))
                            self.agent.cancel("bench: auto-answer failed")
                        continue
                    time.sleep(0.3)
        finally:
            self.done.set()


# ---------------------------------------------------------------------------
# Semantic step feed (same as steer_repl.py).
# ---------------------------------------------------------------------------

def on_step(step: str, data: dict) -> None:
    if step == "reason":
        head = c(f"{BOLD};{YELLOW}", f"⟲ cycle {data.get('iteration')}/{data.get('max_iterations')}")
        guided = "  " + c(f"{BOLD};{MAGENTA}", "← guidance folded in") if data.get("has_guidance") else ""
        say("\n" + head + c(DIM, " thinking…") + guided)
    elif step == "parse_tool_calls":
        say(c(DIM, f"  the model wants {data.get('count')} tool call(s)"))
    elif step == "act":
        say(c(DIM, f"  acting: {data.get('tool')}"))
    elif step == "observe":
        ok = c(GREEN, "ok") if data.get("success") else c(f"{BOLD};{RED}", "ERROR")
        say(f"  {c(BOLD, str(data.get('tool')))} → {ok} {c(DIM, _trunc(data.get('result')))}")
    elif step == "ask_user":
        say(c(f"{BOLD};{CYAN}", f"? agent asks: {data.get('question')}") + c(DIM, "  (type your answer)"))
    elif step == "done":
        say("\n" + c(f"{BOLD};{GREEN}", "✔ final answer") + "\n" + str(data.get("answer") or "") + "\n")
    elif step == "max_iterations":
        say("\n" + c(f"{BOLD};{RED}", f"✖ stopped: hit max_iterations={data.get('iterations')}") + "\n")


# ---------------------------------------------------------------------------
# Provider cache capabilities (queried once, displayed by /cache).
# ---------------------------------------------------------------------------

def probe_cache_capabilities(provider: str, model: str, llm_kwargs: dict) -> dict:
    """Ask abstractcore what this provider supports (mode none/keyed/local_control_plane)."""
    try:
        from abstractcore import create_llm

        llm = create_llm(provider, model=model, **(llm_kwargs or {}))
        caps = llm.get_prompt_cache_capabilities()
        out = caps.to_dict() if hasattr(caps, "to_dict") else dict(caps)  # type: ignore[arg-type]
        close = getattr(llm, "close", None)
        if callable(close):
            close()
        return out
    except Exception as e:  # capability probe must never block the REPL
        return {"error": f"capability probe failed: {e}"}


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------

DEFAULT_PROVIDER = "lmstudio"
DEFAULT_MODEL = "qwen/qwen3-4b-2507"  # 4B, 4-bit, tool-capable, local


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--provider", default=DEFAULT_PROVIDER,
                    help=f"abstractcore provider (default: {DEFAULT_PROVIDER})")
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help=f"model id (default: {DEFAULT_MODEL} — <=4B, 4-bit)")
    ap.add_argument("--base-url", default=None, help="override provider base URL")
    ap.add_argument("--max-iterations", type=int, default=12)
    ap.add_argument("--temperature", type=float, default=0.0,
                    help="generation temperature (0.0 pins A/B arms to comparable tool paths)")
    ap.add_argument("--seed", type=int, default=42, help="generation seed (A/B determinism)")
    ap.add_argument("--cache-bust", action="store_true",
                    help="A/B arm: destroy the shared prefix every cycle (fresh nonce in the system prompt)")
    ap.add_argument("--bench", action="store_true",
                    help="non-interactive: run a scripted tool-using task and print the measurement table")
    ap.add_argument("--bench-task", default=None, help="override the scripted bench task")
    args = ap.parse_args()

    llm_kwargs: dict = {}
    if args.base_url:
        llm_kwargs["base_url"] = args.base_url

    from abstractcore.tools.common_tools import list_files, read_file, search_files

    tools = [list_files, read_file, search_files]
    runtime = create_local_runtime(
        provider=args.provider,
        model=args.model,
        llm_kwargs=llm_kwargs or None,
        tool_executor=MappingToolExecutor.from_tools(tools),
    )

    agent = ReactAgent(runtime=runtime, tools=tools, on_step=on_step, max_iterations=args.max_iterations)

    meter = CacheMeter()
    run_id_ref: dict = {"run_id": None}

    def on_record(rec: dict) -> None:
        if rec.get("run_id") != run_id_ref.get("run_id"):
            return
        meter.on_record(rec)

    runtime.subscribe_ledger(on_record)

    session_cache_key = f"steer:{uuid.uuid4().hex[:12]}"
    bust_flag = threading.Event()
    if args.cache_bust:
        bust_flag.set()

    caps = probe_cache_capabilities(args.provider, args.model, llm_kwargs)

    say(c(f"{BOLD};{CYAN}", "cache-aware steering REPL — react agent"))
    say(f"  provider: {c(BOLD, args.provider)}  model: {c(BOLD, args.model)}")
    say(f"  prompt_cache_key: {c(BOLD, session_cache_key)}  "
        + (c(f"{BOLD};{RED}", "cache-bust ON (A/B arm)") if bust_flag.is_set() else c(GREEN, "cache-friendly (stable prefix)")))
    mode = caps.get("mode", caps.get("error", "?"))
    say(c(DIM, f"  provider cache capability mode: {mode}"
              + ("  (server-side prefix reuse needs no request field — byte-stable prefix is enough)"
                 if mode == "keyed" else "")))
    say(c(DIM, f"  tools: {', '.join(t.__name__ for t in tools)} | max_iterations: {args.max_iterations}"))

    def start_run(task: str) -> "Driver":
        if agent.session_messages:
            say(c(DIM, f"(session carries {len(agent.session_messages)} messages from previous turns — "
                       f"the grown transcript is the shared prefix)"))
        run_id = agent.start(task, temperature=args.temperature, seed=args.seed)
        run_id_ref["run_id"] = run_id
        # Before the first tick: pin the cache identity + the A/B system prompt.
        apply_cache_identity(runtime, run_id, session_cache_key)
        apply_system_prompt(runtime, run_id, bust=bust_flag.is_set())
        say(c(DIM, f"run started: {run_id}"))
        d = Driver(agent, steer_q, bust_flag, bench_mode=args.bench)
        d.start()
        return d

    steer_q: "queue.Queue[str]" = queue.Queue()

    if args.bench:
        task = args.bench_task or (
            "List the files in the scripts/ directory, then read the first 40 lines of "
            "scripts/steer_repl.py, then answer with ONE sentence describing what that script does."
        )
        say(c(BOLD, f"\nbench task: {task}\n"))
        t0 = time.time()
        driver = start_run(task)
        driver.done.wait()
        total = time.time() - t0
        say(c(BOLD, f"\n=== bench complete in {total:.1f}s — per-llm_call measurements "
                    f"({'BUSTED prefix' if bust_flag.is_set() else 'stable prefix'}) ==="))
        say(meter.table())
        say(c(DIM, "\nrun the other arm (--cache-bust toggled) with the same task to compare."))
        return

    say(c(DIM, "  type a task to start; while it runs, type to steer. "
               "/bust on|off /cache /pause /resume /cancel /status /wait /quit") + "\n")

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

        if line == "/cache":
            say(c(BOLD, "cache capability profile:"))
            say(c(DIM, "  " + json.dumps(caps, indent=2).replace("\n", "\n  ")))
            say(c(BOLD, f"cache key: {session_cache_key}   bust: {'ON' if bust_flag.is_set() else 'off'}"))
            say(c(BOLD, "per-llm_call measurements:"))
            say(meter.table())
            continue

        if line.startswith("/bust"):
            arg = line.split(None, 1)[1].strip().lower() if " " in line else ""
            if arg == "on":
                bust_flag.set()
                say(c(RED, "cache-bust ON — every next cycle rewrites the prompt head (prefix cache will miss)"))
                say(c(DIM, "  note: mid-session toggling contaminates the A/B (a busted call evicts the warm slot,"
                           " so the next unbusted call measures cold). For clean numbers use separate --bench runs."))
            elif arg == "off":
                bust_flag.clear()
                if agent.run_id:
                    apply_system_prompt(runtime, agent.run_id, bust=False)
                say(c(GREEN, "cache-bust off — stable prefix restored"))
            else:
                say(c(DIM, f"bust is {'ON' if bust_flag.is_set() else 'off'} — use /bust on|off"))
            continue

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
                say(c(CYAN, "pause requested — takes effect at the next commit point"))
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

        if running():
            state = agent.get_state()
            waiting = getattr(state, "waiting", None)
            is_pause = bool(waiting and str(getattr(waiting, "wait_key", "")).startswith("pause:"))
            if state is not None and state.status == RunStatus.WAITING and waiting and not is_pause:
                agent.resume(line)
                say(c(CYAN, "answer delivered"))
            else:
                steer_q.put(line)
        else:
            driver = start_run(line)


if __name__ == "__main__":
    main()
