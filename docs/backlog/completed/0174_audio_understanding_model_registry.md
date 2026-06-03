# Planned: Audio understanding model registry coverage

## Metadata
- Created: 2026-06-02
- Status: Completed
- Completed: 2026-06-02

## ADR status
- Governing ADRs: ADR-0035
- ADR impact: None expected. This fills model registry data under the existing
  capability routing policy.

## Context
Gateway Console now exposes explicit multimodal capability defaults. Current
defaults can reasonably use `qwen/qwen3.6-35b-a3b` for `input.text`, with
`input.image` and `input.video` covered by text when AbstractCore confirms the
model is vision/video-capable. That does not cover audio.

Online model-card checks show that speech, sound-event understanding, and music
understanding are not equivalent:

- Qwen3.6 35B A3B is documented as text/image/video input, not audio input:
  https://catalog.ngc.nvidia.com/orgs/nim/teams/qwen/models/qwen3.6-35b-a3b
- Qwen2-Audio is an audio-specialized Qwen model for speech, sounds, music, and
  audio QA: https://qwen2.org/audio/
- Qwen2.5-Omni is an omni model with audio support:
  https://huggingface.co/Qwen/Qwen2.5-Omni-7B
- Qwen3-Omni Captioner is the stronger open candidate for arbitrary audio
  captioning / understanding:
  https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Captioner

## Current code reality
- `abstractcore/abstractcore/assets/model_capabilities.json` has broad
  `audio_support`, `vision_support`, and `video_support` booleans.
- The current registry includes Qwen3.6 variants with `audio_support: false`
  and image/video support.
- The registry does not currently include `qwen2-audio-7b-instruct`,
  `qwen2.5-omni-7b`, or `qwen3-omni-30b-a3b-captioner`.
- `abstractcore/abstractcore/assets/README.md` requires source attribution and
  warns not to guess capabilities.
- `abstractcore/tests/assets/test_model_capabilities_schema.py` validates the
  registry shape.

## Problem
The user can configure `input.sound`, but the model registry lacks the most
important open audio-understanding candidates. That makes the Gateway Console
and Core defaults less useful and risks treating generic `audio_support` as a
single capability.

## What we want to do
Add high-confidence audio-understanding model records and aliases to
AbstractCore's canonical model registry, with clear source notes and explicit
audio capability semantics.

## Why
Users need a truthful way to configure non-speech audio understanding and music
understanding without confusing STT models, SFX generators, and music generators.

## Requirements
- Add registry coverage for:
  - `qwen3-omni-30b-a3b-captioner`
  - `qwen2.5-omni-7b`
  - `qwen2-audio-7b-instruct`
- Keep Qwen3.6 variants marked as not audio-capable unless official sources
  show otherwise.
- Mark Qwen3-Omni Captioner as the preferred open candidate for
  `input.sound` and `input.music`, while documenting memory/serving cost.
- Include aliases likely to appear from Hugging Face, LM Studio, Ollama, and
  OpenAI-compatible endpoints.
- Record source URLs in `notes` or source metadata.
- Keep generated-output models separate: this item is about audio input
  understanding, not `output.sound` or `output.music` generation.

## Suggested implementation
- Update `abstractcore/abstractcore/assets/model_capabilities.json` with the
  three audio-understanding candidates and aliases.
- Add focused tests in `abstractcore/tests/providers/` or
  `abstractcore/tests/assets/` proving:
  - Qwen3.6 remains audio false.
  - Qwen2-Audio / Qwen2.5-Omni / Qwen3-Omni resolve as audio-capable.
  - Alias lookup resolves common endpoint names to canonical records.
- Update capability docs with the distinction between speech, sound, and music
  understanding.

## Scope
- AbstractCore model registry and registry tests.
- Core/Gateway docs describing recommended audio-understanding candidates.
- No provider-specific runtime implementation beyond registry metadata.

## Non-goals
- Do not auto-download or load these models.
- Do not set Qwen3-Omni as a hard framework default; it is too large for many
  systems.
- Do not infer sound/music understanding from STT model names.

## Dependencies and related tasks
- `0175_multimodal_capability_taxonomy_schema.md`
- `docs/backlog/completed/0172_explicit_multimodal_default_fallback_routing.md`
- `docs/adr/0035-capability-routing-defaults.md`

## Expected outcomes
- Gateway Console can discover or validate audio-capable candidate models when
  a provider exposes them.
- Core direct users can select these models as `input.sound` and later
  `input.music` defaults.
- Qwen3.6 remains the recommended text/image/video default, not an audio input
  default.

## Validation
- `python -m pytest abstractcore/tests/assets/test_model_capabilities_schema.py`
- Focused provider/model registry tests for the new aliases.
- Manual lookup smoke:
  `python - <<'PY' ... get_model_capabilities('qwen3-omni-30b-a3b-captioner')`

