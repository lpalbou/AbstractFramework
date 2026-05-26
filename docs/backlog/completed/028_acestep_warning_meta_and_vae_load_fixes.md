# 028 — ACE‑Step warning + meta tensor + VAE load fixes

## Summary

Resolved remaining ACE‑Step startup warnings and fixed the VAE meta‑tensor load
failure in Diffusers.

## Why

Runs still showed non‑actionable warnings (Kandinsky autocast, `torch_dtype`,
HF Hub deprecated args) and the VAE could load on meta tensors, causing crashes
when moving to device.

## Report

### What changed

- `abstractmusic/src/abstractmusic/backends/__init__.py`
  - Made Diffusers backend lazy to avoid importing Diffusers when using ACE‑Step.
- `abstractmusic/src/abstractmusic/cli.py`
  - Import Diffusers backend only when requested (prevents unnecessary Diffusers imports).
- `abstractmusic/src/abstractmusic/backends/acestep_v15.py`
  - Use `dtype` for Transformers `from_pretrained` calls to avoid `torch_dtype` warnings.
  - Patch Transformers `torch_dtype` property to map to `dtype` without warnings.
  - Patch HF Hub download to drop deprecated `local_dir_use_symlinks` arg in Diffusers/HF.
  - Use modern parametrizations `weight_norm` for Oobleck with state‑dict key conversion.
  - Load VAE with `low_cpu_mem_usage=False` to avoid meta‑tensor `.to()` crashes.
  - Apply Oobleck weight_norm patch during CPU fallback as well.
- `AGENTS.md`
  - Added notes for VAE load/meta fix and weight_norm key conversion.

### Tests

Per user request, **no additional tests** were run.

## Outcome

ACE‑Step startup logs are cleaner and VAE loading no longer fails with meta‑tensor
errors; weight loading aligns with modern weight_norm without deprecation warnings.

