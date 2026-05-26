# 017 — AbstractMusic ACE‑Step v1.5: fix MPS dtype alignment crash (f32 vs f16)

## Summary

Fixed a hard MPS runtime abort during ACE‑Step generation:

- `mps_add ... input types 'tensor<...xf32>' and 'tensor<...xf16>' are not broadcast compatible`
- `LLVM ERROR: Failed to infer result type(s).`

## Why

After switching MPS defaults to fp16, multiple conditioning/codebook paths could still introduce float32 tensors.  
On this MPS stack, certain mixed f32/f16 arithmetic paths abort the process (not a catchable Python exception).

## Report

### Root causes found

1. **Conditioning dtype mismatch risk** at backend boundary:
   - `text_hidden_states` / `lyric_hidden_states` were not explicitly aligned to model input dtype.

2. **MPS instability in text-encoder conditioning path**:
   - Qwen3 embedding path on MPS could still trigger mixed-dtype MPSGraph aborts in this environment.

3. **Unnecessary tokenizer/detokenizer work for non-cover generation**:
   - In vendored ACE‑Step `prepare_condition(...)`, LM hints were computed even when `is_covers` was all zeros.
   - This touched extra MPS kernels and increased failure surface.

### What changed

- **Backend dtype alignment** (`abstractmusic/src/abstractmusic/backends/acestep_v15.py`)
  - Cast floating conditioning tensors to model dtype/device before calling `model.generate_audio(...)`.
  - Ensure attention masks passed to model are moved to the same device/dtype as corresponding hidden states.

- **Text-encoder runtime strategy on MPS** (`abstractmusic/src/abstractmusic/backends/acestep_v15.py`)
  - Added `_resolve_text_encoder_runtime(...)`.
  - On MPS, run text encoder on **CPU float32** with explicit warning:
    - `WARNING #FALLBACK : Running ACE-Step text encoder on CPU float32 for MPS compatibility ...`
  - Cast resulting conditioning tensors back to model dtype/device before diffusion.

- **Vendored ACE‑Step optimization/fix** (`abstractmusic/src/abstractmusic/vendor/acestep_v15_turbo/modeling_acestep_v15_turbo.py`)
  - In `prepare_condition(...)`, skip tokenize/detokenize LM-hints path when `is_covers` has no positive entries.
  - This avoids unnecessary non-cover compute and reduces exposure to mixed-dtype MPS kernel failures.

- **Regression tests added**
  - `abstractmusic/tests/test_acestep_dtype_alignment.py`
  - `abstractmusic/tests/test_acestep_text_encoder_runtime.py`
  - `abstractmusic/tests/test_acestep_vendor_prepare_condition.py`

### Verification executed

- Unit tests:
  - `cd abstractmusic && /Users/alboul/tmp/abstractframework/.venv/bin/python -m pytest -q`
  - Result: `15 passed`

- CLI smoke run (real entrypoint, MPS):
  - `PYTHONPATH=.../. /Users/alboul/tmp/abstractframework/.venv/bin/abstractmusic --backend acestep t2m "sci fi music" --duration 1 --out .../out_mps_check.wav`
  - Output generated successfully:
    - `/Users/alboul/tmp/abstractframework/abstractmusic/out_mps_check.wav`

## Outcome

The direct MPS mixed-dtype abort is resolved for the user flow.  
ACE‑Step generation remains MPS-first for diffusion, with explicit and controlled fallback behavior for unstable conditioning paths.

