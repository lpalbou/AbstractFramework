# 015 — AbstractMusic ACE‑Step v1.5: fix Transformers “meta tensor” load crash + vendor quantizer to reduce deps

## Summary

Made the ACE‑Step v1.5 backend reliable on modern Transformers by fixing a load-time crash:

- `RuntimeError: Tensor.item() cannot be called on meta tensors`

Also reduced installation friction by **removing the hard dependency** on `vector-quantize-pytorch` (MIT) by vendoring only the minimal quantizer code needed by the ACE‑Step checkpoint.

## Why

- **Correctness**: Transformers v5 initializes models on the `meta` device by default during `from_pretrained()` to reduce peak CPU memory. ACE‑Step’s init path constructs a quantizer that uses Python-level assertions / scalar extraction, which is incompatible with meta tensors.
- **UX / dependency control**: adding `vector-quantize-pytorch` pulls additional transitive deps (notably `einx`) and imposes a stricter Torch floor. We prefer to keep `abstractmusic` install friction low and maintain control over the minimal, permissively-licensed code we must ship.

---

## Report

### Root cause

ACE‑Step’s DiT model initializes an audio quantizer during `__init__` (FSQ / ResidualFSQ).  
Transformers can initialize models on **`meta`** tensors during `from_pretrained()`:

- **Transformers v5**: includes `torch.device("meta")` in `get_init_context(...)`
- **Transformers v4**: uses the `init_empty_weights()` context manager (accelerate integration)

In both cases, the quantizer setup does Python-level checks / scalar extraction, which triggers `Tensor.item()` on meta tensors → crash.

### What changed

- **Meta-init crash fix (v4 + v5)**:
  - Updated the vendored ACE‑Step model class `AceStepConditionGenerationModel` to override `get_init_context(...)` and filter out:
    - `torch.device("meta")` (v5)
    - the generator context wrapping `init_empty_weights()` (v4)
  - File: `abstractmusic/src/abstractmusic/vendor/acestep_v15_turbo/modeling_acestep_v15_turbo.py`

- **Dependency reduction (no `vector-quantize-pytorch`)**:
  - Vendored the minimal MIT quantizer code (derived from `vector-quantize-pytorch`) into:
    - `abstractmusic/src/abstractmusic/vendor/acestep_v15_turbo/vq_residual_fsq.py`
  - Updated ACE‑Step vendored model to import `ResidualFSQ` from that local module.
  - Removed `vector-quantize-pytorch` from `abstractmusic/pyproject.toml` dependencies.

- **Error messaging cleanup**:
  - Updated `abstractmusic/src/abstractmusic/backends/acestep_v15.py` to no longer suggest installing `vector-quantize-pytorch`.

- **Tests**:
  - Added `abstractmusic/tests/test_acestep_vendored_model_init_context.py` to ensure the vendored model filters both meta-init styles.

### Tests executed

- `cd abstractmusic && /Users/alboul/tmp/abstractframework/.venv/bin/python -m pytest -q`

Result: `10 passed`

### Outcome

- The ACE‑Step backend no longer fails during model initialization due to meta tensors.
- `abstractmusic` no longer requires `vector-quantize-pytorch` as an explicit dependency for ACE‑Step.

