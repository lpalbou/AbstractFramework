# 1015 — Memory blocs: many searchable memory blocs, searched or attached to an agent's context

> Package: abstractcore, abstractmemory, abstractruntime, abstractagent, abstractgateway, abstractflow
> Type: proposal
> Created: 2026-10-11
> Priority: normal
> Labels: memory, memory-blocs, retrieval, embeddings, hybrid-search, agents, visualflow

## Summary

Extend the framework's **memory blocs** so a user can have **many memory blocs** (named, each a
set of records with text and metadata) and, for any agent or flow step, choose **which blocs to
search** and/or **which blocs to attach to the context**:

1. **Search** a chosen set of blocs by relevance: hybrid keyword (BM25-class) + vector
   (embeddings), with metadata filters, scored.
2. **Select** deterministically: ALL records of the chosen blocs that match criteria A, B, C
   (metadata filters, stable order, explicit paging).
3. **Attach** a chosen set of blocs to an agent's or LLM call's context, as text (token-budgeted)
   or, for exact reuse on local models, as their prompt-cache (KV) prefix, which blocs already do.
4. **Give** an agent a search tool bound to the blocs it was given (it cannot reach the others).

## Why

Operator, 2026-10-11: "i do not yet have a way to create a 'data collection', do i? by that, i mean
a searchable memory bloc (eg with vector embeddings and BM42-like) that i could give to an agent,
either for it to search in it OR as a deterministic way to select ALL the memories from that 'data
collection' that fits criteria A,B,C." Then: "actually call it 'memory blocs', that's how we call it
in the framework. the idea is to be able to have multiple memory blocs and to be able to search
from some and/or attach them to the context. make those proposals in the backlog."

## Current code reality (2026-10-11)