## Progress checklist
- [x] Add source-backed model records and aliases.
- [x] Add registry tests.
- [x] Update Core/Gateway capability docs.
- [x] Verify Gateway Console route model lists can show these records when the
      configured provider exposes them.

## Guidance for the implementing agent
Do not guess capabilities. Prefer official model cards and provider docs. If a
model only performs STT, it belongs under `input.voice`, not `input.sound` or
`input.music`.

## Completion report

Date: 2026-06-02

Summary:
- Added source-backed audio-understanding entries to AbstractCore's canonical
  model registry:
  - `qwen3-omni-30b-a3b-instruct`
  - `qwen3-omni-30b-a3b-captioner`
  - `qwen2.5-omni-7b`
  - `qwen2-audio-7b-instruct`
  - `audio-flamingo-3-hf` as a non-commercial research candidate
  - `moss-audio-8b-thinking` as an Apache-2.0 candidate
- Added `audio_input_capabilities` as schema-validated metadata with the
  allowed values `speech`, `sound`, and `music`.
- Kept Qwen3.6 variants as `audio_support: false`.
- Removed duplicate/case-only alias risks while validating that there are no
  duplicate model keys in the JSON registry.
- Corrected Qwen3.6 MTP GGUF packaged variants so they no longer advertise
  native image/video support. The base Qwen3.6 BF16/FP8 entries remain
  image/video-capable; the Unsloth MTP GGUF README says `--mmproj` is not yet
  supported with MTP, so those packaged variants are treated as text-only for
  native media routing.

Source review:
- Qwen3-Omni Captioner: HF card says audio input only, text output only,
  one audio input per inference, speech/environmental/music/cinematic SFX
  coverage, and 30-second best-practice clips.
- Qwen2.5-Omni: HF card and config confirm text/image/audio/video input and
  speech/sound/music benchmark categories.
- Qwen2-Audio: HF card confirms voice-chat and audio-analysis modes, including
  non-speech sound examples.
- Unsloth Qwen3.6 MTP GGUF: HF README confirms `--mmproj` is not yet supported
  with MTP, so those two packaged variants should not route native image/video.
- Extended HF scan found Kimi-Audio, Step-Audio R1/R1.1, Voxtral, MiniCPM-o,
  Audio Flamingo 3, and MOSS-Audio. Only Audio Flamingo 3 and MOSS-Audio were
  included in this pass because their model cards gave clear speech/sound/music
  semantics. Audio Flamingo 3 is explicitly marked non-commercial research.

Files touched:
- `abstractcore/abstractcore/assets/model_capabilities.json`
- `abstractcore/abstractcore/assets/README.md`
- `abstractcore/tests/assets/test_model_capabilities_schema.py`
- `abstractcore/tests/providers/test_model_registry_variant_resolution_unit.py`
- `docs/backlog/completed/0174_audio_understanding_model_registry.md`
- `docs/backlog/planned/multimodal-capabilities/README.md`
- `docs/backlog/planned/multimodal-capabilities/0175_multimodal_capability_taxonomy_schema.md`
- `docs/backlog/overview.md`

Validation:
- `PYTHONPATH=abstractcore python -m pytest abstractcore/tests/assets/test_model_capabilities_schema.py abstractcore/tests/providers/test_model_registry_variant_resolution_unit.py -q`
  - Result after reviewer fix: `17 passed in 0.03s`
- Manual lookup smoke via `get_model_capabilities(...)` confirmed:
  - Qwen3-Omni Captioner, Qwen2.5-Omni, Qwen2-Audio, Audio Flamingo 3, and
    MOSS-Audio resolve with `audio_support: true` and
    `audio_input_capabilities: ["speech", "sound", "music"]`.
  - `Qwen/Qwen3.6-35B-A3B` resolves with `audio_support: false`.
  - `unsloth/Qwen3.6-35B-A3B-MTP-GGUF:UD-Q4_K_M` and
    `unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_M` resolve with
    `vision_support: false`, `audio_support: false`, `video_support: false`,
    and `video_input_mode: "none"`.
- Schema tests now include model-key duplicate detection before normal JSON
  loading can silently overwrite duplicate keys.

Residual risks and follow-ups:
- `audio_input_capabilities` is metadata only in this item. Route-specific
  runtime behavior remains owned by `0175_multimodal_capability_taxonomy_schema.md`.
- Model acquisition/download guidance for large local audio models remains owned
  by `0176_multimodal_model_acquisition_guidance.md`.
- Some HF candidates are intentionally not included yet: Kimi-Audio,
  Step-Audio, Voxtral, and MiniCPM-o need route/serving policy review before
  being promoted into the registry or defaults.
