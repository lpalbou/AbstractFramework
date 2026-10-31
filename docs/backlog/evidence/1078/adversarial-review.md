# AbstractAvatar adversarial review

Reviewer: `/root/avatar_adversary`; read-only inspection of product sources; no Apple edits, merges, pushes, or publication. Initial snapshot reviewed 2026-10-31.

## Architecture recommendation

Use one deterministic procedural generator, compiled natively and as WebAssembly, with bounded typed inputs and a standard RGBA frame output. A small versioned JSON object can identify a catalog design plus activity, elapsed time, level, gaze, palette and motion preferences. This object is a parameter contract, not a general-purpose executable format. Platform handlers own playback, timing, lifecycle, palette and compositing; they do not separately reimplement the geometry. No new package is necessary merely for a TUI adapter; a default-off capability/player can consume public rendering primitives without putting product avatar geometry in the base engine.

Alternatives considered:

| Alternative | Strong case | Main limitation |
|---|---|---|
| Independent Swift/TypeScript/Rust ports | Native drawing quality; no bridge | Existing drift and duplicate state/geometry; does not deliver one shared procedural authority |
| Declarative scene/animation format | Reader/player concept; portable authored animations | Live audio/gaze/state procedural behavior needs custom semantics or scripts; inventing a DSL creates complexity/security/parser burden |
| Shared compiled generator + standard frame/adapters | One authority; same inputs and conformance fixtures; simple native and Wasm presentation | Native artifact packaging, ABI buffer lifetime and CPU cost must be solved explicitly |

This recommendation changes if a maintained standard demonstrably captures all live procedures and target runtimes with less complexity. Do not call a custom descriptor an existing media standard.

## Catalog completeness: release-blocking acceptance

- Watch `OrbDesign` in `abstractassistant/watch/apple/Sources/App/Shared/Orb.swift:6-52` enumerates **34** distinct designs, with stable A..Z and CT/MB/AU/MU/HV/SP/CR/AN/CY codes. They span orbs, forms, cosmos, portraits, machines and nature. Its implementation files contain approximately 8k lines of geometry/drawing/state behavior.
- Existing Rust `abstracttui/crates/abstract-avatar` contains **six** shaded designs: Halo, Hover, Vortex, Eclipse, Eye and Rover. These are distinct interpretations from the Swift designs and must preserve their IDs/preferences.
- Existing browser `abstractuic/ui-kit/src/apple_avatar_engine.ts` implements **seven** additional ports: watch-halo, watch-vortex, watch-nebula, watch-rings, watch-liquid, watch-galaxy and iphone-weave. Those are not aliases for the six shaded Rust designs.
- iPhone `OrbWeave.swift` is actual procedural media (five cords, geodesic sphere/raised-hand state), consumed from `Design.swift:141`. Include it in the source inventory even though Apple integrations remain read-only.
- Watch `OrbShape` at `Orb.swift:178` additionally defines composable point-body shapes `planet`, `kitty`, `face`, `wave`. These are distinct from OrbDesign Face/Wave scenes. Preserve their variants too, either as a shape parameter or as three additional explicit catalog designs (6 shaded +34 Watch +1 weave +3 extra shapes =44).
- Catalog tests must compare actual rendered silhouettes/animation/state behavior and preserve unique variant identity. Adding all names while mapping unimplemented styles onto six existing shapes fails the user's requirement.

## Safety/performance findings to preserve or repair

- Existing C ABI bounds render dimensions at512 and live handles at16; this bounds memory around16MiB for pixel buffers but CPU cost is still bounded only by per-frame pixel count and each design's algorithm. Test realistic Qt/web frame budgets and timers, particularly 34 styles.
- Existing `avatar_pixels` returns a raw borrowed pointer after releasing its registry lock. It is invalidated by concurrent render/destroy. Native bindings must synchronize copying or offer a copy-into-caller-buffer API that holds the lock for the copy. Do not expose unsynchronized borrowed buffers to Qt.
- Validate finite numeric inputs, dimensions, palette cardinality/channels, request byte length and invalid enum/style values at all public boundaries. Reject unknown schema/ABI versions explicitly. Do not load arbitrary modules/shaders/scripts from descriptors.
- Hidden/minimized/offscreen views must stop clocks and release handles on disposal; repeated activity/level updates must not multiply or reset timers. Respect reduced motion. A static Error/Waiting state needs meaningful still rendering.
- Preserve actual input state ownership: rendering consumes explicit host state and real audio level; it must not invent microphone activity or own account/session identity.
- Preserve transparent alpha composition and palette semantics across native/Wasm outputs. Geometry parity alone is insufficient if Qt premultiplication or Canvas scaling produces halos.

## Evidence still required

