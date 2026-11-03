# Completed: Installer app upgrade blind spots (boot race, shell token, outside copy)

## Metadata
- Created: 2026-10-17
- Status: Completed
- Completed: 2026-10-17 (released with root 0.11.4)
- Package: abstractframework (scripts/install.sh, scripts/install.ps1)

## Context

Operator, 2026-10-17: "when we update the framework with `curl -LsSf https://abstractframework.ai/install.sh | sh`,
it doesn't update the apps apparently, that's a big issue. I did that on a remote server, it updated
the gateway but not abstractflow for instance, and possibly not the other app."

The installers' apps step (`# >>> apps-upgrade`, added with root 0.11.1) reads the running gateway's
`abstractgateway apps list --json` and brings every installed browser app to `AF_NPM_APPS` with
`abstractgateway apps update <app> --version <pin>`. Reproduced against a hermetic abstractgateway
0.15.1 from PyPI (scratch data dir, port 18082) with Flow 0.9.0 installed; the step had three ways to
leave an app behind, two of them with nothing in red:

1. **Boot race.** The health wait accepted any `/api/health` body naming `abstractgateway`; a gateway
   0.15 answers `"status": "starting"` while it boots and starts its enabled apps on a thread. The
   apps update then ran while an app was still starting.
2. **Shell token wins.** `abstractgateway apps` takes `ABSTRACTGATEWAY_AUTH_TOKEN` from the
   environment before the data dir's bootstrap token. With that variable exported for another
   gateway (as on the operator's Mac) every call answers `Unauthorized`; the step reports "could not
   read the gateway's apps" once, in a long output, and exits 1.
3. **Outside copy hides the install.** When the app's port is held by a copy the gateway did not
   start (a leftover of a gateway that died hard, or `npx` by hand), the gateway lists THAT copy as
   `source: external` with its version, and keeps its own install in `managed_version`. The step
   skipped external rows: the gateway's install stayed old, silently, and `apps launch` returns the
   outside copy instead of starting the install.

Which of the three the remote server hit is in its `<data dir>/logs/install-*.log`; the fix closes
all three.

## What changed

- `scripts/install.sh`, `scripts/install.ps1`: `gw_booted` / `Test-GwBooted` (the health wait and
  the apps step refuse a `"status": "starting"` body); `af_apps_settled` / `Get-AppsSettled` wait up
  to `AF_APPS_START_WAIT` (90 s) for apps the gateway is still starting; the data dir's token goes to
  `apps list` and `apps update` as `--token` (redacted in the shown and logged command); external
  rows carry the gateway's `managed_version`, are updated, and the summary names the outside copy
  (`RUNNING: a copy started outside the gateway, <version> on port <port> (pid <pid>)`), in red with
  the pid to stop when it is not at the pin.
- `tests/test_install_app_upgrade.py`: 22 cases (both installers against a fake gateway): token
  parameter and the loud refusal without it, the wait for a starting app and the bounded wait, the
  outside copy, the boot check.
- `docs/install.md` (Upgrade the apps), `CHANGELOG.md` (Unreleased).

## Evidence

- Hermetic 0.15.1 gateway: with `ABSTRACTGATEWAY_AUTH_TOKEN=stale-value` exported, the old step's
  `apps list` answered `error: Unauthorized`; the new step read the apps and moved Flow's install
  0.9.0 -> 0.10.0 while reporting the outside copies on ports 3001-3005 (the operator's live gateway's
  apps, seen as external by the scratch gateway).
- `python3 -m pytest tests/test_install_app_upgrade.py -q`: 22 passed (pwsh from
  `untracked/root-0.6.2-gate/pwsh`).

## Follow-ups

- The gateway's `abstractgateway apps` CLI could prefer the data dir's bootstrap token over the
  environment when `--data-dir` is given (abstractgateway, not this repo).
- The gateway could tell an outside copy bound to ANOTHER gateway (`external.gateway_url`) from its
  own leftover and offer to replace it; today both are "external".
