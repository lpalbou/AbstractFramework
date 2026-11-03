# 1117 — Gateway stop: the runtime simply stops — is `EffectInterrupted` needed?

> Package: AbstractRuntime, AbstractGateway
> Type: decision
> Created: 2026-11-04
> Priority: high
> Labels: decision-gate, runs, restart, runtime, model-host

## Summary

OPERATOR DECISION GATE (never assignable): decide whether a gateway stop needs the runtime concept
`EffectInterrupted` (shipped in AbstractRuntime 0.17.0, used by the unmerged AbstractGateway #98).
The alternative is to get the same outcome the way the in-process era did: the gateway stops driving
the runtime, and nothing is recorded once the stop has begun. The operator questions the engineering
and asked for a discussion before anything else lands on this path. Until it is decided, AbstractGateway
#98 stays unmerged and nothing new is built on `EffectInterrupted`.

## Why

Operator 2026-11-04, verbatim: "for me this was never required. when the gateway pause/stop, the runtime
stops. the gateway is the one controlling the runtime. if it's not here, it's not a fail, it's just the
runtime not moving forward. so i am very concerned by how you engineer this. and we need to have a
discussion."

The originating ruling (1103, 2026-11-03): "we can pause or interrupt the gateway, it doesn't mean in any
way that a run has failed, just that it is suspended and will resume with the gateway."

### 1. The operator's model

- The gateway controls the runtime: it is what ticks runs.
- When the gateway pauses or stops, the runtime stops moving forward. That is not a failure.
- Nothing has to be recorded about the stop. The run is where its ledger says it is, and it continues
  when the gateway is back.

### 2. What shipped, and what is pending

**AbstractRuntime #33, merged `a61ee08d`, released in 0.17.0 (on PyPI):**
- `EffectInterrupted(BaseException)` in `core/effect_cancellation.py`, exported as
  `abstractruntime.EffectInterrupted`. It is modelled on `EffectKilled`.
- `_execute_effect_with_retry`: on `EffectInterrupted` it appends **no terminal record**, ends the live
  text `cancelled` / `detail: "interrupted"`, and re-raises.
- `tick` lets it through without `record_error`. The run stays RUNNING with the ledger tail STARTED.
- Crash-replay re-sends the effect at the next tick or boot, under the same idempotency key, as
  attempt 1. No automation retry, no attention item and no email.
- Docs:
  - runtime ADR 0002 Consequences: "In every mode, a host stop interrupts an effect (`EffectInterrupted`:
    no terminal record, re-issued on the next tick); only a failure the effect itself met is recorded as
    failed."
  - `docs/architecture.md` crash-ordering invariant 4: "A requested host stop is a crash the host
    announces: identical replay, no terminal record."
- The same PR fixed `automations/attention.py`, which used `"completed"` as an occurrence's error text.
  That fix is independent of this decision.

**AbstractGateway #98 (`fix/host-stop-interrupts-runs`, OPEN, needs the 0.17.0 floor):**
- `model_host.py` `_crashed_error` and `_acquire` raise `EffectInterrupted` when the supervisor is
  stopping (`_stopping`) or the exit was a requested kill.
- `kill(reason, requested=True)` writes no incident and restarts the child at once; a call made during
  that restart waits for the new child. `engines_install.py` (the llama.cpp update) passes
  `requested=True`. Memory-ceiling and unresponsive kills keep 424 plus an incident.
- `host_control.step_gate` closes once a stop begins (signal, tray or console Restart or shutdown).
  No new step starts, and the 30 s drain waits only for the step each run is executing.
- `runner._tick_run` logs one line for an interrupted run and leaves it RUNNING. The shutdown line says
  "runner drain TIMED OUT (…): N run(s) interrupted" instead of "done".
- Gateway ADR 0002 §5 (the step gate at stop) and §7: "A stop the gateway or the operator requested is
  not a failure … the proxy raises the runtime's `EffectInterrupted`, the runtime records no terminal
  step, the run stays running …".

### 3. Why it was built that way

