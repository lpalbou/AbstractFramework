# 1081 — Avatar rendering fidelity and platform quality

> Package: abstractavatar, abstractuic, abstracttui, abstractassistant
> Type: rendering improvement
> Created: 2026-10-31
> Completed: 2026-10-31
> Status: Completed
> Priority: high
> Labels: avatars, rendering, performance, accessibility

## Summary and scope

Improve shared avatar appearance and platform presentation, prioritizing Watch Halo, Wave and
Hover, followed by Rings and Eye. Retain the complete catalog, stable IDs and existing APIs.
Use Apple sources as read-only visual references; do not modify or deploy Watch/iPhone apps.

## Current code reality at intake

AbstractAvatar's native/Wasm generator is integrated in UIC and optional TUI Avatar. Scene
sampling reduces overlap to one of three material channels, limiting layered color/light.
The scene/index is reconstructed per frame. Browser presentation uses synchronous CPU raster
frames, a 256 px backing cap and approximately 2/6/12 fps scheduling. TUI reuses bounded bitmap
and mosaic buffers; richer terminal image facilities exist separately. Watch Orb uses additive
compositing, richer hues, smoothed audio/history and eased motion. Matching portable native/Wasm
frames does not establish Watch fidelity or full platform efficiency.

## Requirements and intended outcome

- Restore richer overlapping light, edge quality and recognizable design-specific behavior.
- Improve resolution/cadence according to platform capabilities, with bounded memory/work,
  explicit motion/visibility behavior, reusable buffers and an efficient default.
- Keep procedural geometry shared; avoid a parallel JavaScript/Swift geometry implementation.
- Preserve deterministic raw rendering, native/Wasm agreement, strict inert descriptors and
  legacy adapters. Plan for composable activity/expression under 1083/1084 without prematurely
  implementing a general scene language or personality engine.
- Compare focused designs at documented states/time/audio and sizes; capture visual evidence
  and measure generation plus practical presentation cost. Do not claim pixel equivalence.

## Non-goals

Package publication, license changes, paid-design infrastructure, arbitrary executable plugins,
Apple client migration, actual entity maintenance or personality assessment.

## Validation

Native/Wasm deterministic/raster agreement, catalog and ABI regression checks, focused reference
previews, bounded quality/resizing, audio/state distinction, reduced motion, hidden/unmount and
failure cleanup. Exercise actual browser and terminal harness paths; profile realistic sizes.
Review compositing and resource regressions independently before completion.

## Dependencies and ADR state

Follows completed 1078; coordinate context work 1082 and future contract 1083/1084. Existing
AbstractAvatar ADR 0001 and TUI ADR 0006 govern generator/presenter ownership. Root ADR 0044 is
proposed for future composable status/expression; no incompatible state migration is required here.

## Completion report

Completed 2026-10-31; implementation and local integrations verified, unreleased.
Original path: `docs/backlog/planned/1081_avatar_rendering_fidelity_and_platform_quality.md`.
Final path: `docs/backlog/completed/1081_avatar_rendering_fidelity_and_platform_quality.md`.

- AbstractAvatar `Frame::rgba` adds bounded antialiased, premultiplied internal material
  compositing with straight RGBA output. Five focus procedures improve corona flow, waveform
  ribbons, shaded Hover surfaces/thrusters, six great-circle rings and asymmetric eye detail.
  All 44 IDs, seven poses, legacy sampling, descriptor schema and ABI remain compatible.
- TUI adopts shared RGBA, capability-selected cell mosaics and a 3 KiB theme palette. A complete
  per-instance cache skips geometry, sampling and mosaic conversion on unchanged host repaints.
  Click attention remains bounded/non-consuming. The generator remains default-off in base TUI.
- UIC adds bounded economy/balanced/high quality, DPR resizing, missed-deadline skipping and
  cancellation before handle allocation. Actual offscreen, hidden, reduced-motion, context-loss
  and disposal behavior is verified. Assistant web ships the verified compiled source snapshot;
  the native wheel is installed in the actual shared `.venv` used by the desktop launcher.
- Core: 15 Rust and 12 Python tests plus 10 subtests; clippy/MSRV, wheel/sdist and public CLI/Rust
  recipes pass. Native/Wasm comparison: 378 frames, maximum difference 1/255 in 5 channels out
  of 7,483,392. Source/artifact checks pass for the frozen source identified in evidence.
- Terminal: 22 Avatar checks, including real Driver forced-repaint cache hits/invalidation and
  transparency; widget policy lints and material-theme tests pass. Complete package validation
  is cross-referenced in 1082. UIC full npm tests and actual Chromium all 44×7 catalog/quality/
  lifecycle checks pass. Assistant build, 62 unit tests and built-app experience checks pass.
  Installed native/Qt checks pass; all 569 watched Apple hashes are unchanged.
- Independent adversarial review: **Approved**, after compositing and invalid-range interaction
  corrections. [Durable evidence and try guide](../evidence/1081/README.md) includes visual
  comparisons, desktop/browser captures, timings, provenance and the final review.
- Coredoc: AbstractAvatar rendering guide and accepted ADR 0002, TUI/UIC API and quality/gaze
  guides, Assistant integration notes, changelogs, existing API/CLI agent skills and LLM indexes
  updated. TUI accepted ADR 0006 continues generator/presenter ownership. No other accepted ADR
  is superseded; root ADR 0044 is explicitly proposed for future contracts.

Residual/follow-up triage: high-quality CPU rendering costs more; measured native median at
160 px rises 0.839→1.857 ms in exchange for fidelity, so no universal speed claim. Watch phase
history/rainbow palette equivalence is not implemented. Safe widget-owned terminal images are
proposed 1085; multi-day clock precision and richer activity/expression remain 1083/1084. Registry
publication, floors and standalone distribution remain proposed 1079. Already running desktop
processes require Assistant-only restart to load the installed wheel; no Gateway restart needed.
No new release, license change, remote CI result, Watch/iPhone edit or production restart occurred.
Rendering priority is closed; future contract design retains its independent priority.
