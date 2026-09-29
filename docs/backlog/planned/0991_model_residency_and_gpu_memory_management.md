# 0991 — Model residency and GPU memory management: one registry, protected/ejectable models, a memory budget, automatic eviction

> Package: abstractruntime (residency registry, eviction), abstractcore (process residency, memory probes, providers), abstractvision / abstractvoice / abstractmusic (capability plugins), abstractgateway (API, console, TUI), abstractflow (model residency node), abstractframework (docs)
> Type: task
> Created: 2026-09-29
> Priority: high
> Labels: residency, gpu, memory, nvidia, apple-silicon, gateway, runtime, console

## Summary

Operator, 2026-09-29: "we normally have a way to make models resident... used in both gateway and
flow... so normally we should be able to easily control if the model stays in memory" and "we
already created something where some models can be protected (can't be ejected) but others can...
reuse that; we definitely need a clean model management system with some automated processes."

The pieces exist but are split per engine, and on the GPU rehearsal (0.6.3, OVH Quadro RTX 5000
16 GB, `untracked/rehearsal-063/`) they did not add up: an image model loaded through
`POST /models/load` was never used by image requests (fixed now, see below), an unload reported
success while the process kept 18.8 GB, and an image request next to LM Studio's 9B text model
(6.5 GiB on the GPU) ran out of GPU memory three times in a row (~2.5 min) before failing with a raw
CUDA error. Build one model management system: a single registry of every loaded model across
engines, per-model residency (resident / protected / ejectable, idle timeout), a memory budget
measured from the device that names the holders, automatic eviction of ejectable models before a
load that would not fit, typed load progress, honest errors that name the cause and the fix, and
one console/TUI view and API over it.

## What was fixed on 2026-09-29 (unreleased, local commits)

1. **Resident image/video models serve generation** — abstractruntime `a96460a`.
   Root cause: `load_model_residency(task="image_generation")` (the Gateway's `/models/load`, the
   console Load button, the flow model residency node) loads into the client's capability residency
   core, a separate `ServerCapabilityProvider` created per client
   (`abstractruntime/.../llm_client.py:5492` `_local_capability_residency_core`, via
   `abstractcore/server/capability_generation.py:507`). Generation never looked there: every local
   image/video request went to `_run_local_image_subprocess` (`llm_client.py:2292`, gate
   `_is_subprocess_safe_image_specs` at `:2104`, env `ABSTRACTRUNTIME_LOCAL_IMAGE_SUBPROCESS`
   default on), which builds a fresh `create_llm(...)` in a child process
   (`media_subprocess.py`) and loads the model again. Even with the subprocess off, generation used
   the route provider's own `self._llm.vision` plugin instance (`abstractcore/providers/base.py:2745`
   `_run_multimodal_spec` → `self.vision`), again not the resident one. So a "resident" model cost a
   full reload per request (54–59 s vs 15–16 s warm) and a second copy of the weights while the
   request ran. The subprocess itself is documented (crash isolation: "Native Apple/Metal backends
   can abort the interpreter", `media_subprocess.py:1-5`) and stays the default.
   Fix: when every media spec names a model RESIDENT in the residency core (the plugin's own
   provider/model matcher, `huggingface` == `diffusers`), the request runs in-process on that core
   (`_resident_media_rows_for_specs` / `_run_resident_media_specs`, `llm_client.py:2195`; wired at
   `:8885`); pooled clients reach the pool's core through `_capability_residency_parent`
   (`:10578`). Same process-wide serialization lock as the subprocess (`_LOCAL_IMAGE_SUBPROCESS_LOCK`,
   `:62`). Metadata `execution_mode="resident_in_process"`, `resident_load_ids`. The explicit load is
   the opt-in; unloading returns to the subprocess. Tests: `tests/test_resident_media_generation.py`
   (8, RED without the fix, including a real AbstractVision plugin run that proves the load's backend
   object is the one generation uses). Runtime docs corrected (`docs/integrations/abstractcore.md`,
   `docs/faq.md`, `docs/api.md` said local media residency was unsupported). Supersedes 0987 item 21.
   **Measured on the OVH VM** (gateway 0.7.3 + this file): `/models/load` 54.4 s once, then two
   images through the gateway in **19.0 s and 17.3 s** (before: 54.3 s and 59.0 s each), no child
   process on the GPU.

2. **A Diffusers unload frees the weights** — abstractvision `47ac360`.
   Root cause: `HuggingFaceDiffusersVisionBackend._unload_locked`
   (`abstractvision/backends/huggingface_diffusers.py`, `for p in pipes: unfuse = getattr(p,
   "unfuse_lora") ... unload = getattr(p, "unload_lora_weights")`) ran `gc.collect()` while the loop
   variable and the two bound methods still referenced the last pipeline, so its reference cycles
   (accelerate offload hooks) survived the collect; glibc also kept the freed heap. Measured on the
   VM: 18.8 GB RSS after `unload()` returned `state: "unloaded"`, 6.2 GB after one more collect,
   1.6 GB after `malloc_trim(0)`. In the gateway this is what killed it: after the unload, the next
   request's subprocess loaded another copy and the kernel OOM killer took the gateway
   (`Out of memory: Killed process 87754 (abstractgateway) anon-rss:22110616kB`, 19:01:16). Fix:
   adapter release in its own frame (`_release_pipeline_adapters`), `_return_freed_host_memory()`
   (`malloc_trim(0)` on Linux) after the collect. Test:
   `tests/test_diffusers_unload_releases_memory_unit.py` (RED without either part).
   **Measured on the VM** (same process, pipeline load without the warm-up generation because LM
   Studio then held 6.5 GiB of the GPU): original code 16 304 MB → **16 277 MB after the unload**;
   with the fix 16 155 MB → **856 MB after the unload**.

## Current code reality (2026-09-29, read in source)

Residency is implemented FOUR different ways, with two different notions of "protected":

| Engine family | Where the weights live | Load / list / unload | "Protected" | Idle timeout | Memory truth |
|---|---|---|---|---|---|
| Text, in-process (MLX, HuggingFace transformers, llama.cpp GGUF) | gateway process | runtime `LocalAbstractCoreLLMClient` / `MultiLocalAbstractCoreLLMClient` `load/list/unload_model_residency`; core `process_residency.resident_rows/eject` (`abstractcore/providers/process_residency.py:77,90`) | **lock**: `lock_model_residency` (`llm_client.py:8306`, `:11395`), claims registry `claims_for` / `eject_unclaimed` (`process_residency.py:173,203`), refusal `model_locked_by_other_client` 409 (`_explicit_eject_guard`, `llm_client.py:4303`); pool eviction skips locked pairs (`:10322`) | none: `ttl_s`/`keep_alive` reported as not applied (`_IN_PROCESS_TIMED_OPTIONS`, `:4219`) | `mlx_residency` / `hf_residency` holder rows, `held_bytes` |
| Text, external servers (LM Studio, Ollama; vLLM planned in 0990) | another process | provider `list_loaded_models` / `unload_model` (`lmstudio_provider.py:779,1010`, `ollama_provider.py:159,233`); host sweep `utils/residency.py:70` | lock is client-side only; Ollama gets `keep_alive` reinforcement, LM Studio "may still evict on its own policy" (`_apply_local_provider_side_lock_knob`, `llm_client.py:~5040`) | Ollama `keep_alive`, LM Studio TTL (provider side) | the server's own API (size, no device split) |
| Media, in-process (Diffusers, MLX-Gen, sd.cpp; TTS/STT; music) | gateway process, per-client residency core | `_local_capability_residency_result` (`llm_client.py:5657`) → plugin `load_resident_model` / `list_loaded_models` / `unload_resident_model` (`abstractvision/integrations/abstractcore_plugin.py:1732-1830`, `abstractvoice/.../abstractcore_plugin.py:1773,4834`) | plugin-level **resident** flag: a resident backend is never retired when another request backend becomes active (`abstractcore_plugin.py:986` `_activate_request_backend`); **`/models/lock` refuses media** ("only supported for text_generation", `_local_model_residency_lock_result`, `llm_client.py:5143`) | none | none (no bytes in the rows) |
| Media, one-shot subprocess (image/video by default) | a child process per request | none: invisible to every listing while it runs | n/a | n/a | none; the parent never sees its GPU use |

Other facts that bound the design:

- **Memory probes exist but are not joined up.** `abstractcore/utils/memory.py:543`
  `get_memory_snapshot()` (system RAM, process, MLX active/cache/peak, `torch.cuda.mem_get_info`
  at `:293`); `utils/host_profile.py:114` (nvidia-smi rows); `utils/context_estimate.py:270`
  (CUDA free bytes for context sizing); gateway `host_metrics.py:46` (nvidia-smi utilization for the
  console). The Diffusers backend decides its CPU offload from `torch.cuda.mem_get_info`
  (`huggingface_diffusers.py:_cuda_offload_decision`), i.e. from whatever happens to be free, with
  no idea who holds the rest. None of them names holders per process (NVML
  `nvmlDeviceGetComputeRunningProcesses` does; the rehearsal OOM message did, from PyTorch:
  "Process 65401 has 6.50 GiB memory in use").
- **The "Loaded models" view** is the console Resources tab (`abstractgateway/console.py:1753`)
  and the TUI store (`console-tui/src/store.rs`), both over `GET /models/loaded`
  (`routes/gateway.py:26210`); actions `/models/load` (`:26891`, with `lock: true` = load then
  lock), `/models/unload` (409 on a locked refusal), `/models/lock`, `/models/unlock`
  (`:26958-26980`). One-shot subprocess work never appears there.
- **Flows** preload through the model residency node (`abstractruntime/visualflow_compiler/visual/executor.py:3084`,
  `adapters/effect_adapter.py:862`) → `MODEL_RESIDENCY` effect (`effect_handlers.py:4680`) → the
  same host facade. With fix 1, a flow that loads an image model before a loop of image nodes now
  gets warm generations.
- **Default switch eject** (clean switch, 2026-09-25) unloads the previous in-process text model
  before building the next, and `_retire_capability_residency_core` (`llm_client.py:10451`) unloads
  resident media engines when capability routes change. Nothing evicts across engine families
  (e.g. LM Studio's text model to make room for an image load).
- **The GPU lock protocol** (`untracked/gpu.lock`, 2026-09-29) exists for agents on this Mac, not
  in the product.

## Design

1. **One registry** (abstractruntime, host scope; one per gateway process, shared by every
   multi-local client, per-user service and entity runtime). A row per loaded model:
   `{id, task(s), engine, provider, model, placement: in_process|external_server|subprocess,
   pid, device: cuda:N|mps|cpu, bytes: {device, host}, residency: resident|protected|ejectable,
   idle_timeout_s, loaded_at, last_used_at, inflight, owner(s), source: explicit|request|default}`.
   It is fed by the existing truths, never guesses: core `process_residency` rows (text in-process),
   the host sweep (LM Studio/Ollama; vLLM when 0990 lands), the capability plugins' loaded lists
   (media), and the one-shot subprocess while it runs (registered on spawn, removed on exit, pid
   known). Unknown stays unknown (a server that does not answer contributes a `stale` row, never
   "nothing loaded").
2. **Residency levels, reusing what exists.** `protected` = today's text **lock** (claims registry,
   409 refusal, force to override) extended to media and external servers; `resident` = today's
   plugin resident flag / explicit load: kept warm, used by generation (fix 1), evictable only by an
   explicit unload or when the operator's budget rule allows it; `ejectable` = anything loaded by a
   request or a default that nobody protected. `/models/lock` stops refusing media tasks.
   Idle timeout per row (in-process engines get a real timer in the registry, external servers get
   their native TTL/keep_alive when they have one).
3. **Memory budget from the device.** CUDA: NVML (`pynvml`/`nvidia-ml-py`, already a torch
   dependency on Linux) for total/free and per-process holders, mapped to registry rows by pid
   (gateway pid → in-process rows, LM Studio / Ollama / vLLM pids → their server rows, subprocess
   pid → its row, anything else "other process"). Apple silicon: unified memory — the Metal
   working-set limit (`recommendedMaxWorkingSetSize`, the ~75% default recorded 2026-09-28) plus
   `mx.get_active_memory`/cache for in-process MLX, server-reported sizes for LM Studio/Ollama,
   system RAM from `get_memory_snapshot`. Host RAM counts too (model CPU offload keeps a 15 GB
   pipeline in RAM; the VM OOM above was host RAM, not VRAM).
4. **Automatic eviction before a load that would not fit.** Every load (explicit, request-driven,
   subprocess spawn) first asks the registry for a fit: the model's expected footprint (catalog size
   / safetensors bytes / measured peak from a previous load, recorded per model) against the device
   and host budget. If it does not fit, evict `ejectable` rows LRU (external servers through their
   own unload API: LM Studio native REST unload, Ollama `keep_alive: 0`, vLLM stop), never
   `protected`, `resident` only when the operator's rule says so, never a row with inflight work.
   If it still does not fit, refuse BEFORE loading with a typed error. The same step runs before
   the default-switch load and before a subprocess spawn.
