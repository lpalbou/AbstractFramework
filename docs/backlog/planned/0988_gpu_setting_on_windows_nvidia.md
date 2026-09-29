# 0988 — The `gpu` setting on Windows + NVIDIA: CUDA torch, prebuilt engines, live progress

> Package: abstractframework (install.ps1), abstractcore, abstractvision, abstractvoice
> Type: task
> Created: 2026-09-29
> Priority: high
> Labels: windows, gpu, installer, packaging, cuda

## Summary

`abstractcore[gpu]` does not install on Windows, and the Windows gpu profile installed by
`install.ps1` runs every torch engine on the CPU. Make `gpu` on Windows + NVIDIA install cleanly
without user action, on CUDA, with live progress, using prebuilt wheels wherever they exist.

## Why

Operator (2026-09-29): "what engines/providers can be installed on windows with proper
inferences … i personally do not care if they are built from source as long as (a) we have good
realtime feedback for users so they understand what's happening and (b) it completes cleanly
without their interventions." The three settings are light / apple / gpu; "gpu" must mean
"everything for an NVIDIA machine" on Windows too.

## Current code reality (2026-09-29, verified against PyPI, wheel contents and `uv` resolves)

Evidence and lock files: `untracked/windows-engines/` (research by a worker, full report in the
session log of 2026-09-29).

1. **CPU torch on Windows.** PyPI's torch 2.14.0 Windows wheel has no CUDA; CUDA builds exist
   only on download.pytorch.org (`cu126` 2.5 GB, `cu130`/`cu132` 1.9 GB). `install.ps1` passes
   no PyTorch index, so diffusers, transformers, music, 3D and torch voices run on CPU.
2. **Three packages block a wheel-only resolve** of `abstractcore[gpu]==2.19.0` on
   Windows/Python 3.12: `vllm` (Linux only upstream; WSL/Docker only), `llama-cpp-python` and
   `stable-diffusion-cpp-python` (source only on PyPI). Without them the whole
   `abstractgateway[gpu,tray]` resolves (257 packages, cu130 torch); the remaining sdists are pure
   Python.
3. **llama.cpp has official prebuilt Windows GPU wheels** on abetlen's index (0.3.35: cu124,
   cu125, cu130, cu132, vulkan, cpu). `install.ps1` uses only the CPU one. The CUDA wheels do not
   bundle cuBLAS/cudart; the loader only searches `%CUDA_PATH%\bin` and its own folder, so
   AbstractCore must `os.add_dll_directory(<torch>\lib)` before importing `llama_cpp` (to verify).
4. **aec-audio-processing** has cp311–cp313 Windows wheels, but `install.ps1` treats it as a
   compiled extra (`-Full` only).
5. **No live output:** `Invoke-Native` writes uv output only to the log, so a multi-GB CUDA
   download looks frozen.
6. **One CUDA major per install.** torch cu130 ships CUDA 13 cuBLAS/cudart/cuDNN 9 in
   `torch\lib`; ctranslate2 (faster-whisper) imports `cublas64_12.dll`; `nvidia-cublas` 13 has no
   Windows wheel. Driver floors: CUDA 13 ≥ 580, CUDA 12 ≥ 525.
7. **stable-diffusion.cpp source build needs MSVC**, whose installer requires elevation (UAC
   cannot be suppressed from a user shell); the CUDA toolkit itself can be installed without
   admin from NVIDIA's redist zips. So an unattended sd.cpp build is not possible for a
   non-admin user.

## Scope

### In scope

- **Packaging markers** (stop the resolve from failing; they cannot choose the CUDA torch build):
  - abstractcore `[gpu]`: `vllm…; sys_platform == 'linux'`;
    `llama-cpp-python…; sys_platform != 'win32'` (the installer adds the prebuilt wheel).
  - abstractvision `[all-gpu]`: `stable-diffusion-cpp-python…; sys_platform != 'win32'`
    (Diffusers on CUDA torch covers image and video on Windows). Keep 0.3.32 (no mlx-gen in gpu).
  - abstractvoice `[gpu]`: unchanged; decide faster-whisper on CUDA 13 (add
    `nvidia-cublas-cu12; sys_platform == 'win32'` + DLL directory, or CPU Whisper).
- **install.ps1 stack choice** from `nvidia-smi --query-gpu=driver_version,compute_cap`:
  - driver ≥ 580 and compute capability ≥ 7.5 → CUDA 13: torch `cu130`, llama `cu130`;
  - driver ≥ 525 → CUDA 12: torch `cu126`, llama `cu125` (no RTX 50; torch 2.15 drops cu126);
  - no working NVIDIA → CPU torch, llama `vulkan`, else `cpu`.
  Use `--torch-backend` if `uv tool install` honours it on Windows (to verify), else an explicit
  PyTorch index plus `torch==2.14.0+cu130` constraints.
- **Live progress:** stream uv output to the console as well as the log, or a heartbeat every
  10–15 s with elapsed time and the last Downloading/Building/Installed line; announce big
  downloads with their sizes first; verbose CMake/Ninja for any source build.
- **Unattended completion:** wheels only by default; aec from its wheel on cp312; soft fallback
  CUDA wheel → vulkan → cpu → skip with a summary line; import + GPU smoke test at the end.
- **AbstractCore hints:** the three-settings wording already covers "not available on this
  machine"; update it where these engines become available on Windows.

### Out of scope

- vLLM on Windows (upstream does not support it; WSL is a separate path).
- stable-diffusion.cpp source builds for non-admin users (MSVC needs elevation). A later option:
  upstream `sd-server.exe` (prebuilt cuda12/vulkan zips, OpenAI-compatible API) behind the
  existing openai-compatible backend.
- Windows ARM64 and AMD ROCm on Windows (recorded below, not implemented).

## Other platforms (recorded)

- **Windows without NVIDIA:** light plus llama.cpp Vulkan/CPU wheel and CPU voice; Ollama and
  LM Studio run natively.
- **Windows ARM64:** torch CPU only (PyTorch cpu index); no ctranslate2 or abetlen llama wheel;
  upstream `llama-server` ARM64 zips and LM Studio exist.
- **Intel Mac:** the last x86_64 macOS torch is 2.2.2, below our floors; recommend light plus
  remote providers or Ollama (CPU).

## Acceptance criteria

- [ ] `uv pip compile "abstractcore[gpu]"` resolves for x86_64-pc-windows-msvc with wheels only
      (pure-Python sdists allowed).
- [ ] `install.ps1 --gpu` on a real Windows + NVIDIA machine completes without user action,
      prints progress at least every 15 s, and ends with torch reporting CUDA, llama.cpp
      offloading to the GPU and a diffusers image generated on CUDA.
- [ ] Driver < 580 selects the CUDA 12 stack; no NVIDIA selects CPU/Vulkan; each path tested.
- [ ] Whisper works (or is explicitly CPU) on the chosen stack.

## Validation

`uv pip compile` checks in CI for Windows; a real Windows + NVIDIA run (none available on this
machine — needs the operator's hardware or a GPU CI runner) for the stack choice, llama cuBLAS
loading, Whisper and torchcodec/FFmpeg.
