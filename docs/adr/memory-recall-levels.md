# ADR: Memory Recall Levels (urgent | standard | deep)

## Status
Accepted (2026-01-19)

## Context

Time and compute are limited resources. A long-term memory system that always “does everything” will be:
- too slow for interactive use,
- too expensive to run continuously,
- hard to debug (because it mixes cheap and expensive behaviors unpredictably).

AbstractFramework already has multiple memory substrates with different cost profiles:
- **Raw evidence archive** (Artifacts + Ledger + Runs): durable, high-fidelity, but expensive to search deeply.
- **Span-index memory** (Runtime `memory_*` effects): cheap metadata filtering + targeted rehydration.
- **Semantic memory** (AbstractMemory KG): durable symbolic assertions with optional semantic retrieval via embeddings.
- **Active Memory** (token-budgeted prompt block): what the LLM can actually use per call.

We need a binding way to express “how much effort should recall spend” so:
- interactive situations can stay fast,
- deeper recall can be explicitly requested or scheduled,
- expensive improvements (reconsolidation) can be amortized offline,
- the system remains trustworthy (no silent downgrades).

## Decision

### 1) Introduce a framework-wide `recall_level` policy

All recall surfaces must accept an explicit `recall_level` enum:

- `urgent` — “I need the best answer now”
- `standard` — “reasonably thorough, bounded”
- `deep` — “explore recursively; connect and learn; can be slow/expensive”

This policy becomes binding across:
- AbstractRuntime memory effects (`memory_query`, `memory_rehydrate`, `memory_kg_query`, and future deep recall effects)
- AbstractGateway endpoints that expose recall (directly or via workflow execution)
- AbstractFlow nodes and workflow templates (pins + defaults)

### 2) No silent downgrade

If a caller requests a recall level that cannot be satisfied (e.g. `urgent` requires a precomputed hot index that doesn’t exist; `deep` requires a scheduler/worker that isn’t enabled), the system must:
- either return a clear error, or
- explicitly return a partial result with an **explicit warning field** (never silent fallback).

### 3) Recall levels define budgets + allowed operations

Each `recall_level` sets *caps* and *permissions* for:
- **latency budget** (wall clock)
- **token budgets** (Active Memory packing)
- **retrieval budget** (top-k, min_score thresholds)
- **graph traversal budget** (max hops, max nodes expanded)
- **rehydration budget** (max artifacts/spans to fetch)
- **LLM budget** (whether LLM summarization/compaction is allowed inline)
- **side effects** (whether new durable knowledge may be written)

### 4) Deep recall is allowed to create “learned shortcuts”

`deep` recall may produce and persist **new derived assertions** (triples) that encode newly discovered connections
so future `urgent` recall becomes faster and more informative.

Constraints:
- derived assertions must be marked as derived (provenance + lineage)
- derived assertions must preserve **(original) ↔ (derived/compact)** lineage
- derived assertions must not delete/overwrite atomic assertions (append-only)

## Definitions (binding)

### Recall
The process of turning a stimulus (query) into a bounded Active Memory block + optional grounded evidence.

### Raw archive vs fast recall
- **Archive**: everything (spans, tool outputs, files) — durable, but not instantly recallable.
- **Fast recall**: curated indices and compactions that support interactive latency.

### “Effort” budgets (non-negotiable caps)
Budgets cap the work performed. They are part of determinism and UX safety.

## Level Profiles (defaults)

These are default profiles. Implementations may expose overrides, but must still respect the *upper bounds*
implied by the selected level (e.g. `urgent` cannot silently act like `deep`).

> Source of truth: `abstractruntime/src/abstractruntime/memory/recall_levels.py`.

### Default Budgets (v0)

The following defaults are **binding** when `recall_level` is provided (callers may override knobs only within these envelopes).

#### Span recall (`memory_query`)

