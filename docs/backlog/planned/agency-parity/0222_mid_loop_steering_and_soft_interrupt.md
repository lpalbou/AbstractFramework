# 0222 — Mid-Loop Steering + Soft Interrupt (type into a running agent; redirect/stop without killing the run)

**Status**: Design converged (2 adversarial reviews folded in, 2026-07-09); implementation gated on a
runtime/gateway seam handshake (posted on agora) — wave 1 (kernel primitive, collision-free) can start
**Date**: 2026-07-09
**Priority**: TOP (maintainer ruling 2026-07-08: "of very high value to me"; includes interrupt, which we
cannot really do today below terminal cancel)
**Components**: abstractruntime (directive store + tick hook + ledger shape), abstractagent (drain/jump
semantics), abstractgateway (command routing + HTTP + tree fan-out), clients (type-while-observing UX)

## Summary
Let a user interleave messages into a RUNNING agent loop while observing it (steering lands at the next
reasoning boundary), and interrupt a loop mid-flight — redirect ("stop that, do this instead") or stop
(conclude cleanly with a summary) — without terminal cancel. Codex CLI is the bar; our design adopts its
queue/drain-gate/ack shape, adapted to durable sync ticks, and beats it on durability (directives survive
crashes and replay; Codex pending input is process-memory).

## Codex ground truth (verified against public codex-rs sources)
- SQ/EQ pair; one `submission_loop` task linearizes all state changes (single writer).
- `Op::UserInput`/`UserTurn` during a task → PENDING INPUT; the turn loop drains it into the next
  sampling request — GATED: `can_drain_pending_input = !model_needs_follow_up` (a steer never lands
  between a tool batch and the model's continuation). `needs_follow_up` and `has_pending_input` are
  separate signals OR-ed into the loop condition.
- `Op::Interrupt` → tokio CancellationToken → streams dropped, sandboxed tool children killed,
  `TurnAborted` emitted; the thread survives. `turn/steer` carries `expectedTurnId` (CAS; retry once
  with server-reported id). TUI keeps un-acked steers pending and requeues them.
- What we CANNOT copy: instant task abort (killing Python threads is unsafe; our LLM_CALL blocks in the
  tick thread). Honest ladder: v1 = boundary responsiveness; phase 2 = cooperative cancellation.

## Load-bearing findings (adversarial reviews, code-cited)
1. **`inject_guidance` is not HTTP-reachable today**: the `/commands` allowlist excludes it
   (`routes/gateway.py:22733-22737`) — hosted steering exists only for direct command-store appends.
2. **The real defect is two writers on one shared object**: the file run-store cache hands back the SAME
   mutable RunState object (`storage/json_files.py:162-166`); the command thread mutating it while a
   tick worker serializes (`json.dump(asdict(run))`) can crash the save and mark the run FAILED
   (`runner.py:742-771`). Re-checking harder cannot fix this; removing the second writer can.
3. **Drain-at-tick-entry is NOT enough**: one tick = up to 100 steps (`tick_max_steps`), so worst-case
   latency would be hours, and a directive landing while the run's final tick parks it WAITING is
   dropped FOREVER (`_submit_tick` inflight drop + scheduler only scans RUNNING/due runs).
4. **Single-writer isn't achieved by the sidecar alone**: cross-run resume paths (subworkflow parent
   resume `runner.py:804-835`, emit_event `601-609`, durable events `628-704`) write run state from
   other workers.
5. **Bare-jump redirect corrupts transcripts**: assistant `tool_calls` without matching tool messages →
   strict providers 400 (the orphan class this repo already paid for).
6. **The abstractflow anchor-listener prototype does not exist in the repo** (zero hits); the closest
   real artifact (`event-inbox-react-agent.json`) proves the fix is a durable mailbox drained at
   boundaries — i.e. this design one level down. REJECTED as the framework capability (cannot reach
   inside Agent-node child runs; WAIT_EVENT-per-iteration blocks the loop); kept as a pattern.
