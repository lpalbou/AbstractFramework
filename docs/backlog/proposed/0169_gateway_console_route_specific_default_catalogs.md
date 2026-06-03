# Proposed: Gateway Console route-specific default catalogs

## Metadata
- Created: 2026-06-01
- Status: Proposed
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0035
- ADR impact: None expected unless the route-catalog contract changes.

## Context
Gateway Console Defaults now maps capability routes to configured provider
connections and discovered models. This fixes the larger UX problem where
Defaults exposed provider URLs/API keys and generic provider choices before the
Gateway had configured credentials.

Gateway already exposes route-specific catalog endpoints for embeddings,
vision, voice, and music, and AbstractFlow uses several of those specialized
catalogs for node authoring.

## Problem
The Console defaults modal currently asks the selected provider for its generic
model list. That is clean enough for text and custom provider profiles, but it
does not fully express route-specific filtering for capabilities such as
`embedding.text`, `output.voice`, `input.voice`, `output.image`, or
`output.sound`.

## What we want to do
Decide and implement the smallest route-specific catalog adapter for Gateway
Console Defaults, reusing existing Gateway catalog routes where possible.

## Why
Defaults should remain simple, but they should not let a user accidentally pick
a text chat model for a voice, music, image, or embedding capability when a
better route catalog exists.

## Requirements
- Keep provider URL/API key configuration in the Providers tab only.
- Keep Defaults as provider + model selection only.
- Reuse existing Gateway catalog endpoints before adding new API surface.
- Preserve configured legacy rows even when their provider/model is no longer
  discoverable.
- Do not ask users to classify model capabilities manually; AbstractCore remains
  the capability metadata owner.

## Suggested implementation
Add a small route-to-catalog mapping in Gateway Console:

- `embedding.text` -> `/api/gateway/embeddings/models`
- `output.voice` -> `/api/gateway/audio/speech/models`
- `input.voice` -> `/api/gateway/audio/transcriptions/models`
- `output.sound` -> `/api/gateway/audio/music/models?task=text_to_audio`
- `output.music` -> `/api/gateway/audio/music/models?task=text_to_music`
- `output.image` / `output.video` -> `/api/gateway/vision/provider_models`
  with the appropriate task when the provider supports that catalog
- fallback -> `/api/gateway/discovery/providers/{provider}/models`

If existing endpoints cannot return a consistent `items`/`models` list for a
route, normalize that first in Gateway rather than hard-coding package-specific
response parsing in the console.

## Validation
- Console unit test that each route family calls the expected catalog URL.
- Regression test that a configured legacy row remains visible/editable when
  the route catalog cannot rediscover it.
- Headless UI check for text, embedding, image, voice, and music default modals.
