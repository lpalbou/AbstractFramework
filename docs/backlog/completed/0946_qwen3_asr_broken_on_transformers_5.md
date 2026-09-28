# 0946 — Qwen3-ASR speech-to-text is broken on Transformers 5.x

> Package: abstractvoice
> Type: task
> Created: 2026-09-27
> Priority: high
> Labels: voice, stt, regression, transformers, next-wave
> Status: completed 2026-09-28 — released in abstractvoice 0.13.0 (tag `v0.13.0` → `1cdd727`)
> Moved: `planned/0946_qwen3_asr_broken_on_transformers_5.md` → `completed/0946_qwen3_asr_broken_on_transformers_5.md` on 2026-09-28

## Summary

Local Qwen3-ASR speech-to-text very likely fails in current framework installs: the vendored model code is
incompatible with the Transformers 5.x versions that framework installs resolve (5.17 at the time of writing).
Three separate breaks; all predate abstractvoice 0.12.0. Fix them, prove the path end to end with the real
checkpoint, and gate it in CI like Qwen3-TTS.

## Why

Found by the abstractvoice release worker on 2026-09-27 while fixing the same class of bug in Qwen3-TTS.
Operator: "you should have fix those before releasing abstractcore, otherwise we need a full release. create
yet another backlog planned item." Must be fixed before the next AbstractCore release.

## Current code reality (abstractvoice 0.12.0, 533aea3)

- `abstractvoice/qwen3_asr/modeling_qwen3_asr.py:1031` passes `input_embeds=` and `cache_position=` to the mask
  helper; Transformers ≥ 5.9 raises `TypeError: unexpected keyword argument 'input_embeds'` (then the same
  `cache_position` error Qwen3-TTS had). Works on 5.8.1.
- `Qwen3ASRConfig()` raises `AttributeError: no attribute 'thinker_config'` on every 5.x: the parent
  constructor asks for the text config before `thinker_config` is set.
- The rotary embedding has no `compute_default_rope_parameters`, which 5.x weight init calls for rope type
  "default".
- Reachable from `stt-hf` and the apple / gpu / all-* extras (loaded via `AutoModel.from_pretrained`).
- Qwen3-TTS got the equivalent fix + a CI job (`test-qwen3-tts`, floor 5.9.0 and latest) in 0.12.0 — reuse it.

## Scope

### In scope

- Port the mask call (no `cache_position`/`input_embeds` per the 5.9+ signature), fix the config construction
  order, add `compute_default_rope_parameters`; record local modifications in the vendored file headers.
- A weight-free test that builds a tiny ASR model, saves and reloads it, and runs a forward pass; a CI job
  installing CPU torch + `.[test,stt-hf]` on the Transformers floor and latest.
- One real-checkpoint check (~2 GB download, allowed for this item) transcribing a known clip.

### Out of scope

- New STT engines; changing the default STT engine.

## Acceptance criteria

- [ ] Real checkpoint transcribes a reference clip on Transformers floor and latest (evidence: text + timing).
- [ ] Weight-free test + CI job green; each fix goes RED when reverted.
- [ ] Released in the next wave BEFORE abstractcore (voice → core → … → root).

## Receipts

- Voice worker report 2026-09-27 (`untracked/release-2026-09-27/voice/`).

## Implementation (wave 2, 2026-09-28) — pending release

abstractvoice branch `wave2/voice` (worktree `untracked/wave2/voice`), local commits, no version bump;
stays planned until the release lands: `ccf64f0` Qwen3-ASR runs on Transformers 5.x, CI tests it on
the floor and the latest Transformers; `339c09f` docs and CHANGELOG [Unreleased]. Evidence and the
real-checkpoint proof: the voice worker's report (untracked/wave2/voice).

## Completion (2026-09-28)

Released in abstractvoice 0.13.0 (`ccf64f0` and the follow-up fixes up to `1cdd727`; CI and Release green, PyPI visible).
Qwen3-ASR runs on Transformers 5.4 through current releases, and refuses older Transformers with a clear error; the real
checkpoint proof is `untracked/wave2/voice/asr-proof.md`. Pinned by root abstractframework 0.6.0 (`abstractvoice==0.13.0`).
Follow-ups: [0968](../planned/0968_voice_follow_ups_after_0_13_0.md).
