# 1171 — The runtime drains the memory-task queue in turns and idle windows, every call in the ledger

> Package: AbstractRuntime (`identity/understanding.py` new, `identity/life.py` hooks, `identity/chat.py` `open_home`, home effect `MEMORY_REWRITE`), AbstractGateway (capability clients, visit-turn and idle drains, lease wait, spawn profiles)
> Type: feature
> Status: planned — paused
> Created: 2026-11-08
> Priority: P1
> Labels: understanding-pass, memory, runtime, gateway, paused, seat-framework

Paused by operator ruling 2026-11-08 (pause all dev); resume = explicit go.

## Summary

The reader side of AbstractMemory's task queue (memory 0060). `drain(...)` takes one queued task at a time, builds
its packet (the verbatim, the summarized digests, the card evidence or the formed dream), skips it as `over_context`
when it does not fit the capability's `max_input_tokens` (never truncated), makes ONE ledgered `LLM_CALL` on the
home runtime with the structured output `{title, digest, keywords, change}` and thinking off, applies the words in
place through memory's verbs (`rewrite_digest`, `author_world_model`, `narrate_dream`) with compare-and-set, and
settles the task. The own-time loop calls it between ticks, in rest naps and in cycle windows; the gateway calls it
after a visit turn has returned its reply and, for a home with no loop, after a visit closes. This is runtime draft
0869 plus the drain parts of gateway draft 1013. Owner: the framework seat (runtime and gateway halves).

## Why

Operator rulings 2026-11-07/08 (root [1146](../1146_understanding_pass_summaries_always_computed.md)): summaries and
metadata are ALWAYS computed, in the background, when the entity is idle, from a persistent queue; a capability model
may write in the entity's first person ("a passive memory process, part of me"); no fixed count per turn — the
drain is activation-driven (sensitivity + a hard safety cap); stored text is never cut (ADR 0054). Today the queue
exists and nothing drains it, so after the one-time backfill ([1181](../completed/1181_one_time_understanding_backfill_on_theforge.md))
every new memory is mechanical again.

## Current code reality (2026-11-08, read on the mains)

- abstractmemory `e74c29c`: `MemorySystem(task_queue=True).tasks` → `MemoryTaskQueue` (`memory_tasks.py`):
  `select_for_window(budget_seconds, sensitivity, window, hard_cap, cost_of, kinds=)`, `claim` (600 s lease),
  `ack`, `release(outcome=retry|defer|skip)`; `KIND_WINDOWS` keeps `dream.narrate` to night/nap and
  `ripple.consolidate` to night; `task_packet(token_budget=56_000)` by default; `understanding_debt()` /
  `enqueue_debt()`. The queue is `None` unless the home is opened with `task_queue=True`.
