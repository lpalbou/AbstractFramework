# Completed: Artifact descriptor contract and ADR

## Metadata
- Created: 2026-06-06
- Status: Completed
- Completed: 2026-06-06

## ADR status
- Governing ADRs: ADR-0018, ADR-0028, ADR-0032, ADR-0035
- ADR impact: ADR-0036 was added and accepted on 2026-06-06. It defines Runtime as the canonical artifact descriptor owner, Gateway as projection/index owner, and Observer as presentation owner.

## Context
Users need to answer simple questions from the runtime UI: is this artifact voice or music, which run/session/turn produced it, what prompt/model/params created it, which source media was used, when was it accessed, and where is the provider trace?

Today some of that information exists transiently in workflow outputs, tags, ledgers, backend metadata, or Gateway route context, but there is no cross-package descriptor contract that all producers and consumers can rely on.

## Current code reality
- `abstractruntime/src/abstractruntime/storage/artifacts.py::ArtifactMetadata` stores only `artifact_id`, `content_type`, `size_bytes`, `created_at`, optional `blob_id`, optional `run_id`, and string `tags`.
- `ArtifactStore.store(...)` accepts content, content type, run id, tags, and optional artifact id, but no structured metadata or provenance object.
- `abstractruntime/src/abstractruntime/integrations/abstractcore/run_facade.py` sets modality/task defaults for image, video, voice, music, and transcription facade runs.
- `abstractruntime/src/abstractruntime/integrations/abstractcore/effect_handlers.py::_runtime_output_tags` records runtime context as tags, including run, workflow, node, actor, session, and parent run when available.
- `abstractgateway/src/abstractgateway/routes/gateway.py::_canonical_artifact_ref` and `_artifact_list_item` derive modality and list fields from tags/MIME type rather than a versioned descriptor.
- `abstractobserver/src/ui/artifact_rendering.ts` classifies render/display kind by MIME, modality, filename/source path, tags, and content sniffing.

## Problem
Tags and UI heuristics cannot carry durable, queryable artifact semantics. They are untyped, producer-specific, hard to validate, and insufficient for access stats, generation provenance, media facts, provider traces, and voice/music separation.

## What we want to do
Define `ArtifactDescriptorV1`, a versioned cross-package contract for artifact identity, classification, ownership, provenance, generation inputs, media facts, access stats, security/action hints, and compatibility tags.

## Why
The artifact descriptor is the foundation for runtime searchability. Without it, Gateway and Observer will keep re-implementing fragile inference, and users will still be unable to understand what computation produced a costly artifact.

## Requirements
- Runtime is the canonical descriptor owner. Gateway may index/project, but it must not invent canonical artifact meaning for new artifacts.
- Keep legacy `ArtifactMetadata` compatibility. Existing artifacts must remain readable.
- Keep `tags` as compatibility/search labels, not as the only provenance channel.
- Define separate `render_kind` and `semantic_kind`. Example: a WAV file can render as `audio` while semantically being `voice`, `music`, `sound`, or `recording`.
- Include ownership/runtime links: tenant/principal when available, session id, run id, parent run id, workflow id, node id, step id/effect id, turn id or ledger cursor, and source ledger/history links.
- Include generation/provenance fields: producer package, capability route/task, provider, model, backend, prompt/input text, redacted params, seed/request ids, source artifact refs, source media refs, and output role.
- Include media facts: image dimensions, video dimensions/FPS/duration, audio duration/sample rate/channels/frames, document page count when available, and extraction confidence/source.
- Include access fields: created at, last accessed at, access count, preview count, download count, and last accessor context when safe to expose.
- Include security/action hints: sensitivity labels, redaction state, available actions, and whether provider trace/audit links are available.
- Define `classification_source` values such as `runtime_declared`, `producer_metadata`, `byte_inspected`, `gateway_legacy_projection`, and `observer_legacy_inferred`.
- Define redaction rules for prompts, tool params, provider payloads, source paths, and voice clone metadata.

## Suggested implementation
1. Draft a framework ADR for `ArtifactDescriptorV1` boundaries and vocabulary.
2. Add a schema module in `abstractruntime` for typed descriptor structures and JSON serialization.
3. Specify compatibility mapping from current `ArtifactMetadata` + `tags` to a legacy descriptor projection.
4. Define stable enum values for `semantic_kind`, `render_kind`, `media.kind`, `provenance.kind`, and `classification_source`.
5. Add fixture artifacts for image, video, voice, music, generic audio, markdown, HTML, JSON, document, and evidence/text.
6. Add contract tests that Gateway and Observer can share or mirror.

## Scope
- Cross-package ADR and vocabulary.
- Runtime descriptor schema and compatibility projection.
- Gateway/Observer contract fixtures.
- Backward-compatible migration semantics for existing `.meta` files.

## Non-goals
- Do not implement the full Runtime catalog/index in this item; see `0189`.
- Do not migrate every media producer in this item; see `0190`.
- Do not redesign the Observer UI here; see `0192`.
- Do not make semantic retrieval part of artifact descriptors. Semantic/vector retrieval belongs in AbstractMemory/KG.

## Dependencies and related tasks
- `0189_runtime_artifact_catalog_and_access_stats.md`.
- `0190_media_generation_provenance_and_enrichment.md`.
- `0191_gateway_artifact_envelope_query_and_provider_traces.md`.
- `0192_observer_canonical_artifact_explorer_ui.md`.
- `docs/backlog/proposed/gateway-control-plane/0151_runtime_explorer_contract.md`.

## Expected outcomes
- A future agent can tell exactly which package owns each artifact descriptor responsibility.
- Voice and music separation is a contract, not an Observer heuristic.
- Gateway and Observer have fixtures that prove they read canonical fields before legacy tags/sniffers.
- Legacy artifacts remain browseable with explicit fallback classification.

## Validation
- ADR added and indexed under `docs/adr/`.
- Runtime schema serialization/deserialization tests pass for v1 descriptors and legacy metadata projection.
- Contract fixtures cover at least one image, video, voice, music, markdown, HTML, JSON, document, evidence text, and generic binary artifact.
- Tests assert that `tags` alone are not required for canonical v1 artifacts.

## Progress checklist
- [x] Write and index the ADR.
- [x] Define descriptor schema and enums.
- [x] Define legacy projection and fallback labels.
- [x] Add fixture artifacts and contract tests.
- [x] Update related backlog items if the ADR changes ownership boundaries.

## Guidance for the implementing agent
Start with the ADR and schema. Avoid broad UI/API edits until the descriptor vocabulary is stable. If the code has already added a descriptor-like shape, reconcile this item with the real implementation before adding another parallel contract.

## Completion report

Implemented the Runtime-owned `ArtifactDescriptor` contract in `abstractruntime`, including versioned serialization, separate `semantic_kind` and `render_kind`, legacy projection from existing metadata/tags, runtime link fields, provenance/generation/media/action maps, and explicit `ArtifactAccessStats`.

Architecture review chose the Runtime-owned descriptor plus Gateway projection model over Observer inference or Gateway-only synthesis. Technical review focused on backward compatibility and source-compatible store signatures. UX review kept the user-facing requirement explicit: Observer should present canonical descriptor fields and visibly label legacy fallback classifications instead of guessing artifact meaning.

Validation:
- `cd abstractruntime && /Users/albou/tmp/abstractframework/.venv/bin/python -m pytest tests/test_artifacts.py`
- `python3 -m py_compile abstractruntime/src/abstractruntime/storage/artifacts.py`

Remaining follow-up work is tracked in `0190` through `0193`: producer enrichment, Gateway envelopes/provider traces, Observer UI consumption, and documentation/skill coverage.
