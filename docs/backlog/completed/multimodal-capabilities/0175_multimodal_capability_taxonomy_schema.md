# Completed: Multimodal capability taxonomy and schema

## Metadata
- Created: 2026-06-02
- Status: Completed
- Completed: 2026-06-03

## ADR status
- Governing ADRs: ADR-0028, ADR-0035
- ADR impact: ADR-0035 was revised on 2026-06-03 to clarify that
  `model_capabilities.json` may expose route-keyed native model support
  metadata, while effective default-row source/status/action metadata remains
  outside the raw registry.

## Context
The framework already routes user-facing defaults through keys such as
`input.voice`, `input.sound`, `output.voice`, `output.sound`, and
`output.music`. However, the canonical model registry still uses broad boolean
fields such as `audio_support`, `vision_support`, and `video_support`.

That broad shape was acceptable when the only audio distinction was "model can
receive audio at all". It is no longer precise enough now that Gateway Console
can configure fallbacks and users expect clear behavior for speech, SFX/audio
scene understanding, and music analysis.

This item is now schema-first. Before adding more route behavior, AbstractCore
needs a clear model-registry contract that every checked-in model entry can be
validated against, plus a normalizer that lets old broad-boolean consumers keep
working while route-aware callers move to `input.*`, `output.*`, `embedding.*`,
and `rerank.*` capability routes.

## Current code reality
- Completion note, 2026-06-03: the schema-first slice below is now implemented.
  `model_capabilities.schema.json` exists, Python schema tests validate
  `capability_routes`, Core exposes route-aware helpers, `/v1/models` accepts
  `capability_route`, Runtime forwards route filters, and Gateway Console uses
  route filters for text-model catalogs. `input.music` is now part of the
  default-route matrix as a music-audio understanding route. Remaining
  media-policy helper migration should be tracked as follow-up work rather than
  reopening this schema item.
- `abstractcore/abstractcore/config/capability_defaults.py` includes
  `input.sound` and `input.music`.
- `docs/adr/0035-capability-routing-defaults.md` lists `music` as a modality
  and defines both `input.music` and `output.music`.
- `abstractcore/abstractcore/assets/model_capabilities.json` uses
  `audio_support` as a coarse boolean and currently has 233 model entries. Every
  model entry is required by tests to include `vision_support`, `audio_support`,
  `video_support`, and `video_input_mode`.
- `abstractcore/tests/assets/test_model_capabilities_schema.py` remains the
  semantic schema enforcement point, and
  `abstractcore/abstractcore/assets/model_capabilities.schema.json` is now a
  reusable JSON Schema artifact for tooling/review.
- Only a small subset of models currently has `audio_input_capabilities`; this
  is a hint field, not an authoritative route contract.
- `abstractcore/abstractcore/providers/model_capabilities.py` exposes
  `ModelInputCapability.AUDIO`, which is too broad for route-specific catalog
  filtering because it cannot distinguish STT, SFX/audio-scene understanding,
  and music understanding.
- `ModelOutputCapability` now keeps legacy `TEXT`/`EMBEDDINGS` while also
  exposing route-specific output enum values for image, video, voice, sound,
  music, scene3d, and rerank.
- Core Server `/v1/models` still accepts legacy `input_type` and `output_type`
  filters, and now also accepts repeatable or comma-separated
  `capability_route` keys such as `input.sound,output.text` or
  `embedding.text`.
- `abstractcore/abstractcore/media/capabilities.py`,
  `abstractcore/abstractcore/media/handlers/*`, provider code, and tests read
  `audio_support` directly.
- `abstractgateway/src/abstractgateway/console.py` maps `input.sound` to an
  audio-input text catalog, and the Sandbox handles generated voice, sound, and
  music separately.
- The Gateway Console defaults table shows effective row metadata such as
  source, status, and available actions. Those are not raw
  `model_capabilities.json` fields; they are computed from configured route
  defaults, model capability coverage, provider catalogs, plugin readiness, and
  control-plane write policy.

## Decision question
Should `model_capabilities.json` stay on broad booleans, move to nested
input/output modality booleans, or become a route-keyed schema that matches the
existing `input.*` and `output.*` capability-default contract?

## Architecture alternatives

### Alternative A: Keep broad booleans plus `audio_input_capabilities`
Steelman: smallest change and lowest code churn. Existing media handlers already
know how to gate native image/audio/video input, and the current schema tests
already enforce the broad fields for every model.

Critique: it cannot tell whether a model can transcribe speech, caption sound
events, analyze music, or all three. It also lets STT models look equivalent to
audio-scene models. It does not solve output routes at all.

