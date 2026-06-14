# ADR-0036: Runtime-Owned Artifact Descriptor Contract

## Status
Accepted (2026-06-06)

## Dates
- Proposed: 2026-06-06
- Accepted: 2026-06-06

## Context

Artifacts are central to observing durable workflows: images, generated voice, music, videos,
HTML captures, markdown reports, JSON snapshots, downloads, provider evidence, and workflow
attachments. Users need to answer questions such as:

- What type of artifact is this, and is an audio file voice, music, sound, or a recording?
- Which session, run, workflow, node, turn, ledger record, provider call, and prompt produced it?
- What model, provider, route, parameters, seed, and source media were involved?
- When was it created, when was it last accessed, and how often was it previewed or downloaded?
- Which UI actions are available, and are provider traces or audit links available?

Before this decision, artifact meaning was split across MIME type, tags, Gateway projections,
workflow ledgers, provider payloads, and Observer heuristics. That made artifact exploration
fragile. A thin client could not reliably distinguish voice from music or recover generation
context without reimplementing runtime-specific inference.

This decision is constrained by existing ADRs:

- ADR-0018 makes Gateway the durable remote control plane for runs.
- ADR-0028 keeps modality packages as capability plugins.
- ADR-0032 keeps higher-level apps Gateway-first and avoids upward packages owning lower-level truth.
- ADR-0035 defines the shared modality vocabulary used by capability routing.

## Decision

### 1) Runtime owns canonical artifact descriptors

`abstractruntime` owns the versioned artifact descriptor contract:

```text
abstractruntime.artifact_descriptor.v1
```

The descriptor is stored with `ArtifactMetadata` and is the canonical source for artifact
classification, runtime links, provenance, generation context, media facts, and action hints.

Gateway and Observer may project and display descriptors. They must not invent canonical meaning
for newly produced artifacts. If they must classify older artifacts without descriptors, that
classification is a legacy fallback and must be labeled as such.

### 2) Tags stay as compatibility labels

Artifact `tags` remain useful for compatibility, quick filtering, and legacy producers, but they
are not the long-term provenance or classification channel.

For legacy artifacts, Runtime may project tags into descriptor fields with a `classification_source`
such as `runtime_tags` or `runtime_mime_inferred`. For new artifacts, producers should write
descriptor fields directly.

### 3) Separate render kind from semantic kind

The descriptor separates:

- `render_kind`: how the artifact should be displayed, such as `image`, `audio`, `video`,
  `markdown`, `html`, `json`, `document`, `text`, or `binary`.
- `semantic_kind`: what the artifact means in the workflow, such as `voice`, `music`, `sound`,
  `recording`, `transcript`, `evidence`, `workflow_snapshot`, or `attachment`.

This distinction is required because the same render type can have different operational meaning.
For example, a WAV file can be generated speech, generated music, a raw recording, or a sound
effect.

### 4) Descriptors carry runtime ownership links and provenance

Descriptor fields include, at minimum:

- runtime links: `session_id`, `run_id` through provenance, `parent_run_id`, `workflow_id`,
  `node_id`, `step_id`, `effect_id`, `turn_id`, `ledger_cursor`, and `actor_id`;
- classification fields: `semantic_kind`, `render_kind`, `modality`, `task`,
  `classification_source`;
- producer and provenance maps for package, capability route, provider, model, backend,
  request ids, source refs, provider trace links, and output role;
- generation maps for prompt or input text, redacted parameters, seed, source artifacts,
  and source media;
- media facts such as image dimensions, audio duration/sample rate/channels/frames, video
  duration/dimensions/FPS when available, document page count when available, and inspection source;
- security and action hints such as sensitivity labels, redaction state, available actions,
  and whether provider traces are available.

Large provider payloads, secrets, API keys, sensitive source paths, and raw clone-voice data must
not be blindly copied into indexed descriptor fields. They should be redacted or linked to a
protected audit/provenance record.