5. **Typed load progress** as `abstract.progress` records (`kind: "load"`, phases `evicting` /
   `downloading` / `loading` / `warming` / `ready`, bytes where known), the same channel image
   generation already uses; the console/TUI show them on the row.
6. **Honest errors.** A refused or failed load names the cause from typed data, never from log
   text: `insufficient_gpu_memory {needed, free, holders: [{row|pid, bytes}]}` with the fix
   ("unload qwen/qwen3.5-9b in LM Studio (6.5 GiB) or mark it ejectable"); an unload that leaves
   memory held reports `ok: false` with the residual (the Diffusers case above reported success).
7. **Console / TUI / API.** One Resources table over the registry: engine, placement, device and
   host bytes, residency level with a control (protect / resident / ejectable), idle timeout, last
   used, inflight, Unload / Force unload; a device bar per GPU with holders; load progress. API:
   `GET /models/loaded` gains the new fields (additive), `POST /models/residency {id, residency,
   idle_timeout_s}`, `/models/lock` works for every task, `GET /models/budget`. Flow: the model
   residency node gets `residency` and `idle_timeout_s` inputs.

## Acceptance criteria

- [x] An image model loaded through `/models/load` (or a flow's residency node) serves the next
      image requests in-process: no reload, no second copy (fix 1; VM: 19.0 s / 17.3 s vs 54–59 s).
- [x] A Diffusers unload returns the weights: host RSS back near baseline after the call (fix 2;
      VM measurement in Receipts).
- [ ] `GET /models/loaded` lists every loaded model across in-process text, external servers,
      in-process media and running subprocesses, each with device/host bytes and a residency level;
      a probe that fails shows up as `stale`, never as absence.
- [ ] `protected` works for every task (media included) and survives: default switch, capability
      route change, pool eviction, automatic eviction; only `force` removes it, and the refusal is a
      409 naming the holder.
- [ ] With LM Studio holding an ejectable 6.5 GiB text model on a 16 GB GPU, an image request
      evicts it first and succeeds in the warm time (+ the text model's unload time); with the text
      model protected, the request fails in under 5 s with `insufficient_gpu_memory` naming LM
      Studio's model, its size and the fix — no three 40 s retries.
- [ ] Idle timeout unloads an ejectable in-process model after N s of no use and the row says so;
      protected/resident rows ignore it.
- [ ] Load progress appears in the console and TUI within 1 s of the load starting.
- [ ] Mac: the same flows with MLX text + MLX-Gen image under the Metal working-set limit; the
      budget reflects unified memory (no double counting of RAM and "VRAM").
- [ ] Every rule above has a test that goes RED without it (fakes for NVML/Metal; no model loads in
      unit tests).

## Validation plan

- **Linux + NVIDIA (OVH VM, Quadro RTX 5000 16 GB, Turing; AWS g4dn.xlarge T4 16 GB per 0989):**
  clean gpu install of the release candidate; LM Studio 9B loaded; run the acceptance scenarios
  above through the gateway API and the console; record `nvidia-smi --query-compute-apps` and
  gateway RSS every 2 s (the `untracked/rehearsal-063/vram*.log` method) and `journalctl -k` for
  OOM kills. Include a 20-request image loop with a resident model (steady RSS/VRAM) and a
  load → unload → subprocess request sequence (no host OOM).
- **Mac (M-series, this machine and a 24 GB one):** the MLX text + MLX-Gen image scenarios under
  the GPU lock protocol (`untracked/gpu.lock`, one model process at a time, `vmmap` not RSS for
  Metal), with the same acceptance criteria against the Metal working-set limit.
- **Windows + NVIDIA** once 0988 ships: the eviction scenario only.

## Receipts

- Rehearsal evidence: `untracked/rehearsal-063/28-gateway-image-{1,2}.json` (OOM after 3 attempts,
  155 s / 127 s), `29-gateway-image-unloaded-{1,2}.json` (54.3 s / 59.0 s),
  `30-direct-flux-klein.log` (load 40.6 s, then 16.4 s / 15.4 s).
- 2026-09-29 VM runs (files on the VM under `~/residency-0991/`): `run.log` (load 54.4 s, resident
  images 19.0 s and 17.3 s through the gateway, unload 0.7 s; the following subprocess request
  killed the gateway by host OOM because of the unload leak), `mem.log` (gateway RSS 213 MB →
  18 466 MB after load → 18 438 MB 30 s after unload), `direct.log` (plugin load/unload in one
  process: 18 821 MB → 18 791 MB after unload → 6 216 MB after gc → 1 583 MB after malloc_trim),
  `direct2.log` (loop variable cleared only: still 16 850 MB — the bound methods also held it),
  `direct3.log` (full fix; the warm-up generation ran out of GPU memory because LM Studio had
  loaded Qwen3.5-9B, 6.5 GiB, meanwhile), `direct4-orig.log` / `direct4.log` (load without warm-up:
  16 277 MB held after unload with the original code, 856 MB with the fix). After the runs the VM's
  installed files were restored to the released ones (md5 checked; backups `*.orig-*` in the same
  directory) and the gateway restarted on 127.0.0.1:8080.
- Commits: abstractruntime `a96460a`, abstractvision `47ac360`. Not pushed, not released.
