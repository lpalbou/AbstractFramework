# Multimodal Capabilities Track

This track collects planned work that tightens AbstractFramework's multimodal
capability contract across AbstractCore, AbstractGateway, AbstractRuntime, and
AbstractFlow.

The schema-first capability clarity slice completed on 2026-06-03. The framework already
separates speech transcription (`input.voice`) from non-speech audio
understanding (`input.sound`), and generated speech/sound/music outputs are
already separate routes. Core now has a route-keyed `model_capabilities.json`
contract, route normalizer, route-aware `/v1/models`, Runtime forwarding, and
Gateway Console model-discovery filters.

Remaining work should be split into focused follow-ups, especially media-policy
migration where route specificity affects behavior and any decision to promote
`input.music` into persisted default routes.

## Reading order

1. `0175_multimodal_capability_taxonomy_schema.md`

Completed predecessor:
- `docs/backlog/completed/0174_audio_understanding_model_registry.md`

## Related decisions and docs

- `docs/adr/0035-capability-routing-defaults.md`
- `docs/adr/0028-capabilities-plugins-and-library-framework-modes.md`
- `docs/backlog/completed/0172_explicit_multimodal_default_fallback_routing.md`
- `docs/backlog/completed/0173_core_provider_endpoint_profiles.md`
- `abstractcore/abstractcore/assets/model_capabilities.json`
- `abstractcore/abstractcore/assets/model_capabilities.schema.json`
- `abstractcore/tests/assets/test_model_capabilities_schema.py`
- `abstractcore/abstractcore/providers/model_capabilities.py`
- `abstractcore/abstractcore/config/capability_defaults.py`
- `abstractgateway/src/abstractgateway/console.py`

## Non-goals

- Do not make Gateway own a second capability schema.
- Do not add nested boolean `input_capabilities` / `output_capabilities` as a
  second vocabulary beside route keys such as `input.sound` and `output.music`.
- Do not store effective default-row source/status/action metadata in
  `model_capabilities.json`; that belongs to Core/Gateway effective defaults,
  provider catalogs, and readiness surfaces.
- Do not silently treat any speech transcription model as a sound or music
  understanding model.
- Do not auto-download large local models as part of capability defaults.