Sources: `untracked/release-2026-11-03/architect-restart-suspend.md` (design A2) and the independent
`untracked/release-2026-11-03/repro-restart-suspend.md`.

- **The in-process era.** Up to gateway 0.18.x the model ran in the gateway process. On SIGTERM the
  runner drained for 30 s, then the process exited, and an LLM call still running died with it.
  Nothing was recorded, the ledger tail stayed STARTED, and the next boot replayed the step (repro E,
  root 0.11.7 pins). This was never written down as a contract, which is why nothing went red when it
  broke.
- **What changed.** Since gateway 0.19.0 (ADR 0002, commit `f6601e2b`, #28; the macOS default since #74,
  2026-10-29) the model runs in a supervised child process.
  - The serve `finally` calls `model_host.stop()` **after** the 30 s drain and **before** the process
    exits. `stop()` closes the child's stdin, and the child exits 0.
  - The tick thread, still blocked on that call, gets EOF. `_crashed_error` did not read `_stopping`,
    so it raised `ModelHostCrashed` (424, not retryable).
  - The runtime then appended FAILED and set the run failed, about 1 s before the process exited.
- **The result.** A polite stop was destructive and a hard kill (SIGKILL) was safe. Automation e3079778,
  occurrence 24 on 2026-11-02 (runs `2c197cfb`, `34497947`, `973e7ef1`), failed after three restarts and
  sent an `automation_failed` email.
- **Why a typed exception.** The architect rejected the gateway-only fix (A1) because it encodes the
  contract as teardown order: correctness depends on the process exit winning a race with a blocked
  thread. A refactor could bring the bug back with every check green. A1 also misses the child-only
  restart (the llama.cpp update), where the gateway stays up. So the design made "the gateway stopped
  it" distinguishable from "it crashed" with a runtime-level type, next to `EffectKilled`.

### 4. The question for the discussion

Can the same outcome be reached **without a new runtime concept**, as the operator's model says? The
proposal to discuss:

1. **The gateway stops driving first.** When a stop begins, the step gate closes (#98 already does
   this, gateway-only). No new step starts.
2. **The drain is only a courtesy.** It waits up to 30 s for the step in flight, so a short call that
   finishes is recorded rather than redone. Its expiry fails nothing; it only ends the waiting.
3. **Nothing is recorded after the drain ends.** Two ways, both gateway-only:
   - (a) when the drain times out, the gateway exits **without** stopping the model host first; the
     child exits on its own when its stdin closes with the parent (ADR 0002 §5);
   - (b) the gateway freezes its run and ledger stores before it stops the model host, so a write from
     a still-blocked tick cannot land.

   Either way the in-flight step stays STARTED, exactly as in the in-process era, and the next start
   replays it.
4. **The child-only restart (llama.cpp update, gateway stays up).** Either:
   - the gateway closes the step gate, waits for in-flight calls, restarts the child and reopens; or
   - the model-host proxy re-sends the in-flight request to the new child itself.

   Both stay inside the gateway; the runtime never sees the restart.
5. **Then `EffectInterrupted` is unnecessary.** It could become internal-only, or be removed in
   AbstractRuntime 0.18. No released package depends on it today: #98, its only user, is unmerged.

## Scope

### In scope

- The operator's decision between the options below, recorded in this item and in the decision store.
- After the decision: the follow-up items (code, tests and ADR wording) in the owning repos.

### Out of scope

- Tool idempotency on replay: a side-effecting tool may run twice. That is pre-existing at-least-once
  behaviour.
- Moving ticks into their own process (0968).
- The `attention.py` "completed" error-text fix, already shipped in 0.17.0.

### Options

