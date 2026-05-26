# 014 — AbstractMusic: ACE‑Step backend should not require `trust_remote_code` (vendor HF model modules)

## Summary

Fixed the `abstractmusic` ACE‑Step v1.5 backend so it loads **without** Transformers `trust_remote_code` by vendoring the checkpoint’s custom Transformers model modules into `abstractmusic`.

## Why

ACE‑Step v1.5 stores its custom Transformers modules under the checkpoint subfolder (`acestep-v15-turbo/`). Transformers `trust_remote_code` only searches the **repo root** for custom modules, which causes runtime failures like:

> `... does not appear to have a file named configuration_acestep_v15.py`

We want a fully open-source, permissive, self-controlled integration that works reliably and avoids runtime remote-code execution.

---

## Report

### What changed

#### Vendored ACE‑Step custom Transformers modules

- Added:
  - `abstractmusic/src/abstractmusic/vendor/acestep_v15_turbo/configuration_acestep_v15.py`
  - `abstractmusic/src/abstractmusic/vendor/acestep_v15_turbo/modeling_acestep_v15_turbo.py`
- Source:
  - HF repo: `ACE-Step/Ace-Step1.5`
  - Revision: `19671f406d603126926c1b7e2adc169acbcade22`
- License:
  - Both files carry **Apache-2.0** headers (permissive).

#### ACE‑Step backend load path (no remote-code execution)

- Updated `abstractmusic/src/abstractmusic/backends/acestep_v15.py`
  - Replaced `AutoModel.from_pretrained(..., trust_remote_code=True)` with loading the vendored class:
    - `AceStepConditionGenerationModel.from_pretrained(...)`
  - Added `_lazy_import_acestep_v15_turbo_model()` for clean lazy imports.

#### Packaging

- Updated `abstractmusic/pyproject.toml` to include:
  - `abstractmusic.vendor`
  - `abstractmusic.vendor.acestep_v15_turbo`

#### Tests + docs

- Updated `abstractmusic/tests/test_acestep_backend_smoke.py` to patch the new lazy importer.
- Updated:
  - `docs/adr/003_abstractmusic_acestep_v15_backend_source_strategy.md`
  - `abstractmusic/README.md`
  - `AGENTS.md`

### Tests executed

- `cd abstractmusic && pytest -q`

### Result

`abstractmusic --backend acestep ...` no longer fails during model load due to missing root-level remote python modules; the integration is self-contained and avoids `trust_remote_code`.

