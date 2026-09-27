# 0934 — Uninstall: `--purge` races the still-running gateway ("Directory not empty") and misses other user-data locations

- **Status:** planned (fix in progress 2026-09-27; adversarial verification pending; the one-liner fetches `scripts/uninstall.sh` from main, so the push is the deployment)
- **Created:** 2026-09-27
- **Area:** root `scripts/install.sh` (`--uninstall` path) and `scripts/uninstall.sh`; seam: abstractgateway `service uninstall`

## Summary
On a Mac with a previous install, `curl … uninstall.sh | sh` answered Y to "Also delete your data" failed at step [3]:
`rm -rf '…/Application Support/AbstractGateway'` → "Directory not empty"; the error text then advised "run the installer again", which is
the install path's remedy. A second run found 12K left. After a reinstall the Assistant still listed old sessions (their text is local,
see abstractassistant 0853) while the gateway-side runs, previews and workspaces were gone.

## Cause (to be confirmed by the reproduction)
Step [1] runs `abstractgateway service uninstall` → `launchctl bootout`, which signals the service and returns; the gateway process tree
(serve, runner, tray supervisor, model workers) keeps writing ledgers/logs/caches for seconds, so entries are re-created while `rm -rf`
walks the tree. Nothing waits for exit, kills stragglers, retries, or verifies. `--purge` removes only the gateway data dir, the
installer copy and `~/Library/Logs/AbstractGateway`; the Assistant's `~/.abstractassistant` (sessions, snapshots, preferences) and other
per-package locations survive.

## Scope
Stop and wait for the whole gateway process tree (pid file + process names; TERM then KILL after a bound), retry-and-verify the deletion,
on failure list the remaining entries and the holding processes and exit non-zero with uninstall-specific advice; extend `--purge` to
every user-data location the packages write (inventory from code; model weights and shared caches excluded unless explicitly requested),
each as its own printed, verified step; idempotent second run; POSIX sh; `--print` unchanged in effect; docs/install.md uninstall section.

## Validation
Hermetic reproduction with a scratch data dir and a background writer (before: "Directory not empty"; after: clean), second run prints
nothing-to-do, answer-N keeps data, a path with spaces, an undeletable `uchg` file → explicit listing + non-zero exit; installer tests;
`sh -n`/shellcheck; adversarial review.

## Progress (2026-09-27)
Fix committed locally as root dee84f9 (unpushed; adversarial review 36 pending). Cause confirmed by a hermetic reproduction (3/3 with a
50 ms background writer): `launchctl bootout` returns before the gateway tree exits, and children started with `start_new_session=True`
(entity own-time loop `abstractruntime identity/life.py:1896-1904`, host download jobs `abstractcore config/host_jobs.py:1620`,
maintenance `process_manager.py:803`, apps `apps_manager.py:951` / `apps_desktop.py:436`, the tray `tray_supervisor.py:338`) keep
writing; the old script killed only an installer-written `gateway.pid` a service install never has (the gateway records its pid in
`run/gateway-serve.json`). Ruled out: `uchg` ("Operation not permitted"), permissions ("Permission denied"), root-owned files (the .pkg
is payload-free and runs the installer as the user), symlinks, mounts. When the old deletion won the race it printed "Done." while the
writer recreated the dir — a silent failure. Fix: step [1] stops the tree (uv tool env python, `$TOOL_BIN/abstractgateway`,
`apps/_support/parent_watch.cjs`, pids from `run/gateway-serve.json` / `run/apps/*.json` / `gateway.pid` + descendants; 20 s wait, TERM,
KILL, rescans; a source-checkout gateway is deliberately not matched); step [3] per-location retries + verification + `ls -lO`/`lsof +D`
listing, refuses to cross a mount, keeps a symlink's target; `--purge` also removes `~/Library/Caches/AbstractGateway`,
`~/.abstractassistant`, `~/Library/Logs/Assistant/abstractassistant-*`, `~/.abstractcode`, `~/.abstractcode-tui`; keeps `~/.abstractcore`,
HF cache and weights (named in the output); `-y`; uninstall-specific advice. Tests: `scripts/tests/test_install_user_path.sh` 65 passed
(+13; 5 red without the fix), other script suites green, `sh/bash/zsh/dash -n`. Follow-ups outside this fix: Windows `install.ps1:354-357`
purge is silent on failure and misses the Assistant/Code data (same repo, next item); gateway `service uninstall` should itself wait for
the tree (abstractgateway backlog); Linux XDG-autostart gateways are not stopped by `service uninstall` (`os_service.py:880-890`).

Review 36 (untracked/missions-2026-09-25/REVIEW/36-uninstall-purge.md): GO for pushing, with defects fixed in root 737a9cb: recorded pids are
stopped only when their command line still points at this install (stale pid file → "left alone"); the mount guard resolves both sides
with `pwd -P`; the app match requires `node -r <this data dir>/apps/_support/parent_watch.cjs`; `--purge` also deletes
`~/Library/Preferences/ai.abstractcore.abstractassistant.plist`; a relative `--data-dir` is made absolute once and `/`, `$HOME`, empty are
refused; a location that reappears one second after the purge fails the run; the scan skips the uninstaller's own descendants. Tests
[7e] +9, 74 passed. Delta review 38 pending before the push.

## Related
abstractassistant 0853 (gateway-first sessions), 0868 (installer signing), 0932 (release trace).