- abstractruntime `da03304`: `identity/cognition_profile.py` — `resolve_capability(home, cap, mind=)`,
  `rebuild_policy(home)` → `{sensitivity 0.5, cap_per_turn 3}`; `life.py` hooks: between ticks
  `_interruptible_sleep(self.tick_seconds)` (~3541), the rest nap and cycle windows, `_night_should_continue`;
  `spawn_loop_process` passes ONE endpoint profile (the mind's). No `identity/understanding.py` on main.
  `LLM_CALL` parks an unreachable endpoint as a durable EVENT wait (root 1168, `da03304`).
- abstractgateway: main `5df15719` holds the capability clients (`EntityRegistry.capability_llm`,
  `capability_llm_factory`, `_entity_capability_llm_handler`, entity patience kwargs, never the mind's speculation)
  and every `EntityHome` opens `MemorySystem(..., task_queue=True)`. The live gateway runs `2a68b105` (before it).
  After the next restart on main, formation, cards and dreams enqueue tasks that nothing drains until this item
  lands: they wait as `pending` (harmless, visible in the queue counts).
- No host-wide generation gate (runtime draft 0868; root [1152](../../proposed/1152_inference_resource_orchestration.md),
  design first). v1 relies on the home lease, the window checks and the capability model being remote (nerin:
  theforge `qwen/qwen3.8-27b`).

## Contract between the two halves (verbatim from `untracked/release-2026-11-07/understanding-drain/DESIGN-drain-v1.md`)

```python
# abstractruntime/identity/understanding.py
def drain(
    home_dir: Path, *,
    trigger: str,                 # "turn" | "idle" | "backfill"
    window: str,                  # a MemoryTaskQueue window: turn | visit | nap | cycle | night | idle
    budget_seconds: float,        # what this window may spend; hard_cap bounds the count
    hard_cap: int,                # cap_per_turn for turn/visit; a large number for idle windows
    parent: Mapping[str, Any],    # {"visit_run_id", "turn_id"} or {"day", "tick"} or {"backfill": id}
    llm_for_capability: Callable[[str], Any],   # capability name -> an abstractcore LLM (built by the host)
    should_continue: Callable[[], bool],        # checked at every task boundary
    holder: str = "memory-tasks",
    now: Optional[str] = None,
) -> Dict[str, Any]:              # the DrainReport below
```

- One durable run per drain window on the home runtime: workflow `memory_tasks.v1`, vars `{trigger, window, parent,
  policy}`; each task = one `LLM_CALL` effect row (usage recorded) + one `MEMORY_REWRITE` effect row (home-only
  handler registered beside `MEMORY_TEND`), so `sources=[{kind: "step", run_id, seq}]` points at a real step
  (memory ADR 0003 decision 11).
- Per task: claim → packet → token measure against `max_input_tokens` (`release(skip, reason="over_context",
  detail={tokens})`, never truncated) → `LLM_CALL` (structured output `{title, digest, keywords, change}`, thinking
  off) → structural validation (JSON shape; `change ∈ {unchanged, refined, revised, overturned}`; `keywords` a list
  of strings; no length caps) → `MEMORY_REWRITE` with `expected_version` (compare-and-set; `stale` → ack superseded)
  → ack.
- `EndpointUnreachableError` or a held home lease → `release(defer, until=now+5 min)`, no attempt spent. Malformed
  output → `release(retry, reason)`. Any other exception → `release(retry)` with the exception class in detail.
- v1 kinds: `digest.rewrite`, `card.author`, `dream.narrate` (nap/night only, and only while the night voice's 20 h
  throttle allows). `ripple.*` stay in the queue (1172).
- DrainReport: `{trigger, window, run_id, selected, applied, unchanged, superseded, deferred, skipped, failed,
  left_out_counts, calls, tokens: {prompt, completion}, seconds, rebuilt: [{task_id, kind, record_id, outcome,
  version, model}], ended_by: "empty" | "budget" | "cap" | "should_continue"}`.
- Spend: `<home>/loop_spend.json` gains `understanding: {by_trigger: {turn|idle|backfill: {calls, tokens, seconds}}}`.
- Capability clients are built by the host: in the loop process from the spawn's capability endpoint profiles
  (`spawn_loop_process(capability_endpoint_profiles={cap: private_resolution})`, one env key, never logged); in the
  gateway from `resolve_capability(...)` + the door's endpoint resolution.

Per-package drafts: `untracked/understanding-pass-2026-11-07/drafts/abstractruntime/0869_memory_task_drain_in_turns_and_idle_windows.md`
and `.../drafts/abstractgateway/1013_cognition_profile_route_and_visit_drain.md` (the route half of 1013 has landed;
the drain half is this item). Worker notes: `untracked/release-2026-11-07/understanding-drain/{runtime,gateway}/NOTES.md`.

## Scope

### In scope

- Runtime: `identity/understanding.py` (drain, prompt builder per kind from `spark.yaml`, structural validator,
  `MEMORY_REWRITE` home handler, report, spend block, CLI `python -m abstractruntime.identity.understanding --home
  DIR --window idle --dry-run | --run --budget-seconds N`); `open_home(task_queue=True)`; loop hooks (between
  ticks, rest nap, cycle window; never when paused; `TickRecord.rebuilt`); spawn capability profiles; night voice
  reads the returned `signals` key and the drain's narration stamps `night_voice.json`.
- Gateway: visit-turn drain on a per-home worker after the reply is returned (`_visit.last_drain`, probe
  `rebuilt[]`, a `#FALLBACK memory rebuild did not run` notice when it could not); idle drain for loop-less homes
  after close; `_acquire_lease` waits up to 2 s when the holder is `memory-tasks` (any other holder keeps the
  immediate 409); spawn passes every capability's private endpoint resolution (fails loudly if the runtime lacks the
  parameter); docs section "What the entity rebuilds and when", CHANGELOG, llms regenerated.

### Out of scope

The generation gate (0868 → 1152), ripple drains (1172), the backfill (done, 1180), Entity app screens, any change in
abstractmemory or abstractcore.

## Acceptance criteria

The memory owner's eleven corrections (DESIGN-drain-v1, 2026-11-08 14:00, abstractmemory `3fbaf10…e74c29c`; they
override the design text where they differ) are acceptance criteria:

