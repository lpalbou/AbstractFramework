# ADR-0026: Truncation Policy and Contract (CRITICAL)

## Status
Accepted (2026-01-25)

## Dates
- Proposed: 2026-01-25
- Accepted: 2026-01-25

## Context

“Truncation” (dropping content because of token/char limits) is **extremely dangerous** in an agentic framework:
- it creates **silent correctness failures** (memory not written, wrong facts ingested, missing provenance),
- it produces **debugging dead-ends** (the system “works”, but the real output was cut),
- it breaks the framework’s contract posture (structured outputs, durable effects, and KG memory all depend on full fidelity).

This was observed repeatedly in production (e.g., KG extraction returning 0–1 assertions because upstream output was truncated).

We need a framework-wide policy that makes truncation:
- explicit,
- observable,
- rare,
- and never used where it can corrupt critical outcomes.

## Definitions

### Lossy truncation (the only thing this ADR governs)
Any operation that **drops user/model/tool/document content** (text/JSON/markdown/tables/messages) for budget reasons.

Examples:
- slicing response text to `N` chars,
- trimming message history,
- clipping tool output previews,
- limiting attachment inlining and dropping the rest.

Non-examples (not governed here):
- stable identifier formatting (UUID prefixes, hash prefixes) where no semantic content is lost.

### Arbitrary truncation vs. memory budget strategies (IMPORTANT)
This ADR is about **arbitrary lossy truncation** (e.g., “cut after 700 tokens/2000 chars”), which silently destroys information.

By contrast, **memory budget strategies** are *intentional selection/compression policies* used to fit a *recall/injection budget* (e.g., `instant | standard | deep` recall), without destroying the underlying stored memory.

Examples of acceptable memory budget strategies:
- selecting **which** memory packets/notes/triples to inject given a token budget,
- compressing memory into summaries **with provenance**,
- chunking large artifacts and indexing them for later retrieval,
- exposing configurable recall levels (e.g. `instant | standard | deep`) that deterministically change what is selected.

Key differences:
- **Arbitrary truncation**: drops content by cutting it; dangerous; must be explicitly warned and is forbidden in critical paths.
- **Budgeted recall**: selects/compresses *what to include* under a clear policy; allowed and expected, but must be transparent (what was selected, why, and what was omitted due to budget).

Rule of thumb:
- If the system *cuts* an item’s content (slicing), it is truncation and must follow this ADR.
- If the system *chooses* items (top‑K, diversity sampling, etc.) and keeps items intact (or summarizes with provenance), it is a budget strategy.

## Decision

### 1) Silent truncation is forbidden (framework-wide)
If content is truncated, the system MUST emit a **warning**. “Warning” includes at least one of:
- an explicit marker in the resulting text (e.g. `… (truncated)`),
- runtime metadata (`truncated=true`, `_truncation`, etc),
- and/or a logged warning event.

No truncation may occur “quietly”.

Observability requirement (attribution):
- The warning MUST be attributable to a responsible component (package/module) and, when possible, the configured source (env var / config key / parameter).
- Example: `finish_reason=length` should surface both the truncation event and the configured `max_output_tokens/max_out_tokens` that caused it.

### 2) Truncation is not allowed for critical correctness paths
Critical paths MUST be designed so truncation cannot corrupt correctness.

This includes at minimum:
- structured output calls (schemas),
- memory ingestion (KG/assertions/notes),
- provenance artifacts (spans, citations),
- durable tool execution outputs that are used as inputs to later steps.

For these paths:
- do not set arbitrary output caps by default,
- treat provider truncation (`finish_reason=length`) as a contract violation:
  - retry with higher output budget,
  - if still truncated, **fail loudly** (unless the caller explicitly opts into truncation).

### 3) Budgets should be met via compression/selection, not truncation
When we must satisfy a budget (token/char):
- prefer **compression** (summaries with provenance),
- prefer **chunking + indexing** (attachments; multi-pass extraction),
- prefer **hierarchical views** (preview vs full open) over destructive clipping.

Truncation is an emergency mechanism; compression is the default mechanism.

### 4) Code hygiene: every lossy truncation must be tagged
All lossy truncation sites must be tagged in code with the literal marker:

`#[WARNING:TRUNCATION]`

Rationale:
- easy to spot in code reviews,
- easy to grep for audits,
- prevents “accidental” truncation from creeping back in.

## Consequences

### Positive
- Fewer silent failures; correctness issues surface immediately.
- Debuggability improves (truncation becomes visible and attributable).
- Contract posture is strengthened for memory, schemas, and provenance.

### Negative
- More visible warnings; some UX surfaces may need to better present truncation metadata.
- Some operations that previously “limped along” will now fail loudly when truncation persists.

### Neutral
- We still support bounded previews for UX/logs, but they must be explicitly marked and searchable.

## Implementation Notes

Recommended pattern for bounded previews:
- preserve full content durably (artifact store / file),
- show a preview with `… (truncated)` marker and/or metadata,
- provide a path to open the full content.

## Related
- ADR-0008: Token Terminology and Parameter Naming
- ADR-0007: Active Context vs Stored Memory (Provenance)
- ADR-0027: Timeout Policy and Contract
- `docs/guides/truncation-mechanisms.md`
