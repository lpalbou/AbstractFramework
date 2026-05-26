# ADR-0007: Active Context vs Stored Memory (Provenance)

## Status
Accepted (2025-12-17)

## Dates
- Proposed: (unknown; predates date tracking)
- Accepted: 2025-12-17


## Context

AbstractFramework must clearly distinguish:
- **What is durably stored and recoverable** (the runtime’s responsibility)
- **What is presented to an LLM for the current step** (the agent’s active context)

Recent `/compact` behavior in AbstractCode highlighted a mismatch:
- The CLI reported compaction success but runtime-backed memory usage did not change.
- Compaction performed text summarization without a durable provenance link to the source span.
- Summarization was unnecessarily slow on large-context models due to conservative chunking defaults.

This is a correctness issue (not just UX): without explicit separation, “memory” becomes ambiguous and tools/UX drift away from what the runtime actually persists and what the agent actually sees.

## Decision

### 1) Define two explicit layers for conversation memory

**Stored memory (durable, runtime-owned)**
- The runtime persists durable state via `RunStore` + `LedgerStore`.
- Large payloads (including archived conversation spans) are stored in `ArtifactStore`.

**Active context (ephemeral view, LLM-visible)**
- The LLM-visible conversation context is represented as `RunState.vars["context"]["messages"]`.
- This list is allowed to be compacted/rewritten as a *view* without losing the underlying stored span.

### 2) Compaction must be provenance-preserving

When older conversation messages are compacted:
- The summarized source span is written to `ArtifactStore` as JSON.
- The inserted summary message (role `system`) embeds provenance metadata pointing at the artifact id and span boundaries.

Minimum summary metadata keys:
- `kind="memory_summary"`
- `source_artifact_id`
- `source_message_count`
- `source_from_timestamp`, `source_to_timestamp` (best-effort)
- `compression_mode`, `preserve_recent`, optional `focus`

### 3) Prefer single-source-of-truth for active context

In UX components (AbstractCode):
- Memory statistics, status bars, and compaction operations must operate on the **run-backed** active context when a run is attached.
- Session-level caches (e.g., `agent.session_messages`) are permitted but must not diverge from the run-backed view.

### 4) “Memorize” is not compaction

Compaction optimizes the *active context view* under token pressure.  
Memorizing stores *memorable knowledge* (decisions/facts) durably without rewriting active context.

We introduce a runtime-owned primitive:
- `EffectType.MEMORY_NOTE`: stores a small note in `ArtifactStore` with tags + explicit provenance sources (`run_id`, `span_ids`, `message_ids`)
- notes are indexed under `_runtime.memory_spans` as `kind=memory_note`, so they can be recalled by time/tags/keyword alongside conversation spans

## Consequences

### Positive
- Eliminates ambiguity: the runtime always has access to everything, while the LLM sees a bounded view.
- Enables “safe compaction”: no destructive loss of message history.
- Creates a clean bridge to AbstractMemory later (semantic retrieval and reconstruction) without forcing it into Runtime now.
- Improves UX correctness: `/memory` and `/compact` describe the same active context the agent will use.

### Negative
- Requires basic provenance handling (message ids/timestamps) to avoid “summary without source”.
- Adds a small amount of complexity to the conversation data model (summary blocks and artifact refs).

### Neutral
- Does not mandate a specific retrieval mechanism (tool-based recall vs runtime policy); it only requires that provenance exists.

## Packages Affected
- **AbstractRuntime**: ArtifactStore is the durable store for archived spans; run vars hold the active view.
- **AbstractAgent**: Agents should treat `context.messages` as the active view and keep messages JSON-safe.
- **AbstractCode**: `/compact` and `/memory` must operate on run-backed context; UX exposes compaction controls.
- **AbstractMemory (future)**: can ingest archived spans + provenance to build semantic/graph memory.

## Related
- ADR-0005: Memory Architecture
- ADR-0002: Effect System Design (durability and waiting)
- Backlog: (new) tasks for recall/expand over artifact-backed spans