| level | `limit_spans` default | `limit_spans` max | `deep` allowed | `connected` allowed | `neighbor_hops` max | `max_messages` default | `max_messages` max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| urgent | 2 | 3 | no | no | 0 | 30 | 60 |
| standard | 5 | 8 | yes | yes | 1 | 80 | 150 |
| deep | 8 | 20 | yes | yes | 2 | 200 | 600 |

#### Rehydration (`memory_rehydrate`)

| level | `max_messages` default | `max_messages` max |
| --- | --- | --- |
| urgent | 30 | 60 |
| standard | 80 | 200 |
| deep | 200 | 800 |

#### KG recall (`memory_kg_query`)

| level | `min_score` default (semantic) | `min_score` floor | `limit` default | `limit` max | `max_input_tokens` default | `max_input_tokens` max |
| --- | --- | --- | --- | --- | --- | --- |
| urgent | 0.55 | 0.50 | 20 | 40 | 600 | 1000 |
| standard | 0.40 | 0.25 | 80 | 200 | 1200 | 3000 |
| deep | 0.25 | 0.00 | 200 | 1000 | 2400 | 6000 |

### `urgent`
Goal: **instant** best-available context.

- Retrieval:
  - semantic search only (if requested); high `min_score`
  - small `limit` (top-k)
- Graph:
  - **0–1 hop** expansion max (optional)
  - no recursive traversal
- Evidence:
  - no automatic evidence rehydration (unless explicitly pinned by the workflow)
- LLM:
  - **no** LLM summarization/compaction inline
- Outputs:
  - small `active_memory_text` (tight budget)
- Side effects:
  - no writes (read-only), except durable logging of the recall event

### `standard`
Goal: good coverage, still bounded.

- Retrieval:
  - semantic + pattern filters
  - moderate `limit`, moderate `min_score`
- Graph:
  - **1–2 hop** bounded neighborhood expansion
  - bounded pathfinding allowed (within loaded subgraph)
- Evidence:
  - small capped rehydration allowed (few spans)
- LLM:
  - optional *lightweight* summarization allowed if needed to fit budget, but must be deterministic in size
- Outputs:
  - moderate `active_memory_text` budget
- Side effects:
  - optional writes of “learned shortcut” assertions ONLY if explicitly enabled by workflow/policy

### `deep`
Goal: explore recursively, connect, and improve future recall.

- Retrieval:
  - iterative retrieval cycles allowed (multi-query)
- Graph:
  - multi-hop traversal allowed, but bounded by:
    - max hops
    - max expanded nodes
    - max wall time
  - can spawn subflows for exploration
- Evidence:
  - allowed, but capped and staged (rehydrate only when needed)
- LLM:
  - allowed for summarization + compaction + conflict detection
  - expensive operations should be scheduled when possible
- Side effects:
  - may persist:
    - compaction summaries
    - derived shortcut edges
    - community metadata
  - must preserve lineage

## Consequences

### Benefits
- Predictable latency and cost.
- Better user trust (explicitly bounded; no silent behavior changes).
- Natural integration point for scheduled reconsolidation.
- Enables emergent improvement: deep recall produces durable shortcuts that improve urgent recall over time.

### Costs / risks
- More API surface area (must be propagated consistently).
- Requires careful tuning of defaults (budgets, thresholds).
- Risk of “missing” context in `urgent` mode unless reconsolidation/hot-indexing is working.

## Implementation Notes (required)

1. `recall_level` must be a first-class pin/field in:
   - AbstractFlow nodes that perform recall (span recall, KG recall, rehydration, future deep recall nodes)
   - AbstractGateway request schemas where recall is exposed
2. Any recall result must be able to carry:
   - `warnings[]` (explicit partial/constraint explanations)
   - `effort` metadata (what budgets were applied and what was actually consumed)
3. Deep recall outputs intended to improve future recall must be written as new assertions with provenance + lineage.

## Related
- `docs/report/2026-01-19_abstract-memory-status.md`
- `docs/guides/memory-components.md`
- `docs/memory-kg.md`
- `docs/backlog/planned/486-framework-recursive-memory-compaction-and-community-detection.md`
- `docs/adr/0019-testing-strategy-and-levels.md`
