# 019 — AbstractMusic ACE‑Step v1.5: switch default infer_method to `sde` (keep `shift=1`)

## Summary

Addressed “very accelerated / vaguely harmonic” outputs by changing the ACE-Step default diffusion update rule from `ode` to `sde` in local `abstractmusic` integration (while keeping `shift=1`).

## Why

Low-memory diagnostics on this Apple Silicon laptop showed:

- `ode` often yields harsher / accelerated-feeling output in this integration path.
- `sde` generally reduces high-frequency aggressiveness and onset density proxies.
- `shift=3` with `sde` was unstable in this local path (can collapse to silence), so `shift=1` remains.

## Report

### What changed

- **Backend default**
  - `abstractmusic/src/abstractmusic/backends/acestep_v15.py`
  - `AceStepV15BackendConfig.infer_method`: `\"ode\"` → `\"sde\"`

- **Regression test**
  - Added `abstractmusic/tests/test_acestep_defaults.py` to assert default is `sde`.

- **Docs**
  - Updated `abstractmusic/README.md` to document default `infer_method=sde` for local stability.
  - Updated `AGENTS.md` note about default method rationale.

### Verification

- Unit tests:
  - `cd abstractmusic && /Users/alboul/tmp/abstractframework/.venv/bin/python -m pytest -q`
  - Result: `17 passed`

- End-to-end generation (single-run, memory-conscious):
  - 10s clip generated successfully with default settings.
  - Spectral proxies vs prior `ode` output indicate reduced high-frequency/onset aggressiveness.

### Notes

- Very short durations can still behave inconsistently depending on seed/settings in this local turbo path.
- For the user’s 10s case, `sde` is currently the safer default.

## Outcome

Default generation is now less prone to accelerated/harsh artifacts in this environment while preserving local-first behavior and low-memory constraints.