### Alternative B: Add nested `input_capabilities` / `output_capabilities`
Steelman: easy to read and close to the existing broad-boolean mental model.
Every model could declare `{ "input": { "image": true }, "output": { "text":
true } }` style support without changing the top-level route-default system.

Critique: it creates a second vocabulary beside the accepted route keys. Core
defaults use `input.sound` and `output.music`; a nested boolean schema would need
another translation layer and can drift from ADR-0035.

### Alternative C: Add route-keyed `capability_routes`
Steelman: aligns the registry with the actual user-facing routing contract.
Field presence means support; values are grouped modality arrays such as
`"input": ["text", "image", "video"]` and `"output": ["text"]`. Broad
booleans remain derived compatibility views until every consumer has moved to
helper APIs.

Critique: temporary duplication can drift unless tests enforce derivation rules,
and route claims require source-backed evidence. A rushed all-model migration
would force guesses.

## Synthesis
Use Alternative C, but implement it in a schema-first, helper-first sequence.
The first code pass should add a JSON Schema asset, Python validation, and a
normalizer before any route-matrix expansion. The final implementation gives all
240 checked-in model entries explicit grouped route metadata, and `input.music`
was added only after route helpers and tests existed.

## Architecture review notes

### Architect A: Platform/data-model charter
Proposed design: make route-level input/output capability sets the authoritative
registry shape, because Gateway Console, Core CLI, Runtime discovery, and Flow
selectors all need the same answer to "what route can this model satisfy?"
Keep legacy booleans generated from that shape so existing provider/media code
does not break in the first pass.

Assumptions: capability defaults are already route-keyed; Core remains the
source of truth for model metadata; Gateway should not invent a second
capability model.

Strongest argument: this aligns model metadata with the actual user-visible
routes and prevents STT models from being misrepresented as music/SFX
understanding models.

Strongest objection: richer schema adds migration overhead and could drift if
old booleans and new route fields are both manually edited.

Evidence that would change this view: if most provider APIs cannot expose
route-specific capabilities or if downstream code only ever needs broad native
audio acceptance, then route-level schema may be over-modeled.

### Architect B: Minimal compatibility charter
Proposed design: keep the public booleans for now, add a helper that maps
model records to route-specific effective capabilities, and migrate consumers
incrementally. The JSON can accept the richer shape, but call sites should
depend on helper APIs rather than raw JSON fields.

Assumptions: Core, Gateway, Runtime, and Flow have many existing direct reads
of `audio_support`, `vision_support`, and `video_support`; breaking those while
also adding new audio models would create avoidable churn.

Strongest argument: a helper-first migration lets us test behavior route by
route and preserve all current defaults while improving precision.

Strongest objection: if the helper remains a compatibility wrapper forever, the
registry never becomes clean and future developers may keep using the old
boolean fields.

Evidence that would change this view: if test coverage proves every consumer
can be switched quickly, a direct schema migration may be cheaper than a long
compatibility phase.

### Architect C: Review/risk charter
Blocking concern: this item must not implement the nested boolean candidate
shape because it would drift from route defaults. The model registry should use
the same route keys as `abstractcore.config.capability_defaults`.

Additional concerns: `/v1/models` and `ModelInputCapability` / `ModelOutputCapability`
are still broad, native audio policy still reads `audio_support`, and evidence is
too thin to require fully source-backed route records for every model in a single
bulk edit.

Mitigation: add the route-keyed schema and normalizer first, require
compatibility derivation tests immediately, migrate catalog/filter consumers
next, and only then promote `input.music`. That sequence has now been followed.

## Problem
`audio_support: true` is too ambiguous for the current UX and routing contract.
It does not tell the Gateway Console or Core whether a model is appropriate for
speech transcription, environmental sound understanding, or music analysis.

## What we want to do
Introduce a route-aligned capability taxonomy in AbstractCore and migrate the
framework to use it for default coverage, catalog filtering, and error messages.

## Why
Users should see accurate, explainable defaults:

- `input.voice`: speech transcription and speech-focused audio analysis.
- `input.sound`: environmental sound, SFX, and audio scene captioning.
- `input.music`: genre, instruments, mood, vocals, structure, and music
  captioning.
- `output.voice`: TTS.
- `output.sound`: SFX / text-to-audio generation.
- `output.music`: music generation.

## Requirements
- Add an explicit route-keyed capability shape to the model registry. Proposed
  field name: `capability_routes`.

  ```json
  {
    "capability_routes": {
      "input": ["text", "image", "video", "voice", "sound", "music"],
      "output": ["text", "image", "video", "voice", "sound", "music"],
      "embedding": ["text", "image"]
    }
  }
  ```

