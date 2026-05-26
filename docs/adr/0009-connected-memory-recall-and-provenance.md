# ADR-0009: Connected Memory Recall (Provenance-First, Graph-Ready)

## Status
Accepted (2025-12-18)

## Dates
- Proposed: (unknown; predates date tracking)
- Accepted: 2025-12-18


## Context

AbstractFramework must support **durable memory** while keeping **active context** bounded and scenario-dependent.
We already have:
- **Stored memory (durable, runtime-owned)** via `RunStore` / `LedgerStore` / `ArtifactStore`
- **Active context (LLM-visible view)** via `RunState.vars["context"]["messages"]`
- Provenance-preserving compaction: summary messages reference archived spans in `ArtifactStore` (ADR-0007)

What is still missing for a robust UX and agent correctness:
- A **first-class recall path** that lets agents request original memory by **time range / topic / person** without ad-hoc per-agent logic.
- **Connected recall**: “give me related spans” (same discussion window / shared tags), which is a prerequisite to future graph-level memory.
- A **provenance handle visible to the LLM**: today provenance may exist only in message metadata, which many prompt builders do not render.

This ADR defines the minimal contracts to enable provenance-based recall now, while keeping space for future semantic/KG memory (AbstractMemory).

## Decision

### 1) Spans are the durable unit of archived episodic memory

When compacting older messages, the runtime stores a JSON artifact:
- `artifact_id` is treated as the stable `span_id`
- payload includes the original messages and a small span header (timestamps, message-id boundaries)

We also support non-conversation “span-like” memory:
- **Memory notes** (`kind=memory_note`): small durable notes (decisions/facts) stored in `ArtifactStore` with explicit provenance sources
- notes are indexed in `_runtime.memory_spans` with point-in-time boundaries (`from_timestamp == to_timestamp == created_at`)

The run maintains an index:
- `RunState.vars["_runtime"]["memory_spans"]`: list of span metadata dicts
- each entry includes:
  - `artifact_id` (`span_id`)
  - time boundaries (`from_timestamp`, `to_timestamp`)
  - message-id boundaries (`from_message_id`, `to_message_id`)
  - `message_count`
  - optional `tags` (e.g., `topic`, `person`, `project`)
  - `summary_message_id` (for reverse linkage)

### 2) Summary ↔ source span linkage must be bidirectional and LLM-visible

Every inserted summary message must:
- embed provenance in metadata (`source_artifact_id`, boundaries) for programmatic correctness
- embed the `span_id` in **visible content** so the LLM can request exact recall without guessing

This avoids relying on prompt builders to render metadata.

### 3) Recall is runtime-owned and provenance-based

Recall is modeled as a runtime-owned operation that:
- filters spans by time range / tags / keyword query (metadata-first)
- optionally performs a bounded deep scan of archived messages (substring match) when needed
- can return the original messages (or excerpts) with provenance
- may optionally rehydrate into active context, but **the default agent path is “return as tool output”**

Semantic/embedding retrieval is explicitly deferred to AbstractMemory.

### 4) “Connected memory” is deterministic (for now)

Connected spans are defined without embeddings:
- adjacency in time (neighbor spans in chronological order)
- shared tag values (e.g., same `topic`/`person`)

This establishes a graph-ready contract without premature KG/embedding systems.

## Consequences

### Positive
- Agents can precisely “open” a summary back into sources using `span_id` (no ambiguity).
- Runtime memory behavior becomes consistent, inspectable, and testable.
- Provides clean seams for future **graph compression** and **AbstractMemory** (semantic/KG) without overengineering today.

### Negative
- Recall results can be large; UX must encourage bounded recall and compaction.
- Without semantic indexing, keyword recall may require bounded deep scans (acceptable for MVP).

### Neutral
- Tags are optional now; extraction of entities/relationships is deferred (AbstractMemory).

## Packages Affected
- **AbstractRuntime**: owns span index, recall APIs/effects, and durability invariants.
- **AbstractAgent**: exposes recall to agents via built-in tool schemas / adapters.
- **AbstractCode**: may provide `/recall` UX and ensure compaction summaries include visible `span_id`.
- **AbstractMemory (future)**: can ingest span artifacts + tags to build semantic/KG retrieval.

## Related
- `docs/adr/0007-active-context-and-memory-provenance.md`
- `docs/backlog/completed/030-abstractruntime-active-context-policy.md`
- `docs/backlog/planned/033-framework-graph-compression-contracts.md`
