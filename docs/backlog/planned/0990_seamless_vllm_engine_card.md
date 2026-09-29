# 0990 — Seamless vLLM Engines card: no-sudo toolchain, gateway-supervised `vllm serve`, per-GPU flags

> Package: abstractgateway (Engines card, supervisor), abstractcore (`gpu` setting, `vllm` provider), abstractframework (docs)
> Type: task
> Created: 2026-09-29
> Priority: normal
> Labels: gpu, linux, nvidia, vllm, engines, gateway, installer

## Summary

On Linux + NVIDIA, vLLM installs from PyPI but does not start on a machine without a system C
compiler: every Triton kernel (vLLM's own sampler, Triton attention, torch.compile/inductor
output) compiles a small C launcher at first use and fails with
`RuntimeError: Failed to find C compiler. Please specify via CC environment variable`. The fix
that needs no sudo and no system packages was found and measured on the OVH test VM: the `ziglang`
wheel as `CC`, through a small wrapper. Build an Engines card "vLLM" in the gateway console:
**Install** (vLLM + that toolchain into the engine's Python), **Start / Stop** (`vllm serve` as a
gateway-supervised process on a free loopback port with per-GPU flags), a health check, and
registration as the `vllm` provider endpoint for routes. Live progress, because the first start
compiles kernels for 60–80 s. Failures name the cause and the fix from typed checks, never from
matching log text.

## Why

The `gpu` setting already installs vLLM into the gateway's Python (`abstractcore[gpu]`,
`engines_install.py::_install_vllm`), but nothing starts it, and on a stock Ubuntu (no
`build-essential`) it cannot start at all. Root backlog 0988/0989 made NVIDIA a supported setting;
vLLM is the high-throughput engine of that setting and should work with zero manual steps.

## Research record (2026-09-29, OVH VM, verified)

Machine: Quadro RTX 5000 16 GB (Turing, compute capability 7.5), driver 595.91.07 / CUDA 13.2,
Ubuntu 26.04, 4 vCPU, 26 GiB RAM. Everything ran as a separate user `vllmtest` in its own uv venv
(`uv venv --managed-python --python 3.12`, python-build-standalone 3.12.14). Logs, scripts, and
the generated wrapper: `untracked/vllm-seamless/` (`logs/`, `scripts/`).

- `uv pip install vllm` resolved **vLLM 0.30.0, torch 2.13.0 (CUDA 13), triton 3.7.1,
  flashinfer-python 0.6.18.post1, transformers 5.17.0** in 24 s. The venv takes 7.6 GB. The
  wheels already include `nvidia-cuda-nvcc` 13.4.92, so `nvidia/cu13/bin/nvcc` exists in the venv.
- The gateway env on the same VM (installed by the gpu setting) resolved **vLLM 0.22.1 / torch
  2.11**. The other `gpu` packages hold vLLM back there. The flags below must work on both.
- Python headers: python-build-standalone ships them
  (`sysconfig.get_paths()["include"]` → `.../cpython-3.12.14-linux-x86_64-gnu/include/python3.12/Python.h`).
  They are not a blocker.

### What needs a compiler, and why (reproduced with PATH stripped of gcc/cc/c++/clang)