- Field presence means that route is supported. Do not add `supported: true`
  objects, task-tag lists, or empty arrays.
- Raw model registry entries describe native model route suitability only. They
  must not store effective-row `source`, `status`, `action`, `configured`,
  `covered_by`, or readiness fields. Those belong to Core/Gateway effective
  defaults and catalog/readiness APIs.
- Route keys must normalize through the same kind/modality vocabulary as
  `capability_route_key()`: `input`, `output`, `embedding`, `rerank` crossed with
  Core modalities such as `text`, `image`, `video`, `voice`, `sound`, `music`,
  and `scene3d`.
- Task or evidence detail belongs in `notes`, `source`, or later structured
  evidence metadata, not in `capability_routes`.
- Keep `vision_support`, `audio_support`, and `video_support` available as
  derived/backward-compatible fields until all call sites are migrated.
- Keep `audio_input_capabilities` as a temporary compatibility hint only. New
  route-aware code should read normalized `capability_routes`.
- Do not let `input.voice` imply `input.sound` or `input.music`.
- `input.music` belongs in ADR-0035 and `iter_capability_default_specs()` only
  after the helper layer exists, so music analysis can be configured separately
  from speech transcription and SFX/audio-scene understanding.
- Keep route-default `output.text` derived from `input.text`. The model
  capability helper may expose `output.text` as a normalized filtering view, but
  the implementation must avoid manual duplicate fields drifting.
- Preserve existing Gateway/Flow behavior for configured rows during migration.
- Add tests that fail if an STT-only model is marked sound/music capable.

## Suggested implementation
- Phase 0, schema and normalizer:
  - Add `abstractcore/abstractcore/assets/model_capabilities.schema.json`.
  - Extend `abstractcore/tests/assets/test_model_capabilities_schema.py` so the
    current v0 shape and the new optional `capability_routes` shape are both
    validated.
  - Add a Core-owned normalizer in the provider/model capability layer, for
    example `get_model_capability_routes(model)`,
    `model_supports_capability_route(model, route)`, and
    `derive_legacy_capability_flags(record)`.
  - Derive routes from legacy fields when `capability_routes` is absent so there
    is no behavior change in the first pass.
- Phase 1, representative records:
  - Add source-backed `capability_routes` for representative text, VLM,
    embedding, STT/audio, sound/music-understanding, generated-media, and omni
    records.
  - Add derivation tests proving broad booleans match normalized compatibility
    views for records that declare routes.
- Phase 2, route-aware discovery:
  - Extend model filtering helpers and `/v1/models` with route-aware filters
    while preserving `input_type` and `output_type`.
  - Move Gateway/Core catalog decisions from raw `audio_support` to route helpers.
- Phase 3, `input.music`:
  - Revise ADR-0035 and `iter_capability_default_specs()` to add `input.music`
    after the schema/helper tests prove route separation. Completed in this item.
- Phase 4, consumer migration:
  - Migrate media policy, handlers, provider discovery, CLI output, and tests away
    from raw broad-boolean reads where route-level meaning matters.
  - Keep compatibility getters until downstream packages no longer depend on the
    old fields.

## Scope
- AbstractCore model capability schema asset, normalization, tests, and docs.
- Gateway Console route/default display and filtering as needed.
- Runtime/Flow only where they consume the effective capabilities.

## Non-goals
- Do not rewrite every provider class in the first pass if a normalization
  helper can safely bridge old fields.
- Do not require hand-authored `capability_routes` for all 233 model entries in
  the first schema pass if that would force unsupported guesses. Final v1
  coverage is required, but conservative omissions are better than false claims.
- Do not make nested boolean `input_capabilities` / `output_capabilities` the
  long-term shape; it would duplicate the existing route-key vocabulary.
- Do not put default-row source/status/action metadata in
  `model_capabilities.json`; the registry is not a readiness or acquisition
  catalog.
- Do not add a new package such as `abstractsound` until concrete backend
  implementation pressure exists.
- Do not auto-select large local audio models as universal defaults.

## Dependencies and related tasks
- `docs/backlog/completed/0174_audio_understanding_model_registry.md`
- `docs/adr/0035-capability-routing-defaults.md`
- `docs/backlog/completed/0172_explicit_multimodal_default_fallback_routing.md`
- `docs/backlog/proposed/multimodal-capabilities/0176_multimodal_model_acquisition_guidance.md`

## Expected outcomes
- The framework can answer "can this model understand speech?", "can it
  understand SFX?", and "can it understand music?" separately.
- The registry has a documented JSON Schema, and every model entry is validated
  consistently instead of relying on informal field additions.
- Gateway Console no longer has to infer audio route suitability from one
  `audio_support` bit.
