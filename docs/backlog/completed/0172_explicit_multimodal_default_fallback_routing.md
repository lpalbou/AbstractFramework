# Planned: Explicit multimodal default fallback routing

## Metadata
- Created: 2026-06-02
- Status: Completed
- Completed: 2026-06-02

## ADR status
- Governing ADRs: ADR-0035
- ADR impact: Revised ADR-0035 to record explicit `input.voice`/`input.video`
  fallback gates and AbstractFlow's loaded-only Model Residency boundary.

## Context
Gateway Console can configure capability defaults such as `input.voice`,
`input.video`, `output.image`, and `output.music`. AbstractFlow also relies on
blank provider/model pins to mean `Auto (Gateway default)`.

The current execution behavior is not strict enough: Core audio/video policies
can still fall back automatically from installed packages or global `auto`
strategy, and Flow still contains surfaces that treat blank text provider/model
pins as missing values.

## Current code reality
- `abstractcore.config.capability_defaults` defines the route contract.
- `abstractcore.config.manager` derives `output.text` from `input.text` and
  currently covers only `input.image` from `input.text`.
- `abstractcore.providers.base` reads `audio.strategy` and `video.strategy` and
  can fall back to STT or sampled video frames without consulting route defaults.
- `abstractgateway.capability_defaults` scopes Core defaults for Gateway.
- `abstractflow.components.ModelResidencyPanel` still renders a Defaults tab,
  even though defaults now belong in Gateway Console.
- `abstractflow.utils.preflight` still blocks blank provider/model pins on
  LLM/Agent nodes.
- `abstractruntime.visualflow_compiler.visual.executor` has a legacy hard
  missing-provider/model path for LLM calls.

## Problem
Users expect the Multimodal Capabilities table to define fallback routing. If
`input.voice`, `input.video`, or `input.sound` are not configured, the runtime
must not silently fall back just because a package is installed.

Flow should also make Gateway defaults explicit: blank provider/model pins are
valid and must remain switchable after users pick a provider.

## What we want to do
Tighten the Core/Gateway/Runtime/Flow contract so capability route defaults are
the fallback gate, while preserving native model support.

## Why
This makes behavior explainable:

- Core owns capability semantics.
- Gateway scopes and edits the defaults.
- Runtime consumes the effective route without stale pins.
- Flow presents `Auto (Gateway default)` as a deliberate choice.

## Requirements
- Native model support may still process media directly.
- STT fallback requires an explicit `input.voice` default or explicit per-call
  `audio_policy="speech_to_text"`.
- Video frame fallback requires either a model that supports image/video input
  or an explicit `input.video` default.
- `input.video` may be covered by `input.text` when the text model supports
  frames/vision, but that covered row must remain overrideable.
- Blank LLM/Agent provider/model pins must be accepted as Gateway/Core defaults.
- AbstractFlow Model Residency must show only loaded/resident models.
- Generative provider dropdowns must include `Auto (Gateway default)` as the
  first switch-back option.

## Suggested implementation
- Decorate `input.video` in Core defaults with `covered_by=input.text` and
  `overrideable=true` when the text model can process image/video frames.
- In Core provider media preprocessing, consult capability route defaults before
  applying STT or frame fallback.
- Pass configured STT route provider/model into the audio transcription fallback.
- Remove the Flow Model Residency Defaults tab and related editor surface.
- Treat blank provider/model as valid in Flow preflight and legacy runtime LLM
  executor.
- Add explicit blank `Auto (Gateway default)` options to provider dropdowns.

## Scope
- AbstractCore fallback gating and capability default decoration.
- AbstractGateway Console default row override behavior.
- AbstractRuntime legacy LLM executor default handling.
- AbstractFlow Model Residency and node provider/model UX.
- Targeted tests and docs updates.

## Non-goals
- No new Gateway-owned provider/default schema.
- No workflow migration that materializes defaults into saved flows.
- No implementation of the future `generate(request, output=...)` abstraction.
- No broad provider catalog refactor beyond targeted option consistency.

## Dependencies and related tasks
- ADR-0035 capability routing defaults.
- `docs/backlog/completed/0170_core_gateway_capability_defaults_config_convergence.md`
- `docs/backlog/proposed/0169_gateway_console_route_specific_default_catalogs.md`

## Expected outcomes
- Unconfigured audio/video/sound inputs do not get silent fallbacks.
- Configured `input.voice` drives STT fallback.
- `input.video` shows coverage when a vision-capable text default can handle
  frames and remains overrideable.
- Flow runs blank-pin LLM/Agent nodes through Gateway defaults.
- Flow Model Residency lists only provider-resident models.

