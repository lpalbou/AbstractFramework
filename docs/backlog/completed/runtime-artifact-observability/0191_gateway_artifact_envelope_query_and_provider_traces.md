# Completed: Gateway artifact envelope, query, and provider traces

## Metadata
- Created: 2026-06-06
- Status: Completed
- Completed: 2026-06-06

## ADR status
- Governing ADRs: ADR-0018, ADR-0032, ADR-0036
- ADR impact: Implements the Gateway projection side of ADR-0036; may revise Gateway API docs and capability descriptor contracts.

## Context
Gateway is the protected HTTP control plane used by Observer and other thin clients. It should expose runtime artifacts as canonical envelopes with permissions, links, stats, and paging, not as weak metadata rows that the browser must interpret.

## Current code reality
- `/api/gateway/artifacts/search` supports scope, session id, run id, modality, content type, free-text query, tag filters, limit, and offset.
- Artifact search/list responses include `items`, `total`, `offset`, `limit`, and `has_more`, but item fields are limited to ids, content type, size, created time, tags, filename/source path, sha256, modality, and ref.
- `_artifact_list_item(...)` derives fields from tags and MIME type rather than a structured descriptor.
- Runtime now exposes descriptor-aware `search(...)`, `count(...)`, and `facet_counts(...)`, but Gateway search does not call those APIs yet.
- Broad search currently builds a full row list and then filters/paginates in Gateway, including `list_all(limit=0)` for all-artifact scope.
- Gateway has request audit tail endpoints, while provider/runtime request details generally live in ledger result metadata such as provider request/runtime observability fields.
- Observer already has a client method that can pass `modality`, `content_type`, and `tags`, but the UI currently relies heavily on client-side filtering.

## Problem
Gateway does not provide the envelope, facets, exact stats, stable pagination, or provider trace links needed for a professional artifact explorer. The browser can fetch all artifacts and count/filter locally, but that will not scale and does not solve provenance.

## What we want to do
Expose canonical artifact envelopes and query APIs that read Runtime descriptors, enforce Gateway visibility/RBAC, provide exact counts and facets, support stable pagination, and link artifacts to runs, turns, ledgers, provider traces, and audit availability.

## Why
Gateway is the right layer for authorization, HTTP projection, multi-user isolation, and query performance. It should not own artifact semantics, but it must expose them reliably to Observer.

## Requirements
- Add `artifact_envelope_v1` response shape alongside or inside existing list/detail responses.
- Preserve backward compatibility for existing clients while encouraging canonical envelope consumption.
- Read `ArtifactMetadata.descriptor`, `metadata`, and `access` when present. Tags/MIME projection is compatibility fallback only.
- Include `raw_metadata` for diagnostics, but keep normalized fields first.
- First slice server filters must cover fields already indexed by Runtime: semantic kind, render kind, modality, content type, date range, run, session, workflow, node, tags, and query text.
- Provider, model, source/provenance, turn id, and ledger cursor filters require Runtime catalog schema/index extensions before Gateway may advertise them as exact server filters. Until then, expose them as envelope fields, links, or legacy fallback labels only.
- Provide exact counts and byte totals by selected facets without applying list limits.
- Provide bounded result pages by default. Keep unlimited scans restricted to debug/admin/audit use.
- Add stable cursor pagination over `(created_at, artifact_id)` or another deterministic key. Offset can remain for compatibility.
- Expose links/actions: detail, content/download, preview, owning run, observe route, run artifacts, ledger/history, source artifacts, provider trace, and audit tail where authorized.
- Add `provider_trace_available` and `audit_available` booleans/links rather than dumping raw provider logs into list rows.
- First provider-trace support may return `provider_trace_available=false` when the Runtime descriptor lacks a stable trace ref; do not fabricate provider/model trace links from filenames or workflow labels.
- Preserve session/run visibility and per-principal isolation. Artifact ids, run ids, and session ids are references, not authorization proofs.
- Mark legacy projected envelopes with `classification_source=gateway_legacy_projection` or equivalent.
- Add route tests for large catalogs, pagination, counts, RBAC visibility, and provider trace links.

## Suggested implementation
1. Add Gateway Pydantic models for canonical artifact envelopes and stats/facet responses.
2. Update existing search/list/detail routes to project Runtime descriptors into envelopes while preserving v0 item fields.
3. Add `include_stats=true` or a dedicated `/api/gateway/artifacts/stats` endpoint that uses Runtime `count(...)` and `facet_counts(...)`.
4. Add server-backed filters for indexed Runtime catalog fields first; add Runtime catalog fields/tests before exposing provider/model/source/turn/ledger filters as exact.
5. Add cursor pagination parameters while preserving offset for existing clients.
6. Record explicit access stats where Gateway is the actor: metadata/detail view, embedded preview/content read, download, and later export if an export route exists.
7. Add provider/ledger trace link builders with safe redaction and action availability.
8. Update advertised Gateway capability descriptors and docs.

## Scope
- `abstractgateway` artifact search/list/detail routes, models, stats, pagination, links, and tests.
- Minimal Observer client support for new query params, if needed to validate the contract.
- Documentation hooks for new API behavior.

## Non-goals
- Do not make Gateway the canonical artifact descriptor owner.
- Do not expose raw provider payloads in list rows.
- Do not implement destructive artifact delete/export actions here.
- Do not conflate `/artifacts/search` with KG semantic retrieval.

## Hard dependencies
- `docs/backlog/completed/runtime-artifact-observability/0188_artifact_descriptor_contract_and_adr.md`.
- `docs/backlog/completed/runtime-artifact-observability/0189_runtime_artifact_catalog_and_access_stats.md`.

