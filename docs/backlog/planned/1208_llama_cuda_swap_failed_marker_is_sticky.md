# 1208 — AbstractCore's llama.cpp CUDA self-swap: a "failed" marker never retries, and a uv venv without uv on PATH always fails

> Package: AbstractCore (utils/llama_cuda_swap.py, 2.35.1)
> Type: bug
> Status: planned
> Created: 2026-11-11
> Priority: P1
> Labels: gpu, install, llama.cpp, next-core-patch

## Summary

Found by the GPU-host check of the 0.14.0 matrix (2026-11-11 10:21 UTC, abstractgateway[gpu]==0.21.0 from PyPI in a
uv-created venv on the operator's NVIDIA host). The swap ran at the first GGUF load and recorded
`{"outcome": "failed", "reason": "neither pip nor uv is available to install the CUDA build"}`: a uv-created venv has no
pip, and the process's PATH did not contain `~/.local/bin` (a non-interactive ssh shell; also a systemd user service
started without the user's login PATH). Two defects follow:

1. **The failed marker is sticky.** `_decide_and_swap` returns the stored outcome for the same llama-cpp-python version
   when it is `failed`, so the swap never retries even once uv or pip becomes available; the user stays on the
   processor until they find and delete `llama_cpp/.abstractcore-cuda-swap.json`.
2. **uv is looked up only on PATH.** The installers put uv in `~/.local/bin` (and `~/.cargo/bin` for older installs);
   a gateway service or a non-login shell often lacks it.

With the marker removed and uv on PATH, the swap ran by itself in 14 s (both console lines), `llama_supports_gpu_offload()`
True on the Quadro RTX 5000, coherent answer: the mechanism is right, its failure handling is not.

## Scope

- A `failed` outcome is retried at the next load when its cause can have changed (no installer found, network), with a
  bounded cadence (once per process start, never in a loop); a `failed` on a cause that cannot change (unsupported
  driver) stays.
- Find uv also at `~/.local/bin/uv` and `~/.cargo/bin/uv` (and the `UV` env var the installers export) before giving up.
- The console line on failure names the remedy: "`python -m pip install --no-index --no-deps --force-reinstall
  --find-links <page> llama-cpp-python==<v>` or run the installer".

## Validation

A uv venv without pip, uv only in ~/.local/bin, PATH without it: the swap finds uv and installs; a failed marker from an
older run is retried once uv is present; an unsupported driver stays failed with its reason.
