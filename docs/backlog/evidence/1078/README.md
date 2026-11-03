# AbstractAvatar implementation evidence — 2026-10-31

Source implementation and authorized repository bootstrap completed; registry publication was not
performed. The shared renderer is [AbstractAvatar](https://github.com/lpalbou/AbstractAvatar),
commit [`346d8f4`](https://github.com/lpalbou/AbstractAvatar/commit/346d8f410fef42c7230442839b5dc646dc3b1204).

## Outcome

- 44 procedural designs: original six shaded variants, 34 Apple design references, three point-body
  shape variants and the iPhone weave. Stable original identifiers and ABI prefix preserved.
- One Rust generator for native/C/Python and browser Wasm; bounded inert JSON descriptor and RGBA8
  frames, PNG previews. No separate geometry interpreter per platform.
- Generic dependency-free TUI FramePlayer; avatar support is default-off in the existing crate.
- Shared UIC adapter, web Assistant adoption, and opt-in desktop/systray Assistant palette avatar.
- Full core docs, schema, architecture diagram/ADR, LLM indexes and a verified usage skill.

## Verification

| Check | Result / evidence |
|---|---|
| Remote core CI | [41166189618](https://github.com/lpalbou/AbstractAvatar/actions/runs/41166189618): all seven jobs green on source `346d8f4`. Native build/API tests on Linux, macOS and Windows with Python 3.10/3.13; Wasm, formatting and Clippy job. |
| Core Rust | Nine tests pass; Clippy denies warnings; Rust 1.87 minimum checked independently. |
| Core Python | Nine worker API cases plus three independent CLI/capacity cases pass. Parent aggregate with root inventory/LLM checks: 18 passed, 10 subtests. |
| Native/Wasm consistency | 320 frame comparisons and 88 public-descriptor comparisons pass; maximum difference is one channel level out of 255. Core's separate 308-frame comparison finds only one differing channel. |
| Rendering scope | All 44 designs across all seven states rendered. Voice responses at elapsed times 0/2.3, state distinctions for 38 added ports, real geodesic weave and approval-hand geometry covered. |
| TUI | 1,810 base tests pass, 23 ignored; 15 avatar tests pass; default compilation tree excludes AbstractAvatar; generic live-frame/hide/no-clock test passes. |
| UIC/browser | Full UI kit suite passes. Actual Chromium gallery covers 44 designs × seven states, at most six live handles, reduced motion, visibility, gaze expiry, disposal and recovery. |
| Web Assistant | 62 unit tests pass; actual browser interactions include all 44 choices, seven-state previews, speech/microphone/approval/Docs controls, keyboard and phone width. |
| Clean npm closure | Fresh `npm ci --ignore-scripts --no-audit --no-fund` and production build pass with published ui-kit 0.9.6 / panel-chat 0.6.4. New avatar and shared Docs artifacts are canonical generated snapshots, not local dependency overlays. |
| Desktop Assistant | 231 relevant tests pass, including real native RGBA frames and full Qt palette integration. Independent minimize/restore/close check confirms clocks/handles stop and recover. |
| Native packaging | Fresh platform wheel built with redirected Cargo target environment, installed in an isolated Python 3.13 environment and tested without source-path/native-library fallback. Source archive excludes native binaries. |
| Assistant installed dependency | Built wheel installed into `abstractassistant/.venv`. Actual Qt widget imports the installed package, renders, hides and releases resources with no `PYTHONPATH` or explicit library override. User preferences and running production processes were not changed. |
| Actual stack runtime correction | Operator screenshot exposed a different launch environment. Renderer installed and verified in `untracked/deploy/root/.venv` → shared workspace `.venv`; actual Settings refresh recovers all 44 designs and Qt renders correctly. [Repair receipt](runtime-environment-repair.md). |
| Workspace | Inventory check passes for 36 packages/23 repos. Inventory/installer shell suite: 12 pass, including intentional bad-manifest mutations. Same-name Python/Rust registry resolution has regressions. |
| Coredoc | Public links resolve; LLM indexes and three package skill validators pass; actual Python/CLI recipes executed. |
| Apple restriction | All 569 tracked Watch/iPhone file hashes match the [baseline](apple-baseline.json); Apple git diff remains empty. |
| Adversarial review | [Approved](adversarial-review.md), including the final state-clarity and canonical Docs artifact delta. One reviewer and three workers were used. |

## Frozen renderer identity

- Source SHA256: `55013a168d211f3919df102d98bf13258ed2718c11ff064933533a18a270e5d0`.
- Wasm SHA256: `561a5da8f606595b09d7e71d31017724c15f6e6a47cd022a3288f00618cd6a7c`.
- [Provenance record](renderer-provenance.json) matches core, UIC source/dist and Assistant vendor artifacts.
- [Fresh npm install log](npm-ci.log), [production build log](production-build.log), and
  [remote CI result](ci.json). `/tmp/abstractavatar-final-registry-path` also points to the local
  isolated source tree used for the registry-only build.

## Detailed receipts and visuals

- [Core](core-review.md), [clients](clients-review.md), [desktop](desktop-review.md),
  [independent review](adversarial-review.md).
- [Public 44-design gallery](../../../../abstractavatar/docs/media/catalog.png).
- [Desktop capture](screenshots/desktop.png), [web Assistant](screenshots/web-assistant.png),
  [browser gallery capture](screenshots/web-gallery.png).
- Additional local captures: `/tmp/abstractavatar-final/` (seven contact sheets and 308 individual
  frames), `/tmp/abstractavatar-assistant-web-final/`, `/tmp/abstractavatar-terminal-catalog.png`.

Ports preserve procedural design vocabulary and state behavior; they are not a claim of identical
SwiftUI rasterization. Apple apps were not integrated, built for deployment or signed. Remote CI
proves the shared core on three OSes; the desktop GUI was exercised locally through Qt, not as a
signed production installer. Registry release and physical platform distribution remain separate.
