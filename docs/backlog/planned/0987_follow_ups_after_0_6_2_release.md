# 0987 — Follow-ups after the 0.6.2 release (vision 0.3.31, core 2.19.0, root 0.6.2)

> Package: abstractvision, abstractcore, abstractframework
> Type: task
> Created: 2026-09-29
> Priority: normal
> Labels: follow-up, release, video, install-settings, docs

## Summary

Non-blocking findings from the tag gates of abstractvision 0.3.31, abstractcore 2.19.0 and root
0.6.2. Each line is small; split into its own item when picked up.

## Current code reality (2026-09-29)

Released: abstractvision 0.3.31 (c307d1d), abstractcore 2.19.0 (ee9a115, crate
`abstractcore-console` 0.4.1), root 0.6.2 (79da0a7). Gateway 0.7.2 unchanged.

## Items

**AbstractVision**
1. After a TI2V-5B run the backend drops the model (the denoiser is released before decode), but
   the AbstractCore plugin's `list_loaded_models` still reports it resident
   (`abstractcore_plugin.py:1748`). Drop the record, or make the release optional for a preloaded
   model (each rebuild costs about a minute). **Tracked in abstractvision
   `docs/backlog/planned/029_loaded_model_records_follow_backend_truth.md`.**
2. The TI2V `flow_shift` default reads 3.0 in the registry and provider metadata at every canvas
   (`mflux.py:488`); above 832x480 the backend leaves mlx-gen's 5.0. A form pre-filled from the
   metadata sends 3.0 with a 1280x704 request.
3. `tests/test_wan_vae_tiling.py` uses a per-pixel stand-in decoder, so removing the tile blend
   keeps every test green. Use a decoder that mixes neighbouring pixels.
4. The MLX cache cap is process-global (`mflux.py:4142`, restored `:4162`): two concurrent Wan
   generations in one process can leave the 8 GiB cap in place (speed, not correctness).
5. Playground text-to-video width defaults to 720, which TI2V rejects (multiples of 32).
6. `[gpu]`/`[all-gpu]` pull mlx-gen → `mlx[cuda13]` on Linux: about 2.1 GB of CUDA 13 wheels
   that core never routes (mlx-gen is Apple-only in core) and a glibc 2.35 floor for `[gpu]`.
   Measure mlx-gen on CUDA first, else make the marker Darwin-only. **Tracked in abstractvision
   `docs/backlog/planned/030_gpu_parity_with_mlx_gen.md` (GPU parity with MLX-Gen).**

**AbstractCore**
7. `model_fit.py` (~416) still adds the "KV cache estimated without model geometry" note before the
   measured-need override; the note now appears on every measured video fit with no KV added.
8. The image table's "Not available" rows for Intel Mac and Windows say "diffusers (included with
   abstractcore[gpu])" (`capability_defaults.py:498`); `[gpu]` is the Linux setting and pulls
   vLLM. Point to the direct install, as the HuggingFace hint now does.
9. Remaining bare-package hints: `vision_config.py:231`, `openai_provider.py:1315/1355/1407`,
   `base.py:3611`, `pil_text_renderer.py:60`, `apps/extractor.py:516`, `apps/judge.py:626`,
   `embeddings/manager.py:709`. **Items 8, 9, 11, 12: in progress (operator 2026-09-29: only the
   three settings are ever advised; sweep across repos, unreleased).**
10. The 24 GB TI2V sentence says "It fits once macOS lets the GPU use 20 GiB"; the raised verdict
    is tight. Say tight.
11. Direct-install hints print a POSIX-quoted command (`shlex.join`), which breaks in cmd.exe when
    the Python path has spaces.
12. `registry.py:542` (endpoint-profile clone) copies `installation_extras` but not
    `direct_install_packages`.
13. The macOS default GPU limit is assumed at 75%; this 128 GB M5 Max reports 107.5 GiB (84%), so a
    light install (no mlx to read the real limit) reports `needs_gpu_limit` where mlx reports
    `tight`. Verify on real 8 GB and 24 GB hardware before the website quotes those numbers.
14. The `mlx` alias now installs the whole `apple` setting (torch, llama-cpp-python); ai-space pins
    it. Tell downstream repos to move to the three settings.
