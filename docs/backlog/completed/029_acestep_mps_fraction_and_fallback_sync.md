# 029 — ACE‑Step MPS fraction + fallback device sync

## Summary

Aligned the MPS memory fraction with Apple’s recommended max memory, reduced
startup warnings, and fixed the CPU fallback crossfade device mismatch.

## Why

Runs were capped at ~10.67 GiB despite requesting 16 GiB, and the MPS→CPU
fallback crashed due to mixed MPS/CPU tensors during crossfade.

## Report

### What changed

- `abstractmusic/src/abstractmusic/backends/acestep_v15.py`
  - Added psutil fallback for system memory detection.
  - Compute MPS fraction using `torch.mps.recommended_max_memory` when available.
  - Allow per‑process memory fraction up to 2.0 while keeping env ratios ≤1.0.
  - Removed Diffusers modular pipelines patch to avoid experimental warnings.
  - Ensured CPU fallback moves `wav_accum` to CPU before crossfade and syncs devices.
- `abstractmusic/src/abstractmusic/__init__.py`
  - Set `DIFFUSERS_SLOW_IMPORT=0` early to avoid slow import noise.
- `AGENTS.md`
  - Documented the new MPS fraction basis.

### Tests

Per user request, **no additional tests** were run.

## Outcome

The MPS cap can now honor a 16 GiB request (via per‑process fraction), and the
fallback crossfade no longer crashes due to mixed device tensors.