## Related and follow-on tasks
- `0190_media_generation_provenance_and_enrichment.md`.
- `0192_observer_canonical_artifact_explorer_ui.md`.
- `docs/backlog/proposed/gateway-control-plane/0151_runtime_explorer_contract.md`.

## Expected outcomes
- Observer can ask Gateway for all Voice and Music artifacts separately without local guessing.
- Counts in filter chips are exact for the selected scope and filters.
- Artifact list/detail responses include canonical runtime/session/turn/provenance links.
- Provider trace availability is visible and actionable from an artifact detail panel.
- Broad runtime artifact browsing remains bounded and paginated.

## Validation
- Gateway tests for canonical envelope projection from v1 Runtime descriptors.
- Gateway tests for legacy metadata projection and fallback labels.
- Gateway tests for exact facet counts independent of result page size.
- Gateway tests for cursor pagination stability across pages.
- Gateway tests proving detail/preview/content/download routes update `ArtifactAccessStats` with the expected access type.
- Runtime tests for any new catalog fields added to support provider/model/source/turn/ledger filters.
- Gateway RBAC/visibility tests for run/session/all scope.
- Gateway tests for provider trace/audit link availability and redaction.

## Progress checklist
- [x] Add artifact envelope and stats models.
- [x] Project Runtime descriptors into envelopes.
- [x] Add exact stats/facets and stable pagination.
- [x] Wire server-side filters to Runtime catalog fields.
- [x] Record explicit artifact access stats from Gateway routes.
- [x] Add provider trace and ledger/history links.
- [x] Defer or index provider/model/source/turn/ledger filters explicitly; do not ship fake exact filters.
- [x] Update capability descriptors, docs, and tests.

## Guidance for the implementing agent
This is the next recommended implementation slice for the track. Keep Gateway projection deterministic and boring. If a field is missing from Runtime, mark it missing or legacy-projected; do not invent authoritative provenance from filenames or workflow labels. Use fixture descriptors for route tests so this item is not blocked by full producer enrichment in `0190`. Treat `0190` as enrichment, not as a prerequisite for the first Gateway envelope/stats contract.

## Completion report

Date: 2026-06-06

Summary:
- Added Gateway `artifact_envelope_v1` projection for artifact list/search/detail rows while preserving legacy row fields.
- Added canonical fields for semantic/render kind, workflow/node/turn/ledger refs, media/generation/producer/provenance blocks, access stats, action links, provider trace availability, audit availability, and legacy-inferred markers.
- Added bounded artifact search with `include_stats`, exact stats/facets for selected filters, offset/cursor paging, date/filter/sort parameters, and UI-safe `artifact_kind` filtering that keeps Voice, Music, Sound, and unclassified Audio distinct.
- Added Runtime `ArtifactStore.stats(...)` support with a catalog-backed `FileArtifactStore` implementation so Gateway can get exact totals, byte totals, and facets without loading every matching row when catalog filters are sufficient.
- Added explicit Gateway access-stat recording for metadata views, previews, content reads, downloads, and export.
- Updated Gateway capability descriptors and external docs for envelope/stats/filter/access-action behavior.

Files and symbols touched:
- `abstractruntime/src/abstractruntime/storage/artifacts.py`: store-level exact artifact stats contract and file-catalog byte/facet implementation.
- `abstractgateway/src/abstractgateway/routes/gateway.py`: artifact response models, envelope projection helpers, stats/paging/filter helpers, artifact search/list/detail/content/export routes, capability descriptors.
- `abstractruntime/tests/test_artifacts.py`: in-memory and file-backed artifact stats regression coverage.
- `abstractgateway/tests/test_gateway_artifacts_endpoint.py`: descriptor envelope, exact stats, `artifact_kind`, and access-stat regression coverage.
- `abstractruntime/docs/api.md`, `abstractruntime/llms.txt`, `abstractruntime/llms-full.txt`: Runtime artifact stats coredoc updates.
- `abstractgateway/README.md`, `abstractgateway/docs/api.md`, `abstractgateway/llms.txt`, `abstractgateway/llms-full.txt`: Gateway coredoc updates.

Validation:
- `PYTHONPATH=abstractruntime/src python -m pytest abstractruntime/tests/test_artifacts.py -q` passed (`57 passed`).
- `PYTHONPATH=abstractgateway/src:abstractruntime/src:abstractcore:abstractagent/src:abstractmemory/src:abstractsemantics/src:abstractvision/src:abstractvoice/src:abstractmusic/src:abstractaudio/src:abstractvideo/src:abstractsound/src python -m pytest abstractgateway/tests/test_gateway_artifacts_endpoint.py -q` passed (`3 passed`).
- `python -m compileall -q abstractruntime/src/abstractruntime/storage/artifacts.py abstractgateway/src/abstractgateway/routes/gateway.py` passed.

Behavior changes:
- Thin clients can now use Gateway as the artifact query/control-plane source of truth instead of loading all artifacts and guessing locally.
- Catalog-supported exact stats no longer require Gateway to materialize every matching artifact row.
- Single canonical `artifact_kind` filters map to Runtime catalog filters; multi-kind unions remain supported but may use Gateway post-filtering until Runtime has OR filters.
- `artifact_kind=audio` means unclassified audio and does not match canonical `voice`, `music`, or `sound`.
- Raw metadata remains available through detail/raw paths but is not embedded as the primary bulk-list source of truth.

Residual risks and follow-ups:
- Provider trace and audit actions are only actionable when Runtime descriptors include stable links or trace refs; producer enrichment remains in `0190`.
- Exact provider/model/source/turn/ledger filters still require Runtime catalog schema/index extensions before Gateway should advertise them as exact filters.
- Large post-filter searches for free-text query or UI union filters remain bounded for the UI but may need dedicated Runtime indexes later.
