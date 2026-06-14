# Runtime artifact observability backlog track

## Status
Completed; no active planned items remain in this track. The README is retained as the design record for the track.

## Purpose
This track defines the canonical artifact metadata, provenance, search, and UI contract needed to make runtime artifacts genuinely explorable. It covers the user workflow behind the Runtime and Observe tabs: find active computation, separate voice from music, inspect an artifact, understand how it was generated, and jump back to the run, turn, ledger, provider trace, and source assets.

The central principle is that Observer must not guess artifact meaning. Runtime should persist canonical artifact descriptors. Gateway should expose, index, and authorize those descriptors. Observer should render and navigate them, keeping sniffing only as a clearly marked fallback for legacy artifacts.

## Decision question
Where should AbstractFramework store and expose artifact type, media facts, generation provenance, access statistics, and runtime links so Observer can monitor real work without inferring from filenames, MIME types, or raw content?

## Current reality
- `abstractruntime` now persists `ArtifactMetadata.metadata`, `ArtifactMetadata.descriptor`, and explicit `ArtifactAccessStats`; `FileArtifactStore` maintains a repairable SQLite catalog for exact counts, facet counts, filters, offsets, and bounded pages.
- Runtime output helpers distinguish generated media at the request level. Image, video, voice, music, sound/audio, and transcription-facing paths set `modality`/`task`, and descriptor-aware Runtime/Gateway paths now store structured metadata/descriptors rather than tags only.
- Generated-media descriptors preserve prompt/TTS text, provider/model/backend, output format/index, redacted params, source refs, request/run/session/workflow fields, and security labels where available.
- Gateway parent-run projection preserves generated child artifact descriptor/metadata while updating parent-facing session/workflow/node fields and retaining projected-from provenance/source refs.
- `abstractgateway` now exposes `artifact_envelope_v1` rows, exact stats/facets, bounded pages, access-stat actions, and `artifact_kind` filtering for thin clients.
- `abstractobserver` now consumes Gateway artifact envelopes/stats, separates semantic kind from render kind, labels generic audio as Unclassified audio, and keeps legacy fallback classification visible.
- Observer Runtime Activity now provides canonical queues, a dense searchable/sortable table, selected-run detail/actions, readable wait context, monitor-first navigation, loaded-page count labels, and offline/focus/responsive states. Destructive run controls are routed through Observe so users see the full run narrative first.
- Provider/runtime audit information is split across Gateway request audit logs and runtime ledger/provider metadata. Artifact envelopes expose provider/audit availability and links when descriptors provide them; richer producer trace capture remains planned.

## Architecture alternatives considered

### Alternative A: keep Observer inference
This is the smallest UI-only change and works for some legacy artifacts, but it keeps repeating the current failure mode. Users cannot trust filters, provenance, voice/music separation, access stats, or generation details because the browser is guessing.

### Alternative B: Gateway-only projection
Gateway could synthesize an `artifact_envelope_v1` from tags, ledger records, MIME type, and route context. This is useful as a migration bridge, but it still makes Gateway invent artifact meaning and does not help direct Runtime users or package-local tooling.

### Alternative C: Runtime-owned artifact descriptor plus Gateway index
Runtime persists a versioned descriptor with identity, classification, ownership, provenance, generation, media, access, and security/action fields. Gateway exposes and indexes it with RBAC, stats, pagination, and provider-trace links. Observer consumes that descriptor directly. This is the preferred boundary.

### Alternative D: ledger/event-sourced artifact index
Runtime could emit `artifact.created`, `artifact.accessed`, and `artifact.derived` ledger records, and Gateway could materialize a query index. This gives excellent auditability, but it is a larger migration and should support, not replace, the canonical runtime descriptor.

### Alternative E: external search backend first
Postgres, SQLite FTS, or a dedicated search backend would help very large runtimes, but an external index should not be the source of truth. It is an optimization behind Gateway/Runtime contracts.

## Synthesis
Use Alternative C, with room for Alternative D/E as implementation details.

Runtime owns artifact identity and canonical descriptors. Gateway owns HTTP projection, authorization, pagination, stats, provider-trace links, and optional indexes. Observer owns the human workflow and visual rendering. Capability packages and runtime producers must pass structured metadata into Runtime instead of relying on tags.