| Component | Needs | When | Avoidable? |
|---|---|---|---|
| Triton NVIDIA driver `cuda_utils.c` + per-kernel `__triton_launcher.c` | a **C compiler** (`CC`, else `which gcc`/`clang`) + Python headers + libcuda | first Triton kernel of the process. In 0.30 that is the V2 runner's gumbel sampler, so **eager mode fails too** (log B) | **No**, on any GPU generation |
| torch.compile (inductor) → Triton | the same C compiler | engine warm-up, unless `enforce_eager` / `-cc.mode=0` | yes, but Triton still needs it |
| FlashInfer JIT (attention on cc 10.x, top-k/top-p sampler on cc ≥ 8.0, vLLM 0.22's default attention on Turing) | **nvcc + a GNU C++ host compiler with libstdc++** | first use. For the sampler that is the **first request with top_p/top_k**: a runtime crash, not a startup error | yes: `VLLM_USE_FLASHINFER_SAMPLER=0`, the Triton/FlashAttention backends, or `flashinfer-jit-cache` |

- Log A (defaults, no compiler): `InductorError: RuntimeError: Failed to find C compiler`.
  Log B (`enforce_eager`, no compiler): the same error from `sample/gumbel.py` → `triton/backends/nvidia/driver.py`.
- vLLM 0.22.1 picked FLASHINFER attention on Turing and died with `Could not find nvcc and
  default cuda_home='/usr/local/cuda' doesn't exist` (root `untracked/gpu-linux/21-vllm-after.log`).
  vLLM 0.30 picks TRITON_ATTN on cc 7.5 by itself (`FlashAttention.supports_compute_capability`
  is `>= 8.0`, and FlashInfer is gone from the Turing list).

### The toolchain: `ziglang` wheel as `CC` (verified)

`uv pip install ziglang` (0.16.0, 395 MB installed) plus a generated `/bin/sh` wrapper
(`scripts/generated-cc-wrapper.sh`, generator `scripts/mkzig.sh`) that does two things:
1. It runs `zig cc -target x86_64-linux-gnu.2.28 …`. With an explicit target, zig uses only its
   bundled glibc headers and stubs and its own lld. `-v` shows no `/usr/include`, so the machine
   needs no `libc6-dev`, no binutils and no gcc. The output runs on any glibc ≥ 2.28.
2. It rewrites Triton's GNU `-l:libcuda.so.1` into the resolved path (searching the `-L` dirs,
   then `/usr/lib/x86_64-linux-gnu`, `/usr/lib64`, `/usr/lib`, `/usr/lib/wsl/lib`). Without a
   system `cc`, zig's lld fails with `unable to find library -l:libcuda.so.1`. With gcc on PATH the
   same command links, which is exactly the kind of machine-dependent failure the card must not have.

The first zig compile builds its libc stubs in 3.9 s (46 MB, `ZIG_GLOBAL_CACHE_DIR`). Later
compiles take 0.03 s.

**nvcc with zig as the host compiler does NOT work** (log FI). nvcc accepts zig/clang as `-ccbin`,
but zig ships LLVM libc++ 21. CUDA 13 `crt/host_defines.h` rejects libc++ < 22 on x86, and forcing
past that (`-D_ALLOW_UNSUPPORTED_LIBCPP`, nvcc pinned to 13.0.88 to match cudart 13.0) ends in
cudafe++ errors inside libc++ `<chrono>`. No pip wheel ships libstdc++ headers. So the design
avoids FlashInfer JIT instead of trying to feed it. The alternative for cc ≥ 8.0 is
`flashinfer-jit-cache==<flashinfer version>+cu130` from `https://flashinfer.ai/whl/cu130`
(1.5 GB, AOT cubins for sm_80/89/100a/103a/120, no nvcc needed). It installed and loaded without
JIT on the VM, but has no sm_75 kernels (`no kernel image is available`, log FI2).

### Measurements (Qwen/Qwen3-1.7B, fp16 auto-cast from bf16, max_model_len 4096 offline / 8192 serve)

| Mode | First start (cold caches) | Warm start | 1 stream decode | Batch |
|---|---|---|---|---|
| vLLM defaults (torch.compile + CUDA graphs), zig CC, GMU 0.6 | 101.5 s | 60.1 s | 85.6 tok/s | 16 prompts: 905 tok/s |
| `enforce_eager` | 57.8 s | 21.3 s | 40.8 tok/s | 16 prompts: 531–626 tok/s |
| **`-cc '{"mode":0,"cudagraph_mode":"FULL_DECODE_ONLY"}'`** (recommended) | 61.4 s | 27.0 s | 84.0 tok/s | 16 prompts: 891 tok/s |
| `vllm serve`, recommended flags, GMU 0.45, cold (zig + Triton + vLLM caches wiped) | **74.3–75.8 s to `/health` 200** | **35.2 s** | **85.2–85.6 tok/s**, TTFT 66–80 ms | 8 concurrent HTTP streams: 502–508 tok/s |
| `vllm serve` Qwen/Qwen3-4B-AWQ (Marlin kernels), GMU 0.45 | 44.4 s (Triton cache warm) | – | 98.6 tok/s, TTFT 91 ms | 8 concurrent: 576 tok/s |

