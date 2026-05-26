# 025 — Reduce ACE‑Step startup warnings

## Summary

Reduced avoidable ACE‑Step startup warnings by preventing Diffusers slow imports
and updating rope validation in the vendored ACE‑Step config.

## Why

The previous startup emitted non‑actionable warnings (Kandinsky autocast and
deprecated rope validation), which made it harder to spot real issues.

## Report

### What changed

- `abstractmusic/src/abstractmusic/backends/acestep_v15.py`
  - Disable `DIFFUSERS_SLOW_IMPORT` in‑process if enabled to avoid importing
    unrelated transformer modules that trigger Kandinsky autocast warnings.
- `abstractmusic/src/abstractmusic/vendor/acestep_v15_turbo/configuration_acestep_v15.py`
  - Use `standardize_rope_params()` and `validate_rope()` if available, with a
    safe fallback, removing the deprecated `rope_config_validation()` warning.
- `AGENTS.md`
  - Documented the Diffusers slow‑import mitigation.

### Tests

Per user request, **no additional tests** were run.

## Outcome

ACE‑Step startup logs are cleaner, with only actionable warnings remaining.