7. The framework already has THREE racy/divergent inbox implementations (`_runtime.inbox`,
   `events_inbox`, entity home command inbox) — this primitive must be their convergence point, not a
   fourth.

## The design (amended; 9 amendments folded)
**Primitive (abstractruntime)**: a per-run durable DIRECTIVE SIDECAR (append-only, JSONL/SQLite, same
lock discipline as `JsonlCommandStore` so appends never race compaction) whose ONLY consumer is the
tick thread. Directives: `guidance{message}`, `interrupt{mode: redirect|stop, message?}` (+ future
`event`). Idempotency watermark `_runtime.directives_applied` (bounded ring of command_ids) lives IN
run.vars so application+dedup commit in ONE atomic run save; sidecar compaction only after that save.
Per-entry fault isolation: malformed entries → FAILED ledger record + dead-letter, never a bricked run.
Every application writes a ledger record `effect.type="directive"`,
`idempotency_key="system:directive:<command_id>"`, principal stamped SERVER-side.
**Latency (the "one in-flight effect" bound made true)**: a host-injected `on_step_boundary(run)`
callback invoked where `_abort_if_externally_controlled` already sits (`runtime.py:~1428`), executed ON
the tick thread — the gateway wires it to the sidecar drain. Plus a sidecar-pending scan in
`_schedule_ticks` submitting drain ticks REGARDLESS of run status (closes the WAITING drop).
**Steering semantics (abstractagent)**: drained guidance rides the existing trailing ephemeral message
(NEVER the system prompt — 0212 prefix stability is pinned by test). Codex drain gate adopted: never
fold a steer between a tool batch and its continuation; reason-node drain satisfies this by
construction and the contract is stated for review/compaction steps.
**Redirect**: resolve pending tool calls through the OBSERVE path — synthesize per-call "interrupted by
user" results into `_temp.tool_results` (deny-path shape, `runtime.py:1762-1775`), clear
`_temp.pending_tool_calls`, then route to reason. Never bare-jump with unanswered tool_calls.
**Stop**: route to the conclude machinery (`max_iterations_node` landing pad) → run COMPLETES with a
best-effort summary; `cancel_run` stays the hard fallback (a stop against a hung provider hangs in v1).
**Interrupt during WAITs** (composes existing surfaces; NOT configurable — one rule per wait reason):
- steer + WAITING(approval): PRESERVE the wait (queued; auto-approve/Approve-All must check the sidecar
  before auto-resuming); interrupt: deny+redirect atomically, resume payload marked
  `{"interrupted": true, "command_id": ...}` so the ledger distinguishes it from a user deny; the
  delegate executor is never invoked.
- steer + WAITING(ask_user): the steer IS the answer (resume with the text; never an empty
  "[User response]:").
- interrupt + WAITING(subworkflow): tree fan-out via `_list_descendant_run_ids` — stop cancels the
  child subtree; redirect interrupts children through their own sidecars (no orphaned children burning
  tokens; orphan completion cannot resurrect the parent — verified, but double-delegation cost is real).
