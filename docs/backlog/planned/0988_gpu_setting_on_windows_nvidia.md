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

- [x] `uv pip compile "abstractcore[gpu]"` resolves for x86_64-pc-windows-msvc with wheels only
      (pure-Python sdists allowed). (With this checkout's wheels; on PyPI after the release.)
- [ ] `install.ps1 --gpu` on a real Windows + NVIDIA machine completes without user action,
      prints progress at least every 15 s, and ends with torch reporting CUDA, llama.cpp
      offloading to the GPU and a diffusers image generated on CUDA.
- [ ] Driver < 580 selects the CUDA 12 stack; no NVIDIA selects CPU/Vulkan; each path tested.
- [ ] Whisper works (or is explicitly CPU) on the chosen stack.

## Implementation (2026-09-29, unreleased; no Windows or NVIDIA hardware available)

Commits (nothing pushed, tagged or released):

| Repo | Where | Commit | What |
|---|---|---|---|
| abstractcore | main | `2ae6b4b` | `[gpu]`: `vllm; sys_platform == 'linux'`, `llama-cpp-python; sys_platform != 'win32'`, `abstractvision[all-gpu]>=0.3.32`. Windows x86_64 now has the `gpu` setting in hints and the Engines screen (ARM64/Intel Mac still none); the llama.cpp hint/row there says "on Windows the AbstractFramework installer adds llama.cpp's prebuilt GPU build; with plain pip, llama.cpp is not part of abstractcore[gpu] on Windows". `abstractcore/utils/windows_dll.py`: before the first `import llama_cpp`, on win32 only, `<torch>\lib` goes into `os.add_dll_directory` **and** the front of `PATH` (llama-cpp-python loads `llama.dll` with `winmode=0`, the legacy search that resolves dependents through `PATH`); torch is never imported (`find_spec`). On win32 the GGUF lane runs `llama_backend_init()` before `llama_supports_gpu_offload()` (the Windows wheels ship `ggml-cuda.dll` / `ggml-vulkan.dll` as separate backend DLLs). Docs, CHANGELOG [Unreleased], recommended-models, llms-full. |
| abstractvision | main | `a8b8ab3` | `all-gpu`: `stable-diffusion-cpp-python; sys_platform != 'win32'` (0.3.32 entry extended); tests, README, getting-started, llms-full. |
| abstractvoice | main | `52c1d95` | `gpu`/`all-gpu` add `nvidia-cublas-cu12>=12.4` and `nvidia-cuda-runtime-cu12>=12.4` with `sys_platform == 'win32'` (both publish `py3-none-win_amd64` wheels; `nvidia-cublas` 13 has none). `compute/windows_cuda.py` adds `site-packages\nvidia\{cublas,cuda_runtime,cudnn}\bin` to the DLL search and `PATH` before faster-whisper loads; `best_faster_whisper_device()` on win32 picks `cuda` only when `ctypes.WinDLL("cublas64_12.dll", winmode=0)` loads, else `cpu` with a warning. CHANGELOG [Unreleased], docs/installation.md. |
| abstractframework | branch `feat/windows-gpu` (worktree `untracked/windows-gpu-root`), **not main** | `6e38c2f` | install.ps1 + CI + docs/install.md, below. |

install.ps1 (gpu profile):

- **Stack** from `nvidia-smi --query-gpu=driver_version,compute_cap,name --format=csv,noheader`
  (the lowest compute capability of all GPUs; a driver too old for `compute_cap` is judged by its
  version alone; missing/failing nvidia-smi = no NVIDIA): driver >= 580 and cc >= 7.5 -> CUDA 13
  (torch `cu130`, llama `cu130`); driver >= 525 -> CUDA 12 (torch `cu126`, llama `cu125`); else
  PyPI's CPU torch, llama `vulkan` then `cpu`. The decision and the reason are printed and repeated
  in the summary (`GPU stack:`). Windows on ARM: CPU, no llama wheel.
- **PyTorch build:** `uv tool install --torch-backend cuXXX`. Verified on uv 0.11.14 that tool
  installs honour it (a `--torch-backend cu130` tool install on macOS asked
  `download.pytorch.org/whl/cu130` and found only manylinux/win_amd64 `+cu130` wheels; uv prints
  "experimental"; the uv docs still say "only uv pip"). A uv whose `uv tool install --help` lacks the
  option gets `--index https://download.pytorch.org/whl/cuXXX --index-strategy unsafe-best-match`
  plus constraints `torch==2.14.0+cuXXX`, `torchvision==0.29.0+cuXXX`, `torchaudio==2.11.0+cuXXX`
  (that resolve was checked: identical pins to the `--torch-backend` resolve). A `==2.14.0`
  constraint accepts `2.14.0+cu130` (uv: `>=2.14.0, <2.14.0+`), so the release matrix keeps working
  (it pins no torch anyway). A stack change on an existing install adds `--reinstall-package` for
  the three torch packages; `bootstrap.env` records `TORCH=` and `LLAMA=`.
- **Attempts:** CUDA torch + llama(stack) -> CUDA torch without llama -> the previous path with
  PyTorch's CPU build (llama `vulkan`/`cpu`, voice retry), each announced.
- **llama.cpp:** after the install, in the gateway's environment, each build is checked the way
  AbstractCore loads it (a fresh process: AbstractCore's `prepare_llama_cpp_import` when present,
  `import llama_cpp`, `llama_backend_init()`, `llama_supports_gpu_offload()`); a GPU build is kept
  only when it offloads, the cpu build when it imports. Otherwise the next build is swapped in with
  `uv pip install --python <env> --no-index --find-links <build page> --no-deps --reinstall-package
  llama-cpp-python --refresh-package llama-cpp-python`; when none loads it is uninstalled (never a
  broken import) and the summary says so.
- **Final checks:** `torch.cuda.is_available()` + device name (a CUDA build that does not import is
  replaced by the CPU build; one that imports without CUDA is kept, engines on CPU, cause printed);
  faster-whisper's device via AbstractVoice (warns when the installed AbstractVoice predates the
  cuBLAS 12 check on the CUDA 13 stack). Summary lines `PyTorch:`, `GGUF:`, `Whisper:`.