## Validation
- Core unit tests for `input.video` coverage and audio fallback gating.
- Runtime/Flow tests for blank provider/model defaults.
- Frontend build/type check for changed Flow surfaces.
- Manual browser check for Model Residency and node provider dropdowns.

## Progress checklist
- [x] Patch Core fallback/default behavior.
- [x] Patch Gateway Console row state.
- [x] Patch Runtime/Flow default behavior.
- [x] Run targeted validation.
- [x] Update docs and completion notes.

## Guidance for the implementing agent
Prefer the existing capability-default contract over a new abstraction. If a
fallback cannot be proven from native model support or an explicit route, fail
with a clear configuration error.

## Completion report

### Date

2026-06-02

### Summary

Implemented explicit multimodal fallback routing across Core, Gateway,
Runtime, and Flow:

- `output.text` stays derived from `input.text`.
- `input.image` is covered by `input.text` when the text model is image-capable
  and remains read-only.
- `input.video` is covered by `input.text` when visual-frame support is known,
  but remains overrideable for a dedicated VLM/video route.
- `input.voice` is now the normal STT fallback gate. Installed STT packages do
  not create hidden audio fallback behavior.
- `input.sound` is not used as speech transcription fallback.
- Flow LLM Call and Agent nodes accept blank provider/model pins as
  Gateway/Core defaults.
- Flow generative provider dropdowns expose `Auto (Gateway default)` as the
  first switch-back option.
- Flow Model Residency now shows provider-resident loaded models only; default
  editing lives in Gateway Console and config CLIs.

### Files and symbols touched

- `abstractcore.config.manager`: effective route decoration for `output.text`,
  `input.image`, and `input.video`.
- `abstractcore.providers.base`: audio/video policy gates and explicit
  route-driven STT/video fallback.
- `abstractruntime.integrations.abstractcore.llm_client`: endpoint-profile
  resolver propagation to local Core clients.
- `abstractruntime.visualflow_compiler.visual.executor`: blank LLM provider/model
  runtime-default handling.
- `abstractgateway.hosts.bundle_host`: provider endpoint resolver attachment.
- `abstractgateway.console`: default-row labels/actions for covered and
  overrideable route defaults.
- `abstractflow` Model Residency, Properties Panel, Base Node, and preflight
  utilities.

### Validation

- `python -m py_compile abstractcore/abstractcore/providers/base.py abstractcore/abstractcore/config/manager.py abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py abstractgateway/src/abstractgateway/hosts/bundle_host.py abstractruntime/src/abstractruntime/visualflow_compiler/visual/executor.py`
- `pytest -q abstractcore/tests/config/test_capability_defaults_config.py abstractcore/tests/media_handling/test_audio_policy.py abstractcore/tests/media_handling/test_video_policy.py`
  - Result: 23 passed.
- `PYTHONPATH="$PWD/abstractruntime/src:$PWD/abstractcore:$PWD/abstractgateway/src:$PYTHONPATH" pytest -q abstractruntime/tests/test_visualflow_prompt_only.py abstractruntime/tests/test_provider_endpoint_profile_resolution.py`
  - Result: 8 passed.
- `PYTHONPATH="$PWD/abstractruntime/src:$PWD/abstractcore:$PWD/abstractgateway/src:$PYTHONPATH" pytest -q abstractgateway/tests/test_gateway_provider_defaults.py abstractgateway/tests/test_gateway_console.py`
  - Result: 14 passed.
- `cd abstractflow && npm run build`
  - Result: TypeScript and Vite build completed; Vite kept the existing large
    chunk warning.

### Architecture review notes

The deliberate split is:

- Core owns route schema, model-capability interpretation, and fallback policy.
- Gateway scopes and edits those Core routes per runtime/principal.
- Runtime passes scoped defaults into Core without inventing another defaults
  schema.
- Flow authors workflows and shows Auto/default choices without persisting
  deployment-specific defaults into the flow JSON.

The main tension was whether Gateway should paper over missing fallback routes
because packages are installed. The stricter design won because it makes the
Multimodal Capabilities tab authoritative: if `input.voice` or `input.video`
is unset, there is no hidden fallback except native support by the current
model.

### Documentation updates

- Root capability-routing guide and configuration guide.
- ADR-0035 capability routing defaults.
- AbstractCore centralized configuration docs.
- AbstractGateway configuration and README docs.
- AbstractFlow README, architecture, and web-editor docs.

### Residual risk and follow-up

- Runtime/provider catalogs still need continued cleanup toward a single
  user-facing `generate(request, output=...)` abstraction. That is explicitly
  out of scope here and remains a future design task.
