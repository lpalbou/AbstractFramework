# AbstractAvatar rendering handoff — 1081

Scope: AbstractAvatar only. Apple sources were read-only. No commit, push, publish or restart.

## Result

- Additive `Frame::rgba(x,y,pixel_size,&Palette)` retains host material colors, straight-alpha RGBA, bounded analytic/Gaussian antialiasing, shaded solid surfaces and soft light.
- Existing `Frame::sample`, all44 style IDs, ABI1 and descriptor1 stay available and compatible.
- Source-directed improvements: WatchHalo uneven5+3 streamers/flowing corona; WatchWave five translucent waveform ribbons +five-arm working spiral; WatchHover opaque domed barrel/darkvisor/eyes/articulatedarms/threeplumes/floorpool; WatchRings six icosahedral great circles/depth/beads; WatchEye asymmetriclids/irisfibers/pupil/brow/lashes/catchlight.
- Host palette authority preserved. Three ramps cannot reproduce an independent six-hue Apple palette; version1 remains stateless and has no phase/history controller.

## Frozen artifact

source_sha256:13e81e09b65e28b84b4dfa4ce58313bf0d5ee4bc5f8478baa582d084b5e8d059
wasm_sha256:d576a6a584f09c6b9a124c93476c7a73a69ae9e147014e2d26dda5974273c067

Artifacts: abstractavatar/artifacts/avatar_core.wasm +provenance.json +libabstractavatar.dylib; same nativebinary bundled in python/abstractavatar/_native.

## Validation

- cargo test --all-features:15 passed; clippyallfeatures/alltargets denywarnings passed.
- Pythonpytest tests:12passed +10subtests; sourceartifact/sourcehash check passed.
- Native/Wasm parity:378frames at32/64/128pixels;7,483,392channels, only5differ by1/255,max1. Distinct materialramps, partialalphas,8voicebands andnoambientWasmimports exercised.
- MSRV1.87 lockedoffline alltargets/allfeatures check passed.
- Wheel+sdist: dist/abstractavatar-0.1.0-py3-none-macosx_26_0_arm64.whl andabstractavatar-0.1.0.tar.gz. Freshwheel-env9APItests+CLIrender passed; bundledlib matchesfreshwheel-native target andall308style/stateframes matchsourceartifact byteforbyte. Platformwheel notpure-any;sdistcontainsRustsource+checker.mjs+docs+tests, excludesnativebinaries.
- Both publicRustdocsamples compiled+ran; CLIcatalog/render passed; coredoc indexesfresh.

## Evidence

- baseline.png and final-focused.png:matched5styles×7states160px.
- themes.png:warm/cool/monochromeReady/Speaking.
- catalog-{state}.png:seven44style sheets;308individualPNGs.
- docs/media/catalog.png updated; final-timing.json exact measurements.
- Matched210nativeframes160px:baseline median.839/max1.271ms;finalmedian1.857/max5.393ms under concurrent local load.
- All44×7at128px:median1.182/max3.698ms.

## Docs

New docs/rendering.md andADR0002; API/gettingstarted/framecontract/architecture/FAQ/README/changelog updated. Existing packageagentskill maintained becausePythonCLI/Rust/descriptor are operablesurfaces requiring boundedinputs/lifecycle/paletteknowledge; addedRGBArecipe,MIT+unreleasedmetadata,limits. llms.txt/full regenerated. CIportablejob nowruns reproducibleparitychecker.

Final independentadversarial approval belongs toparent/reviewer; no claim of release readiness.
