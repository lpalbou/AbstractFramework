# 027 — ACE‑Step warnings + CPU fallback fixes

## Summary

Reduced remaining startup warnings, fixed the CPU fallback dtype mismatch, and
applied the MPS cap earlier so it affects torch initialization.

## Why

Users still saw non‑actionable warnings and MPS OOM fallback failures during
longer runs.

## Report

### What changed

- `abstractmusic/src/abstractmusic/backends/acestep_v15.py`
  - Added helpers to disable Diffusers slow import, patch `hf_hub_download`
    deprecated args, and use `dtype` for Transformers `from_pretrained` calls.
  - Patched `weight_norm` to the new parametrizations API, including the
    Oobleck module’s local reference.
  - Hardened MPS OOM fallback by always reloading the VAE on CPU float32.
  - Applied MPS memory fraction when torch is already loaded.
- `abstractmusic/src/abstractmusic/cli.py`
  - Apply MPS cap settings immediately after argument parsing.
  - Disable Diffusers slow import early in CLI startup.
- `AGENTS.md`
  - Documented MPS cap application via `torch.mps.set_per_process_memory_fraction`.

### Tests

Per user request, **no additional tests** were run.

## Outcome

Startup warnings are reduced and MPS OOM fallback should complete without dtype
mismatch crashes.