Implementation pending. Need catalog coverage matrix, native/Wasm same-input frame parity, malformed-request/ABI/resource tests, TUI core-without-avatar build, registry/source dependency closure, Qt and browser lifecycle tests, actual screenshots across representative styles/states, and an Apple working-tree hash/diff unchanged receipt.

Apple baseline: `/tmp/abstractavatar-apple-baseline.json` contains SHA256 hashes of569 tracked files under `abstractassistant/phone/iphone` and `watch`; initial git status clean. At final review compare every hash and Apple git diff. Visual strategy: render every catalog ID in all seven activity states into static contact sheets, verify shape/state distinctions rather than name count; inspect representative closeups against known source cues (portraits, robots, rings/nature/space/forms; woven geodesic and raised hand), then exercise live TUI/browser/Qt lifecycle. Native/Wasm byte parity verifies common generation but is not proof of fidelity to Swift references; those are separate obligations.

## First substantive implementation review

Inspected new `abstractavatar` Rust core, C ABI, Python binding/package setup, descriptor schema, documentation, TUI generic frame player, UIC adapter and Qt integration. Viewed `/tmp/abstractavatar-preview/catalog-speaking.png` and actual palette capture `/tmp/abstractavatar-desktop/assistant-desktop.png`.

Independently executed evidence:

-44 styles rendered at96px, speaking state, level0.7/time2.3:44 distinct SHA256 hashes; median0.58ms, worst1.04ms on this machine. Measurement file `/tmp/abstractavatar-adversary-bench.json`.
- Actual offscreen Qt show/minimize/restore/close: shown native handle+timer; minimized handle released/timer stopped despite QWidget.isVisible()==true; restored reacquires; close releases. No gateway or microphone used.
- All569 Apple source hashes still identical, Apple git status empty.
- Python rejects null gaze/bands and invalid numeric bounds. Integral JSON schema_version semantics being aligned by core worker; this was not left as a final failure claim.

Findings sent for correction:

1. **P1 packaging correctness:** `setup.py` and `scripts/build_artifacts.py` invoke Cargo honoring ambient target-dir while then copying `ROOT/target/release`. Custom CARGO_TARGET_DIR/Cargo config can produce an absent or stale binary in the wheel. Core worker is using explicit target directories/host triple to eliminate the mismatch.
2. **P1 source-fidelity:** initial iPhone weave port uses simple elliptical globe rings rather than the source's subdividedicosahedral mesh. Core worker is replacing that with actual12-vertex/20-face-derived120-edge geometry and smoothing/resampling the hand.
3. **P1 state-input behavior:** independently comparing level0 vs1 for fixed speaking state/time produces byte-identical frames for watch-lotus, watch-black-hole, watch-accretion and watch-cruiser. Source defining behavior is voice-reactive petals/stamens, ring/hotspot, star/ring bands and car dash. Core worker notified to restore and test these effects.
4. **P2 adapter request-history leak:** `AvatarRenderer.renderFrame` sets explicit bands and calls `draw`, but public `draw` retains them on later ordinary calls, unlike native defaults. Same direct draw inputs can depend on previous descriptor. Clients worker notified to centralize through a private path, resetting bands to the scalar level defaults for direct draw and testing custom→direct parity.

Positive observations: native `avatar_render_copy` now holds the registry lock through copying into caller-owned storage; Python serializes handle operations and returns owned bytes. Bounds, unknown version/fields/state/style handling and explicit missing-native errors are present. Qt is optional, uses real host state and owned QImage copies, has no ambient library search or inference fallback. TUI FramePlayer is generator-independent; convenience avatar imports are gated behind default-off feature.

Current verdict: **Conditional Approval pending the above fixes and final artifact/browser evidence**. The findings are actionable; do not reintroduce separate geometry ownership or declare pixel-identical Swift fidelity.

## Final candidate review

**Verdict: Approved for the reviewed source implementation and local native/browser scope.** No remaining blocking source finding after the corrections below. This is not an approval to publish or a certification of unexecuted Linux/Windows/Apple signed distributions.

All four actionable findings were corrected:

- Setup and artifact generation pass explicit `--target-dir` and native host triple; copies come from the exact selected build location. The setup path clears foreign native filenames before copying the host artifact. Core worker separately built/installed an isolated wheel under a redirected Cargo environment and checked a source archive contains Rust source without bundled native executables.
- iPhone weave contains the source-style subdividedicosahedral mesh, two Chaikin smoothing passes and240 arc-length-resampled hand points. Viewed the final Listening contact sheet: recognizably geodesic. Viewed Waiting: a recognizable raised hand.
- Four missing speaking-level effects restored with source-specific bloom/stamen, ring/hotspot, star/ringbands and dashboard behavior. Independently re-rendered all44 at time0 and2.3, level0 versus1: every design changes. Existing unrelated nonvoice phases do not acquire fake speech motion.
- Public browser `draw` delegates to normalized descriptor rendering; custom bands/gaze are set for each request and ordinary draws restore scalar-level/default gaze. Static source review confirms no stale request-history path remains; clients worker added an explicit sequence regression.

