# ADR-0024: Attachment Placeholders + Compaction Invariants (No Duplicate File Content)

## Status
Proposed

## Dates
- Proposed: 2026-01-19
- Accepted: TBD

## Context

We want attachments (files and media) to be first-class inputs across clients (AbstractCode Web/TUI, AbstractObserver, AbstractFlow) while keeping these properties:

- **No duplicated file content in LLM-visible conversation messages**: a file should not be inlined repeatedly across turns and replays.
- **Durability + replayability**: attachments must be reconstructible after UI reloads; provenance must remain available.
- **Bounded retrieval**: when a model needs more than what is already attached, it must explicitly retrieve *bounded* content (line ranges / excerpts) rather than dragging entire documents into the active context.
- **Compaction safety**: `/compact` (or runtime `MEMORY_COMPACT`) must never “damage” the attachment access contract. Placeholder syntax must remain stable.

ADR-0023 establishes *path resolution + authorization* (workspace root + mounts). This ADR establishes *how attachments are represented in prompts* and the invariants that protect token-efficiency and replay correctness.

## Decision

### 1) Store once, reference everywhere (ArtifactStore + session registry)

All attachment bytes live in the runtime’s `ArtifactStore` and are indexed in a **session attachment registry** (durable, per session). The registry records at least:

- `artifact_id` (stable key for bytes),
- `handle` (canonical `@virtual/path` when available),
- `sha256` (dedup/versioning),
- `content_type`, `size_bytes`, `added_at`.

Dedup rule: if `{handle, sha256}` already exists for the session, ingestion returns the existing attachment reference (no duplicate storage and no duplicate prompt injection).

### 2) Placeholders, not inline file text (metadata-only system blocks)

The LLM does **not** receive full file contents as chat messages. Instead, the runtime injects **metadata-only** system placeholders:

1. **Active attachments** (per LLM call)
   - Derived from the call’s `payload.media`.
   - Semantics: “already included in this call as media; do not call filesystem tools or `open_attachment` for these unless you need something not present.”

2. **Stored session attachments** (session index)
   - Derived from the session attachment registry.
   - Semantics: “stored for the session; not necessarily included in this call.”

These placeholders are the stable “links” surface for attachments.

### 3) Explicit on-demand retrieval via `open_attachment`

When the model needs text content that is not already attached for the current call, it uses:

- `open_attachment(handle='@…', start_line=..., end_line=...)` for bounded excerpts (preferred)
- or `open_attachment(artifact_id='…', start_line=..., end_line=...)`

For non-text media, `open_attachment` may re-attach the artifact as `media` for the *next* LLM call.

### 4) Compaction invariants

Runtime compaction (`MEMORY_COMPACT`) must preserve the attachment access contract:

- The placeholders are **system messages**, and compaction must keep system messages verbatim (current runtime behavior).
- Any future compaction strategy that rewrites system messages must either:
  - preserve the “Active attachments” and “Stored session attachments” blocks byte-for-byte, **or**
  - regenerate them from the registry + call media in a way that is semantically identical.

We treat the placeholder blocks as a **stable interface** between runtime and models. They must never be summarized away.

## Consequences

### Positive
- Prevents accidental “context rot” where the same document is repeatedly duplicated in chat history.
- Keeps active context lean while still allowing strong RAG-like workflows via bounded retrieval.
- Makes replay consistent across clients: attachments are durable and referenced via stable handles.

### Negative
- Models must learn to use `open_attachment` for deeper access rather than expecting file text to be in the conversation transcript.
- Hosts must render attachment chips/metadata from attachment refs (not inferred from message text).

### Neutral
- This ADR does not decide the future semantic-index/RAG layer (e.g., embeddings/SQL), only the prompt surface and invariants.

## Packages Affected
- AbstractRuntime (session attachment registry, `open_attachment`, placeholder injection, compaction invariants)
- AbstractCore (media payload contract)
- AbstractGateway (attachment ingest/upload endpoints, path policy, artifact API)
- AbstractCode / AbstractObserver (UX + replay built from durable sources)

## Related
- ADR-0007: `docs/adr/0007-active-context-and-memory-provenance.md`
- ADR-0017: `docs/adr/0017-host-ui-events-and-durable-prompts.md`
- ADR-0019: `docs/adr/0019-testing-strategy-and-levels.md`
- ADR-0023: `docs/adr/0023-file-attachment-path-resolution-and-authorization.md`
- Completed backlogs:
  - `docs/backlog/completed/473-framework-session-attachment-registry-and-open-tool-v0.md`
  - `docs/backlog/completed/474-framework-unify-read-file-with-attachments-and-dedup-active-context-v0.md`
  - `docs/backlog/completed/475-abstractcode-web-artifact-backed-attachments-v1.md`
  - `docs/backlog/completed/505-framework-open-attachment-media-support-and-opened-media-injection-v1.md`
  - `docs/backlog/completed/506-framework-attachments-active-vs-session-clarity-and-handle-robustness-v1.md`

