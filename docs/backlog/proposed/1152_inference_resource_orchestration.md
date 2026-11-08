# 1152 — Inference resource orchestration across local and remote engines (design before any build)

> Package: AbstractCore (engine/endpoint capability + load reporting), AbstractRuntime (the gate/queue), AbstractGateway (host view), a light AbstractCore agent on remote inferencers
> Type: architecture, discussion first
> Created: 2026-11-08
> Priority: medium; NOT in the current release (or only a very simple local version)
> Labels: inference, gpu, scheduling, theforge

## Operator ruling (2026-11-08 ~05:00)

On the proposed "generation gate" (background memory work waits while a foreground generation uses the same engine):
"so we need that, but we need to discuss how you plan to do it. We have potentially the orchestration of multiple
endpoints/providers, some remote, so you may not have the information you need, unless we consider we need to deploy
on those inferencers a light version of abstractcore (or equivalent) which may inform us in real time of the available
resources. This is not a simple task, this needs to be discussed before any development. You can make your proposals
but I would not put that in this release, or only a very simple version."

## The problem

Foreground generations (a visit turn, a chat, an automation) and background work (summaries, understanding, backfill)
share engines: the local GPU (one model at a time, ruling 2026-09-29), theforge-nvidia (`compat-theforge-nvidia`,
one GPU, shared KV pool ≈120–140k tokens, prefill in the thousands of tk/s, decode 40–50 tk/s, concurrency possible),
and paid relays. Nothing today tells the runtime whether an engine is busy, how much KV is free, or how long a request
will queue; background work can slow a conversation or exhaust a pool.

## Proposals (for discussion)

1. **Very simple v0 (candidate for the current wave, ≤6 h, local only):** a cross-process gate in the runtime keyed
   `local` for the local GPU: every foreground generation registers while it runs; background tasks wait while a
   foreground entry exists. Remote engines are not gated (treated as always available) and the drain's own budget caps
   concurrency. Honest limits stated in the docs.
2. **Remote awareness (the discussion the operator wants):** a light AbstractCore "inferencer agent" deployed beside
   each remote engine (theforge first) that reports in real time: loaded models, KV pool used/free, in-flight requests,
   queue depth, tokens/s; the runtime's gate reads it and the gateway shows it (Resources page). Alternative without
   deployment: infer from the engine's own metrics endpoints where they exist (vLLM/llama.cpp server `/metrics`,
   LM Studio) — partial and engine-specific.
3. **A scheduler, later**: priorities (foreground > interactive background > backfill), per-engine admission by KV
   budget, fairness across entities, and the cognition profile (runtime draft 0867) choosing engines by availability.

## Decisions to take before any build

- Do we deploy a light AbstractCore on theforge (what it reports, who owns it), or rely on engine metrics?
- Is v0 (local-only gate) worth shipping now, given that the understanding pass defaults to theforge?
- Where does the host view live (gateway Resources page) and what does an entity see of it?

## Related

Root 1146 (understanding pass) and runtime draft 0868 (the gate; now a decision-gate item); ruling 2026-09-29 (one
model process at a time, `untracked/gpu.lock`); the GPU memory rulings of 2026-09-28.

## Note 2026-11-08 (understanding-pass track; paused by operator ruling 2026-11-08, pause all dev; resume = explicit go)

- The generation gate is this item's design question, not a build of the understanding pass: DESIGN §6 "Host-wide
  generation gate" (`untracked/understanding-pass-2026-11-07/DESIGN.md`) and runtime draft 0868
  (`untracked/understanding-pass-2026-11-07/drafts/abstractruntime/0868_host_wide_generation_gate.md`: foreground
  in-flight files per engine key under `<data>/gates/<key>/`, one background slot taken only when nothing is in flight,
  `cancel_event` on a foreground arrival, a local second-model refusal) are the candidate for proposal 1 (v0).
- The drain v1 ([1171](../planned/understanding-pass/1171_understanding_drain_in_turns_and_idle_windows.md)) ships
  without a gate: it relies on the home lease, the window checks and the capability model being remote (theforge).
  Night narration and ripple consolidation go through the memory-task queue (see the 2026-11-08 note in
  [1150](1150_sleep_and_dream_phases_on_request_or_accumulation.md)).
- First measured data for per-engine admission, from the backfill on theforge
  ([1181](../completed/1181_one_time_understanding_backfill_on_theforge.md)): 4 requests in flight was the best point
  (overall 31.6 calls/min, 916 prompt tok/s, 66 completion tok/s); at 5, completion throughput fell and median latency
  rose 47%.
