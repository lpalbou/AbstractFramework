# 016 — AbstractMusic ACE‑Step v1.5: MPS memory budget + fp16 defaults (18‑GB Macs)

## Summary

Improved Apple Silicon (MPS) reliability for ACE‑Step v1.5 generation on memory‑constrained machines by:

- switching MPS “auto dtype” defaults from **fp32 → fp16** (bf16 disabled)
- making VAE decode fallback less thrashy: once MPS decode fails, we decode the remainder on CPU

## Why

We observed MPS out‑of‑memory during VAE decode on an 18‑GB unified‑memory Mac.  
The root cause was primarily **memory amplification from fp32 casting** when loading checkpoints on MPS (weights often stored in bf16/fp16). This can double the footprint and push the process over PyTorch’s MPS allocator limits.

## Report

### What happened in the log

The pipeline successfully:

- loaded the ACE‑Step DiT checkpoint
- downloaded and loaded the **Qwen3 embedding** text encoder (used to turn the prompt into `text_hidden_states` conditioning tensors)
- downloaded and loaded the VAE

Then, during **VAE decode**, MPS ran out of memory and `abstractmusic` triggered a `#FALLBACK` to CPU decode.

### Key changes

- **MPS dtype defaults** (`abstractmusic/src/abstractmusic/backends/acestep_v15.py`)
  - `auto` model dtype on MPS is now **fp16** (instead of fp32)
  - `auto` VAE dtype on MPS is now **fp16**
  - bf16 on MPS now falls back to fp16 (explicit `#FALLBACK` warning)

- **VAE decode fallback behavior** (`abstractmusic/src/abstractmusic/backends/acestep_v15.py`)
  - if MPS VAE decode throws `RuntimeError`/`NotImplementedError`, we move the VAE to CPU and keep decoding the **remainder** on CPU to avoid repeated MPS↔CPU moves per chunk

- **Tests**
  - added `abstractmusic/tests/test_acestep_mps_dtype_defaults.py` to lock the new fp16‑on‑MPS defaults

- **Docs**
  - updated `abstractmusic/README.md` and `AGENTS.md` to reflect fp16‑on‑MPS defaults for ACE‑Step

### Tests executed

- `cd abstractmusic && /Users/alboul/tmp/abstractframework/.venv/bin/python -m pytest -q`

Result: `11 passed`

## Outcome

ACE‑Step on MPS no longer defaults to fp32 (which caused unnecessary memory pressure) and the MPS VAE decode fallback is now more stable when it does trigger.

