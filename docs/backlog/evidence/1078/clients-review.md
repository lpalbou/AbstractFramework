# AbstractAvatar client implementation and verification

## Scope and ownership

Implemented TUI generic raster presentation/optional avatar adapter, UIC canonical Wasm/Canvas/React integration, and Assistant web canonical-artifact adoption. No Watch or iPhone files modified. No commits, pushes, registry publishing or production requests were performed by this worker. Existing concurrent UI edits were preserved and migrated to compatible wrapper names; parent owns Docs snapshot and desktop worker owns native tray integration.

## Implementation

- Base AbstractTUI: `FramePlayer` reads live `Signal<Arc<Bitmap>>`, row-major straight-alpha RGBA, delegates to existing Image mosaic presentation, owns no interpreter/timer/audio/network. Hidden players unsubscribe from frames.
- `avatar` is default-off; only the convenience adapter depends optionally on registry package `abstractavatar`. No sibling path in Cargo.toml. Existing Code CLI/Core console/Gateway console manifests opt in explicitly. Preview examples require that feature. In-tree duplicate crate sources/manifest/header/examples removed; migration README retained. Standalone source verification uses explicit per-command local patch for the unpublished dependency, no machine config.
- UIC Canvas adapter validates data-only schema1 descriptors, finite normalized level/gaze/optional8bands and bounded time, catalog identity/field/memory bounds and no host imports. Descriptors cannot select uploaded code/URLs. Optional Wasm byte source is trusted embedding only.
- `draw` and `renderFrame` share one private paint path. Every call resets absent gaze and uses scalar envelope when bands are absent. Custom spectral frame followed by draw has no hidden residual state.
- ActivityAvatar consumes the canonical generator for all44 designs, samples actual host inputs, freezes elapsed animation time while hidden, stops clocks for reduced motion/loss/unmount and expires gaze. Apple component/engine names retained as thin canonical adapters, no duplicate JS geometry.
- Gallery pages6 renderers under16-handle cap; all44 designs selectable across8pages.
- Assistant web AppAvatar/default watch-halo/settings/controls preserved. Generated UI adapters + exact Wasm/provenance bundled under `web/src/vendor/abstractavatar`, with hashes checked during build; type imports point to that canonical artifact. Three old-public-kit avatar type errors fixed.

## Independent verification

- `cargo tree --no-default-features --edges normal` with explicit local patch: NO AbstractAvatar compiled dependency.
- Base `cargo check --no-default-features --all-targets` passes.
- Base library suite:1810 passed,23 ignored; no failures.
- FINAL avatar-enabled targeted suite:15 passed on frozen geometry (41.46s). Includes full44 speaking-amplitude and44x7 narrow/large renders, hiding/restoration, pointer expiry, zero idle/hidden clocks. Original6-specific motion/margins stay scoped to those shapes; source-derived designs can have stationary rest poses or edge-reaching artwork.
- Generic FramePlayer live-frame/hide/no-clock regression passes.
- Full ui-kit npm test suite passes (shared control checks plus avatar/compatibility); finalgeometry reran dedicated avatar/bounds and browser suites.
- FINAL native/Wasm parity:320frames (44x7 +12 original gaze) max channel error1 under unchanged tolerance2. Public Python/Canvas same-descriptor parity:88frames, both absent and explicit spectral bands, passes. Fixtures:/tmp/abstractavatar-native-parity; exporter:/tmp/abstractavatar-export-parity.py.
- Descriptor malformed/unknown field/bounds checks, handle caps/disposal and mixed draw/renderFrame history regression pass.
- FINAL real Chromium gallery:44designs x7states,max6live; Ready12frames/1.1s,activegaze32/500ms,postexpiry12/1.1s; reducedmotion0frames,5mountcycles,contextrestore,zeroJSerrors.
- Assistant web unit tests:62 passed. Local standalone artifact build passes. FINAL realbuilt UI passed44catalog selections,7Apple previews all7states, reducedmotion/visibility, speech/mic/draft/approval/Docs/phonewidth/keyboard recovery andzeroJSerrors, including the parent canonicalDocs snapshot.
- Existing TUI/UIC package-agent skills updated for actual APIs; both structural validators pass.
- Current Assistant diff lists no Watch/iPhone path changes.

## Visual evidence

Terminal all44-design native catalog:/tmp/abstractavatar-terminal-catalog.png (speaking), generated through actual TUIlayout/mosaic. Its height derives from catalog length, so headless export includes all styles instead of truncating at the former six.

FINALgallery:/tmp/abstractavatar-browser-final/web-ready.png,web-listening.png,web-speaking.png,web-error.png,catalog-page-0.png through catalog-page-7.png. Reviewed actual rendered images, including distinct contours/faces, transparent art and error states.
Assistant:/tmp/abstractavatar-assistant-web-final/ (final pipeline), earlierverified UI /tmp/abstractavatar-assistant-web/watch-halo.png,iphone-weave.png,avatar-preview.png. Actual settings, selection, live artwork and control layout inspected.

## Final artifact identity

- abstractavatar/artifacts/provenance.json: source `55013a168d211f3919df102d98bf13258ed2718c11ff064933533a18a270e5d0`, Wasm `561a5da8f606595b09d7e71d31017724c15f6e6a47cd022a3288f00618cd6a7c`
- abstractuic/ui-kit/src/avatars/provenance.json: source `55013a168d211f3919df102d98bf13258ed2718c11ff064933533a18a270e5d0`, Wasm `561a5da8f606595b09d7e71d31017724c15f6e6a47cd022a3288f00618cd6a7c`
- abstractuic/ui-kit/dist/avatars/provenance.json: source `55013a168d211f3919df102d98bf13258ed2718c11ff064933533a18a270e5d0`, Wasm `561a5da8f606595b09d7e71d31017724c15f6e6a47cd022a3288f00618cd6a7c`
- abstractassistant/web/src/vendor/abstractavatar/avatars/provenance.json: source `55013a168d211f3919df102d98bf13258ed2718c11ff064933533a18a270e5d0`, Wasm `561a5da8f606595b09d7e71d31017724c15f6e6a47cd022a3288f00618cd6a7c`

All four metadata copies match the definitive frozen core. Both source and binary changed for the final38-port state-clarity refinement; parity and gallery evidence were rerun on these bytes.

## Clean-install check

True clean npm-ci scratch reproduction exposed one PREEXISTING DocsAssistantPanelOptions.visible publication mismatch after avatar type imports were fixed. Parent is resolving it via canonical compiled Docs artifact snapshot, preserving voicePreferences/visible rather than hiding type errors. Parent owns final isolated registry-only build. Scratch path:/tmp/abstractavatar-isolated-web-path. Do not claim closure until parent validation passes.

## Files for doc regeneration

TUI docs/api.md,CHANGELOG.md,skills/abstracttui/SKILL.md; UIC docs/avatars.md,CHANGELOG.md,skills/abstractuic/SKILL.md; Assistant web/README.md. Parent owns TUI README/ADR0006,llms regeneration,newrepo docs,inventory/backlog.

## Adversarial corrections adopted

Sine-hash native/Wasm divergence was reproduced without relaxing tolerance, then fixed in core. Public draw no longer retains previousbands/gaze. Missing bands now mean scalarlevel in everyband, matchingPython/Rust. All44 speaking-amplitude expectations retained; core corrected five actual omissions. Geometry-specific legacy6 fixtures are scoped rather than forcing allsource-derived styles to share corners/motion/silhouette behavior.
