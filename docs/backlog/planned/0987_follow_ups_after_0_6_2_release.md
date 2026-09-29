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

## Acceptance criteria

- [ ] Each item fixed with a test that goes RED without it, or closed with a recorded decision.

## Receipts

`untracked/vision-gate/`, `untracked/core-2.19.0-gate/`, `untracked/root-0.6.2-gate/`,
`untracked/wave4-STAGE.md`.
