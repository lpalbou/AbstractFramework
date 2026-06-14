# Planned: Media generation provenance and enrichment

## Metadata
- Created: 2026-06-06
- Status: Completed
- Completed: 2026-06-06

## ADR status
- Governing ADRs: ADR-0028, ADR-0035, ADR-0036
- ADR impact: Implements producer-side adoption of ADR-0036. May revise capability metadata guidance if producer responsibilities change.

## Context
Generated media is where artifact metadata matters most. A user inspecting an image, video, voice clip, or music file should see the prompt/input, provider/model/backend, key parameters, source media, and measured media facts without opening raw ledger JSON.

## Current code reality
- Runtime artifact storage now accepts structured `metadata` and `descriptor` fields and persists media facts/access stats.
- Runtime generated-media specs set modality/task for image, video, voice, music, and transcription, but `abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py::_store_generated_bytes` still persists only tags and bytes.
- Runtime generated-media normalization preserves returned item metadata in workflow output JSON, but the durable artifact descriptor is not filled from that metadata.
- `abstractruntime/src/abstractruntime/integrations/abstractcore/effect_handlers.py::_augment_output_request_for_runtime` adds run/session/workflow tags to output specs; it does not yet build an `ArtifactDescriptor`.
- Gateway parent-run projection (`abstractgateway/src/abstractgateway/routes/gateway.py::_gateway_project_artifact_to_parent_run`) copies generated child artifact bytes and tags into the parent run, but does not yet preserve descriptor/metadata.
- Gateway STT stores transcript artifacts with tags for source audio/provider/model, but does not pass descriptor fields or source refs.
- AbstractCore capability paths and modality packages can expose provider/model/backend/metadata, but those fields are inconsistent and need a redacted builder before becoming descriptor data.

## Problem
The framework can generate media but cannot reliably answer how that artifact was produced. The information exists in different package-specific places and is often dropped before artifact persistence.

## What we want to do
Normalize generated-media metadata across Core, Runtime, Vision, Voice, Music, and Gateway-facing paths, then pass it into the Runtime artifact descriptor instead of only returning it transiently.

## Why
Observer should show "this music was generated from prompt X using provider/model Y with duration Z" because Runtime stored that fact, not because the UI guessed from a workflow name or filename.

## Requirements
- Preserve metadata from capability results into Runtime artifact descriptors.
- Preserve descriptor and structured metadata when Gateway projects child-run generated artifacts into a parent run.
- Normalize producer fields: package, capability route, backend, provider, model, task, request id, run id, session id, workflow id, node id, step/effect id, turn/ledger cursor, and source ledger refs.
- Normalize generation fields: prompt/input text, negative prompt when supported, text used for TTS, redacted params, seed, requested output format, output count/index, and source media/artifact refs.
- Normalize image fields: width, height, format, source image refs, edit vs pure generation, mask/source role where available.
- Normalize video fields: width, height, duration, FPS, frame count, source image/video refs, and generation mode.
- Normalize music fields: prompt, lyrics or instrumental/null-lyrics state, requested duration, measured duration, sample rate, channels, frames, provider/model/backend, and source audio refs if any.
- Normalize voice fields: input text, language, provider/model, voice id/name/profile, cloned voice flag, cloned/source voice refs, quality/speed/style settings, and sensitivity/redaction labels.
- Normalize transcription fields: source audio artifact id/ref, language, provider/model, timestamps/segments when available, and transcript artifact relation.
- Extract media facts from bytes when producer metadata is missing or incomplete. Use safe optional inspectors and emit explicit fallback fields when unavailable.
- Redact secrets and high-risk payloads. Store large raw provider requests as trace-linked artifacts or ledger refs, not as indexed descriptor fields.
- Add package-level tests that prove metadata survives from producer output to Runtime artifact list/detail.

## Suggested implementation
1. Start with a narrow vertical slice in Runtime generated-media storage: build descriptors from normalized generated items and pass them to `ArtifactStore.store(...)`.
2. Preserve descriptor/metadata through Gateway parent-run projection.
3. Add redaction rules before storing prompt/params/provider payloads in descriptor fields.
4. Update Vision, Voice, and Music artifact helpers/managers to fill canonical fields incrementally.
5. Add route-specific regression tests for image generation/edit, TTS, STT, text-to-music, and one video path.
6. Add fixtures proving metadata is preserved through child-run projection and Gateway envelope projection.

## Scope
- `abstractruntime` generated-media storage and metadata normalization.
- `abstractcore` capability result/facade metadata preservation where current server paths drop metadata.
- `abstractvision`, `abstractvoice`, and `abstractmusic` metadata adapters.
- Focused Gateway contract tests as needed to prove metadata survives the route boundary.