**Single-writer completion (abstractgateway)**: per-run write mutex covering tick execution, drain, and
the residual cross-run resume writers; converge `events_inbox` delivery onto the sidecar (delete
`_deliver_durable_event`'s shared-record write) and DELETE the old `_apply_inject_guidance` mutation
path in the same wave (partial adoption = false safety).
**CAS steering (Codex adoption)**: optional `expected_iteration`/expected wait_key on the steer API;
mismatch → reject with actual value, client retries once. **Ack as first-class observable**: clients
keep a steer "pending" until a ledger record names its directive id; undrained directives at run end
surface as "not seen".
**Local path**: `ReactAgent.send_message(text)` / `.interrupt(message, mode)` between step() calls
(host-thread mutation, race-free; replaces racy `BaseAgent.inject_message` load-mutate-save).
**Other adapters**: interrupt messages ALWAYS also ride the inbox so CodeAct/MemAct degrade to
guidance (no silent no-op).
**Auth**: interrupt/steer added to route policies with per-run ownership check; documented honestly —
in single-user token mode, steering is token-equivalent to prompt injection into a running agent.
**Replay safety bonus**: drained guidance changes the LLM_CALL payload → changes the idempotency hash →
a replayed run can never reuse a pre-steer cached result for a post-steer request.

## Placement ruling
- abstractruntime: DirectiveStore (storage/, CommandStore precedent), `_runtime.control.interrupt` flag
  semantics (ADR-0013 precedent), `on_step_boundary` hook, directive ledger record shape. NOT a new
  EffectType (effects are node-requested outbound; steering is host→run inbound — ADR-0002) and NOT a
  bare vars convention (vars conventions created the three racy copies).
- abstractagent: drain/jump semantics (reason tail rendering, redirect/stop routing, review interplay).
- abstractgateway: command verb + HTTP allowlist fix, sidecar routing, tree fan-out, per-run mutex,
  events_inbox convergence.
- clients (abstractcode/flow/assistant): composer over the live ledger SSE + "seen at iteration N" ack.

## Scope
v1 semantics: agent loops only (steering a deterministic Code node is meaningless; flows keep
pause/cancel per ADR-0013, and any flow can opt in by reading the drained var). Phase 2 (separate):
cooperative in-flight cancellation — requires a streaming execution path in the LLM handler (none
today: one blocking client call), shell killpg exists, `_call_with_timeout` daemon tools are
non-abortable, and disown-and-abort is permissible ONLY for pure sampling, never TOOL_CALLS.

## Known edges (documented, tested)
- Interrupt at a review boundary consumes a review round (budget interplay).
- Redirect at `iteration == max_iterations` lands the message in the conclusion prompt (correct; pinned).
- ask_user wait keys are deterministic per node — a delayed interrupt resolves whichever wait currently
  holds the key ("interrupt the run NOW" semantics; pinned).
- Adjacent pre-existing hole (NOT widened, must not be claimed fixed): the generic `resume` command
  already lets any token bearer approve any wait (`runner.py:513-521`; no ownership check).

## Required tests (21, from the adversarial review — ship with implementation)
Same-tick boundary visibility; WAITING-run directive survives inflight drop; replay-after-compaction
single application; redirect synthesizes results for unanswered tool_calls; mid-batch pending clear;
interrupt-deny never reaches executor; interrupt resume ledger-marked; parent interrupt stops child
subtree; orphan completion no resurrection; drain vs subworkflow-resume no lost update; poison
directive dead-letters + run still ticks; sidecar append during compaction not lost; stop completes
with summary (not CANCELLED); redirect at iteration cap concludes with guidance; interrupt between
review and review_parse; ask_user interrupt resumes with marked response; terminal-run directive no-op
+ GC; HTTP interrupt stamps server principal; duplicate command_id single inbox entry; CodeAct
degrades to guidance; local send_message between steps.

## Sequencing (collision map honored)
All three hot files carry uncommitted work: `runtime.py`/`models.py` (entity lane), `runner.py`/
`routes/gateway.py` (entity lane + my 0217c), `react_runtime.py` (my 0212/0213/0217 wave). Handshake
posted on agora (commons) naming the exact seams before hot-file edits.
- Wave 1 (collision-free, can start now): `abstractruntime/storage/directives.py` (new file) + tests;
  local `ReactAgent.send_message/interrupt` (my files).
- Wave 2 (after handshake): `on_step_boundary` hook (runtime.py), gateway routing + allowlist + mutex +
  events_inbox convergence, ReAct redirect/stop semantics.
- Wave 3: client UX (composer + ack) + live Codex-parity demo: steer a running gateway agent from the
  UI mid-iteration and interrupt it, with the ledger showing directive records.
