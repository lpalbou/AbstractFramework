# 020 — AbstractMusic ACE‑Step v1.5: upstream-aligned src_latents + non-finite guard/retry

## Summary

Addressed silent/invalid outputs and aligned text2music behavior closer to upstream ACE‑Step inference:

- seeded random `src_latents` instead of silence
- non‑finite latent retry with explicit `#FALLBACK`
- prompt handling aligned to upstream (raw prompt, SFT optional)
- shift default aligned to upstream (`3.0`)
- chunk masks default to zeros to avoid constant feature injection

## Why

User reported rapid harmonic noise or completely silent files.  
We observed `RuntimeWarning: invalid value encountered in cast` during WAV encoding, indicating NaN/Inf propagation.  
Upstream inference uses raw prompt tags and stochastic latents rather than silence‑seeded context.

## Report

### What changed

- **Text2music `src_latents` initialization**
  - Now seeded random noise by default (`use_random_src_latents=True`).
  - Silence init remains optional for debugging.

- **Prompt handling**
  - Default uses raw prompt/tags (no SFT wrapper).
  - `use_sft_prompt=True` preserves previous instruction/meta format.

- **Scheduler defaults**
  - `shift=3.0` (upstream default for turbo schedule).
  - `infer_method=ode` (upstream default), with explicit retry fallback.

- **Chunk mask handling**
  - Default `chunk_mask_mode="zeros"` to avoid injecting constant features.

- **Non‑finite safeguards**
  - Detect non‑finite latents; retry once with alternate infer method and incremented seed (`#FALLBACK`).
  - Sanitize non‑finite waveform values before PCM encoding.

- **Tests**
  - Updated smoke tests for new defaults.
  - Added `test_acestep_nonfinite_retry.py`.

### Tests executed

- `cd abstractmusic && /Users/alboul/tmp/abstractframework/.venv/bin/python -m pytest -q`
  - Result: `18 passed`

## Outcome

The pipeline now follows upstream‑aligned logic where possible, and avoids silent/invalid WAVs by guarding non‑finite latents and audio. The output still depends on model quality, but we have removed the known silent/NaN failure mode and removed SFT prompt mismatch by default.

