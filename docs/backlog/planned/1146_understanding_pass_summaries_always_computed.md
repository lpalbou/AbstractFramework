# 1146 — Understanding pass: summaries and metadata are always computed, in the background, with a ripple

> Package: AbstractMemory (verbs, display block), AbstractRuntime (understanding pass, persistent queue, cognition
> profile), AbstractGateway (digest fields served), AbstractEntity (provenance badge; other agent)
> Type: architecture + implementation
> Created: 2026-11-07
> Priority: HIGH (operator 2026-11-07/08: "critical"; discuss with the AbstractEntity agent first, they may have started)
> Labels: entities, memory, runtime, summaries

## Operator rulings (2026-11-07 evening, memory note `entity-understanding-pass-2026-11-07`)

- Summaries and metadata must ALWAYS be computed: a queue of understanding tasks, drained when idle, eventual
  consistency; the queue is PERSISTENT (in the runtime, or a higher-level memory-task queue inside abstractmemory).
- A disruptive fact delivered in the present re-interprets earlier memories: reaction (surprise) → ripple through
  connected memories until an activation threshold → consolidation in the sleep/dream phase.
- Per-capability model config (dialogue, semantic extraction, summaries, understanding), defaulting to the entity's mind.
- Backfill everything once (theforge-nvidia endpoint, Qwen 3.8 27B; context < 140k tokens is fine).
- Rewrite IN PLACE (keep record id, history, usage; store previous text + provenance); never mint new records.
- AbstractNote's prompts/shapes port into abstractmemory; its lease queue and library API do not.

## Root cause (report `untracked/summaries-investigation-2026-11-07/root-cause-report.md`)

Every memory node has only a mechanical summary. abstractmemory's verbs exist (`apply_redigestion`,
`author_world_model`) but the runtime never calls them: `apply_redigestion` has no caller; `author_world_model` is
unreachable in personal time (chat.py returns the mechanical close first) and never called by the visit workflow; the
night narrator reads `signals` that `dream_pass` never returns (0 narrations in 17 homes); the gateway serves no
digest / digest_method / authored_by / card target. 0 authored cards anywhere; castor's 29/34 "entity-authored" digests
are leaked model reasoning from a manual pass on 2026-07-13, still live.

## Plan — superseded by the Entity owner's DESIGN.md (≈82.5 h in 15 steps, 2026-11-08)

The authoritative plan is `untracked/understanding-pass-2026-11-07/DESIGN.md` §15 and its drafts; the outline below is
the earlier estimate and stays only as history. Adjustments ruled the same evening: the persistent task queue lives in
**abstractmemory** (a higher-level queue of memory tasks, per home DB) and the runtime drains it (runtime 0869: N tasks
per turn, the rest in idle windows, every call a ledgered LLM_CALL in a durable run, oversize tasks skipped as
`over_context`, never truncated); rewrites are IN PLACE with versions (memory 0059); a cognition profile per capability
in `cognition.yaml` beside `substrate.yaml` with a Mind setting `memories_rebuilt_per_turn` (default 1; runtime 0867,
gateway 1013); a host-wide generation gate so background work never competes with a foreground generation on the same
engine (runtime 0868, decision-gate); the ripple is first-class: the entity's own ```revise``` election triggers it,
the existing spreading-activation threshold spreads it, sleep consolidates it as a "what this changes" note (runtime
0870, memory 0061); `dream_pass` returning its signals is a one-line memory fix; the night voice's 20 h throttle retires
in favour of the queue's budgets. Build order: gateway serve-stored-fields first (3 h, can ship alone) → memory
(signals 0.5 h; versions 9 h; queue 7 h) → runtime (profile 4 h; gate 6 h; drain 10 h; loop hooks 5 h) → gateway routes
7 h → backfill preflight 3 h → entity app 8 h → ripple 12 h → entity strip 2 h → live backfill (hypnos pilot first) →
docs 3 h. Framework owns the runtime and gateway steps; the Entity owner the memory, app and backfill steps.

### Earlier outline (history, ~26 h)

1. **Memory (~8 h, first):** `understanding_debt()` (lists rewrite candidates, mechanical cards, un-narrated dreams);
   additive `narrate_dream()`; `dream_pass` returns its signals; display block adds digest, digest_method, authored_by,
   target, redigested_from, current replacement.
2. **Runtime (~15 h):** `understanding.py`: one model call per item on the home's model (`_narrator_llm`), reasoning
   stripped, short/fenced output rejected, applied through the memory verbs with author + model recorded, bounded per
   window and resumable; a persistent queue; scheduled after the sleep pass under the dream lease, then idle naps and
   cycle windows; spend counted in `loop_spend`; the ripple (spreading activation over connected memories: verify the
   existing attention-window code before writing new); per-capability model config.
3. **Gateway (~3 h, can ship alone):** the verbatim route returns digest, digest_method, authored_by, target/revision/
   source_count and superseded_by; summaries without a verbatim are served as their full text.
4. **App (~3 h, Entity owner):** provenance badge, "understanding as of", graph hover carries the summary.
5. **Backfill once** with the operator's endpoint; cost table in the report (nerin ≈ 0.75 M tokens).

Open point (1 h+): nothing checks whether the GPU/model is idle; a host-wide one-model gate for local engines needs a
decision (GPU lock rule of 2026-09-29).

## Coordination (settled 2026-11-08 ~02:00)

Same split as 1145: framework = runtime (0867–0870) + gateway (1012–1013); Entity owner = abstractmemory (0059–0061),
app (0001–0002), backfill (1137). They have started the app only (25 local commits, operator-tested); no base-package
code yet. Blocked on the operator's 8 decisions (DESIGN.md §16): in-place rewrite accepted (amends ADR 0003)? may a
capability model write in the entity's first person with the badge naming the model? `memories_rebuilt_per_turn`
default 1 / max 5, visits too or loop ticks only? steady-state rebuilds on paid relays or on theforge? build the
generation gate now (6 h) and refuse a second local model in v1? backfill castor's 34 "entity-authored" digests (29 with
leaked reasoning) and keep candidates/dedup groups out? `extraction` has no consumer: disabled or hidden? retire the
night voice's 20 h throttle, and record surprise as a feeling (default: words only)?

## Acceptance criteria

- [ ] After one night, every episode and summary node of a test home has a model-written digest with `authored_by`.
- [ ] A disruptive present fact re-opens the connected earlier memories (ripple) and the dream consolidates them.
- [ ] Rewrites keep the record id and carry the previous text + provenance.
- [ ] The queue survives a gateway restart (persistent) and resumes.