### 5) Access stats are explicit

Runtime owns explicit artifact access stats alongside the descriptor. The store exposes an API such
as `record_access(...)` for metadata views, previews, downloads, content reads, and programmatic
loads.

Plain `get_metadata()` and `load()` remain side-effect free. This keeps library mode predictable
and lets Gateway or a UI layer decide which user-visible operations should update stats.

### 6) File stores maintain a repairable catalog

File-backed runtime stores may maintain an indexed catalog for exact counts, facet counts, and
bounded paging. The catalog is a projection of descriptor metadata and must be repairable from
metadata sidecars.

The metadata sidecar remains the durable source of record. If the catalog is missing or corrupt,
Runtime can rebuild it from `.meta` files.

### 7) Gateway projects; Observer renders

Gateway may expose descriptor envelopes, search routes, exact counts, filtered pages, provider
trace links, and access-stat mutation routes. Gateway should treat Runtime descriptors as source of
truth and add only control-plane derived fields such as auth-filtered actions, URLs, and transport
links.

Observer should render the descriptor in human-readable views. It may provide fallbacks for legacy
data, but those fallbacks should be visually distinguishable from canonical runtime-declared data.

## Consequences

### Positive

- Voice and music separation becomes a contract, not a UI heuristic.
- Artifact Explorer can filter and count by canonical fields without unlimited UI-side fetches.
- Provider/model/prompt provenance can be added consistently by modality integrations.
- Legacy artifacts remain browseable through explicit projection labels.
- Gateway-first apps keep a stable lower-layer source of truth.

### Negative

- Runtime artifact metadata becomes a broader contract and needs wider review for changes.
- Producers must be updated to populate descriptors instead of relying only on tags.
- Provider provenance requires careful redaction and linking discipline.

### Neutral

- The descriptor is not semantic/vector search. Semantic retrieval remains owned by AbstractMemory
  and related knowledge-layer integrations.
- The catalog is an operational projection, not a second artifact source of truth.

## Enforcement

- New artifact-producing runtime integrations should write descriptor fields directly.
- Gateway artifact routes should prefer descriptor fields over tags and MIME inference.
- Observer should not infer canonical artifact meaning when descriptor fields are present.
- Legacy fallback classifications must preserve their `classification_source`.
- Tests should cover descriptor serialization, legacy projection, access stats, catalog repair,
  exact counts, and filtered paging.

## Validation

Implemented runtime validation includes:

- descriptor serialization and legacy metadata projection;
- voice/music projection from legacy tags;
- explicit access counters for preview/download-style operations;
- file-backed catalog persistence, filtering, facet counts, and repair from `.meta` sidecars;
- additive descriptor enrichment that preserves inspected media facts.

Focused validation command:

```bash
cd abstractruntime
/Users/albou/tmp/abstractframework/.venv/bin/python -m pytest tests/test_artifacts.py
```

## Packages Affected

- AbstractRuntime
- AbstractGateway
- AbstractObserver
- AbstractCore
- AbstractVoice
- AbstractVision
- AbstractMusic
- AbstractFlow

## Related

- ADR-0018: Durable Run Gateway and Remote Host Control Plane
- ADR-0028: Capabilities Plugins + Library/Framework Modes
- ADR-0032: Package Dependency Boundaries and Gateway-First Apps
- ADR-0035: Capability Routing Defaults
- `docs/backlog/completed/runtime-artifact-observability/0188_artifact_descriptor_contract_and_adr.md`
- `docs/backlog/completed/runtime-artifact-observability/0189_runtime_artifact_catalog_and_access_stats.md`
- `docs/backlog/completed/runtime-artifact-observability/0190_media_generation_provenance_and_enrichment.md`
- `docs/backlog/completed/runtime-artifact-observability/0191_gateway_artifact_envelope_query_and_provider_traces.md`
- `docs/backlog/completed/runtime-artifact-observability/0192_observer_canonical_artifact_explorer_ui.md`
