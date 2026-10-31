# 1079 — AbstractAvatar registry release and consumer distribution

> Package: abstractavatar, abstracttui, abstractassistant, abstractuic, abstractframework
> Type: release preparation
> Created: 2026-10-31
> Priority: high
> Labels: release, packaging, native, wasm, dependency-floors

## Summary

Prepare registry publishing and consumer distribution for the completed AbstractAvatar
implementation, when the operator authorizes the next release wave. This proposal is a release
follow-up, not authorization to publish or install production applications.

## Current code reality

- [1078](../completed/1078_abstractavatar_shared_procedural_generation_and_platform_players.md)
  delivered source to `lpalbou/AbstractAvatar` main, commit `346d8f4`, with all seven CI jobs green.
- Rust and Python distributions share the normalized name `abstractavatar`, version 0.1.0.
  PyPI/crates.io exact-name lookups returned 404 at completion; names are not reserved by a lookup.
- `.github/workflows/ci.yml` tests native packages on three OSes and Wasm, but has no publish job.
  Local platform wheel and portable source archive are verified; no registry version is published.
- TUI's convenience adapter has a default-off optional dependency on abstractavatar >=0.1.0.
  Cargo still resolves optional package metadata; local source checks use an explicit per-command
  patch while the first registry version is absent. No sibling path or global Cargo config is required.
- Assistant's `[avatar]` extra requires abstractavatar >=0.1.0. Web consumes pinned generated
  canonical adapters/Wasm; its shared Docs snapshot also bridges a pending shared-package release.

## Proposed direction

1. Confirm registry ownership and target-version availability, then configure trusted publishing
   and review minimal release workflows. Native Python wheels must contain the matching platform
   library; the source archive must build it and contain no stale host binaries.
2. Reuse exact-commit tests/review and registry visibility gates: publish the shared crate/Python
   package before dependent metadata/floors, then TUI and actual consumers in dependency order.
3. Refresh source locks after registry visibility. Publish fresh UI-kit/panel-chat versions and
   replace web snapshots with equivalent published artifacts when those APIs are available.
4. Build/test the desktop optional extra and platform bundles; keep public signing/notarization
   distinct from source-package readiness. Root installer pins change only in an approved wave.

## Promotion criteria

- Operator approves a release wave containing AbstractAvatar and affected consumers.
- The coordinator confirms target names, credentials/environments and exact publishing refs.
- Scope identifies which Python/native/web consumers ship and which remain source-only.

## Validation

- Registry-only Cargo/pip/npm installs resolve the same reviewed APIs and renderer identities.
- Fresh wheels on each supported platform load natively; source builds do not require a sibling
  checkout; Wasm provenance matches the reviewed source.
- Consumers retain all 44 designs, seven states, visibility/motion/copy behavior and one audio owner.
- Root pins and install manifest match the published wave, with no claim that a source push is a
  registry release.

## Non-goals and ADR state

No publication is authorized here, no Apple app migration, and no new rendering architecture.
Existing AbstractAvatar ADR 0001, TUI ADR 0006 and root release ADR 0034 govern this work.
