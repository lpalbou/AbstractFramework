# 0233 — Real run cancellation: abort in-flight LLM calls

**Status**: completed
**Priority**: P1 (wastes paid/GPU compute; operator-visible; blocks honest `/cancel`)
**Component**: AbstractRuntime (`core/runtime.py` cancel path), AbstractCore (provider HTTP
layer + `cancel_event`), AbstractGateway (`_apply_run_control`), AbstractCode-TUI (`/cancel`)
**Created**: 2026-08-02
**Completed**: 2026-09-23 (record written 2026-09-25)
**Related**: ADR-0013 (durable run controls: pause/resume/cancel), ADR-0014 (runtime-authoritative
timeouts), ADR-0027 (timeout policy)

---

## Summary

`/cancel` marks a run cancelled and returns; **the in-flight LLM generation keeps running to
completion.** On a local model this is directly visible as GPU still busy on an abandoned
request. The operator observed two simultaneous generation slots on LM Studio and asked whether
parallelism was intended — it was not: one slot was an abandoned generation from a cancelled run.

Cancellation is currently a **state write**, not an abort.

## Evidence (CONFIRMED, 2026-08-02)

Traced end to end:

| step | file | behaviour |
|---|---|---|
| 1 | `abstractcode-tui/src/runner.rs:1781` | sends the cancel command |
| 2 | `abstractcode-tui/src/gateway/mod.rs:629` | `submit_command(run_id, "cancel")` |
| 3 | `abstractgateway/runner.py:1408` | `_apply_run_control` |
| 4 | `abstractruntime/core/runtime.py:1302` | **`cancel_run` = `status=CANCELLED; save`** |

No cancel token, no HTTP abort, no thread signal. The tick thread stays blocked inside
`llm.generate()` until the provider returns.

Slot-span analysis of `~/.lmstudio/server-logs/2026-08/2026-08-02.1.log` (72 closed
generations): **5 overlapping generation pairs, the largest 211s**. Task 594 was still burning
the GPU when the next request was launched on another slot; it later died via
`Client disconnected. Stopping generation...`.

abstractcore already exposes `cancel_event` (`core/retry.py:319`) — but it only slices **backoff
waits**, and nothing in the runtime or gateway ever passes one.

## Why it matters

- **Wasted compute**: an abandoned generation runs to completion on paid APIs and on local GPUs.
- **Operator confusion**: cancelling appears to do nothing; concurrent slots look like a
  parallelism bug.
- **Honesty**: the run reports `CANCELLED` while work continues — the run state and the world
  disagree, the same class this framework's ADRs exist to prevent.
- **Interaction with timeouts**: an abandoned generation can outlive its run and, on LM Studio,
  a later `srv stop: cancel task` can cancel a *different* in-flight task (observed) — one
  client's abandonment corrupting another's request.

## Proposal

A cancellation token threaded through the four layers, with abort at the HTTP boundary.

1. **AbstractCore** — accept a cancellation token on `generate()`/`stream()` and honour it at the
   HTTP layer, not just in backoff. For `httpx`, close the response/stream on signal so the
   socket drops and the server stops generating (LM Studio, Ollama and vLLM all stop on client
   disconnect). Extend the existing `cancel_event` rather than inventing a second mechanism.
2. **AbstractRuntime** — `cancel_run` creates/sets the token for the run's in-flight effect
   before writing `status=CANCELLED`, then lets the tick thread unwind. `LLM_CALL` and
   `TOOL_CALLS` handlers pass the token down. The ledger records the abort as a distinct outcome
   (`cancelled_in_flight`), never as a normal completion or a fault.
3. **AbstractGateway** — `_apply_run_control` triggers the token synchronously and reports whether
   the in-flight call was actually aborted, so the client can tell the difference between
   "marked cancelled" and "stopped".
4. **AbstractCode-TUI** — `/cancel` reports the honest outcome ("cancelled; generation aborted"
   vs "cancelled; a generation is still finishing"), never implying more than happened.

## Validation

- Start a long local generation, `/cancel` mid-flight; assert the LM Studio log shows the
  generation stopping **within seconds** of the cancel, and that no slot remains busy.
- Assert the ledger carries `cancelled_in_flight` and no fabricated completion.
- Assert a cancelled run's tokens stop accruing at the abort point.
- Regression: cancelling a run with no in-flight LLM call still behaves as today.
- Concurrency: cancelling run A must not disturb run B's in-flight generation (the observed
  LM Studio cross-cancel hazard).

## Notes

Scope is deliberately cross-package; it cannot be fixed in one seat. Sequencing suggestion:
abstractcore first (the token + HTTP abort is the load-bearing piece), then runtime, then the
gateway/TUI reporting.

## Completion report

- Completed: 2026-09-23 (released that day); report written 2026-09-25 during the post-release
  backlog trace. The item was still in `planned/` although the work shipped: backlog drift.
- What landed (from the CHANGELOGs at the released tags):
  - abstractcore 2.13.41: `generate(..., cancel_event=threading.Event)`; providers declaring
    `supports_generation_cancel()` stop the running decode (MLX per sampled token; HTTP lanes close
    the request); typed `GenerationCancelledError`, never retried; `unload_model()` cancels and
    drains in-flight calls; the AbstractCore server cancels on client disconnect (499).
    Doc: `abstractcore/docs/generation-cancel.md`.
  - AbstractRuntime 0.4.32: `Runtime.cancel_run(...)` signals the running effect and passes the
    event to AbstractCore; stopped steps are recorded `cancelled` (`StepStatus.CANCELLED`,
    `EffectOutcome.cancelled`) with `cancelled_by`, never retried;
    `core/effect_cancellation.py` (`inflight_effects()`, `request_model_effects_cancel`); eject
    records `cancelled_by: "model_eject"`.
  - abstractgateway 0.2.30: Stop cancels the run tree and the executing model call; kill switch
    `stop_kill_switch_s` (default 10 s, `0` disables) injects `EffectKilled` into a call that
    ignores its cancel; ledger steps carry `cancelled_by` / `killed_by`.
- Validation: missions H and I (2026-09-23), orchestrator-verified — decode stops within one token,
  run tree `CANCELLED` in ~60 ms; HTTP lanes (LM Studio, Ollama, llama.cpp server, vLLM, remote
  AbstractCore) sever the socket so the server stops decoding (LM Studio 51% → 0% GPU); MLX eject
  memory 4,110 → 769 MB. Evidence: `untracked/missionH/`, `untracked/missionI/`,
  `untracked/missions-2026-09-22/SUMMARY.md` (second wave table).
- Residual risks / follow-ups:
  - The abstractcode terminal app does not know the `cancelled` step status (SUMMARY, third-wave
    known limits). Owner: abstractcode; not tracked in this root backlog.
  - Remote AbstractCore routes carry no phase events and cancel only by socket close.
  - AbstractRuntime `MODELS_ENGINES_MIN_ABSTRACTCORE` still says 2.14.0 while the 0.4.34 cancel
    signature needs 2.15.1: tracked by 0872.
- ADR state: no new rule beyond ADR-0013 (durable run controls); ADR impact None.
