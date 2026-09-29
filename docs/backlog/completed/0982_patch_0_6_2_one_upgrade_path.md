# 0982 — Patch 0.6.2: one upgrade path (the line, the .command, the consoles and the tray run one installer)

> Package: abstractframework (installers, docs); abstractgateway 0.7.2 (console crate 0.11.1); abstractcore 2.19.0
> Type: task
> Created: 2026-09-28
> Priority: high
> Labels: installer, upgrade, self-update, patch-wave
> Status: completed 2026-09-28. Staged on root `wave4/root` for root 0.6.2; it ships after abstractcore 2.19.0 and abstractgateway 0.7.2 are on PyPI (cascade GO 2026-09-28)

## Summary

Implementation record for root 0.6.2. Gateway 0.7.1's Update ran `uv tool upgrade abstractgateway`,
which never moves an installer install (uv keeps the installer's `==` pin), and it compared against
PyPI's newest gateway instead of the framework release. Root 0.6.2 makes the installer the one
upgrade: re-running the line, the Mac `.command`, and Update in the web console, the terminal
console and the tray all run the same `install.sh`.

## What shipped (root)

- **docs/install-upgrade** (`cfa352f`): `--pin latest` runs `uv tool install --upgrade`; the Upgrade
  section; README / Getting started lead with Install.
- **feat/one-upgrade-path** (`210bb18` … `9a32d07`, merged in `wave4/root`):
  - install.sh detects the install (`found: upgrading to` / `already up to date`), remembers
    `--data-dir` (via the gateway pointer), `--no-console`, `--no-code-cli`, `--no-core-cli`,
    `--no-tray`, `--full` (`--with-*` / `--no-full` turn them back), writes the release matrix
    (`AF_FRAMEWORK_VERSION`, `AF_PY_MATRIX`) as uv constraints, restarts the gateway when anything
    moved (launchd, a running systemd user unit, background), falls back to a background start when
    the login item fails, prints `Changes:`; `--no-start` says a restart is due; `--print-versions`
    names the release and the matrix;
  - install.ps1 parity (stops a running gateway before files change on Windows);
  - `Install AbstractFramework.command` runs the latest install.sh, its bundled copy only offline.
- **Release commit (this item)**:
  - pins abstractcore 2.19.0, abstractgateway 0.7.2, crate abstractgateway-console 0.11.1 (others
    unchanged from 0.6.1); manifest regenerated with the generator; installers' pins and matrix;
    docs version tables;
  - install.sh / install.ps1: under `--no-start` (`-NoStart`, the gateway's Update run), a recorded
    port held by a process the installer does not recognise as its own (for example a hand-started
    `serve`) is kept, never moved to the next free port and recorded; the summary says so and that a
    restart is due. `test_install_user_path.sh` [18] is RED on the merged install.sh (2 checks: the
    port moved to 18871), GREEN after; `test_install_ps1_no_start_keeps_the_recorded_port_like_install_sh`
    RED on the previous install.ps1;
  - docs/install.md: Upgrade rewritten for gateway 0.7.2 (Update runs install.sh; URL, commit,
    sha256 and command shown; installed / already up to date / didn't finish; Windows PowerShell
    line; the `.command` upgrades; remembered options); options table; installers strategy and
    user-journeys aligned; CHANGELOG `[0.6.2]`; llms regenerated.
- Gateway side (abstractgateway 0.7.2, `e34c59c` on its `main`): `self_update.py` installer path,
  one `update_view()` for every client, the launchd bootout -> bootstrap race fix, tray "already up
  to date", tiers read from core.

## Validation

See `untracked/wave4-STAGE.md` (gate results for both repos).

## Follow-ups

- [0983](../planned/0983_follow_ups_after_0_6_2.md).

## Receipts

- `untracked/one-upgrade-note.md` (design, RED evidence, per-surface user flow);
  `untracked/wave4-STAGE.md`.
