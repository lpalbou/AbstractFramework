# Planned: LLM and Agent model input artifacts

## Metadata
- Created: 2026-06-04
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0023 file attachment path resolution and authorization, ADR-0024 attachment placeholders and compaction invariants, ADR-0032 package dependency boundaries and gateway-first apps, ADR-0035 capability routing defaults
- ADR impact: None if the implementation reuses existing artifact refs, Gateway visibility checks, Runtime media handoff, and Core capability routes. Revisit ADR-0035 only if new modality names or route semantics are introduced.

## Context
Flow authors need to pass model input artifacts into `LLM Call` and `Agent` nodes. These artifacts are request data for the model, not prompt text, not system prompt text, and not hidden prompt interpolation.

Examples:

- image artifact + prompt: "describe this image"
- video artifact + prompt: "summarize the scene"
- voice/audio/music artifact + prompt: "transcribe, classify, or analyze this"
- several file artifacts + prompt: "compare these PDFs, images, transcripts, and recordings"
- mixed image/video/audio artifacts + prompt: "compare these inputs"

The framework already has Core route metadata (`input.image`, `input.video`, `input.voice`, `input.sound`, `input.music`) and Gateway/Runtime artifact refs. The missing piece is a first-class Flow authoring abstraction for node-local model input artifact lists that lower into the existing Core/Runtime media path.

## Current code reality
- `abstractflow/src/types/nodes.ts` defines `LLM Call` and `Agent` with `context`, `system`, `prompt`, `tools`, `prompt_cache_binding`, `thinking`, and structured-output pins, but no explicit model-input artifact pin or collector node.
- `abstractflow/src/types/flow.ts` defines artifact pin types for `artifact`, `artifact_image`, `artifact_audio`, `artifact_text`, and `artifact_video`. It does not define separate `artifact_voice`, `artifact_sound`, or `artifact_music` pin types.
- `abstractflow/src/utils/artifactInputs.ts` and `abstractflow/src/utils/mediaArtifacts.ts` already treat audio artifacts with `modality` tags such as `voice`, `music`, and `sound` as audio-compatible.
- Flow media nodes such as Generate Image, Image-to-Video, Generate Voice, Generate Music, and Transcribe Audio already use artifact pins and the unconnected artifact upload affordance.
- `abstractflow/src/utils/preflight.ts` validates required media artifact pins for media nodes, but has no LLM/Agent artifact compatibility check.
- `abstractgateway/src/abstractgateway/routes/gateway.py::_normalize_run_context_media` normalizes run-level `attachments` / `media` into `input_data.context.attachments`, and run start validates artifact refs before handoff.
- `abstractruntime/src/abstractruntime/visualflow_compiler/visual/executor.py::_create_llm_call_handler` maps explicit `context.attachments` to `pending["media"]` for LLM calls.
- `abstractruntime/src/abstractruntime/visualflow_compiler/compiler.py` forwards parent context attachments into LLM calls when `include_context` is enabled and can put context attachments into Agent subworkflow vars.
- `abstractagent/src/abstractagent/adapters/media.py::extract_media_from_context` turns `context.attachments` / `context.media` into `payload.media` for runtime-backed agents.
- Completed backlog items `0175`, `0177`, and `0178` already provide route-keyed capabilities, Flow route-aware model discovery, and reasoning propagation. This item should build on those, not duplicate them.

## Decision Question
How should Flow expose model input artifacts for `LLM Call` and `Agent` nodes while preserving Gateway/Runtime/Core as the authority for artifact visibility, execution, and model capability compatibility?

## Architecture Alternatives

### Alternative A: Add direct artifact pins to LLM Call and Agent
Add pins such as `image_artifact`, `video_artifact`, `audio_artifact`, and maybe `input_artifacts` directly to both node templates.

Steelman: this is visible and easy for a naive user. It reuses existing artifact-pin upload behavior and keeps the graph compact for a single artifact.

Critique: it scales poorly for mixed inputs, duplicates pin sets on two central nodes, and creates pressure to add one pin per semantic audio subtype. It also makes compatibility logic harder because each pin has to map to a route and combine with the selected provider/model.

### Alternative B: Use only the existing `context` object
Document that users should put artifacts under `context.attachments` or `context.media`, and rely on existing Runtime/Agent extraction.

Steelman: this needs little code and matches current runtime behavior. It keeps model input artifacts in the durable context object.

