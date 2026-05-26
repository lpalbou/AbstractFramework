# 022 — Fix ACE‑Step VAE CPU fallback dtype mismatch

## Summary

Fixed the ACE‑Step VAE CPU fallback so the VAE and input tensor dtypes match after
an MPS out‑of‑memory error.

## Why

The fallback decoded on CPU with float32 inputs while the VAE remained in float16,
triggering:

```
RuntimeError: Input type (float) and bias type (c10::Half) should be the same
```

## Report

### What changed

- `abstractmusic/src/abstractmusic/backends/acestep_v15.py`
  - On MPS VAE decode failure, move the VAE to CPU **float32** and also move
    latents to CPU float32 before resuming tiled decoding.

### Tests

Per user request, **no additional tests** were run.

## Outcome

MPS OOM fallback now completes on CPU without dtype mismatch crashes.

