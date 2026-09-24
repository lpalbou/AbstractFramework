# 0855 — One-line install, first-run console and model/engine management (root 0.2.0)

> Package: abstractframework (with abstractcore 2.14.0, AbstractRuntime 0.4.33, abstractgateway 0.3.0, crates abstractcore-console 0.2.0 and abstractgateway-console 0.7.0)
> Type: task
> Created: 2026-09-23
> Completed: 2026-09-23
> Priority: high
> Labels: install, bootstrap, console, models, engines, release

## Summary

Make installing and configuring AbstractFramework dead simple on macOS, Linux and Windows: one
line installs the gateway, registers it as a login service, starts it on loopback and opens its
console through a one-time sign-in link; a first-run guide sets up an engine and a default model;
local models and engines are browsed, downloaded, deleted and installed from both entry points
(AbstractCore and the gateway) in the web consoles, the terminal consoles and the CLI.

## What landed in this repository

- `scripts/install.sh` / `scripts/install.ps1`: uv-based bootstrap (profile detection, uv +
  Python 3.12, `uv tool install "abstractgateway[<profile>,tray]==<pin>"`, `service install`,
  health wait, `claim-url`, optional Node/Ollama/LM Studio/crates, `--print`, `--uninstall`).
  Default pin: gateway 0.3.0, so the service and claim-link path is the default.
- `abstractframework doctor` host/tool/gateway/engine probes (read-only), `--no-network`,
  `--timeout`, JSON schema `abstractframework_doctor_v2`.
- Install manifest schema v2 (`bootstrap`, console-first `post_install`), ADR-0038.
- `CRATE_RELEASE_VERSIONS`; bootstrap crate pins tested against it.
- Workspace inventory `scripts/lib/packages.txt` (30 packages, 21 repositories, tiers and edges,
  including the new `abstractcore-console` crate), `deps.sh`, tiered `status/build/push/pull`.
- CI `bootstrap-smoke` (Ubuntu, macOS, Windows).
- Docs: README quick start, install, getting started, architecture (distribution and
  Models/Engines diagrams), API, FAQ, glossary, installers, llms files, CHANGELOG 0.2.0.

## Follow-ups

0856 (Windows validation), 0857 (crates.io trusted publishing), 0858 (`allow_engine_install`
console toggle), 0859 (launcher port defaults), 0860 (ADR-0034 order list).

## Receipts

- Release report: `untracked/mission-install/release-root-0.2.0.md` (local, not published).
- Design and contracts: `untracked/mission-install/DESIGN.md`, `CONTRACTS.md` (local).

## Follow-up status (2026-09-25 trace)

All five follow-ups remain open after the 2026-09-24 waves (0856, 0857, 0858, 0859, 0860 carry
2026-09-25 status notes). The next wave's records: 0863–0867.