- Skipping torch.compile but keeping decode CUDA graphs keeps 98 % of the throughput and halves
  both start times. Eager mode loses half the decode speed.
- VRAM: Qwen3-1.7B at GMU 0.45 = 6.86 GB in `nvidia-smi` (3.22 GiB weights, 2.86 GiB KV = 26,784
  tokens). Qwen3-4B bf16 (8 GB of weights) does not fit in 0.45 × 16 GB, but the AWQ build does.
- The final recipe run (explicit `--attention-backend TRITON_ATTN`, `VLLM_USE_FLASHINFER_SAMPLER=0`,
  a top_p/top_k request) worked. Its speed (52.7 tok/s) is contaminated: LM Studio's llama-server
  (another worker, 6.65 GB) was running on the same GPU at the same time. This is itself the
  memory/compute-sharing case the card must handle.
- AbstractCore 2.19.1 (PyPI) `create_llm("vllm", model="Qwen/Qwen3-1.7B", base_url="http://127.0.0.1:<port>/v1")`:
  `generate` → `'Paris'` (the `<think>` block was stripped), streaming gave 41 chunks, and
  `list_available_models()` → `['Qwen/Qwen3-1.7B']`. With a small `max_tokens`, Qwen3 spends the
  budget on thinking and streams no content. That is expected, and `--reasoning-parser qwen3` is
  optional.

### Not done / to verify

