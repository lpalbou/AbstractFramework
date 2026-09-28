# 0968 — Voice follow-ups after AbstractVoice 0.13.0

> Package: abstractvoice, abstractruntime
> Type: task
> Created: 2026-09-28
> Priority: normal
> Labels: voice, errors, transformers, floors

## Summary

Items found by the voice 0.13.0 tag gates that did not block the release: error wording and status accuracy where a provider or engine cannot run, and an inconsistent Transformers floor between profiles and Qwen3-TTS.

## Why

Ledger (voice RELEASED line): "runtime local_list_tts_models should copy catalog unavailable_reason into error; voice_catalog openai-compatible/auto raise when default engine is unkeyed openai; 'openai:tts-1' form message; engine_runtime reports Qwen3-TTS installed regardless of transformers version; profile floors >=5.4 vs TTS 5.9."

## Current code reality (2026-09-28)

- abstractvoice 0.13.0 (`1cdd727`): profile extras floor `transformers>=5.4.0`, the `qwen3-tts` extra `transformers>=5.9.0,<6` (pyproject lines 65/93/155/164/178).
- abstractruntime 0.7.0 `integrations/abstractcore/discovery_queries.py:1136` `local_list_tts_models` returns `error=str(exc)` without the catalog's `unavailable_reason`.

## Scope

### In scope

- `voice_catalog(provider='openai-compatible'|'auto')` does not raise when the default engine is an unkeyed OpenAI engine; it reports the reason.
- A clear message for the `openai:tts-1` (provider:model) form.
- `engine_runtime_status('qwen3_tts')` reports not installed when Transformers is below the TTS floor.
- One consistent Transformers floor story across the profile extras and the TTS extra.
- AbstractRuntime `local_list_tts_models` carries `unavailable_reason` into its error.

### Out of scope

- New engines.

## Acceptance criteria

- [ ] Each point has a test that is RED on 0.13.0 / runtime 0.7.0.

## Validation

Per point, a unit test.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