| | Keep (as shipped + #98) | Internalise | Remove (operator's model) |
|---|---|---|---|
| What | `EffectInterrupted` stays a public runtime type; #98 merges as is | The runtime keeps the behaviour but drops the export and the public docs; only the gateway raises it. Variant: the gateway raises its own `BaseException`, which runtime 0.16/0.17 already lets through with no terminal record (undocumented behaviour, counted by `record_error`; read in the 0.16.0 code, not tested) | Gateway-only: gate closed at stop, drain as courtesy, no write after the drain (exit before `model_host.stop()`, or freeze the stores), child restart only when idle or a re-send inside the proxy. `EffectInterrupted` removed in runtime 0.18 |
| New runtime concept | Yes, public | Yes, hidden (or implicit) | None |
| Covers the child-only restart | Yes | Yes | Yes, via the idle restart or the proxy re-send |
| Fragility | Low: explicit type, survives teardown refactors | Medium: a hidden contract, or one that relies on undocumented `BaseException` handling | Medium: relies on exit order or a store freeze; guarded only by the e2e tests below |
| Release coupling | Runtime 0.17.0, then the gateway floor | Runtime 0.17.x or 0.18, then the gateway | Gateway only; runtime 0.18 removes the type |
| Cost | Merge #98 | A runtime patch plus #98 changes | Rework #98 (keep its step gate, drain line and requested-kill incident change), new tests, runtime removal |

### Tests that pin the behaviour

**Independent of the mechanism (they stay in every option):**
- Gateway `tests/test_host_stop_interrupts_runs_e2e.py` (#98, opt-in, real `serve --model-host
  process`): SIGTERM mid-call on a plain run, a chat turn and an automation `run_now`. After the stop
  the run is `running` with no FAILED record. The next start completes it (attempt 1). No
  `automation.retry_scheduled`, no notification. These are the operator's contract.
- Gateway unit tests (#98):
  - the step gate closes once a stop begins, and step 2 never starts;
  - a kill for the child's own fault (memory ceiling) still gives 424 plus an incident;
  - the drain line names the interrupted runs.

**Specific to keep or internalise:**
- Runtime `tests/test_effect_interrupted.py`.
- The #98 unit tests asserting `EffectInterrupted` from a stop and from a requested restart.

**Replacing them under remove:**
- After the drain ends, no ledger or run-store write lands (store freeze or exit order), with a mutation
  check that stops the model host first and must go red.
- A requested child restart never runs under an in-flight call: it waits for idle, or the proxy
  re-sends.

### ADR wording per option

- **Keep:** runtime ADR 0002 and invariant 4 as shipped; gateway ADR 0002 §5 and §7 as in #98.
- **Internalise:** the runtime ADR sentence drops the type name ("a host stop leaves the effect in
  flight without a terminal record; it is re-issued on the next tick"); gateway §7 names the
  mechanism as gateway-internal.
- **Remove:**
  - runtime invariant 4 becomes "A host stop is a crash: the host stops ticking, nothing the effect in
    flight would have written after the stop began is written, and the next start replays it". The
    ADR 0002 sentence is removed or reworded the same way.
  - gateway §7 becomes "A stop the gateway or the operator requested is not a failure: the gateway
    closes the step gate, waits up to the drain for the step in flight, and exits before stopping the
    model host, so nothing is recorded after the stop began; a child restart the gateway asks for
    happens only when no request is in flight". §5 keeps the step-gate sentence.

## Acceptance criteria

- [ ] Operator: the discussion held and the decision recorded (keep / internalise / remove), with the
      wording for runtime ADR 0002 and gateway ADR 0002.
- [ ] Coordinator: AbstractGateway #98 held until the decision; then merged as is (keep) or reworked
      (internalise / remove).
- [ ] Remove or internalise only: an AbstractRuntime 0.18 item for the type's removal or
      de-export, with its tests replaced as listed above.
- [ ] Every option: the mechanism-independent e2e tests stay and pass on the released matrix.

## Receipts

- Runtime: AbstractRuntime #33 (merged `a61ee08d`, released 0.17.0).
- Gateway: AbstractGateway #98 (open, `fix/host-stop-interrupts-runs`).
- Origin: backlog 1103.
- Evidence: `untracked/release-2026-11-03/architect-restart-suspend.md`,
  `untracked/release-2026-11-03/repro-restart-suspend.md`,
  `untracked/council-2026-11-02/automation-failure-973e7ef1.md` (untracked, not in the repo).
