# 136 — ai-space: Portable Semantic Retrieval + Graph Memory (SQLite+sqlite-vec, /query-integrated)

**Status**: Completed (archived)  
**Date**: 2026-04-14  
**Priority**: High (scaling + determinism + UX)  
**Components**: ai-space (app), abstractcore (blocs + metadata + embeddings), abstractmemory (graph/hypergraph), abstractsemantics (predicate allowlist)

## Summary

ai-space currently scales caching well (per-bloc KV artifacts), but **catalog-level retrieval does not scale**:
having an LLM “read one giant `metadata.json`” hits context limits and is non-deterministic.

This item implements a **portable, deterministic stage‑0 retrieval layer** plus a **canonical relationship graph**
to regain composability across independently cached blocs.

Key decisions:
- **Documents/caches live in AbstractCore** (file blocs, KV artifacts, per-bloc `meta.jsonld`).
- **Relationships live in AbstractMemory** (append-only temporal triples; graph/hypergraph-ready).
- **ai-space uses a local SQLite DB** as a retrieval accelerator:
  - `sqlite-vec` for semantic KNN (default)
  - FTS5 optional for advanced lexical matching (acronyms/filenames/rare tokens)
- **Single UX entrypoint** for retrieval: `/query <target> <message...> [-- filters...]` (no `/index` command family).

## Context / constraints (ADRs)

- **ADR-0001 Layered architecture**: no dependency cycles; app composes packages.
- **ADR-0005 Memory architecture**: long-term memory/graph is a separate package (AbstractMemory).
- **ADR-0009 Connected memory recall**: graph-ready recall contracts; provenance-first.
- **ADR-0019 Testing strategy**: ship Level A/B tests; keep deterministic, restart-safe semantics where relevant.
- **ADR-0026 Truncation policy (CRITICAL)**: forbid silent truncation; all caps must be tagged and visible.
- **ADR-0029 Dependency policy**: keep dependencies minimal by default; heavy/optional features must be gated.

## Problem

1) **Retrieval over large catalogs breaks**:
- A single consolidated `metadata.json` quickly exceeds model context limits.
- LLM-based “candidate selection” is non-deterministic and fragile (JSON parsing, truncation).

2) **Cached blocs are not composable by default**:
- Each bloc is cached independently (KV prefixes), so cross-bloc structure is lost unless we rebuild it explicitly.
- We need a durable graph/hypergraph layer (superblocs + edges) to express “this set belongs together”.

## Decision

### 1) Canonical graph/hypergraph lives in AbstractMemory

Superbloc membership and future edges are represented as append-only assertions (temporal triples):

- Node ids:
  - `sb:<id>` (superbloc)
  - `bloc:<sha256>` (file bloc node id)
- Predicates (from AbstractSemantics allowlist where possible):
  - `dcterms:hasPart` (`sb:<id> dcterms:hasPart bloc:<sha>`)
  - `dcterms:isPartOf` (optional inverse)

Because AbstractMemory v0 is append-only, membership edits are modeled as operations:
- `attributes={"op":"add"}` or `attributes={"op":"del"}`
- Current membership is computed by folding the latest op per `(sb, predicate, bloc)` by `observed_at`.

### 2) Deterministic stage‑0 retrieval uses local SQLite + sqlite-vec

We build/maintain a local DB under ai-space state:
- `~/.abstractcore/ai-space/search/<model-slug>/meta.sqlite`

Schema (v0, minimal):
- `blocs(id INTEGER PRIMARY KEY, sha TEXT UNIQUE, filename, path, kind, mod, lang, tok, title, desc, kw_json, tp_json, ...)`
- `blocs_vec` (sqlite-vec virtual table; `rowid = blocs.id`)
- `index_meta(embed_model TEXT, dim INT, built_at, updated_at)` (single row)
- optional `blocs_fts` (FTS5) for advanced lexical/hybrid retrieval

Retrieval mode (default):
- Embed query via `abstractcore.embeddings.EmbeddingManager` (configurable provider/model).
- KNN on `blocs_vec` → topK candidates.
- Apply deterministic facet filters by joining against `blocs` (and restricting to the target superset).

No silent fallback:
- If semantic retrieval cannot run, fail with an actionable message.
- If lexical/hybrid is requested but FTS5 is unavailable, fail with an actionable message.

### 3) UX unification: `/query` is the only query entrypoint

`/query <target> <message...> [-- <filters...>]`

Targets:
- `session:<id|title>` (session memory with history)
- `blocs:all` / `blocs:<ids>` / `blocs:<range>`
- `sb:<id>` / `sb:any(id1,id2)` / `sb:all(id1,id2)`

Planner (deterministic):
1. Expand target → superset (session selected_memory, explicit bloc ids, superbloc membership via AbstractMemory)
2. If superset “large” → stage‑0 retrieval against SQLite (semantic default)
3. Run existing KV pipeline on candidates (optional router → map → reduce)

Explainability:
- `/query ... --explain` prints retrieval mode, SQL, params, candidate sha12 list (+scores).
- `/debug on` logs prompts/outputs and stage decisions (ADR-0004 observability + ADR-0026 truncation tags).

## Alternatives considered

- **KùzuDB**: compelling “graph + vector + FTS” surface and good wheels, but upstream `kuzudb/kuzu` is archived (too risky as a core dependency).
- **LanceDB**: strong vector indexing, but heavier deps and does not replace the need for a canonical relationship layer; keep optional.
- **DuckDB VSS**: powerful analytics, but persistent ANN caveats make it a poor default durable substrate.
- **LLM reads metadata catalog**: rejected (non-deterministic + context limits + parsing failure modes).

