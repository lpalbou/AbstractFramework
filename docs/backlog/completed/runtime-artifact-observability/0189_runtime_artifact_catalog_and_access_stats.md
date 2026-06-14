# Completed: Runtime artifact catalog and access stats

## Metadata
- Created: 2026-06-06
- Status: Completed
- Completed: 2026-06-06

## ADR status
- Governing ADRs: ADR-0018, ADR-0032
- ADR impact: Implements the Runtime storage portion of ADR-0036.

## Context
Runtime artifacts are persisted by reference so large payloads do not inflate run state. That storage layer is the right place to own durable artifact descriptors, access counters, and queryable catalog metadata.

## Current code reality
- `ArtifactMetadata` has no first-class `metadata`, `descriptor`, `session_id`, `workflow_id`, `turn_id`, `last_accessed_at`, or `access_count` field.
- `FileArtifactStore.list_all(limit=0)` glob-loads metadata files and JSON-decodes them in memory before sorting by `created_at`.
- `load()` and `get_metadata()` are read-only lookups. They do not mutate access timestamps or counters.
- `search(...)` filters simple metadata fields and tags only. It explicitly is not semantic search.
- Artifact ids can be run-namespaced while `blob_id` remains the global content hash, but the current metadata does not expose richer identity or derivation facts.

## Problem
Runtime cannot answer artifact explorer questions efficiently or canonically. Broad lists scan files, access stats do not exist, and descriptor fields needed by Gateway/Observer are either missing or hidden in untyped tags.

## What we want to do
Extend Runtime artifact storage with a backward-compatible descriptor catalog that persists structured metadata, access stats, and indexable fields while keeping existing artifact ids, blob dedupe, and `.meta` compatibility.

## Why
Runtime is the only layer shared by direct library use, Gateway-hosted runs, package integrations, and future tooling. If it does not own the descriptor and access APIs, every app has to reconstruct artifact facts differently.

## Requirements
- Add backward-compatible descriptor storage. Existing metadata files must load without migration.
- Preserve `artifact_id`, `blob_id`, content-addressed storage, run-scoped artifact ids, and current content paths.
- Add an explicit metadata update path for descriptor enrichment and access stats. Avoid hidden write side effects in plain `get_metadata()` unless the ADR chooses that behavior deliberately.
- Add `record_access(...)` or equivalent for metadata view, preview, content read, download, and programmatic load paths.
- Track at least `last_accessed_at`, `access_count`, `preview_count`, `download_count`, and safe actor/session/principal context when available.
- Add first-class descriptor fields for session, workflow, node, step/effect, parent run, turn/ledger cursor, semantic kind, render kind, media facts, generation/provenance, and source refs.
- Provide an indexed catalog or manifest that supports exact counts and filtered paging without a full file scan for normal Gateway/Observer queries.
- Keep values <= 0 meaning "unlimited" only for debug/audit paths. Normal Explorer usage should use bounded pages.
- Make metadata extraction pluggable and safe. Missing optional media inspectors must emit explicit fallback metadata, not fail the artifact write.
- Ensure concurrent writes and access-stat updates do not corrupt metadata files.

## Suggested implementation
1. Add descriptor fields to `ArtifactMetadata.from_dict`/`to_dict` with defaults for legacy files.
2. Add `ArtifactDescriptorV1` and `ArtifactAccessStats` structures in Runtime.
3. Add `store(..., metadata=..., descriptor=...)` support while preserving old call signatures.
4. Add `update_metadata(...)` and `record_access(...)` APIs on `ArtifactStore`.
5. Add a file-backed catalog/index, likely SQLite or an append/repairable manifest, keyed by `(created_at, artifact_id)` and selected descriptor facets.
6. Add a repair/reindex path that rebuilds the catalog from existing `.meta` files.
7. Add runtime tests for legacy reads, new writes, concurrent access updates, pagination, and catalog repair.

## Scope
- `abstractruntime` artifact metadata schema, file store, in-memory store, tests, and docs hooks.
- Compatibility with existing Gateway and package calls.
- Catalog/index needed for exact counts and stable paging.

## Non-goals
- Do not implement Gateway HTTP routes here; see `0191`.
- Do not implement Observer UI here; see `0192`.
- Do not add semantic/vector search to the artifact store.
- Do not store unredacted provider secrets, raw API keys, or large provider payloads as indexed metadata.

## Dependencies and related tasks
- `0188_artifact_descriptor_contract_and_adr.md`.
- `0190_media_generation_provenance_and_enrichment.md`.
- `0191_gateway_artifact_envelope_query_and_provider_traces.md`.

## Expected outcomes
- Runtime can list and page artifacts by canonical descriptor fields.
- Runtime can return exact counts for selected facets without relying on a UI-side unlimited fetch.
- Access stats update through explicit APIs and appear in artifact descriptors.
- Legacy artifacts remain readable and are labeled as legacy/inferred when projected.

## Validation
- Runtime unit tests for legacy `.meta` loading.
- Runtime unit tests for storing descriptors and structured metadata.
- Runtime unit tests for `record_access(...)` counters and timestamps.
- File-backed catalog tests for cursor/offset paging, exact counts, filters, repair/reindex, and malformed metadata.
- Concurrency test or lock test for metadata/access updates.

## Progress checklist
- [x] Add descriptor-compatible metadata fields.
- [x] Add update and access-stat APIs.
- [x] Add catalog/index and repair path.
- [x] Preserve legacy metadata compatibility.
- [x] Add focused runtime tests and docs hooks.

## Guidance for the implementing agent
Keep the storage migration boring and reversible. Favor explicit compatibility projection over clever inference. Re-check Gateway and Observer callers before changing method signatures so the first migration remains source-compatible.

## Completion report

Implemented a backward-compatible Runtime artifact catalog and access-stat layer in `abstractruntime`.

Key changes:
- `ArtifactMetadata` now persists structured `metadata`, canonical `descriptor`, and explicit `access` stats while still reading old `.meta` files.
- `ArtifactStore.store(...)`, `store_text(...)`, and `store_json(...)` accept optional structured metadata and descriptor fields without breaking existing callers.
- `update_metadata(...)` and `record_access(...)` provide explicit enrichment/access paths; `load()` and `get_metadata()` remain side-effect free.
- `FileArtifactStore` maintains a repairable SQLite projection catalog under the artifact store directory for exact counts, facet counts, filters, offsets, and bounded paging.
- The catalog rebuilds from `.meta` sidecars and stores metadata atomically, preserving content-addressed blobs and run-scoped artifact ids.
- Audio WAV duration/sample-rate/channel/frame facts and image dimensions are inspected when supported; unsupported media inspectors record explicit fallback metadata instead of failing writes.

Architecture review kept SQLite as an internal repairable projection, not a second source of truth. Technical review tightened additive descriptor updates so later enrichment cannot wipe inspected media facts. UX review drove the exact-count and canonical-filter requirements so Observer can offer filters like voice/music/audio without unlimited fetches or browser-side inference.

Validation:
- `cd abstractruntime && /Users/albou/tmp/abstractframework/.venv/bin/python -m pytest tests/test_artifacts.py`
- `python3 -m py_compile abstractruntime/src/abstractruntime/storage/artifacts.py`

The artifact test suite includes a threaded `record_access(...)` regression test for file-store metadata locking.

Remaining follow-up work is tracked in `0190` through `0193`: producer-level provenance enrichment, Gateway query/envelope routes, Observer UI consumption, and user/tooling documentation.
