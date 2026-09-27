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

## Related
abstractassistant 0853 (gateway-first sessions), 0868 (installer signing), 0932 (release trace).
