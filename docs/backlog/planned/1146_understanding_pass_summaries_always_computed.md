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

## Plan (from the report; ~26 h + ~3 h app; order matters)

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

## Coordination

Same split as 1145 (framework: memory verbs if free, runtime, gateway; Entity owner: app). Their answer, and whether they
have already started the memory verbs, is appended here.

## Acceptance criteria

- [ ] After one night, every episode and summary node of a test home has a model-written digest with `authored_by`.
- [ ] A disruptive present fact re-opens the connected earlier memories (ripple) and the dream consolidates them.
- [ ] Rewrites keep the record id and carry the previous text + provenance.
- [ ] The queue survives a gateway restart (persistent) and resumes.