15. Opening an Office document still runs `nvidia-smi` inside unstructured and may download NLTK
    data on first use (the telemetry itself is off since 2.19.0).
16. `tests/providers/test_generation_cancel_http_unit.py::test_guard_severs_a_raw_blocked_read` is
    timing-dependent: it failed the v2.19.0 release run once (`severed` 0) and passed on rerun.
    Make it deterministic.

**Root**
17. Older token wording remains outside the pages 0.6.2 changed; sweep for "read the token from the
    file" (the installer's pre-token fallback is allowed).
18. A leftover install lock whose pid was reused by another process blocks runs until that process
    exits (Ctrl-C under dash skips cleanup); the refusal names the pid.
19. Website: refresh the recommendations from the published core 2.19.0 export and apply the
    release-day flips (`untracked/site-rethink/REPORT.md` §15). The site stays unpublished until
    the operator says so.

**Rehearsal 0.6.3 (Linux + NVIDIA, Quadro RTX 5000 16 GB, 2026-09-29)**
20. Re-running the installer after a hand-started gateway starts a second gateway on the same
    data. With a gateway started by hand on 8080 (the summary's own `Start:` line), the preflight
    reports "port 8080 is in use by another process; using 8081 (kept for future runs)", persists
    8081, and the run then starts another `abstractgateway serve` on 8081 with the same
    `ABSTRACTGATEWAY_DATA_DIR`. Two gateways then write one store, and the pointer
    (`~/.abstractframework/gateway.json`) moves to 8081. The installer should recognise its own
    gateway on the port (pid file, pointer, `/api/health` and data dir) and reuse or restart it,
    moving to another port only for a foreign process, without persisting the move when the
    process was ours. Receipt: `untracked/rehearsal-063/32-no-nvidia-smi-print.log` line 15.
    Owner: root `scripts/install.sh` (and `install.ps1` for the same check).
    **Fixed in root 0.6.4** (branch `fix/installer-064`): the listener's pid (lsof/ss;
    Get-NetTCPConnection) running abstractgateway and serving this data dir (its serve record
    `run/gateway-serve.json`, its `--data-dir`, Linux `/proc/<pid>/environ`) is this install's
    gateway: the port is kept and the installer's start replaces it; one on another port is stopped
    too; `--no-start` leaves it running. Tests: `test_install_user_path.sh` [21] (sh + dash),
    `tests/test_install_ps1_own_gateway.py`; mutation-checked. Validated on Linux only (the OVH GPU
    VM, `install.sh`); `install.ps1` has function-level tests and a CI re-run step on Windows, no
    real Windows validation of a hand-started gateway.
21. Gateway image requests reload the model in a subprocess on every request: 54-59 s per image
    through the gateway (`29-gateway-image-unloaded-{1,2}.json`: 54.3 s, 59.0 s) against 16 s per
    image in one process (`30-direct-flux-klein.log`: load 40.6 s once, then 16.4 s and 15.4 s),
    FLUX.2 [klein] 4B on Diffusers with model CPU offload. Keep the image model resident in a
    long-lived worker (with the model-residency eject rules that already cover text) or reuse it
    across requests. Owner: abstractgateway / abstractruntime local image generation path.

