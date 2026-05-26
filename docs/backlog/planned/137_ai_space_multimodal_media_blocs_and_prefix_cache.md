# 137 — Multimodal MediaBlocs + Prefix KV Caching (Images/Audio/Video) for ai-space

**Status**: Planned  
**Date**: 2026-04-14  
**Priority**: High (multimodal roadmap + cost/perf)  
**Components**: abstractcore (blocs + prompt-cache), ai-space (REPL + `/query`), abstractmemory (graph), abstractsemantics (predicates), optional vector DB backends

## Summary

Extend the “cache-first bloc” idea beyond plain text files:

- Introduce **MediaBlocs** (images/audio/video) as first-class cached items.
- Support **multimodal retrieval** (text↔image, image↔image) via embeddings + vector index.
- Investigate and (if feasible) implement **prefix KV caching for multimodal prefill** so that repeated queries over the *same image/media* reuse the expensive prefill and only pay decode (generation) tokens.

This item is explicitly split into:
1) a deterministic, portable **retrieval** story (works even without KV caching), and  
2) a provider/model-dependent **multimodal KV caching** story (harder; research + prototype).

## Why

ai-space currently optimizes repeated access to large text memories by caching per-file KV prefixes. Real “personal memory” is multimodal:

- screenshots, scanned notes, diagrams
- photos, whiteboards
- voice notes / podcasts
- videos

We want:
- **fast search** over these assets
- **fast repeated questioning** over the same asset(s)
- durable relationships between assets and text blocs (graph)

## Constraints (ADRs)

- **ADR-0001 Layered architecture**: no dependency cycles; app composes packages.
- **ADR-0007/0009 provenance**: retrieval and summaries must keep traceability to the original asset.
- **ADR-0026 truncation**: no silent truncation in critical paths (schemas, ingestion, provenance).
- **ADR-0029 dependency policy**: keep default deps permissive and minimal; multimodal should be optional where possible.

## Scope (v0 vs v1)

### v0 (must ship first)

- MediaBlocs store in **AbstractCore** (like file blocs, but for media).
- Deterministic semantic retrieval over media using embeddings + a vector index (default: SQLite + `sqlite-vec`).
- `/query` can target media superset(s) via the same grammar as text blocs (exact syntax TBD; see “UX” below).
- Graph relationships (AbstractMemory) can relate:
  - `media:<sha256>` ↔ `bloc:<sha256>`
  - `sb:<id>` includes both media and text nodes (hypergraph-ready).

### v1 (research + prototype)

- Provider-specific support for **multimodal prefix KV cache save/load/fork** (image prefill reuse).
- At least one working backend (pick 1):
  - HuggingFace VLM (Transformers) **or**
  - llama.cpp VLM (GGUF) **or**
  - MLX VLM (if mature enough)

## Proposed architecture

### 1) MediaBlocs live in AbstractCore (documents/caches)

Rationale: a “bloc” is a **materialized artifact** (content-addressed snapshot + per-model cached compute artifacts). That’s AbstractCore territory.

Proposed store layout (parallel to file blocs):

`~/.abstractcore/blocs/media/<sha256>/`

- `bytes.bin` (or original extension) — stored snapshot of the asset
- `meta.json` — path, timestamps, mime, dimensions/duration, hashes
- `derivatives/`
  - `caption.txt` (optional)
  - `ocr.txt` (optional)
  - `asr.txt` (optional; for audio/video)
  - `thumb.jpg` (optional)
- `embeddings/<embed-slug>.json` (or a central DB) — vectors for retrieval
- `kv/<provider+model hash>.{safetensors,npz,...}` — **only if** multimodal prefix KV caching is supported

### 2) Graph/hypergraph lives in AbstractMemory (relationships)

Node ids:
- `bloc:<sha256>` (text file bloc)
- `media:<sha256>` (media bloc)
- `sb:<id>` (superbloc)

Edges/predicates (via AbstractSemantics allowlist):
- `dcterms:hasPart` (superbloc membership)
- future: `cito:cites`, `prov:wasDerivedFrom`, `schema:about`, “sameEvent”, etc.

### 3) Retrieval index is pluggable (default SQLite+sqlite-vec)

We keep the *stage‑0 retrieval interface* minimal and backend-agnostic:

- `ingest(items)` (text + media metadata; produces/updates vectors)
- `query(text|image, restrict_ids, top_k) -> candidates`

Default backend:
- SQLite + `sqlite-vec` (portable, single file)

