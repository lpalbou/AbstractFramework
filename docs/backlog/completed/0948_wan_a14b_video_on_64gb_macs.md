# 0948 — Wan2.2 A14B 8-bit as the video recommendation on 64–95 GiB Macs

> Package: abstractcore
> Type: task
> Created: 2026-09-27
> Priority: normal
> Labels: video, catalog, apple-silicon, next-wave
> Status: completed 2026-09-28 — released in abstractcore 2.18.0 (tag `v2.18.0` → `238b693`)
> Moved: `planned/0948_wan_a14b_video_on_64gb_macs.md` → `completed/0948_wan_a14b_video_on_64gb_macs.md` on 2026-09-28

## Summary

Since abstractcore 2.17.0 the recommended `output.video` route (Wan2.2 TI2V-5B) is written only on Macs where it
fits (about 96 GiB and up: it needs ~58 GiB at AbstractVision's default canvas). Below that, video is
`unavailable`. The operator states that Wan2.2 A14B runs on 64 GiB Macs, especially with the framework's own
8-bit packages on Hugging Face (`AbstractFramework/wan2.2-t2v-a14b-diffusers-8bit`,
`AbstractFramework/wan2.2-i2v-a14b-diffusers-8bit`). Make A14B 8-bit the recommendation on 64–95 GiB Macs, with a
measured memory figure at the canvas it will actually be run at.

## Why

Operator, 2026-09-27: "wan 2.2 14b: i think you can enable it at 64gb ram, especially if people use the 8bit we
created and published on huggingface." / "i am pretty sure it does [fit 64 GB]."

## Current code reality (abstractcore 2.17.0, 6592d4b)

- Catalog rows `wan2.2-t2v-a14b` / `wan2.2-i2v-a14b` exist (mlx-gen, 8-bit packages, 39.7 GiB); their `resident`
  field was REMOVED in 6592d4b because the only published figure (~28 GiB) was measured at 384x224 with
  `--low-ram`, not the default canvas; their fit therefore uses the file size → `tight` on 64 GiB, `fits` on
  128 GiB (verified with `recommended_artifact_fit`).
- The recommendation (`capability_defaults.py`, video selector) names TI2V-5B only; 64 GiB Macs get
  `recommendation_unavailable` for `output.video`.

## Scope

### In scope

- Measure A14B 8-bit peak memory on a 64 GiB Mac (or with an equivalent MLX memory cap on a larger one) at the
  canvas the gateway/AbstractVision will use by default on such hosts; record it as `resident` with source.
- If needed, a host-aware default canvas for video (smaller on 64 GiB) decided with the operator, applied in
  AbstractVision/the gateway so the measurement and the run agree.
- Recommendation per memory band: 64–95 GiB → A14B 8-bit (T2V, I2V or both — operator decision), ≥ 96 GiB →
  TI2V-5B (or A14B if the operator prefers).

### Out of scope

- Non-Apple hosts (no local engine; see 0945 for cloud).

## Acceptance criteria

- [ ] A real A14B 8-bit run on a 64 GiB configuration at the chosen canvas (evidence: peak memory, time).
- [ ] Plan/seed/apply/"Download all" per band; tests per synthetic host; Apple goldens updated deliberately.
- [ ] Both consoles show the band's recommendation.

## Receipts

- Core tag-gate review 2026-09-27 (gate-core); release ledger.

## Implementation (wave 2, 2026-09-28) — pending release

abstractcore branch `wave2/core` (worktree `untracked/wave2/core`), local commits, no version bump;
stays planned until the release lands: `8d86550` Wan2.2 T2V-A14B 8-bit measured resident (71.59 GiB
MLX peak at 1280x720x81); `2ed029c` Wan2.2 I2V-A14B 8-bit measured resident (71.71 GiB at
1280x720x81) and the A14B per-band fit tests.

## Completion (2026-09-28)

Released in abstractcore 2.18.0: Wan2.2 T2V-A14B and I2V-A14B 8-bit carry their measured resident memory (about 72 GiB at
1280x720, 81 frames), so the fit reads `too_large` on 64 GiB Macs, `needs_gpu_limit` on 96 GiB Macs and `fits` from 128 GiB.
The recommended video route is unchanged (Wan2.2 TI2V-5B from about 96 GiB): the measurement shows A14B 8-bit does not fit
64–95 GiB Macs at the default canvas, so it is not recommended there. Pinned by root abstractframework 0.6.0.
