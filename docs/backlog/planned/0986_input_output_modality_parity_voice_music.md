# 0986 — Input/output modality parity: audio input decomposed into voice and music

> Package: abstractcore, abstractvoice, abstractmusic
> Type: task
> Created: 2026-09-29
> Priority: normal
> Labels: multimodal, input, parity

## Summary

Outputs are decomposed by modality (voice through AbstractVoice, music through AbstractMusic, image/video through AbstractVision, 3D through Abstract3D), but input shows a single "audio" kind: an audio-capable model, or speech-to-text through AbstractVoice. Inputs and outputs should have the same decomposition so users and apps reason about one symmetric set: voice in/out, music in/out, image in/out, video in/out, 3D in/out, documents in, text in/out.

## Why

Operator (2026-09-29): "do we really have 'audio' as input and not also the decomposition voice/music? … we should have parity between input/output." The website's multimodal section exposes the asymmetry.

## Current code reality (2026-09-29)

- AbstractCore media input handles audio through audio-capable models or speech-to-text (AbstractVoice); there is no music-understanding input path (e.g. music captioning/analysis, stem or tempo analysis) and no explicit "voice vs music" input kind. Verify in `abstractcore/media/` and the capability registry before implementing.

## Scope

### In scope

- An explicit input kind per modality mirroring outputs; music input (analysis/captioning through AbstractMusic or a suitable model) and voice input (speech-to-text, speaker features) as distinct capabilities.
- Capability registry, `media=` policy and docs updated so input and output tables line up.

### Out of scope

- New model training.

## Acceptance criteria

- [ ] Documentation shows a symmetric input/output table; each input kind has a working path or a stated "not available yet".
- [ ] Tests for the new input kinds.

## Validation

Hermetic tests with small fixtures; one real run per new input path on cached models.