- [ ] 1. Every host opens entity homes with `MemorySystem(task_queue=True)` and uses `MemorySystem.tasks` (not
      `.task_queue`); a test fails when a home is opened without it.
- [ ] 2. Budget: a task costs 60 s by default; `budget_seconds ≥ hard_cap × 60` (or `cost_of` from measured
      seconds), else every task is left out as `over_budget`; the verb's own ack (with `task_id`) is accepted.
- [ ] 3. Ripple tasks are never claimed then deferred: `select_for_window(kinds=["digest.rewrite", "card.author",
      "dream.narrate"])` reports them as `filtered`; v1 calls neither `refresh_ripples` nor `seed_ripple`, and the
      report says so.
- [ ] 4. Cards: `author_world_model` raising ValueError (stale, evidence changed, no standing card) is a refusal;
      `expected_fingerprint` (the basis before `@rev`) is passed and the standing card is re-checked before the call.
- [ ] 5. `embedder_unavailable` is a returned refusal → `release(defer)`.
- [ ] 6. Same text → the verb returns `unchanged` and does not ack: the drain acks with outcome `unchanged`; a new
      title or keywords with the same digest is not written; absent keywords pass `None` (`[]` deletes them).
- [ ] 7. Stale tasks settle without a model call (expected_version ≠ basis_version, target gone or closed);
      `task_id` is always passed to the verbs.
- [ ] 8. `task_packet(token_budget=max_input_tokens − template overhead)`; a non-empty `left_out` is
      `over_context`, skipped with its count.
- [ ] 9. The idle drain ends when a selection comes back EMPTY (sub-gate tasks stay queued).
- [ ] 10. One task claimed at a time (select → claim the first → run → select again).
- [ ] 11. `cause` passed to the verb is the task's own cause; "turn"/"idle" never reach it as a cause.

Contract learnings from the paused build (runtime NOTES, 14:10):

- [ ] A window that claims nothing starts no run (`run_id: None` in the report).
- [ ] On `EndpointUnreachableError` the `LLM_CALL` handler parks the drain run WAITING
      (`endpoint_unreachable:<base_url>`): the drain releases `defer`, excludes that capability for the window and
      resumes with `resume(payload={}, max_steps=0)`. Root 1168's scope revision (operator 2026-11-08 14:40, next
      release) turns that wait into a person-facing decision card; a drain run is background memory work and must
      keep this defer path and never raise a "needs you" card — reconcile with 1168 when either lands.
- [ ] `enqueue_card` stamps `basis_version=0` on every revision: cards are stale-checked by evidence fingerprint and
      standing card, never by version.
- [ ] The hermetic `find -newer` check allows `memory.sqlite3`, `runtime_<slug>.sqlite3`, `loop_spend.json`, the
      artifact store, `home.sqlite3` (+ `-wal`/`-shm`) and `.writer_lease`, and nothing else.

Behaviour (both halves):