## Non-goals
- Do not add new media generation capabilities.
- Do not require optional heavy media dependencies for basic artifact writes.
- Do not index raw prompts or provider payloads before redaction/sensitivity policy is settled.
- Do not treat legacy artifacts without metadata as a failure; project them with fallback classification.

## Hard dependencies
- `docs/backlog/completed/runtime-artifact-observability/0188_artifact_descriptor_contract_and_adr.md`.
- `docs/backlog/completed/runtime-artifact-observability/0189_runtime_artifact_catalog_and_access_stats.md`.

## Related and follow-on tasks
- `docs/backlog/completed/runtime-artifact-observability/0191_gateway_artifact_envelope_query_and_provider_traces.md`.
- `docs/backlog/completed/multimodal-capabilities/0175_multimodal_capability_taxonomy_schema.md`.

## Expected outcomes
- New image, video, voice, music, audio, and transcription artifacts carry durable structured provenance.
- Voice and music are distinguishable even when both are `audio/wav`.
- Artifact detail can show generation prompt, provider/model, source media, and measured duration/dimensions without reading raw ledger JSON.
- Missing inspectors or unsupported metadata paths are visible as explicit fallbacks.

## Implementation completed
- Added a Runtime-owned `build_artifact_descriptor_payload(...)` helper in `abstractruntime.storage.artifacts` so Gateway producers can use the Runtime descriptor contract without hand-authoring a parallel schema.
- Enriched AbstractCore Runtime generated-media storage in `llm_client.py` so generated image, video, voice/TTS, music, sound/audio, and existing artifact refs receive descriptor and structured metadata.
- Preserved prompt or TTS text, requested format, output index, negative prompt, redacted generation parameters, provider/model/backend, runtime provider/model, source media refs, request id, run/session/workflow/node/turn/ledger fields, and security/redaction labels where available.
- Redacted exact `token` fields and related credential keys in nested capability metadata, bounded long strings, and labeled prompt/text fields as user content in descriptor `security`.
- Preserved source artifact filename/content type/modality through Runtime media resolution so image edit and image-to-video source refs remain useful.
- Preserved descriptor and structured metadata when Gateway projects generated child artifacts into the parent run, while updating parent-facing session/workflow/node fields and retaining projected-from provenance/source refs.
- Updated Gateway direct transcription storage to use the Runtime descriptor helper, including source-audio refs and route parameters.
- Updated Gateway direct generated-image raw-byte fallback to store Runtime descriptors instead of tag-only artifacts.
- Sanitized descriptor-provided action links in Gateway envelopes so Observer only receives relative Gateway/UI links, not arbitrary provider URLs.
- Fixed schema normalization so required structured-output fields remain required even if the JSON Schema declares a `default`.

## Validation
- `PYTHONPATH=abstractruntime/src python -m pytest abstractruntime/tests/test_abstractcore_run_facade.py abstractruntime/tests/test_llm_call_response_schema_normalization.py -q`
- `PYTHONPATH=abstractgateway/src:abstractruntime/src python -m pytest abstractgateway/tests/test_gateway_artifacts_endpoint.py -q`
- `python -m compileall -q abstractruntime/src/abstractruntime/storage/artifacts.py abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py abstractruntime/src/abstractruntime/integrations/abstractcore/effect_handlers.py abstractgateway/src/abstractgateway/routes/gateway.py`

## Progress checklist
- [x] Add shared descriptor/metadata builder and redaction rules.
- [x] Pass generated-media descriptor/metadata into Runtime artifact storage.
- [x] Preserve descriptors during Gateway child-to-parent artifact projection.
- [x] Normalize Music metadata paths for prompt/provider/model/requested duration/measured duration in the Runtime AbstractCore generated-media path.
- [x] Normalize Voice TTS/STT metadata paths for text/language/provider/model/voice/source refs in the Runtime/Gateway generated-media path.
- [x] Normalize Vision-style image/video metadata paths for prompt/provider/model/source refs and inspected dimensions in the Runtime AbstractCore generated-media path.
- [x] Add cross-package preservation tests for Runtime/Core and Gateway route boundaries.

## Residual follow-up
- Direct package-native artifact writers in `abstractvision`, `abstractvoice`, or `abstractmusic` that bypass the Runtime AbstractCore generated-media path should adopt `build_artifact_descriptor_payload(...)` as they are touched.
- Provider trace storage remains descriptor/link driven; richer provider payload traces should be stored as separate redacted artifacts or Gateway-owned trace records, not indexed descriptor fields.

## Guidance for the implementing agent
Do not sweep every modality first. Start by tracing one concrete artifact, such as `wf_abstractcore_run_facade_text_to_music`, from request to artifact store to Gateway envelope. Make that path fully correct, including parent-run projection, before broadening to every modality.
