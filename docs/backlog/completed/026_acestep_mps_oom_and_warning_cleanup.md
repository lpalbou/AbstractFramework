# 026 — ACE‑Step MPS OOM fallback + warning cleanup

## Summary

Reduced remaining startup warnings and hardened MPS OOM handling for ACE‑Step,
including a higher default MPS memory cap (16 GiB).

## Why

Users still saw non‑actionable warnings and MPS OOM errors at longer durations.
They requested a cap up to 16 GiB with no excess.

## Report

### What changed

- `abstractmusic/src/abstractmusic/backends/acestep_v15.py`
  - Default MPS cap raised to 16 GiB (clamped at 16).
  - Added a `weight_norm` patch using the modern parametrizations API to avoid
    deprecation warnings from the VAE.
  - Hardened MPS OOM fallback by offloading MPS state before CPU decode and
    re‑slicing latents on CPU.
- `abstractmusic/src/abstractmusic/cli.py`
  - Default `--mps-max-memory-gb` updated to 16.
- `abstractmusic/README.md`
  - Updated MPS cap note to 16 GiB.
- `AGENTS.md`
  - Updated the MPS memory cap note to 16 GiB.

### Tests

Per user request, **no additional tests** were run.

## Outcome

Startup warnings are reduced and MPS OOM handling is more robust, with a higher
default cap that aligns with the 16 GiB requirement.