Independent final checks run by this reviewer:

- `cargo test --manifest-path abstractavatar/Cargo.toml --all-features --locked`: **9 passed**.
- Native Python unit discovery with explicit current library: **8 passed**.
- Own all44 amplitude comparison at both times: **88 design/time comparisons passed**.
-32 concurrent calls sharing one Python renderer return identical stable owned bytes.
- Integral numeric schema_version1.0 accepted; bool version, null gaze/bands and nonfinite/out-of-bound numerics refused.
- `scripts/build_artifacts.py --check`: source/artifact hashes match.
- `scripts/docs.py --check`: documentation indexes current. All default coredoc pages present; public relative links resolve; architecture has a Mermaid diagram. Consumer agent skill is warranted by the API/CLI/descriptor ownership contract and its examples accurately match the API.
- All569 Apple tracked-file hashes remain identical to the initial baseline; git status for phone/iphone and watch is clean.
- Old TUI embedded geometry source is gone; only its README pointer remains. Generic FramePlayer has no AbstractAvatar dependency; avatar convenience module and dependency are default-off.

Visual artifacts inspected: final44 Speaking, Waiting and Listening contact sheets, actual Qt palette capture, final browser gallery Speaking/page8 Error captures, and the available actual mobile-width web Assistant portrait capture. The newer Face/Imprint, Contour/Membrane and Rover/Spark silhouettes are meaningfully distinct. Gallery pagination limits active presenters instead of exhausting the native handle budget. Browser's generated pixels and native lifetime behavior have separate proof rather than inferring one from the other.

Other-agent evidence consumed (not independently rerun in this lens): native/Wasm308frames differ in only one channel by1/255; expanded wrapper/descriptor parity and browser lifecycle checks; desktop231 relevant tests; isolated wheel/source-archive construction. Coordinator should cite their final exact paths/counts and complete any still-running browser suite before its own completion report.

Residual scope/risks: portable designs are source-informed procedures, not pixel-identical Swift rendering or an automatic migration of Watch/iPhone. Platform palette/sampling and the discrete state/time contract differ from additional Apple host-specific phase blending/history. Real signed tray distribution, Linux/Windows native binaries and registry publication were not exercised or authorized by this review. These limitations do not invalidate the checked source behavior; they must not be advertised as completed delivery.

## Final focused delta approval

**Approved** at source SHA256 `55013a168d211f3919df102d98bf13258ed2718c11ff064933533a18a270e5d0`, Wasm SHA256 `561a5da8f606595b09d7e71d31017724c15f6e6a47cd022a3288f00618cd6a7c`.

Reviewed only the post-approval changes rather than repeating unchanged work:

- New source-driven scans/head motion/orbits/fibres strengthen Thinking/Working differentiation for the38 added ports. Waiting adds dimmed identity plus a quiet orbit; Error adds a static explicit badge. Reviewed updated Thinking/Error contact sheets. Independently ran `test_ported_activity_has_distinct_work_thought_wait_and_error_cues`: **passed** for all38 ports. These cues do not invent microphone activity or change the original six shaded identities.
- Independently reran source/artifact checksum verification: **passed**, matching the exact hashes above.
- Reviewed `web/scripts/sync_docs_assistant.mjs`, its generated canonical Docs bundle/declaration provenance and App import/build-check changes. Artifact and source filenames are constrained, source parity is available explicitly, and normal standalone builds verify shipped artifact hashes without requiring a sibling checkout.
- Independently executed the Docs updater `--check --check-source`: **passed**. Parsed the generated module using esbuild's actual import graph: only `react/jsx-runtime`, `react`, `react-dom`, `@abstractframework/ui-kit` remain external. No second embedded React/UI-kit/audio owner or unknown imported module was found. The bundled Docs code remains generated from canonical panel-chat sources rather than a new hand-maintained fork. Coordinator's isolated registry-only build proof addresses the version-skew failure this snapshot fixes.
- Independently rechecked569 Apple hashes and git status: **unchanged/clean**.

No new blocking source/artifact-boundary finding. Existing publication and cross-platform distribution limits above still apply. Client worker reports final real Chromium44×7 gallery/lifecycle tests,320 raw parity plus88 public-descriptor parity, and full UIC/base-TUI checks; coordinator should consume its final report and expanded Assistant experience result before claiming complete end-user delivery.