Critique: it hides an important model-call concept behind a generic object pin. Users will keep putting artifact IDs into prompts or system prompts, and Flow cannot give modality-specific upload, validation, or model compatibility feedback.

### Alternative C: Add a `Model Input Artifacts` collector node plus one LLM/Agent input pin
Create a pure data node that collects one or more artifacts by modality and emits a normalized `model_input_artifacts` array. Add a single advanced `input_artifacts` pin to `LLM Call` and `Agent`; the pin accepts either one artifact ref or a list, but the normalized runtime contract is always a list. Runtime lowers it to LLM `media` and Agent `context.attachments`.

Steelman: this keeps prompt/system text clean, supports mixed media, gives one place for modality labels and upload affordances, and avoids bloating every model node. It also preserves the existing artifact-ref transport and makes route compatibility checks explicit.

Critique: it adds one more node for simple cases unless the LLM/Agent pin also allows direct unconnected upload. The collector must be designed carefully so it does not become a second artifact store or a provider-specific preprocessing node.

### Alternative D: Extend the run-start artifact input picker only
Let users upload/select artifacts at run start and rely on `use_context` / inherited `context.attachments` for LLM/Agent nodes.

Steelman: this matches existing Gateway run-start validation and keeps node templates unchanged.

Critique: it is run-global, not node-local. It cannot express "this artifact goes to this one LLM call but not the next", and it makes multi-step workflows brittle.

## Tensions
- Node simplicity vs visible modality control: direct pins are obvious but clutter central nodes; a collector is cleaner but adds an extra graph element.
- Static compatibility vs runtime truth: Flow can query route-aware catalogs, but Gateway/Runtime/Core must still validate artifact refs and model capability at execution time.
- Audio umbrella vs semantic audio routes: storage can remain `artifact_audio`, but the UX needs to distinguish speech/voice, non-speech sound/audio, and music where route compatibility matters.
- Context inheritance vs explicit inputs: inherited run context is useful for chat-like flows, but node-local model artifacts need explicit graph wiring.

## Synthesis
Use Alternative C with a small compatibility path from Alternative A.

Add a first-class `Model Input Artifacts` collector node that emits an ordered list of normalized artifact refs plus per-item intended input modality. Add one `input_artifacts` pin to `LLM Call` and `Agent`. For simple cases, the unconnected `input_artifacts` pin may use the existing artifact upload/select affordance, but the durable representation should still be the same normalized list.

Do not put artifact bytes, paths, or base64 in the prompt or node config. The graph should carry canonical artifact refs such as `{"$artifact": "...", "modality": "image"}` and let Gateway/Runtime/Core resolve and authorize them.

## Recommendation
Implement model input artifacts as an artifact-ref collection contract:

- Flow:
  - Add a `Model Input Artifacts` pure data node that can collect several artifact refs, including several files of the same modality.
  - Add an `input_artifacts` pin to `LLM Call` and `Agent`, likely hidden/advanced until connected or configured.
  - Reuse the existing browser upload / Gateway artifact select affordance for unconnected artifact pins, with multi-select or repeated-row UX where practical.
  - Present supported modality labels from Core/Gateway capability routes: image, video, voice/speech, sound/audio, music, and later scene3d.
  - Prefer existing `artifact_audio` transport for voice/sound/music while preserving semantic `modality` or `input_route` metadata.
- Runtime:
  - Normalize `input_artifacts` into an ordered `pending["media"]` list for LLM calls.
  - Normalize `input_artifacts` into an ordered Agent child `context.attachments` list so AbstractAgent's existing media extraction path works.
  - Preserve explicit empty lists as "no artifacts for this call" and avoid double-including inherited context attachments.
- Gateway:
  - Continue validating artifact refs before run start/resume where refs are user-provided.
  - Expose enough route/model capability metadata for Flow preflight and tooltips without moving model capability ownership into the browser.
- Core:
  - Remains the authority for whether a selected provider/model natively supports `input.image`, `input.video`, `input.voice`, `input.sound`, or `input.music`, and whether configured fallback routes can cover the request.