**Release 0.6.3 publish (2026-09-30)**
22. uv's cached index right after a release: `uv tool install ... 'abstractgateway[gpu]==0.7.4'`
    failed "no version of abstractgateway[gpu]==0.7.4" minutes after the publish until
    `uv cache clean abstractgateway` (PyPI's simple pages allow a 10-minute cache). **Fixed in root
    0.6.4**: both installers pass `--refresh-package` for abstractgateway and every release-matrix
    package on every install (a conditional request each). Owner: root installers.
23. Launch flags, not environment variables (operator ruling): the summary's Start line and the
    background start printed `ABSTRACTGATEWAY_USER_AUTH=1 ABSTRACTGATEWAY_DATA_DIR=... abstractgateway
    serve`. **Fixed in root 0.6.4**: `abstractgateway serve --data-dir <dir>` (gateways 0.3+ turn
    user auth on by themselves; `--pin` 0.1/0.2 keep the environment). Still open: the installer
    passes the data dir to its other gateway commands (`network`, `service install`, `claim-url`)
    through the exported `ABSTRACTGATEWAY_DATA_DIR`, and the service-mode Start line
    (`abstractgateway service install --port N`) names no `--data-dir` for a custom data dir.
24. `scripts/tests/test_install_user_path.sh` on Linux (Ubuntu 26.04, dash): 6 checks fail on main
    (v0.6.3) and on the 0.6.4 branch alike, all outside the installer changes: "pointer: mode 0600"
    (`stat -f` prints a filesystem block on GNU), the two `<data>/apps/bin/abstractcode` uninstall
    checks, the two `--pin latest` / release-pin install-line checks and "nothing changed: the
    running gateway is left alone" (the tests' recorded `GATEWAY_SPEC` carries the tray extra, which
    a Linux sandbox without a display does not install). Receipt: `untracked/root-064-vm/suite-linux*.txt`.
    Owner: root tests.

**0.7.0 end-to-end proofs (Mac + Linux GPU, 2026-09-30; fixed items are in the 0.7.1 patch wave)**
25. Uploaded and published workflows land in `site-packages/abstractgateway/flows/bundles`, which
    `uv tool install` of a new version wipes (Linux end-to-end F3). `GatewayHostConfig.from_env()`
    (`config.py`) sets `flows_dir` to the packaged directory unless `ABSTRACTGATEWAY_FLOWS_DIR` is
    set; `/bundles/upload`, `DELETE /bundles/{id}` and publish write `host.bundles_dir`. A data-dir
    mechanism exists only for hosted per-user runtimes (`service.py`: `<data>/users/<t>/<u>/flows`
    with the shared dir mounted read-only). Not small: with no override, `flows_dir =
    <data_dir>/flows` (created at boot) and `framework_flows_dir` = the packaged dir;
    `bundle_host.load_from_dir` / `reload_bundles_from_disk` take a SEQUENCE of read-only framework
    dirs (per-user hosts get `[<root data>/flows, packaged]`); a boot migration COPIES (never moves)
    every `*.flow` in the packaged dir that is not in the distribution's file list
    (`importlib.metadata.files("abstractgateway")`) into `<data_dir>/flows`, logging each; shipped
    bundles become read-only (`source_kind: "framework"`: check the UIs keyed on it);
    `verify_basic_agent_loadable` runs on the packaged dir; docs (install/upgrade, workflows,
    `config_cli`). Tests: an upload survives a simulated package-dir wipe; packaged bundles still
    load; per-user hosts see admin uploads; the migration copies only non-shipped files.
    Owner: abstractgateway.
26. AbstractCode web fills the tool list only on first connect
    (`abstractcode/web/src/lib/settings_defaults.ts:65-90`: the reconnect branch only removes tools
    that disappeared), so an existing user never sees tools enabled later (the email tools after
    "Agent email tools" is turned on; Linux end-to-end F2). The gateway side is fixed in 0.7.1 (a run
    started without `input_data.tools` gets the email tools when they are active). Small fix: a
    `tools_known?: string[]` field in `Settings` (`web/src/lib/storage.ts`), set on first connect to
    every enabled name; on reconnect append enabled names not in `tools_known`, then store the
    current enabled set (tools the user switched off stay off: they are already known).
    Owner: abstractcode web.
27. Existing installs keep a stored text route their install cannot run (a light install that
    was seeded `mlx/...` by 0.7.0): 0.7.1 never recommends or seeds such a route and flags it
    (`engine_missing`) in every grid, but does not rewrite a stored route. Decide whether
    `upgrade_recommended_seed` should replace a SEEDED (never operator-edited) route whose engine
    is missing. Owner: abstractcore config.

## Acceptance criteria

- [ ] Each item fixed with a test that goes RED without it, or closed with a recorded decision.

## Receipts

`untracked/vision-gate/`, `untracked/core-2.19.0-gate/`, `untracked/root-0.6.2-gate/`,
`untracked/wave4-STAGE.md`.
Items 20-21: `untracked/rehearsal-063/`.
