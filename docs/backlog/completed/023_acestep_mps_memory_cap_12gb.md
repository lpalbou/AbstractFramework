# 023 — Add MPS memory cap support (12 GiB default)

## Summary

Added a configurable MPS memory cap for ACE‑Step, defaulting to ~12 GiB on Apple Silicon.

## Why

Longer generations can exceed MPS memory limits and crash; a cap keeps usage within a safe budget.

## Report

### What changed

- `abstractmusic/src/abstractmusic/backends/acestep_v15.py`
  - Added MPS high‑watermark configuration (`mps_max_memory_gb`, `mps_high_watermark_ratio`).
  - Configures `PYTORCH_MPS_HIGH_WATERMARK_RATIO` early for MPS/auto devices.
  - Hardened VAE CPU fallback by ensuring the VAE is moved/reloaded on CPU float32.
- `abstractmusic/src/abstractmusic/cli.py`
  - Added `--mps-max-memory-gb` and `--mps-high-watermark-ratio` CLI flags.
- `abstractmusic/README.md`
  - Documented the MPS memory cap default and overrides.
- `AGENTS.md`
  - Added a note about the new MPS memory cap support.

### Tests

Per user request, **no additional tests** were run.

## Outcome

ACE‑Step now respects a ~12 GiB MPS memory cap by default and provides explicit overrides.

