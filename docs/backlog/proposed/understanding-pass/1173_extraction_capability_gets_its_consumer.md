# 1173 — The `extraction` capability gets the consumer it was reserved for

> Package: AbstractMemory (0050 entity registry, 0051 claim lifecycle and revision log), AbstractRuntime (drain kinds, cognition profile), AbstractGateway (profile route copy), AbstractEntity (Settings → Mind row)
> Type: feature
> Status: proposed
> Created: 2026-11-08
> Priority: P3
> Labels: understanding-pass, extraction, memory, paused

Paused by operator ruling 2026-11-08 (pause all dev); resume = explicit go.

## Summary

The cognition profile has three capabilities: `summaries`, `understanding` and `extraction`. The first two have
consumers (memory task kinds, drained by [1171](../../planned/understanding-pass/1171_understanding_drain_in_turns_and_idle_windows.md));
`extraction` is configurable, validated, shown in Settings → Mind and resolved, but nothing calls it. Its intended
consumer is the memory extraction lane of abstractmemory 0050 (entity registry, candidate lookup decided by an
injected reader) and 0051 (claims with provenance, revision log). This item wires that consumer once those exist.

## Why

Operator decision 7 (DESIGN §17, 2026-11-08): "Extraction capability: keep visible, default to theforge-nvidia, same
model." A visible setting that changes nothing is a silent no-op; the profile must either drive work or say it does
not yet.

## Current code reality (2026-11-08)

- abstractruntime `identity/cognition_profile.py`: `CAPABILITIES = ("summaries", "understanding", "extraction")`;
  the docstring says `extraction` "is reserved for the memory extraction lane". No caller resolves it.
- abstractmemory `memory_tasks.py` (`e74c29c`): task kinds map only to `summaries` and `understanding`.
- abstractmemory backlog `planned/knowledge_graph_convergence/0050_entity_registry_identity_and_reversible_merges.md`
  and `0051_claim_lifecycle_and_revision_log.md`: planned, unbuilt; both keep "the extraction prompt and its schema
  (consumer framing)" out of memory, so the prompt belongs to the host (this item).
- `runtime/entities/nerin/cognition.yaml` sets all three capabilities to `endpoint:compat-theforge-nvidia` /
  `qwen/qwen3.8-27b`, thinking none; castor, hypnos and ephemeral have no profile (inherit the mind).

## Scope

### In scope

- New memory task kind(s) for extraction (owned by memory, enqueued at formation), capability `extraction`, drained by
  the 1171 drain with an extraction template and a structural schema; results applied through 0050/0051's verbs.
- Until then: the Settings → Mind row and the profile GET state plainly that extraction has no work yet (no silent
  setting).

### Out of scope

Building 0050/0051 themselves (memory owner); any regex or NLP heuristic to find entities (ruling 2026-09-27).

## Promotion criteria

Memory 0050/0051 built; 1171 merged; the operator's go.

## Acceptance criteria

- [ ] A formed episode naming a person enqueues one extraction task; the drain resolves it with the `extraction`
      capability's model and the registry gains or reuses one entity with a match reason.
- [ ] With `extraction` pointed at a different model than `summaries`, the ledger shows each call on its own model.
- [ ] Before the consumer exists, GET `/entities/{name}/cognition-profile` and Settings → Mind say extraction has no
      work yet.

## Testing

- `python -m pytest tests/test_understanding_drain.py -q -k extraction` (abstractruntime, when built)

## Receipts

- DESIGN §7 and §16.7/§17.7: `untracked/understanding-pass-2026-11-07/DESIGN.md`.
