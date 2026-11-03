# 1078 — AbstractAvatar: shared procedural generation and platform players

> Package: abstractavatar, abstracttui, abstractuic, abstractassistant
> Type: feature + extraction + integration
> Created: 2026-10-31
> Status: Completed 2026-10-31 (implementation and source repository; packages unpublished)
> Priority: high
> Labels: avatars, procedural-media, portability, accessibility, rendering, desktop, web

## Summary

Build AbstractAvatar in `lpalbou/AbstractAvatar` as the owner of existing procedural avatar
generation, its catalog and state contract. Platform handlers present frames using their native
capabilities. AbstractTUI remains a general-purpose engine with a generic frame player and opt-in
avatar integration; no separate terminal adapter package is introduced. Integrate the web and
desktop/systray Assistant. Watch and iPhone are reference sources only and must not be modified.

## Why

Operator, 2026-10-31: "this is to share the procedural way to produce those avatars under different
states"; "it should contains all the avatars we have done so far"; "do not touch the watch or iphone
except to read what they did". Product/repository name is **AbstractAvatar**, package/import name
`abstractavatar`, without a hyphen. Previously persisted style identifiers remain stable.

## Initial code reality (preserved intake snapshot)

- The six-style Rust core lives under `abstracttui/crates/abstract-avatar`; AbstractTUI depends on
  it unconditionally. Native/C/Wasm exports exist, with bounded dimensions and handles.
- AbstractUIC presents that Wasm renderer through Canvas/React. An additional Apple-inspired
  browser renderer contains seven procedural styles and must not become a second algorithm owner.
- Watch `OrbDesign` contains 34 designs, plus composable point-body shapes. iPhone has its own
  weave. Reusing matching display names is not sufficient to preserve distinct visual variants.
- Assistant web already uses ActivityAvatar. Desktop/systray Assistant has no shared avatar widget.
- Existing native borrowed-buffer APIs need synchronized ownership/copy behavior. Hosts need
  visibility, reduced-motion and disposal discipline.

## Scope

### In scope

- Independent AbstractAvatar Rust library, native C ABI, bundled Wasm and Python binding; full
  catalog with source mapping, distinct existing designs and deterministic state/audio/time/gaze.
- Versioned bounded parameter descriptor, standard RGBA8 frames and PNG previews. Shared compiled
  generation instead of independently interpreted geometry implementations or arbitrary scripts.
- Dependency-free generic TUI raster frame source/player; avatar convenience support is opt-in.
- UIC canonical renderer/catalog, bounded lifecycle, web Assistant and desktop Assistant controls.
- Core docs, architecture decision, user API/examples, LLM indexes and package agent skill when
  the final public API meets coredoc's operating-surface criteria.
- One independent adversarial reviewer and up to three implementation workers, in available slots.

### Out of scope

- Editing, building for deployment, signing or installing watch/iPhone applications.
- New inference, microphone capture, network services, identity/voice ownership or machine daemons.
- Package publication and unrelated release preparation. Existing release gates still apply.

## Architecture and dependencies

AbstractAvatar owns deterministic generation; each platform owns presentation, host state,
palette and clocks. Core has no UI toolkit or remote execution capability. A descriptor selects
trusted built-in generation and is not an executable plugin. The new repository's ADR 0001
records this contract; AbstractTUI ADR 0006 is updated to reflect separate ownership and opt-in
integration. No additional adapter crate is needed.

## Acceptance criteria

- [x] Catalog accounts for every reference design/variant; existing keys retain their meaning.
- [x] Distinct styles and states are visually reviewed; no name-only aliases substitute for ports.
- [x] Native and Wasm render the same input within a documented numerical tolerance; dimensions,
      descriptors, handles, bytes and cleanup are bounded and checked.
- [x] AbstractTUI default builds without AbstractAvatar; opt-in hosts retain avatar behavior.
- [x] Browser and desktop Assistant expose selection, motion and useful actual activity states;
      hidden/reduced-motion views stop clocks and dispose handles.
- [x] Python distribution includes its native library; missing artifacts are explicit and imports
      do not search arbitrary libraries or mutate the machine.
- [x] Core docs and examples match executed APIs; generated LLM indexes are current.
- [x] Adversarial findings are resolved and verification includes actual rendered artifacts.
- [x] Watch/iPhone tracked-file hashes match the pre-work baseline.

## Receipts

- Initial audit: `untracked/release-review-2026-10-31/REPORT.md`.
- [Completion evidence](../evidence/1078/README.md), including 569-file Apple baseline, renderer
  hashes, tests, screenshots and adversarial approval.
- Source repository: [AbstractAvatar](https://github.com/lpalbou/AbstractAvatar), initial commit
  `346d8f4`; [seven CI jobs green](https://github.com/lpalbou/AbstractAvatar/actions/runs/41166189618).

## Completion report

Extracted the generator into independent AbstractAvatar, preserved six shaded variants and added
the source-informed Apple catalog/body shapes/weave for 44 designs. Shared native/C/Python/Wasm
generation drives the TUI, UIC, browser Assistant and opt-in desktop palette. Descriptor and
resource boundaries, copy ownership, public API docs and usage skill are implemented and tested.

Adversarial findings were fixed: real geodesic/hand geometry, missing audio responses, distinct
state cues, Cargo output-directory correctness and browser spectral/gaze history. Native/Wasm
agreement is within one channel level; the gallery and real browser/Qt views were inspected.
Source CI is green on Linux/macOS/Windows, Python 3.10/3.13, and Wasm. No Watch/iPhone file changed.

The former planned path is this same filename under `planned/`; the final path is under
`completed/`. Package registry publication and signed/native app distribution were explicitly
outside this implementation. [1079](../proposed/1079_abstractavatar_registry_release_and_consumer_distribution.md)
preserves the next release prerequisites; no release is implied by this completion.