## Completed slices
- `docs/backlog/completed/runtime-artifact-observability/0198_observer_observability_replay_workbench.md`: `history_bundle` now carries bounded replay artifact summaries and indexed best-effort session turns, and Observer has a read-only Replay tab.
- `docs/backlog/completed/runtime-artifact-observability/0188_artifact_descriptor_contract_and_adr.md`: ADR-0036 and the Runtime descriptor contract are complete.
- `docs/backlog/completed/runtime-artifact-observability/0189_runtime_artifact_catalog_and_access_stats.md`: Runtime descriptor persistence, access stats, exact counts, filters, paging, and repairable file catalog are complete.
- `docs/backlog/completed/runtime-artifact-observability/0190_media_generation_provenance_and_enrichment.md`: Runtime/Gateway generated-media descriptors, redaction, projection preservation, and tests are complete.
- `docs/backlog/completed/runtime-artifact-observability/0191_gateway_artifact_envelope_query_and_provider_traces.md`: Gateway envelope/search/stats/access-action projection is complete.
- `docs/backlog/completed/runtime-artifact-observability/0192_observer_canonical_artifact_explorer_ui.md`: Observer canonical Artifact Explorer consumption and UI redesign are complete.
- `docs/backlog/completed/runtime-artifact-observability/0193_runtime_artifact_coredoc_and_explore_skill.md`: Runtime artifact coredoc, LLM docs, and validated `runtime-explore` skill are complete.
- `docs/backlog/completed/runtime-artifact-observability/0194_observer_runtime_activity_monitor_and_wait_actions.md`: Runtime Activity operational supervision and wait-action routing are complete.

## Post-foundation review history

The review below explains why the implementation sequence prioritized Gateway
and Observer projection before producer enrichment, Runtime Activity, and final
docs/skill work. All items in the sequence are now complete.

### Architect lens
Decision question: after Runtime descriptors/catalogs exist, should the next work prioritize producer metadata, Gateway projection, Observer UI, or docs?

Alternatives weighed:
- Producer-first (`0190`): best for rich provenance, but users still cannot see the new Runtime descriptor fields because Gateway and Observer remain v0.
- Gateway-first (`0191`): exposes the new lower-layer contract, exact stats, and server filters to all thin clients; provenance can be sparse at first and enriched later.
- Observer-first (`0192`): visible improvement, but it would force another round of client inference or N+1 metadata calls unless Gateway exposes canonical envelopes first.
- Docs-first (`0193`): useful for maintainers, but premature if Gateway/Observer behavior still disagrees with the new contract.

Synthesis at the time: make `0191` the next blocking implementation slice. It should project Runtime descriptors and exact catalog stats first, using descriptor fixtures rather than waiting for every producer to be enriched. Then `0192` can consume the envelope without guessing. `0190` should run as a narrow vertical enrichment slice in parallel or immediately after the Gateway contract, starting with generated media and parent-run projection.

Evidence that would change this order: if Gateway cannot safely expose descriptor envelopes without a producer-enrichment pass, then complete the smallest `0190` path first for one generated media family and use it as the `0191` fixture.

### Technical review lens
- Blocking risk: Gateway search/list currently still uses v0 list rows and local filtering; this means the Runtime catalog work from `0189` is not yet useful to Observer.
- Compatibility requirement: `0191` must preserve existing `ArtifactListItem` fields while adding `artifact_envelope_v1`, not break current clients.
- Data-loss risk: generated child artifacts projected into parent runs must preserve descriptor/metadata, not only tags.
- Executability risk: `0191` must distinguish filters supported by the current Runtime catalog from future provider/model/source/turn/ledger filters that require catalog schema extensions.
- Test requirement: `0191` needs route tests for exact counts independent of page limit, descriptor projection, legacy fallback labels, and RBAC visibility.

