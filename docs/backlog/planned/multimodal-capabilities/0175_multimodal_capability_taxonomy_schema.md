# Planned: Multimodal capability taxonomy and schema

## Metadata
- Created: 2026-06-02
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0035
- ADR impact: May revise ADR-0035 if `input.music` is promoted into the route
  matrix.

## Context
The framework already routes user-facing defaults through keys such as
`input.voice`, `input.sound`, `output.voice`, `output.sound`, and
`output.music`. However, the canonical model registry still uses broad boolean
fields such as `audio_support`, `vision_support`, and `video_support`.

That broad shape was acceptable when the only audio distinction was "model can
receive audio at all". It is no longer precise enough now that Gateway Console
can configure fallbacks and users expect clear behavior for speech, SFX/audio
scene understanding, and music analysis.

## Current code reality
- `abstractcore/abstractcore/config/capability_defaults.py` includes
  `input.sound` but not `input.music`.
- `docs/adr/0035-capability-routing-defaults.md` lists `music` as a modality
  but only defines `output.music`, not `input.music`.
- `abstractcore/abstractcore/assets/model_capabilities.json` uses
  `audio_support` as a coarse boolean.
- `abstractcore/abstractcore/providers/model_capabilities.py` exposes
  `ModelInputCapability.AUDIO`, which is too broad for route-specific catalog
  filtering because it cannot distinguish STT, SFX/audio-scene understanding,
  and music understanding.
- `abstractcore/abstractcore/media/capabilities.py`,
  `abstractcore/abstractcore/media/handlers/*`, provider code, and tests read
  `audio_support` directly.
- `abstractgateway/src/abstractgateway/console.py` maps `input.sound` to an
  audio-input text catalog, and the Sandbox handles generated voice, sound, and
  music separately.

## Decision question
Should audio input capability be modeled as one broad `audio_support` boolean,
or as explicit voice/sound/music input capabilities that preserve backward
compatibility?

## Architecture alternatives

### Alternative A: Keep `audio_support` only
Steelman: smallest change and lowest code churn. Existing media handlers already
know how to gate native audio input.

Critique: it cannot tell whether a model can transcribe speech, caption sound
events, analyze music, or all three. It also lets STT models look equivalent to
audio-scene models.

### Alternative B: Replace booleans with a full capability matrix immediately
Steelman: cleanest long-term data model; every model has explicit input/output
capabilities.

Critique: high migration risk. Many existing call sites and tests read
`audio_support`, `vision_support`, and `video_support`. A hard replacement would
create unnecessary breakage across Core, Runtime, Gateway, Flow, and docs.

### Alternative C: Add explicit sub-capabilities and derive legacy booleans
Steelman: gives the framework accurate capability decisions while keeping old
callers working during migration.

Critique: temporary duplication can drift unless tests enforce derivation rules
and docs clearly identify the new fields as authoritative.

## Synthesis
Use Alternative C. Add precise capability fields, keep broad booleans as derived
compatibility fields, and migrate route/default decisions to the precise fields.

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
- Add an explicit capability shape to the model registry. Candidate shape:

  ```json
  {
    "input_capabilities": {
      "text": true,
      "image": true,
      "video": true,
      "voice": false,
      "sound": false,
      "music": false,
      "scene3d": false,
      "document": false
    },
    "output_capabilities": {
      "text": true,
      "image": false,
      "video": false,
      "voice": false,
      "sound": false,
      "music": false,
      "scene3d": false
    }
  }
  ```

- Keep `vision_support`, `audio_support`, and `video_support` available as
  derived/backward-compatible fields until all call sites are migrated.
- Do not let `input.voice` imply `input.sound` or `input.music`.
- Add `input.music` to ADR-0035 and `iter_capability_default_specs()` after the
  helper layer exists, so music analysis can be configured separately from
  speech transcription and SFX/audio-scene understanding.
- Keep `output.text` derived from `input.text`.
- Preserve existing Gateway/Flow behavior for configured rows during migration.
- Add tests that fail if an STT-only model is marked sound/music capable.

## Suggested implementation
- Add schema normalization helpers in AbstractCore that return precise
  route-level capability sets and derived legacy booleans.
- Update registry schema tests to accept and validate the new shape.
- Migrate capability checks in media handlers and Gateway effective defaults
  from raw `audio_support` to route-specific helpers.
- Add `input.music` after the helper layer exists and docs/ADR are revised.
- Update Gateway Console labels and route catalogs so `input.sound` and
  `input.music` are distinct when both exist.

## Scope
- AbstractCore model capability schema, normalization, tests, and docs.
- Gateway Console route/default display and filtering as needed.
- Runtime/Flow only where they consume the effective capabilities.

## Non-goals
- Do not rewrite every provider class in the first pass if a normalization
  helper can safely bridge old fields.
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
- Gateway Console no longer has to infer audio route suitability from one
  `audio_support` bit.
- Core direct users can configure `input.sound` and, if added, `input.music`
  with route-appropriate models.
- Old code paths keep working until the migration is completed.

## Validation
- Registry schema tests for precise input/output capabilities.
- Unit tests for derived legacy booleans.
- Core media-policy tests proving STT-only models do not satisfy
  `input.sound` or `input.music`.
- Gateway Console test proving route-specific audio rows expose the correct
  provider/model candidates.

## Progress checklist
- [ ] Add capability normalization helper and schema validation.
- [ ] Add source-backed capability records for representative text, VLM, STT,
      sound, music, and omni models.
- [ ] Migrate Core capability checks to helpers.
- [ ] Add `input.music` to ADR-0035, route specs, Core CLI, Gateway Console,
      and route-specific filtering after helper tests pass.
- [ ] Update Gateway Console and docs.

## Guidance for the implementing agent
Treat precise capabilities as authoritative and old booleans as compatibility
views. Preserve behavior until tests prove every consumer uses the precise
route helpers.