- `apt-get remove build-essential` was **not** run: the VM is shared with a release-rehearsal
  worker whose install may build wheels. Compiler absence was simulated with a PATH containing
  every `/usr/bin` tool except compilers, and the zig target is hermetic (no system headers,
  libs or linker, except the driver's libcuda). The first real no-gcc machine run is still to do.
- **Ampere / Ada / Hopper / Blackwell**: the per-cc table below is read from vLLM 0.30 source
  (`platforms/cuda.py::_get_backend_priorities`, `topk_topp_sampler.py`), not run. Needs a cc ≥ 8.0
  card (0989).
- **Windows**: vLLM has no Windows support upstream. The card shows "Run it in WSL2 (Ubuntu) or
  point the gateway at a remote vLLM server". Inside WSL2 the same Linux recipe should apply
  (libcuda is at `/usr/lib/wsl/lib`, already in the wrapper's search list). To verify.
- aarch64 Linux (GH200 / Jetson): needs the `aarch64-linux-gnu.2.28` zig target. Not tested.

## Design

### 1. Install (typed plan, no admin)

- **Where.** Decision for the operator: keep vLLM in the gateway's Python (today's behavior, which
  shares torch with the other gpu engines and gets whatever vLLM the other pins allow, 0.22.1 on
  the VM), or give it a dedicated engine venv under `gateway_engines_dir()/vllm/venv` (a fresh
  resolve gets the newest vLLM; +7.6 GB; no pin fights). Either way `vllm serve` runs as its own
  process, so the provider seam is the same HTTP endpoint. Recommendation: a dedicated venv,
  because vLLM pins exact torch versions and the process is separate anyway.
- **Packages.** `vllm` (+ torch CUDA wheels chosen by `--torch-backend=auto`, as `_vllm_argv`
  does today) + `ziglang` (marker `sys_platform == 'linux' and platform_machine == 'x86_64'`, or
  `aarch64`). For cc ≥ 8.0 there is an opt-in "faster sampling" item: `flashinfer-jit-cache` from
  the flashinfer index, 1.5 GB. Plan sizes shown on the card: about 7.6 GB installed for vLLM and
  torch, about 0.4 GB for zig, and 1.5 GB for the optional jit-cache.
- **Toolchain step.** Write `<env>/toolchain/cc` (the wrapper above, with the absolute zig path
  from `ziglang.__file__`) and record it in the engine's state file. Then verify it: compile a
  3-line C file that includes `Python.h` and `cuda.h` and links `-l:libcuda.so.1` with the exact
  Triton flags. A non-zero exit → `InstallFailed(code="toolchain_failed")` with the compiler's
  stderr in the job log.
- **Markers.** vLLM stays Linux-only (`sys_platform == 'linux'`). On Windows / macOS the card is
  `supported: false` with the existing reasons (`engines_install.py` line ~903), plus the WSL2
  sentence for Windows.
- Progress: pip bytes via the existing `_pip(ctx, …, lo, hi)` job machinery.

### 2. Start (gateway-supervised process)

Command, built from typed host facts only:

```
env CC=<env>/toolchain/cc  ZIG_GLOBAL_CACHE_DIR=<engines>/vllm/cache/zig
    TRITON_CACHE_DIR=<engines>/vllm/cache/triton  VLLM_CACHE_ROOT=<engines>/vllm/cache/vllm
    VLLM_USE_FLASHINFER_SAMPLER=0            # unless flashinfer-jit-cache is installed and cc >= 8.0
    VLLM_NO_USAGE_STATS=1  DO_NOT_TRACK=1  HF_HOME=<the gateway's HF home>
<env>/bin/vllm serve <model> --host 127.0.0.1 --port <free port>
    --served-model-name <model> --max-model-len <from model card / user>
    --gpu-memory-utilization <computed, see 4>   (or --kv-cache-memory-bytes)
    -cc '{"mode":0,"cudagraph_mode":"FULL_DECODE_ONLY"}'     # "Fast start" (default)
    [--attention-backend TRITON_ATTN]                         # when compute capability < 8.0
```

- **Per-cc flags.** The compute capability comes from NVML
  (`nvidia-smi --query-gpu=compute_cap` or `pynvml`). It is a number, not text matching.

  | cc | Attention | Sampler | dtype | Notes |
  |---|---|---|---|---|
  | < 7.5 | – | – | – | unsupported: CUDA 13 (the torch/vLLM wheels) dropped Maxwell/Pascal/Volta. The card says so |
  | 7.5 (Turing) | `--attention-backend TRITON_ATTN` (explicit, because vLLM 0.22 picks FLASHINFER here) | Triton | bf16 checkpoints auto-cast to fp16 (vLLM does it) | FP8 not supported; AWQ/GPTQ via Marlin works |
  | 8.x, 9.x, 12.x | default (FLASH_ATTN, prebuilt in the vLLM wheel) | `VLLM_USE_FLASHINFER_SAMPLER=0` unless jit-cache | auto (bf16) | to verify on hardware |
  | 10.x (B200/GB200) | default is FLASHINFER → **requires `flashinfer-jit-cache`** (install it automatically for cc 10.x) or `--attention-backend FLASH_ATTN` | as above | auto | to verify |
- **Modes.** "Fast start" (above: 61 s cold / 27 s warm offline, 98 % throughput) is the default.
  "Max throughput" drops `-cc` (torch.compile + CUDA graphs: 101 s cold / 60 s warm, about +2 %).
  "Debug" adds `--enforce-eager`.
- **Supervision.** `setsid` process group, stdout/stderr to `<engines>/vllm/logs/serve-<ts>.log`,
  pid + port + argv + env digest in `<engines>/vllm/state.json`. Stop sends SIGTERM to the group,
  waits 30 s, then SIGKILL. The gateway stops it on its own shutdown and never leaves it running
  past the gateway (no systemd unit, no persistence). A crash moves the card to `failed` with the
  exit code and log tail.
- **Health.** `GET /health` 200, then `GET /v1/models` lists the served name → `running`. Timeout
  300 s cold / 120 s warm, from the recorded "first start done" marker, not from log lines.
- **Registration.** On `running`, register `vllm` with `base_url = http://127.0.0.1:<port>/v1`
  (AbstractCore `VLLM_BASE_URL` semantics, default `http://localhost:8000/v1`) in the gateway's
  provider config, so routes can choose `vllm/<model>`. Unregister on stop. The port is picked
  free at each start and never assumed to be 8000.

### 3. Live progress for the first start

Progress comes from typed signals only:
1. pip install (existing job events).
2. "Preparing the compiler (first time)": the toolchain self-test.
3. "Loading the model": process alive, `/health` not yet up.
4. "Compiling GPU kernels and capturing graphs (first start ≈ 1–1.5 min, later ≈ 30 s)": elapsed
   time against the recorded previous start duration.
5. "Ready": health OK.

The log is streamed to the card verbatim for users who expand it. No state is derived by
matching log text.

### 4. GPU memory

- Before starting, read NVML `memory.free` / `memory.total`. `gpu_memory_utilization` is a
  fraction of **total** memory, and vLLM refuses to start when free memory is below it. Compute
  `gmu = min(user_budget_bytes, free_bytes − 1 GiB margin) / total_bytes`. Refuse with a typed
  reason when the result is below weights + a minimum KV (weights size from the model's
  safetensors index), naming the processes that hold the GPU (NVML compute-apps: LM Studio
  llama-server, the gateway's own diffusers/voice engines) and offering "stop <engine>" actions.
- Prefer `--kv-cache-memory-bytes` when the user sets an explicit budget, so vLLM does not grab a
  fraction that other local engines later need. The gateway's image/voice engines load lazily and
  can OOM later if vLLM took most of the card: show vLLM's reserved share on the card, and the
  same share in the image/voice engines' fit checks.

### 5. Failures (cause + fix, from typed checks)

| Check (before or at start) | Card message |
|---|---|
| No NVIDIA driver / NVML init fails | "No NVIDIA driver is loaded. Install the recommended driver (`sudo ubuntu-drivers install`) and reboot." |
| Driver too old for the torch CUDA build (NVML driver version < 580 for cu13) | name both versions and the fix |
| cc < 7.5 | "This GPU (compute capability X) is older than the CUDA 13 build of vLLM supports." |
| Toolchain self-test exit ≠ 0 | "The bundled compiler could not build a test file", with stderr attached and a "Reinstall toolchain" action |
| Free VRAM below the need | list the holders, with "Stop <engine>" actions (section 4) |
| Model not downloaded / gated | the existing model-download flow and HF licence prompt |
| Process exits before health | exit code + log tail + "Start again in Debug mode" |

## Acceptance criteria

- [ ] On a fresh Ubuntu with only the NVIDIA driver (no build-essential), Engines → vLLM → Install
      → Start serves a model with no terminal step, and `apt list --installed | grep gcc` stays empty.
- [ ] Turing (cc 7.5) and one cc ≥ 8.0 card both start with flags chosen from NVML cc, and a
      top_p/top_k request succeeds on both (the cc ≥ 8.0 FlashInfer sampler path).
- [ ] Routes can select `vllm/<model>`. AbstractCore `create_llm("vllm", base_url=…)` generates and
      streams through the gateway.
- [ ] Start refuses with a named reason when another engine holds the VRAM. Stop frees the GPU
      (NVML shows no vLLM process).
- [ ] First-start progress shows the compile phase. A warm start is ≤ 40 s for a 2B model on the
      test VM.
- [ ] Every check in the failure table has a test that removes its input and goes red.

## Receipts

- Evidence: `untracked/vllm-seamless/logs/` (A/B = no compiler, C–H = zig modes, FI/FI2 = the
  FlashInfer/nvcc attempts, S1–S5 = `vllm serve`), `untracked/vllm-seamless/scripts/`
  (`mknocc.sh`, `mkzig.sh`, `generated-cc-wrapper.sh`, `serve.sh`, `bench.py`, `core_test.py`).
- Earlier: `untracked/gpu-linux/10-vllm.log`, `21-vllm-after.log`.
- Related: 0988 (gpu setting on Windows), 0989 (NVIDIA test machines).