### UX review lens
- Users do not benefit from producer enrichment until Gateway and Observer show it. The first user-visible win is server-backed type/semantic filters with exact counts and a detail panel that says whether metadata is canonical or legacy-inferred.
- Naive users need plain labels: Voice, Music, Sound, Image, Video, Document, Markdown, HTML, JSON, Text, Other.
- Expert users need stable paging, copyable ids/refs, provider trace availability, run/turn/ledger links, and no default unlimited fetch.
- The Artifact Explorer should degrade honestly: "legacy inferred" is acceptable; silent browser guessing is not.
- Runtime users also need a separate activity workflow: Needs attention, Waiting for me, Running now, Failed, Finished, with clear stop/cancel/resume/approve/reject/submit actions and enough ledger context to know what a waiting run expects.

## Recommended follow-up
1. Investigate Observer wait handling as a replayable session chat/handoff (`0195`) instead of continuing to refine the narrow answer modal.
2. Design a first-class Session -> Turn -> Run/Subrun -> Artifact/Log hierarchy (`0196`) before adding more Runtime Activity structure.
3. Add a Gateway run-stats endpoint if Runtime Activity needs exact queue counts across more than the loaded run page.
4. Adopt `build_artifact_descriptor_payload(...)` in direct media-package artifact writers that bypass Runtime AbstractCore generated-media storage.
5. Design provider trace storage as redacted Gateway-owned trace records or artifacts instead of indexed raw provider payload fields.

## Items
- `docs/backlog/completed/runtime-artifact-observability/0198_observer_observability_replay_workbench.md`: make `history_bundle` the Observer replay handoff and add a read-only Replay tab.
- `docs/backlog/completed/runtime-artifact-observability/0190_media_generation_provenance_and_enrichment.md`: preserve generated-media metadata from Core/Runtime/Voice/Vision/Music paths.
- `docs/backlog/completed/runtime-artifact-observability/0191_gateway_artifact_envelope_query_and_provider_traces.md`: Gateway canonical envelopes, exact stats, cursor pagination, filters, and trace links.
- `docs/backlog/completed/runtime-artifact-observability/0192_observer_canonical_artifact_explorer_ui.md`: Observer canonical descriptor consumption, voice/music/audio split, and provenance/actions.
- `docs/backlog/completed/runtime-artifact-observability/0193_runtime_artifact_coredoc_and_explore_skill.md`: document the runtime artifact/retrieval model and create `runtime-explore` only after docs and contracts are stable.
- `docs/backlog/completed/runtime-artifact-observability/0194_observer_runtime_activity_monitor_and_wait_actions.md`: make Runtime Activity and waiting-run handling useful, clear, and actionable at scale.

## Reading order
Start with ADR-0036 and completed items `0188`, `0189`, `0191`, and `0192` for the storage/query/UI foundation. Then read `0194` for runtime supervision, `0198` for read-only replay handoff, `0190` for generated-media provenance, and `0193` for docs and skill guidance.

## Related material
- ADR-0018 durable run gateway and remote host control plane.
- ADR-0028 capabilities plugins and library/framework modes.
- ADR-0032 package dependency boundaries and gateway-first apps.
- ADR-0035 capability routing defaults.
- ADR-0036 runtime-owned artifact descriptor contract.
- `docs/backlog/proposed/gateway-control-plane/0151_runtime_explorer_contract.md`.
- `docs/backlog/completed/multimodal-capabilities/0175_multimodal_capability_taxonomy_schema.md`.
- `docs/backlog/completed/runtime-artifact-observability/0188_artifact_descriptor_contract_and_adr.md`.
- `docs/backlog/completed/runtime-artifact-observability/0189_runtime_artifact_catalog_and_access_stats.md`.
- `abstractruntime/src/abstractruntime/storage/artifacts.py`.
- `abstractruntime/src/abstractruntime/integrations/abstractcore/effect_handlers.py`.
- `abstractgateway/src/abstractgateway/routes/gateway.py`.
- `abstractobserver/src/ui/artifact_rendering.ts`.
- `abstractobserver/src/ui/app.tsx`.

## Non-goals
- Do not make Observer the source of truth for artifact type, provenance, access, or generation metadata.
- Do not expose raw provider logs or sensitive prompt/tool payloads without redaction and RBAC.
- Do not make semantic artifact search a substitute for AbstractMemory/KG retrieval.
- Do not require a new `abstractexplorer` package before Gateway/Observer contracts prove a package split is needed.
- Do not silently rewrite legacy artifacts; support explicit legacy fallback classification.
