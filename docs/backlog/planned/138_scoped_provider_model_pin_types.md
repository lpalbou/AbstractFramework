# 138 - Scoped provider pins with generic model pins across AbstractFramework

Status: planned/started
Owner: AbstractFramework
Created: 2026-05-15

## Problem

VisualFlow needs to distinguish text, image, voice, and future media provider catalogs. A generic `provider` pin is not enough because it cannot tell the UI which Gateway catalog to query.

Model values, however, do not need separate visual pin types. Once a provider is selected, the model catalog is scoped by that provider and by the node/input context. Separate `model_text`, `model_image`, and `model_voice` types add complexity without improving user-facing behavior.

## Decision

Use scoped provider pin types and a generic model pin:

- `provider_text`: text/LLM providers.
- `provider_image`: image-generation providers.
- `provider_voice`: TTS/STT/voice providers.
- `model`: model id/name, scoped by the selected provider and node/input context.
- Future: `provider_music`, `provider_video`; keep `model` generic.

Legacy `provider` remains accepted for old text flows. Legacy `model_text`, `model_image`, and `model_voice` remain accepted as compatibility aliases only; new built-in nodes and user-created pins should use `model`.

## Compatibility rules

- `provider_text`, `provider_image`, and `provider_voice` do not connect across modalities.
- Legacy `provider` may connect to scoped provider pins for backward compatibility.
- `model` connects to any model value. The catalog lookup is contextual, not encoded in the pin type.
- Legacy `model_*` aliases connect to `model` and each other for old saved flows, but should not be shown as normal authoring choices.
- `string` remains allowed into provider/model pins for advanced dynamic values.

## Layering

AbstractCore owns capability and catalog contracts by modality. AbstractGateway exposes those contracts as text, vision, and voice catalog routes. AbstractRuntime consumes existing runtime keys (`provider`, `model`, `image_provider`, `image_model`, `tts_provider`, `tts_model`, `stt_provider`, `stt_model`). AbstractFlow owns the VisualFlow pin taxonomy and uses scoped provider pins to choose the right Gateway catalog for a generic `model` pin.

## Implementation plan

1. Keep `provider_text`, `provider_image`, and `provider_voice` in the VisualFlow schema and frontend type system.
2. Change built-in Agent/LLM/media nodes to emit generic `model` pins while preserving existing pin IDs.
3. Keep runtime and gateway compatibility for legacy `model_*` aliases.
4. Update frontend connection validation so provider pins are scoped but model pins are generic.
5. Update launch/run forms so `provider_image` uses the image catalog, `provider_voice` uses voice/STT catalogs, and the associated generic `model` pin uses the selected provider's scoped catalog.
6. Keep existing AbstractCore/Gateway endpoints unchanged; the distinction is route/capability based, not a Core pin-type concern.

## Non-goals

- Renaming runtime payload fields.
- Teaching AbstractCore about VisualFlow pin names or colors.
- Removing old `model_*` aliases before a migration window.
- Adding music/video before their capability catalogs are standardized.

## Validation checklist

- VisualFlow validation accepts scoped provider pins and generic model pins.
- Existing saved flows with legacy `model_*` pins still load.
- Built-in media nodes no longer emit `model_image` / `model_voice`.
- Run Flow launch forms query the correct provider/model catalogs for text, image, and voice inputs.
- Gateway input schemas serialize scoped provider pins and generic model pins as strings.