## Requirements
- `LLM Call` and `Agent` must support node-local model input artifacts independently of prompt and system prompt.
- `input_artifacts` must support a list of artifact refs, not only a single artifact. A single ref is accepted as input convenience but normalized to a one-item list.
- The list may include several files/artifacts of the same modality and mixed modalities when the selected/effective model route can accept them.
- The serialized VisualFlow shape must remain JSON-safe and must not embed binary payloads.
- Artifact refs must remain canonical Gateway/Runtime refs, not browser paths or server filesystem paths.
- Route compatibility must be checked at authoring/preflight where possible and at runtime before model execution where necessary.
- For Auto provider/model defaults, compatibility checks must use the effective Gateway/Core default route rather than assuming a specific local model.
- Mixed artifact lists must preserve user-authored order because order can affect model interpretation.
- Audio-like artifacts must preserve semantic intent when known:
  - `input.voice` for speech/voice input and STT-like use;
  - `input.sound` for environmental sound, SFX, and general audio scene analysis;
  - `input.music` for music analysis.
- Existing `context.attachments` behavior must continue to work for imported/legacy flows.
- User-facing validation must say which route is missing, e.g. "Selected model does not support `input.video`; choose a video-capable model or configure a fallback route."

## Suggested implementation
1. Define a small normalized model-input-artifacts schema, for example:

   ```json
   [
     {"$artifact": "artifact-id", "modality": "image", "input_route": "input.image"},
     {"$artifact": "artifact-id", "modality": "music", "input_route": "input.music"}
   ]
   ```

2. Add Flow helpers that normalize a single artifact ref, array of refs, or collector output into that list. Empty/null entries should be dropped unless the user explicitly configured an empty list to suppress inherited attachments.
3. Add `input_artifacts` to `LLM Call` and `Agent` node templates and serialize/migrate it like other pins.
4. Add the `Model Input Artifacts` node with modality-aware repeated artifact rows/slots and one output pin.
5. Extend Flow preflight and live connection feedback to validate artifact modality and selected/default route compatibility using Gateway/Core discovery.
6. Extend Runtime LLM Call lowering so `input_artifacts` takes precedence over inherited `context.attachments` and maps to `pending["media"]`.
7. Extend Runtime Agent lowering so `input_artifacts` becomes child `context.attachments` and does not require users to hand-author a context object.
8. Add Gateway run/resume validation coverage if the new input can arrive outside existing run-start `input_data` validation.

## Scope
- AbstractFlow node templates, type definitions, artifact input helpers, connection validation, preflight, and relevant docs.
- AbstractRuntime VisualFlow compiler/executor lowering for LLM Call and Agent.
- AbstractGateway artifact-ref validation and capability discovery only if current routes do not give Flow enough information.
- AbstractAgent tests only if Runtime Agent lowering cannot be proven through current context attachment behavior.

## Non-goals
- Do not create a new artifact storage system.
- Do not inline binary data into VisualFlow JSON, prompts, messages, or ledger records.
- Do not make Flow parse or own `model_capabilities.json`.
- Do not implement transcription, image captioning, or music analysis as separate preprocessing in this item. The artifact is model input; model/fallback execution remains Core/Runtime work.
- Do not change generated media output nodes except where their artifact outputs connect to the new input-artifacts path.
- Do not solve generic file import/export; see proposed item `abstractflow/docs/backlog/proposed/0095_file_nodes_artifact_io_boundary_resolution.md`.

## Dependencies and related tasks
- ADR-0023, ADR-0024, ADR-0032, ADR-0035.
- Completed root backlog item `0175` multimodal capability taxonomy and schema.
- Completed root backlog item `0177` Flow route-aware provider and model selection.
- Completed root backlog item `0178` Gateway and Flow reasoning control propagation.
- AbstractFlow completed items `0092` and `0093` for artifact picker and artifact visibility/handoff.
- AbstractFlow proposed item `0095` for broader file/artifact IO boundary resolution.

## Expected outcomes
- Flow authors can wire or upload artifacts into LLM Call and Agent nodes as model input data.
- Flow authors can pass several artifacts/files to one model call without encoding them into prompt text.
- Prompt and system prompt remain text-only instructions/content fields, not artifact transport fields.
- Runtime LLM effects receive explicit ordered `media` lists when model input artifacts are configured.
- Agent subworkflows receive ordered `context.attachments` lists from the node-local input artifacts.
- Inherited run/session attachments still work, but explicit node artifacts override or compose with them by documented policy.
- Compatibility errors point at missing input routes and selected/default model constraints.

