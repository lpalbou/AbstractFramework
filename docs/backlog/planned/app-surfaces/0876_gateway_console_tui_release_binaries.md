# 0876 — Release binaries and `SHA256SUMS` for the gateway's terminal console

> Package: abstractgateway (console-tui crate `abstractgateway-console`, release workflow); abstractcore (`abstractcore-console`) if it shares the gap
> Type: feature
> Created: 2026-09-25
> Priority: normal
> Labels: apps, release, rust, install

## Summary

The gateway installs Code's terminal app in one click because abstractcode publishes GitHub release
binaries (macOS arm64/x86_64, Linux x86_64/arm64 glibc, Windows x86_64) with `SHA256SUMS` and
provenance. The gateway's own terminal console (`abstractgateway-console` 0.8.0) is on crates.io
only, so the console can only show `cargo install abstractgateway-console`, which needs a Rust
toolchain a non-technical user does not have.

## Current code reality

- abstractgateway `release.yml`: crate job publishes to crates.io (token; see 0857); no binary
  matrix, no `SHA256SUMS`.
- The gateway's `install-tui` path already verifies `SHA256SUMS` and GitHub's digest for Code
  (mission Y), and names the console's own TUI on the Done step.

## Scope

### In scope

- A release-workflow matrix building the console binary for the same targets as abstractcode,
  uploading archives + `SHA256SUMS` + provenance to the `v*` GitHub release.
- The console TUI accepts the same one-time sign-in handover as Code's TUI.
- The gateway's install-tui path installs it like Code's.

### Out of scope

- musl / Windows arm64 builds (Code does not ship them either).

## Acceptance criteria

- [ ] The next gateway release carries the binaries and `SHA256SUMS`; checksums verify.
- [ ] Console Done step offers Install/Open for the terminal console on a machine without cargo.

## Testing

- `gh release view v<next> -R lpalbou/AbstractGateway --json assets -q '.assets[].name'`
- `python -m pytest abstractgateway/tests/test_gateway_apps_tui.py -q`

## ADR status

- ADR impact: None.

## Receipts

- `untracked/missionY/REPORT.md` ("Open for app owners"), `untracked/missionY/inventory.md`; 0857.