- **Live progress:** the uv installs run through `Invoke-LiveProcess` (ProcessStartInfo, Windows
  argument quoting, both streams read asynchronously): every line to the log, uv's lines to the
  console as they come (package lists counted, log only), and `... still working (Nm SSs elapsed;
  last: Downloading torch (1.9GiB))` after 15 s of silence. Big downloads are announced first
  (torch cu130 about 1.9 GB, cu126 about 2.5 GB; llama cu130 220 MB, cu125 480 MB, vulkan 45 MB).
- **aec-audio-processing** left the Windows compiled list (cp311–cp313 wheels; install.ps1 uses
  3.12); install.sh keeps it (no macOS/Linux wheels).
- Smoke scripts run from a temp `.py` file, not `-c` (Windows PowerShell 5.1 mangles double quotes
  in native arguments).

CI (`.github/workflows/ci.yml`, bootstrap-smoke on windows-latest): `install.ps1 -Print -Profile gpu`
with no nvidia-smi and with a fake `nvidia-smi.cmd` (581/8.9 -> cu130, 560/8.6 -> cu126, 516 -> CPU);
`uv pip compile` wheels-only for x86_64-pc-windows-msvc of (a) what install.ps1 installs (its
overrides, the release matrix, cu130, llama cu130 wheel) and (b) plain `abstractcore[gpu]` at the
release matrix's AbstractCore. **(b) is red until the matrix pins an AbstractCore with the markers
(after 2.19.0)**, so `feat/windows-gpu` merges with the release that bumps the matrix, not before.
Both steps were run locally with portable pwsh 7.4.6: (a) passes, (b) fails on 2.19.0 as expected.

GPU runners: the repo belongs to a personal account (`lpalbou`, owner type User); GitHub's GPU
larger runners need a Team/Enterprise Cloud organization, and the repo has 0 self-hosted runners.
Nothing was configured; see 0989 for test machines.

### Verified (no hardware needed)

