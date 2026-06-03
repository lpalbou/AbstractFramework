# Multimodal Capabilities Planned Track

This track collects planned work that tightens AbstractFramework's multimodal
capability contract across AbstractCore, AbstractGateway, AbstractRuntime, and
AbstractFlow.

The immediate focus is audio input clarity. The framework already separates
speech transcription (`input.voice`) from non-speech audio understanding
(`input.sound`), and generated speech/sound/music outputs are already separate
routes. The remaining work is to make the model registry and route schema
explicit enough that Gateway Console, Flow nodes, Core direct usage, and future
`generate(request, output=...)` calls can make correct provider/model choices
without hidden fallbacks.

## Reading order

1. `0175_multimodal_capability_taxonomy_schema.md`

Completed predecessor:
- `docs/backlog/completed/0174_audio_understanding_model_registry.md`

## Related decisions and docs

- `docs/adr/0035-capability-routing-defaults.md`
- `docs/backlog/completed/0172_explicit_multimodal_default_fallback_routing.md`
- `docs/backlog/completed/0173_core_provider_endpoint_profiles.md`
- `abstractcore/abstractcore/assets/model_capabilities.json`
- `abstractcore/abstractcore/config/capability_defaults.py`
- `abstractgateway/src/abstractgateway/console.py`

## Non-goals

- Do not make Gateway own a second capability schema.
- Do not silently treat any speech transcription model as a sound or music
  understanding model.
- Do not auto-download large local models as part of capability defaults.