- Core direct users can configure `input.sound` and `input.music` with
  route-appropriate models.
- Old code paths keep working until the migration is completed.

## Validation
- Registry schema tests for `model_capabilities.schema.json` plus the existing
  Python invariants.
- Unit tests for normalized `capability_routes` and derived legacy booleans.
- Core media-policy tests proving STT-only models do not satisfy
  `input.sound` or `input.music`.
- `/v1/models` and provider filtering tests proving route filters can distinguish
  `input.voice`, `input.sound`, `input.music`, `output.text`, and
  `embedding.text`.
- Gateway Console tests proving route-specific audio rows expose the correct
  provider/model candidates.
- Suggested focused commands:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
    abstractcore/tests/assets/test_model_capabilities_schema.py \
    abstractcore/tests/providers/test_model_capabilities.py \
    abstractcore/tests/server/test_model_capability_filtering.py -q
  ```

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
    abstractcore/tests/media_handling/test_audio_policy.py \
    abstractcore/tests/media_handling/test_video_policy.py \
    abstractcore/tests/media_handling/test_provider_handlers.py -q
  ```

## Progress checklist
- [x] Add `model_capabilities.schema.json` and keep the Python schema tests as
      semantic invariants.
- [x] Add capability-route normalization helpers and legacy-flag derivation.
- [x] Add source-backed route records for representative text, VLM, embedding,
      STT/audio, sound, music, and omni models; generated-media model catalogs
      remain capability-plugin owned.
- [x] Migrate Core model filtering and `/v1/models` to route-aware helpers while
      keeping broad filter compatibility.
- [ ] Migrate Core media policy and capability checks to helpers where route
      specificity matters.
- [x] Add `input.music` to ADR-0035, route specs, Core CLI, Gateway Console, and
      route-specific filtering after helper tests pass.
- [x] Update Gateway Console and docs.

## Guidance for the implementing agent
Treat route-keyed `capability_routes` as the intended authoritative model.
Treat old booleans as compatibility views. Preserve behavior until tests prove
every route-sensitive consumer uses the precise helper APIs.

## Completion report

Date: 2026-06-03

Summary:
- Added route-keyed `capability_routes` support to AbstractCore model metadata,
  including schema validation and route helper APIs.
- Preserved legacy `input_type` and `output_type` filtering while adding
  `capability_route` filters for Core Server `/v1/models`.
- Threaded route filters through provider discovery, AbstractRuntime's
  AbstractCore discovery facade, Gateway discovery endpoints, and Gateway
  Console defaults catalog lookups.
- Added representative route records for text/VLM/video, audio-understanding,
  omni, and text-embedding models. Generated media provider readiness remains
  on capability plugin catalogs, not in the raw model registry.

Key files/symbols:
- `abstractcore/abstractcore/assets/model_capabilities.json`
- `abstractcore/abstractcore/assets/model_capabilities.schema.json`
- `abstractcore/abstractcore/providers/model_capabilities.py`
- `abstractcore/abstractcore/server/app.py`
- `abstractruntime/src/abstractruntime/integrations/abstractcore/discovery_queries.py`
- `abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py`
- `abstractgateway/src/abstractgateway/routes/gateway.py`
- `abstractgateway/src/abstractgateway/console.py`

Docs updated:
- `abstractcore/abstractcore/assets/README.md`
- `abstractcore/docs/server.md`
- `abstractcore/docs/capabilities.md`
- `abstractcore/README.md`
- `abstractruntime/docs/integrations/abstractcore.md`
- `abstractgateway/docs/configuration.md`
- `abstractgateway/README.md`
- `docs/configuration.md`

Validation:

```bash
  PYTHONPATH=abstractcore:abstractruntime/src:abstractgateway/src pytest -q \
    abstractcore/tests/assets/test_model_capabilities_schema.py \
    abstractcore/tests/providers/test_model_capabilities.py \
    abstractcore/tests/config/test_capability_defaults_config.py \
    abstractcore/tests/server/test_model_capability_filtering.py \
    abstractcore/tests/providers/test_provider_model_discovery_base_url_unit.py \
    abstractruntime/tests/test_abstractcore_discovery_facade.py \
    abstractgateway/tests/test_gateway_discovery_endpoints.py \
    abstractgateway/tests/test_gateway_console.py \
    abstractgateway/tests/test_gateway_provider_endpoint_profiles.py
```

Result: 117 passed, 11 warnings.

Residual follow-ups:
- Migrate route-sensitive media policy/handlers from raw booleans to route
  helpers where the distinction affects behavior.
- Keep generated-media acquisition/download guidance in item 0176 and capability
  plugin catalogs, not in `model_capabilities.json`.
