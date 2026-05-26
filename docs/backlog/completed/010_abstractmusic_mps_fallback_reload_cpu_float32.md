# 010 — AbstractMusic MPS fallback: reload CPU in float32 (clean fallback)

## Summary

Improved `abstractmusic`’s Apple Silicon **MPS** fallback behavior for Diffusers audio pipelines:

- When encountering the known PyTorch MPS limitation (`Output channels > 65536…`), `abstractmusic` now retries on **CPU with `torch_dtype=float32`** (instead of moving a float16 pipeline to CPU).
- Added an explicit `WARNING #FALLBACK` message (no silent behavior).
- Added a unit test covering the MPS→CPU reload logic without requiring real model downloads.
- Documented upstream references and the official PyTorch env var for MPS fallback.

## Why

The previous fallback could trigger Diffusers warnings about float16 on CPU and lead to slow/fragile execution. The “clean” and predictable path is: **MPS failure → CPU(float32)**.

## Report

### What changed

- `abstractmusic/src/abstractmusic/backends/diffusers_audio.py`
  - On known MPS failure, reload pipeline on CPU with `torch_dtype=float32` and retry.
  - If a pipeline is configured to run on `cpu` with `torch_dtype=float16`, coerce to float32 with explicit `WARNING #FALLBACK`.
  - Removed emoji from warning output to keep logs clean.

- `abstractmusic/tests/test_diffusers_backend_mps_fallback.py`
  - Added a unit test that monkeypatches the backend to simulate the MPS error and confirms:
    - config switches to CPU/float32
    - WAV bytes are produced
    - `WARNING #FALLBACK` is emitted

- `abstractmusic/README.md`
  - Added upstream references:
    - PyTorch `PYTORCH_ENABLE_MPS_FALLBACK` env var docs
    - PyTorch issue tracking the MPS channel-limit error

### Tests executed

- `cd abstractmusic && pytest -q`

### Empirical verification

Ran `abstractmusic` on an MPS-enabled machine and confirmed:

- The known MPS error triggers a single `WARNING #FALLBACK`.
- No “float16 pipeline on CPU” warning spam occurs.
- A WAV file is produced successfully.

