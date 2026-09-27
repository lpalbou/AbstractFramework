# 0944 — MiniMax-H3 local video on Apple silicon through MLX-Gen

> Package: abstractvision, abstractcore
> Type: task
> Created: 2026-09-27
> Priority: normal
> Labels: video, mlx-gen, catalog, partial-download, next-wave

## Summary

MLX-Gen (the Apple silicon image/video engine AbstractVision wraps) runs MiniMax-H3 locally, but the framework
cannot: AbstractVision refuses every video family except Wan, and AbstractCore would download the whole
`MiniMaxAI/MiniMax-H3` repository (about 498 GB) where MLX-Gen needs about 134 GiB of it. This item wires
MiniMax-H3 end to end on 128 GiB Macs: engine support in AbstractVision, a partial-download field in the
AbstractCore catalog, a catalog row with an honest fit, and the consoles' video category showing it.

## Why

Operator, 2026-09-27: "mlx-gen does enable minimax h3, but maybe we haven't updated abstractvision and
abstractcore" — and, on the release order: "bad planning, you should have done that before releasing
abstractcore. changing it now would mean doing yet another full release ... create a backlog planned item
instead." Must land in the NEXT wave, before AbstractCore is released again (see
`feedback-release-plan-lower-packages-first`).

## Current code reality (2026-09-27, abstractvision 0.3.30, abstractcore 2.17.0)

- `abstractvision/src/abstractvision/backends/mflux.py:3966` refuses any video family other than Wan;
  `minimax-h3` is absent from `_MFLUX_MODELS` (`:211`) and the aliases (`:509-538`); `_ensure_model_impl`
  (`:2748`) has no dispatch for it.
- AbstractCore's materializer downloads whole Hugging Face repos for mlx-gen artifacts
  (`abstractcore/config/model_materializer.py`, `_download_huggingface`); there is no per-artifact
  `allow_patterns` in the seed schema (`abstractcore/assets/model_downloads_catalog.json`,
  `model_catalog.py` validator).
- Wan2.2 rows (TI2V-5B, T2V-A14B, I2V-A14B) are in the catalog since 2.17.0 with the `video` tag and the
  `resident` fit field; MiniMax is not.
- MLX-Gen memory figures (its `docs/minimax-h3.md`): 80.5 GiB MLX memory at 960x544, 84.8 GiB at 1344x768
  → 128 GiB Macs only. 8-bit quantization is mandatory there; frame count rule 17n+5; `video_shift`;
  a Turbo adapter; an audio track to mux.

## Scope

### In scope

- AbstractVision: a `minimax-h3` family (config `minimax_h3`), dispatch in `_ensure_model_impl`, 8-bit load,
  the frame-count rule and `video_shift`, the Turbo adapter, audio muxing; unit tests with a fake MLX-Gen.
- AbstractCore: a validated, optional per-artifact `allow_patterns` (list of globs) in the seed, honoured by
  `_download_huggingface` (and by the gateway's download progress/size estimate); MLX-Gen's own
  `get_download_patterns` as the source of the patterns (cite it).
- A catalog row for MiniMax-H3 (mlx-gen artifact, `video` tag, `resident` measured at AbstractVision's default
  canvas with source) — offered where it fits (128 GiB Macs), not added to "Download all" unless the operator
  decides so.
- Both consoles show it under Video (they render catalog rows generically since 2.17.0 / console 0.10.0).

### Out of scope

- The cloud MiniMax API (0945).
- Changing the recommended `output.video` route.

## Acceptance criteria

- [ ] A MiniMax-H3 generation runs on a 128 GiB Mac from the gateway sandbox (real run, evidence: artifact +
  timings + peak memory).
- [ ] The download fetches only the pattern-matched files (measured bytes ≈ 134 GiB, not 498 GB).
- [ ] Fit: `fits`/`tight` on 128 GiB, `too_large` below; tests per host.
- [ ] Tests go RED when the family, the dispatch or `allow_patterns` is removed.
- [ ] Released bottom-up in one wave: abstractvision → abstractcore → gateway → root.

## Receipts

- Video worker report 2026-09-27 (parity/video, abstractcore d8a057d); release ledger
  `untracked/release-2026-09-27/PLAN.md`.