## Validation
- Flow tests:
  - node templates expose `input_artifacts` on `llm_call` and `agent`;
  - collector node emits ordered normalized artifact ref lists;
  - single artifact refs normalize to one-item lists;
  - several file/artifact refs of the same modality are accepted when the route supports them;
  - artifact upload/select can populate `input_artifacts`;
  - image/video/audio artifact connection validation accepts compatible refs and rejects incompatible refs;
  - preflight reports missing route support for incompatible selected models.
- Runtime tests:
  - LLM Call with several `input_artifacts` emits `EffectType.LLM_CALL` payload `media` with the same order;
  - Agent with several `input_artifacts` starts a subworkflow with ordered `vars.context.attachments`;
  - explicit empty `input_artifacts: []` suppresses inherited attachments;
  - legacy `context.attachments` still works.
- Gateway tests:
  - run start/resume rejects stale or unauthorized artifact refs carried by the new field;
  - session-visible artifacts can be passed through the new field without requiring run ownership.
- End-to-end smoke:
  - upload/select an image artifact, wire it through `Model Input Artifacts` to `LLM Call`, and run against a vision-capable model;
  - upload/select an audio/music artifact, wire it to `Agent`, and confirm the child LLM call receives media or fails with a route-specific actionable error.

## Progress checklist
- [ ] Confirm current Gateway discovery can answer model/provider route compatibility for Flow preflight.
- [ ] Define the normalized `input_artifacts` schema.
- [ ] Add Flow collector node and LLM/Agent input pins.
- [ ] Add Flow connection, preflight, upload/select, and migration support.
- [ ] Add Runtime LLM Call lowering to `media`.
- [ ] Add Runtime Agent lowering to `context.attachments`.
- [ ] Add Gateway validation tests for artifact refs carried by `input_artifacts`.
- [ ] Update Flow/Runtime/Gateway/Core docs and LLM indexes after implementation.

## Review pass

### Blocking Issues
- **Security and visibility**: artifact refs in the new field must pass Gateway/Runtime visibility checks. A browser-authored artifact id cannot bypass session/run ownership checks just because it is nested under a model input field.
- **Compatibility truth**: Flow must not decide model compatibility from local hardcoded lists. It should use Gateway/Core route-aware discovery and still allow runtime failure when live provider behavior disagrees.
- **Agent path parity**: updating only LLM Call would leave Agent, the primary long-running model path, inconsistent. Agent must lower node-local artifacts into child `context.attachments`.
- **Prompt confusion**: no implementation should stringify artifact refs into `prompt` or `system`.

### Non-Blocking Issues
- Consider whether the UI should eventually show semantic audio chips for voice, sound, and music while keeping the underlying pin type as `artifact_audio`.
- Consider whether `input_artifacts` should compose with inherited context attachments or override them by default. The recommended default is: explicit field wins; an optional "also include context attachments" switch can be added later if users need composition.

### Architecture Fit
This fits the existing package boundaries if Flow owns authoring UX, Gateway owns artifact visibility and discovery, Runtime owns graph lowering, AbstractAgent consumes context attachments, and Core owns provider/model media capability behavior.

### Naive User View
Users should see an obvious "model input artifacts" concept next to prompt/system, with upload/select controls and modality labels. They should not need to know `context.attachments` exists.

### Expert User View
Experts need stable JSON refs, explicit route compatibility diagnostics, reproducible ordering, and the ability to wire computed artifact refs from other nodes.

### Operations
Large artifacts should stay in the artifact store and be streamed/materialized by existing infrastructure. Logs and ledger records should contain refs and metadata, not payload bytes.

## Risks And Evidence Needed
- Need evidence that current Gateway discovery can cheaply check selected provider/model support for combined routes such as `input.image,output.text` and `input.video,output.text`.
- Need evidence that Core fallback behavior for voice/sound/music input is explicit enough to produce good runtime errors rather than silent transcription or captioning.
- Need browser/UI proof that the collector node does not make the common single-image case too verbose.
- Need regression tests that existing flows using `context.attachments` and run-start attachments remain compatible.

## Guidance for the implementing agent
Start with the current code, not this design text. Re-check `LLM Call`, `Agent`, artifact picker, Gateway artifact validation, Runtime LLM lowering, and AbstractAgent media adapters before editing. Keep the implementation small and explicit: a normalized artifact-ref list, one LLM/Agent input pin, one collector node, and tests proving the data reaches model media input without becoming prompt text.