## Implementation plan

1) **Move ai-space to top-level repo layout**
   - Create `ai-space/` as a standalone package (own `pyproject.toml` + tests + docs).
   - Update workspace dev instructions: `pip install -e ./abstractcore -e ./abstractmemory -e ./abstractsemantics -e ./ai-space`.

2) **AbstractMemory: add a portable persistent store**
   - Implement `SQLiteTripleStore` (stdlib `sqlite3`; no extra deps).
   - Keep semantic queries opt-in; error if `query_text/query_vector` is used without configured backend (no silent fallback).

3) **ai-space: replace superbloc file-store with AbstractMemory graph**
   - Implement `SuperBlocGraph` adapter in ai-space over `TripleStore`.
   - Enforce predicate allowlist via AbstractSemantics (fail loudly on unknown predicates unless explicitly configured).

4) **ai-space: implement SQLite+sqlite-vec retrieval accelerator**
   - Schema + ingestion from per-bloc `meta.jsonld`.
   - Embeddings via `abstractcore.embeddings.EmbeddingManager` (config-driven model id).
   - Deterministic topK KNN + facet filtering + superset restriction.

5) **ai-space: unify query UX**
   - Implement `/query <target> <message...> [-- filters...]` as the primary entrypoint.
   - Keep legacy commands as thin aliases initially; document deprecation path.

6) **Tests + docs**
   - Unit tests: graph membership fold semantics (add/del/clear).
   - Unit tests: retrieval schema + deterministic candidate selection with a tiny metadata fixture.
   - Integration tests: `/query sb:<id> ...` expands membership → retrieval → map/reduce with stub provider.
   - Update ai-space docs: new architecture, install, `/query` flows, and `--explain`.

## Acceptance criteria

- Works on macOS/Linux/Windows (no daemon).
- No LLM-over-catalog path remains in the default retrieval planner.
- `/query` can target blocs, superblocs, and sessions with one grammar.
- Superbloc membership is durable and graph-ready (AbstractMemory).
- Truncation/timeouts obey ADR-0026/0027 (all caps are visible + tagged).

---

## Completion report (2026-04-14)

### What shipped

- Deterministic **semantic stage‑0 prefilter** (SQLite + `sqlite-vec`) built from `/cache metadata` (no “LLM reads the catalog”).
- A durable **superbloc membership graph** stored as append‑only temporal triples (AbstractMemory).
- Unified query UX: `/query <target> <message...> [-- flags...]` (legacy superbloc query commands deprecated).
- Observability: `/query ... --explain` prints semantic prefilter details; `/debug on` logs prompts/outputs per query.
- ADR‑0026 compliance for output caps and bounded previews: all truncation/cap sites are tagged `#[WARNING:TRUNCATION]`.

### Where data lives

- File blocs + KV artifacts: `~/.abstractcore/blocs/files/<sha256>/`
- Sessions: `~/.abstractcore/ai-space/sessions/<session_id>/`
- Metadata catalog snapshot: `~/.abstractcore/ai-space/catalogs/<model-slug>/metadata.json`
- Semantic search DB: `~/.abstractcore/ai-space/search/<embed-slug>/meta.sqlite`
- Superblocs KG store: `~/.abstractcore/ai-space/kg.sqlite`

### How to run (editable installs)

From `/Users/albou/tmp/abstractframework/`:

```bash
pip install -e ./abstractcore -e ./abstractmemory -e ./abstractsemantics -e ./ai-space
ai-space
```

### Minimal demo (semantic prefilter + superbloc graph)

1) Cache a folder:

```text
/model mlx:mlx-community/Qwen3.5-9B-MLX-4bit
/cache /path/to/mnemosyne/memory --ext md --catalog
```

2) Build `metadata.json` + semantic DB (required for semantic prefilter):

```text
/cache metadata
```

3) Create a superbloc and attach blocs (ids come from `/blocs list`):

```text
/superbloc lineage add 1:50
/superbloc lineage
```

4) Query the superbloc with semantic prefilter enabled:

```text
/route meta on
/query sb:lineage What were the last experiments we did? --explain
```

### End‑to‑end query flow

1) **Target expansion**: `/query sb:<id> ...` expands to member `bloc:<sha256>` ids via AbstractMemory triples (folding `attributes.op=add|del` by `observed_at`).
2) **Semantic prefilter (optional)**: when `/route meta on`, ai-space embeds the user question and runs deterministic KNN in `sqlite-vec` restricted to the superset; keeps top‑K candidates.
3) **KV fan‑out**:
   - If `/route on`, ai-space runs a per‑bloc **YES/NO router** sequentially (load stable KV once, fork temp, route, optionally answer, clear temp + unload stable).
   - If `/route off`, it runs the per‑bloc extraction prompt on all candidates.
4) **Reduce**: a final reducer call synthesizes the answer from per‑bloc results + (optional) session transcript.

### Tests run

- `ai-space`: `pytest -q`
- `abstractmemory`: `pytest -q`
- `abstractsemantics`: `pytest -q`
- `abstractcore`: `pytest -q tests/test_bloc_metadata_json_extract.py`

### Follow-ups

- Optional FTS5 lexical index for advanced “exact token/path/acronym” matching and hybrid ranking.
- Expand superblocs from “membership only” to richer graph/hypergraph edges (claims, citations, tensions, chronology) using AbstractMemory primitives.