- `uv pip compile "abstractcore[gpu]"` (this checkout's wheels: core, vision 0.3.32, voice) for
  x86_64-pc-windows-msvc, `--only-binary :all:` except four pure-Python sdists
  (antlr4-python3-runtime, encodec, langdetect, transformers-stream-generator): py3.12 cu130,
  py3.12 cu126, py3.13 cu130, py3.11 cpu all resolve, torch `+cuXXX`, no vllm / llama-cpp-python /
  stable-diffusion-cpp-python (abstractcore `tests/install`, opt-in). The installer's own resolve
  (`abstractgateway[gpu,tray]==0.7.2` + overrides + matrix + llama cu130) also resolves wheels-only.
- Stack decision, torch selection, llama fallback order (fake uv + fake python), live progress
  (heartbeat, streaming, exit code, argument quoting), -Print plans: `tests/test_install_ps1_gpu_stack.py`
  (23 tests, pwsh), each mutation-checked red. Root suite 79 passed / 3 skipped (siblings absent in
  the worktree); `test_install_user_path.sh` 185 passed (one earlier run 184/1, not reproducible);
  `test_inventory.sh` 12 passed.
- DLL preparation and platform simulation: abstractcore `tests/utils/test_windows_dll_unit.py`,
  abstractvoice `tests/test_windows_cuda_whisper_device.py` (red-checked). Suites: abstractcore
  5616 passed (the 7 failures of that run came from the test environment's `HF_HUB_OFFLINE=1` and
  one marker assertion, both fixed/rerun green), abstractvoice 550 passed, abstractvision 375 passed.
- Wheel facts: abetlen 0.3.35 win_amd64 wheels exist for cu124/cu125/cu130/cu132/vulkan/cpu; the
  CUDA wheel ships `ggml-cuda.dll` (117 MB) without cuBLAS/cudart; ctranslate2 4.8.2 win wheel
  bundles only `cudnn64_9.dll` (the cuDNN dispatcher) and loads cuBLAS by name.

### Not verified (needs a Windows + NVIDIA run, 0989)

- That `uv tool install --torch-backend` downloads and installs the cu130/cu126 build on Windows
  (proven on macOS by the index it queries and in `uv pip compile`, not by a Windows install).
- That llama.cpp's cu130/cu125 builds load with `torch\lib` on the DLL search and report GPU offload;
  whether `llama_supports_gpu_offload()` needs `llama_backend_init()` first (both are done).
- faster-whisper on CUDA 13: cuBLAS 12 from the NVIDIA wheels next to torch's CUDA 13 cuDNN 9
  sub-libraries (ctranslate2's `cudnn64_9.dll` dispatcher may load torch's CUDA 13 cuDNN; the Whisper
  encoder's convolutions need cuDNN). Falls back to CPU only when cuBLAS 12 does not load, not on a
  cuDNN failure at transcription time.
- torchcodec/FFmpeg on Windows, a Diffusers image on CUDA, the heartbeat on Windows PowerShell 5.1
  (tested on pwsh 7.4.6 only), `nvidia-smi` output format on real drivers.
- Whisper on the CUDA 13 stack with the **released** AbstractVoice 0.13.0: it has no cuBLAS 12 check,
  so it may pick CUDA and fail at the first transcription; the installer warns.

### Release sequence and follow-ups

1. abstractvision 0.3.32 (all-gpu marker) -> 2. abstractvoice next patch (cuBLAS 12 wheels + check)
   -> 3. abstractcore next (markers, vision floor 0.3.32; raise the voice floor to that patch) ->
   4. root: bump the matrix, merge `feat/windows-gpu` (CI step (b) turns green). Until 3 ships,
   install.ps1 keeps working through its overrides; the CUDA llama builds then fail the loader check
   (2.19.0 has no DLL preparation) and fall back to Vulkan/CPU, which is the intended safe path.
2. install.sh on Linux + NVIDIA: not mirrored (not small). abetlen publishes manylinux_2_35
   cu124/cu125/cu130/cu132 wheels; PyPI's Linux torch is already CUDA. A follow-up would pick the
   llama CUDA wheel from the driver and reuse the loader check; Linux CUDA llama wheels need
   libcublas from the `nvidia-*` wheels torch pulls, on `LD_LIBRARY_PATH` or preloaded.
3. aec-audio-processing: Windows wheels cp311–cp313 only; a Python 3.14 install would need a
   compiler again (install.ps1 pins 3.12).
4. stable-diffusion.cpp on Windows: upstream `sd-server.exe` (cuda12/vulkan zips) behind the
   openai-compatible backend (out of scope above).

## Validation

`uv pip compile` checks in CI for Windows; a real Windows + NVIDIA run (none available on this
machine — needs the operator's hardware or a GPU CI runner) for the stack choice, llama cuBLAS
loading, Whisper and torchcodec/FFmpeg.