Optional backends (future):
- LanceDB (multimodal ergonomics; large-scale ANN)
- Graph DB w/ vectors (only if mature + portable across OS)

## Multimodal embeddings (retrieval)

Key point: the vector DB is modality-agnostic; multimodal retrieval is enabled by choosing an embedding model that maps:
- images → vectors
- text queries → vectors
in the **same space**.

We must select:
- a default multimodal embedding model (permissive license, small, good quality)
- a portable runtime (avoid fragile GPU-only stacks; macOS/Linux/Windows)

Open question: whether `sentence-transformers` is the right base for image embeddings in this framework, or whether we need a separate small multimodal embedder module.

## Multimodal prefix KV caching (the hard part)

“Cache images like text blocs” means:

1) Prefill the model with the **image input + a stable instruction header**.
2) Persist the resulting prefix KV cache to disk.
3) For each question:
   - load stable KV
   - fork to temp
   - append the question as suffix prompt
   - decode
   - clear temp (stable remains immutable)

Reality check:
- This requires a provider/model implementation that exposes **save/load/fork** for multimodal prefix state.
- Many VLM implementations treat image features as special inputs rather than plain tokens; “KV cache” semantics may differ.
- For v1 we should pick ONE backend and make it correct, rather than trying to generalize prematurely.

## UX (must stay simple)

No new “/index …” command family.

`/query <target> <message...> [-- flags...]` remains the entrypoint.

We need a clean target grammar extension (proposal):
- `blocs:...` (existing text blocs)
- `sb:...` (existing superblocs)
- `media:all` / `media:<ids>` (new)
- `mem:all` (union of blocs + media in scope)

This is intentionally deferred until v0 implementation to avoid breaking current usage.

## Research plan (for the next agent)

### R1 — Can we do image prefix KV caching with MLX today?

Prompt:
> Investigate whether MLX (mlx-lm / mlx-vlm) supports VLM inference with reusable KV caches and whether those caches can be persisted and reloaded.  
> Specifically: can a vision model accept an image, produce a prefix cache, and later reuse it for multiple suffix questions without reprocessing the image?  
> If yes, identify the exact cache object type, whether it’s mutated during decode, and whether it can be serialized (safetensors/npz).  
> Provide a minimal repro script and performance numbers.

### R2 — HuggingFace Transformers VLM KV caching feasibility

Prompt:
> For popular permissively licensed VLMs (Qwen2.5-VL, LLaVA variants, SigLIP-based), determine whether Transformers exposes `past_key_values` that include the image-conditioned prefix and whether those can be saved/loaded deterministically.  
> If image prefill cannot be captured by KV caches alone, explain what additional state is required.  
> Provide a recommended implementation approach in AbstractCore’s provider interface.

### R3 — llama.cpp / GGUF multimodal cache feasibility

Prompt:
> Investigate llama.cpp’s current multimodal support (LLaVA, Qwen-VL GGUF, etc.) and whether it provides a stable API to save/load KV caches including image-conditioned prefixes.  
> If supported, document the APIs and file formats and propose how AbstractCore would wrap it.

### R4 — Pick default multimodal embedding model + runtime

Prompt:
> Recommend a default multimodal embedding model for text↔image retrieval that is permissively licensed, small, and runs on macOS/Linux/Windows.  
> Compare quality, speed, memory, and licensing for a shortlist (e.g., CLIP/SigLIP variants).  
> Specify the runtime stack (sentence-transformers vs open_clip vs transformers) and any pitfalls (torch install size, MPS/CUDA behavior).

### R5 — How to integrate optional LanceDB cleanly

Prompt:
> Design a backend interface so the default remains SQLite+sqlite-vec, but LanceDB can be plugged in without changing `/query` UX or the higher-level planner.  
> Identify where to put the abstraction boundaries (ai-space vs abstractmemory vs abstractcore).

## Acceptance criteria (v0)

- Can ingest and list MediaBlocs locally (portable, no daemon).
- Can build a deterministic vector index and query it via `/query` without any LLM-over-catalog step.
- Can relate `sb:<id>` to both `bloc:<sha>` and `media:<sha>` via AbstractMemory triples.
- Clear errors when multimodal features are unavailable (no silent fallback).

## Acceptance criteria (v1)

- One provider/model backend can:
  - cache a single image prefix to disk
  - reuse it across multiple questions with only suffix prefill + decode
  - preserve immutability via fork-to-temp semantics
- Performance validation shows meaningful speed/cost improvement vs re-prefill.

