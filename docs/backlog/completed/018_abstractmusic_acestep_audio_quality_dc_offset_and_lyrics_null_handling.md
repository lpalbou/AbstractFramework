# 018 — AbstractMusic ACE‑Step v1.5: audio quality fix (DC offset amplification + no-lyrics handling)

## Summary

Investigated a “generation succeeds but output sounds like noise” issue and implemented two targeted quality fixes:

1. remove per-channel DC offset before peak normalization
2. use a proper null lyric condition for instrumental prompts (no synthetic `"[Instrumental]"` text)

## Why

Empirical findings:

- Raw ACE-Step VAE decode produced tiny-amplitude waveforms with slight DC bias.
- Existing peak normalization amplified that bias into large one-sided output, perceived as noisy/invalid.
- No-lyrics requests were using a placeholder lyric string, which is weaker than a true null lyric condition.

## Report

### What changed

- **Audio postprocess**
  - Added `_remove_dc_offset(...)` in `abstractmusic/src/abstractmusic/backends/acestep_v15.py`.
  - Applied DC-centering immediately after VAE decode and before normalization.

- **No-lyrics conditioning**
  - For missing lyrics, backend now creates:
    - `lyric_ids = 0` (single token)
    - `lyric_mask = 0` (null condition)
  - This replaces prior synthetic placeholder lyric text behavior.

- **Tests**
  - Added `abstractmusic/tests/test_acestep_audio_postprocess.py` for DC-centering behavior.
  - Updated `abstractmusic/tests/test_acestep_backend_smoke.py` to assert null lyric mask path for no-lyrics requests.

- **Docs/notes**
  - Updated `abstractmusic/README.md` and `AGENTS.md` with the new behavior and rationale.

### Verification

- Unit tests:
  - `cd abstractmusic && /Users/alboul/tmp/abstractframework/.venv/bin/python -m pytest -q`
  - Result: `16 passed`

- End-to-end CLI run:
  - `abstractmusic --backend acestep t2m "sci fi music" --duration 10 --out out_quality_check.wav`
  - Command completed successfully.

- Waveform sanity stats after fix (from generated WAV):
  - channel means near zero (`~ -4e-06`, `~ 6e-06`)
  - no longer one-sided
  - healthy variance (`std ~ 0.12 / 0.11`)

## Outcome

ACE-Step outputs are no longer dominated by normalization-amplified DC bias, and instrumental requests use cleaner null lyric conditioning. This addresses the observed “noise-like output” failure mode while keeping the local-first architecture intact.