- [ ] With a fake LLM: cap 2 runs exactly 2 tasks between ticks; cap 0 runs none and starts no run; a rest nap drains
      until its end; a visit, a pause, a STOP or `wake_at` ends the drain at the next task boundary with no task left
      leased.
- [ ] Every applied task has a completed `LLM_CALL` ledger row with usage, and its version cites that `(run_id, seq)`.
- [ ] Malformed output is released `retry` with reason `malformed output: …`; nothing is written.
- [ ] A visit turn with cap 1 and a pending task runs exactly one task AFTER the reply was returned, and the next
      probe lists it; a visitor message during a drain write is accepted within 2 s; a loop-less home drains after
      close until a selection is empty; a spawned loop receives two capability profiles end to end.
- [ ] Mutants go red: drop `should_continue()`; pass `expected_version=None`; remove the context check; drop the
      loop/paused guard of the idle drain.
- [ ] A real-model run on a scratch HOME copy (theforge, one GPU lock rule respected), `scripts/ci_local.sh` in both
      repos, an adversarial review, and the operator's user test before merge to any release.

## Testing

- `python -m pytest tests/test_understanding_drain.py tests/test_entity_brain_effects.py -q` (abstractruntime)
- `python -m pytest tests/test_entity_understanding_drain.py tests/test_entity_session_tools_api.py -q` (abstractgateway)
- `python -m abstractruntime.identity.understanding --home <scratch copy> --window idle --dry-run`
- `scripts/ci_local.sh` (each repo)

## State at pause (2026-11-08 ~14:10)

Shas: pending from the runtime/gateway owner for the final word; what the worker notes and `git log` show now:

- **Runtime half** (`untracked/release-2026-11-07/understanding-drain/runtime/NOTES.md`): NOTHING committed;
  abstractruntime main at `ed7d605`, every tracked file put back to HEAD. Left UNTRACKED for resumption:
  `src/abstractruntime/identity/understanding.py` (the whole drain with the contract signature, DrainReport, the
  two-node `memory_tasks.v1` run, `CapabilityClient`, prompt/validator, spend block, CLI),
  `tests/test_understanding_drain.py` (20 tests: 13 green, 7 red — three test bugs, one reason mapping, two
  tracebacks unread, one hermetic-list gap; causes in NOTES), `changelog.d/understanding-drain.md`, plus
  `runtime/existing-files-uncommitted.patch` (EffectType.MEMORY_REWRITE, the home handler beside MEMORY_TEND,
  `open_home(task_queue=True)`, the loop_spend `understanding` block, `build_capability_llm_factory`). Not started:
  loop hooks, spawn profiles, night-voice key, docs.
- **Gateway half** (`untracked/release-2026-11-07/understanding-drain/gateway/NOTES.md`, written before the revert):
  KEPT on main `5df15719` (capability clients; `task_queue=True` homes; 3 tests). REVERTED by `a1ec23ab` / `4fe24103`:
  the visit-turn drain `e8170ff4` and its changelog `021c5ccc`, because they import
  `abstractruntime.identity.understanding.drain`, which does not exist while the runtime half is paused
  (`entity_drain.py` is recoverable from `e8170ff4`). Not done: the idle drain (built, one neighbouring test
  `test_end_while_waiting_for_approval_cancels_without_running_tools[/close]` failed undiagnosed, reverted), the 2 s
  lease wait, spawn `capability_endpoint_profiles`, docs. Gateway main has moved on since (`d4fdb3a4`, backlog only).

Resume order: runtime commit 1 (patch + the seven red tests) → gateway re-applies `e8170ff4` against the real drain →
loop hooks + spawn profiles (both halves land together) → idle drain + lease wait → docs → gates.

## Receipts

- Design + corrections: `untracked/release-2026-11-07/understanding-drain/DESIGN-drain-v1.md` (operator go relayed
  by the Entity owner 2026-11-08 13:10).
- Parent: [1146](../1146_understanding_pass_summaries_always_computed.md); release: [1179](../1179_release_wave_understanding_pass.md).