- **Memory blocs today** (AbstractCore `abstractcore/core/file_blocs.py`, "File 'memory blocs':
  persistent extracted-text snapshots + per-model KV artifacts"): a bloc is ONE content-addressed
  text snapshot (`FileBlocRecord`: sha256, bloc_id, path, summary, keywords, estimated_tokens…)
  under `~/.abstractcore/blocs`, plus per-(provider, model) KV prefix artifacts
  (`core/bloc_kv.py`). `FileBlocStore.list()` enumerates blocs; there is no search over their
  content and no multi-record bloc.
- **Gateway** exposes them: `/api/gateway/blocs` (list), `/blocs/upsert_text`, `/blocs/record`,
  `/blocs/delete`, `/blocs/kv/{manifest,list,ensure,load,delete,prune}`
  (`abstractgateway/src/abstractgateway/routes/gateway.py` ~27880-28071, models ~25565-25612).
- **Attach to context (exact reuse)**: Agent and LLM Call nodes take `prompt_cache_binding` ("durable
  exact-reuse prompt-cache binding from Gateway blocs"), carried as `_runtime.prompt_cache_binding`
  (`abstractruntime/.../visualflow_compiler/compiler.py` ~1556-1559). One binding per call; KV is
  model-specific (local engines).
- **Memory notes** (`memory_note` "Memorize", `memory_query` "Recall", `memory_tag`;
  `abstractflow/src/types/nodes.ts` ~2296-2380): text + string tags, scopes run / session / global
  (no per-user, no named store). Search is a lowercase substring scan over metadata, tags and note
  text (`abstractruntime/src/abstractruntime/memory/active_context.py:253-260`; the handler is
  "intentionally metadata-first and embedding-free", `core/runtime.py` ~4943). Deterministic
  select-all by tags works today (`tags_mode: all`, large `limit`). Pin says default limit 5, the
  adapter uses 10 (`visualflow_compiler/adapters/effect_adapter.py` ~379).
- **Knowledge graph** (`memory_kg_assert` / `memory_kg_query`): triples with semantic search when an
  `embedding.text` route exists (`integrations/abstractmemory/effect_handlers.py`; gateway store
  `abstractgateway/src/abstractgateway/memory_store.py`, LanceDB default). Cosine over all
  candidates in Python (`abstractmemory/src/abstractmemory/sqlite_store.py:422-505`); no keyword
  search; `owner_id` is the only namespace (advanced).
- **Hybrid (FTS5/BM25 + vector + exact)** exists only for entity homes
  (`abstractmemory` completed item 0019; `sqlite_store.py:243-275`; callers in `channels.py`,
  `probe.py`, `reconstruct.py`).
- **Agents**: tools `recall_memory` / `remember_note` / `remember` / `compact_memory`
  (`abstractagent/src/abstractagent/logic/builtins.py`) search notes by substring, the model picks
  scope and tags (no binding to a collection). The Agent node's `memory` pin pre-injects recalled
  memory; its `use_semantic_search` is not implemented and points to a "planned: 464" item that
  does not exist (`visualflow_compiler/compiler.py` ~757-765, ~1994-1999).
- **Gateway**: `/kg/query`, `/embeddings` endpoints only; no collection, ingestion, listing or
  deletion API; no console page except the KG explorer
  (`abstractuic/monitor-active-memory/src/KgActiveMemoryExplorer.tsx`).
- Related backlog: `abstractflow/docs/backlog/proposed/0124_author_visible_memory_inspector_semantic_recall_kv.md`
  (memory inspector, semantic `memory_query`, KV, merging the two systems: the closest, but no
  collections); `docs/backlog/planned/agency-parity/0219_react_retrieval_and_project_memory.md`
  (ReAct recall on the abstractmemory engine); abstractmemory 0012 (LanceDB hardening), 0015
  (export/import); abstractcore 0801 (reranker).
- What works today without blocs: example flow **"Data collection demo (memory notes)"** registered 2026-10-11 on
  the operator's gateway (`runtime/visualflows/bcef3d3c.json`): five tagged notes, a deterministic
  select (italian + vegetarian + quick → exactly 2 of 5, verified on a local runtime), an agent
  searching with `recall_memory`. Keyword/tag only.

## Proposals

Each proposal is to be challenged by the reviews below; together they are one direction, in
order.

**P1. A memory bloc holds many records.** Keep today's single-document bloc as a record kind and
let a bloc be a named container (`bloc id`, owner, created with an embedding model recorded) of
records `{id, text, metadata, embedding?, source?}`, with idempotent upsert by a caller key (no
duplicates on re-run). Storage in AbstractMemory (its SQLite store already has FTS5/BM25 + vectors
for entity homes; one table set per bloc).

**P2. Search across chosen blocs.** One search over a list of blocs: hybrid BM25 + vector with
metadata filters, scored and attributed to the bloc each hit came from. Keyword-only when no
embedding route is configured, said in the result (never silent).

**P3. Deterministic select.** All records of the chosen blocs matching metadata filters A, B, C,
in a stable order with explicit paging; no ranking, no hidden limit.

**P4. Attach blocs to a context.** An Agent / LLM Call input `memory_blocs` (a list) attaches the
chosen blocs: as rendered text within a token budget (any provider), or as their KV prefix when
the model is local and a KV artifact exists (today's `prompt_cache_binding`, generalised from one
bloc to a list). The run records which blocs were attached and how.

**P5. An agent tool bound to its blocs.** `search_memory_blocs` (and optionally
`select_memory_blocs`) exposed to an agent only over the blocs its node lists; the model chooses
the query, never the blocs.

**P6. Nodes.** Memory Bloc Add (upsert records), Search, Select, Delete records; all with a
`blocs` pin (one or many). Flows can build a bloc from files, web pages or previous results.

**P7. Console.** Create / list / inspect / delete blocs, see records and sizes, re-embed with
another model; document ingestion (chunking PDFs, pages) if decided in v1.

**P8. Clean-up on the way.** The Agent node's `use_semantic_search` option is not implemented and
points to a "planned: 464" item that does not exist (`compiler.py` ~757-765, ~1994-1999): replace
it by P4/P5 or remove it. Decide how memory notes (`memory_note` / `memory_query`) and the KG relate
to blocs (0124 proposes merging the memory systems).

## Decisions for the operator

1. Are memory notes and the KG kept beside blocs, or become bloc kinds (one memory model)?
2. Who owns a bloc: a user, a workflow, an entity, the gateway (shared)? Sharing rules?
3. Attach as text, as KV, or both (who chooses: the node or automatic)?
4. Document ingestion (chunking, PDF/web) in v1, or records only?
5. Metadata types: strings only, or numbers/dates with range filters?

## Required adversarial reviews

A design review before code (bloc model, store, scoring, filters, attach modes, agent binding, migration of notes and existing text blocs)
and an implementation review after (recall quality on a real corpus, filter determinism, scale,
re-run idempotency), with mutation-checked tests, so the abstraction and implementation are as
clean, simple, robust and efficient as possible.

## Acceptance criteria

- [ ] Create several memory blocs, fill them from a flow (re-running does not duplicate), search a
      chosen set (hybrid, scored, attributed) and select from it (deterministic, complete).
- [ ] An Agent node given blocs X and Y can search X and Y and nothing else, and can have them
      attached to its context (text within budget, or KV when available).
- [ ] Blocs are listed, inspected and deletable in the console.
- [ ] Both adversarial reviews done and findings resolved.

## Receipts

- (to fill)
