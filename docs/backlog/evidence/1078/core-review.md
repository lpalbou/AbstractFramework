# AbstractAvatar core implementation and proof

## Implemented scope

New independent repository `/Users/albou/tmp/abstractframework/abstractavatar`, local `main`, origin `https://github.com/lpalbou/AbstractAvatar.git`. No commits, pushes, tags, registry publishes or Apple source edits were performed by this worker. Cargo/Python package name `abstractavatar`, product AbstractAvatar.

44 real procedural designs: six preserved original shaded Rust designs, 34 source-derived Apple picker scenes, three original OrbShape body variants and iPhone weave. Machine-readable provenance/catalog in `catalog.json`; stable original first six ids/codes. The ports are source-derived adaptations, not a claim of pixel-identical SwiftUI rasterization. Native/Rust/Wasm use one generator; hosts present frames rather than reproduce geometry.

Geometry: bounded scene primitives precomputed once per Frame and spatially indexed; default geometry zero external dependencies. Frame Clone (not Copy), sample borrows. Optional serde JSON feature parses a strict versioned inert descriptor; no executable scene language, URLs or file evaluation. C/native/Wasm ABI1 preserved with additive bands, clear-bands and atomic render-copy helpers. 1..512 dimensions, max16 live handles, max4096 primitives per scene; source tests ensure no design exhausts the bound.

Source identity details retained: actual subdivided icosahedron for woven geodesic (120 edges), two Chaikin passes and 240 arclength samples for approval hand; source-specific floral bloom, black-hole flare, accretion star/bands, Cruiser dashboard; distinct horizontal Contour and vertical Membrane; Rover round lenses versus Spark box shutters. Ready/Thinking/Working/Waiting/Error distinct for all38 ported styles. All44 Speaking designs respond to level at time0 and2.3; added no fake audio to other phases. Original six shaded implementations unchanged.

Python: catalog(), strict validate_descriptor(), Renderer with RGB theme anchors, explicit/package-only native library loading, owned RGBA bytes copied under native lock, shared-instance thread safety and deterministic cleanup. CLI catalog/render outputs JSON/PNG with standard library. Wheels bundle the native lib and use platform-specific py3-none tags; source distributions omit platform binaries.

## Frozen artifacts

- source SHA256 `55013a168d211f3919df102d98bf13258ed2718c11ff064933533a18a270e5d0`
- Wasm SHA256 `561a5da8f606595b09d7e71d31017724c15f6e6a47cd022a3288f00618cd6a7c`
- native developer library: `/Users/albou/tmp/abstractframework/abstractavatar/target/release/libabstractavatar.dylib`
- Wasm: `/Users/albou/tmp/abstractframework/abstractavatar/artifacts/avatar_core.wasm`
- package-native copy: `/Users/albou/tmp/abstractframework/abstractavatar/python/abstractavatar/_native/libabstractavatar.dylib`

No further source edits planned unless a new blocking review finding requires coordinated changes.

## Independently executed checks

- `cargo +1.87.0 check --manifest-path abstractavatar/Cargo.toml --all-targets --all-features --locked --offline --target-dir /tmp/abstractavatar-msrv`: pass (6.20s), verifies declared MSRV including optional JSON dependencies.
- `cargo clippy --manifest-path abstractavatar/Cargo.toml --all-targets --all-features -- -D warnings`: pass.
- `cargo test --manifest-path abstractavatar/Cargo.toml --all-features`: 9 passed, 0 failed (0.98s last full state implementation pass).
- `PYTHONPATH=abstractavatar/python python3 -m unittest discover -s abstractavatar/tests -p test_python_api.py -v`: 9 passed (0.216s). Includes 44×7 renders, all44 audio response at0/2.3s, state clarity, strict JSON, bad numeric/palette/bands, atomic owned copies and same-renderer thread contention.
- Independent native/Wasm parity, 308 frames (44×7),64px, identical theme/input: only ONE channel differs by1/255 across approximately5million channels; no channel differs by more than1. This is numerical tolerance, not byte-identical-all-frames.
- `python3 abstractavatar/scripts/build_artifacts.py --check`: pass against frozen source.
- `CARGO_TARGET_DIR=/tmp/abstractavatar-wheel-redirect python3 -m build --wheel --sdist --outdir /tmp/abstractavatar-wheel abstractavatar`: pass. Explicit target-directory/host prevents Cargo env/config redirection from selecting absent/stale artifacts. Redirect directory unused; bundled lib matched newly built explicit target. Wheel Root-Is-Purelib:false and platform tag correct. Source archive contains Rust/schema/docs/gallery, no dylib/so/dll.
- Fresh wheel installed in isolated Python3.13 venv (source build Python3.12); all9 public API tests pass0.482s, catalog44 and PNG render CLI work without Rust/source checkout at runtime.

## Artifacts for operator/reviewer

- wheel `/tmp/abstractavatar-wheel/abstractavatar-0.1.0-py3-none-macosx_26_0_arm64.whl`, SHA256 `00253efe5fa853ec37ce326d641a1e4043ca6afe5cf23c7d66599f445850e311`
- source archive `/tmp/abstractavatar-wheel/abstractavatar-0.1.0.tar.gz`
- isolated wheel environment `/tmp/abstractavatar-wheel-smoke`
- all308 individual PNG frames and seven contact sheets `/tmp/abstractavatar-final/`
- public full44 catalog `/Users/albou/tmp/abstractframework/abstractavatar/docs/media/catalog.png`
- median128px render 0.813ms, max 1.696ms over308 frames, observed on this Apple development host; not a cross-device performance promise.

## Review fixes completed

Sine-based procedural randomness initially amplified native/libm differences; replaced only scene seeds with deterministic integer avalanche, restoring parity. Ported weave's true geodesic/hand geometry after adversarial comparison. Fixed missing voice effects and weak state distinctions with regressions. Corrected Cargo target-dir handling, nullable optional descriptor mismatch, numerical schema_version1.0 compatibility and optional-field serialize/parse roundtrip. No review tolerance was loosened to hide the seed bug.

## Remaining scope outside this worker

Coordinator owns coredoc/ADR/backlog and workspace inventory; client worker owns TUI/UIC/web adapters and copied artifacts; desktop worker owns systray integration. Adversarial reviewer owns final independent verdict. This worker has not certified those consumers or signed/public distribution. Linux/Windows builds are configured for CI but not independently executed here. Apple source remains read-only.
