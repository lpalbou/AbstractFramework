# 1340 — Windows: the one-line upgrade works when the gateway was started at login

> Package: framework (scripts/install.ps1)
> Type: bug
> Created: 2026-11-24
> Priority: high
> Labels: windows, installer, upgrade, start-at-login

## Summary

On Windows, re-running the one-line installer (to upgrade) on an install whose gateway was started by "start
at login" stops at the preflight with "port 8080 (the gateway's Network setting) is already in use by another
process". The installer does not recognise its own running gateway, so the documented upgrade cannot run
while the gateway is up, which is the normal state. The fix is written and proven on one machine, on a local
branch; this item ships it with a regression test.

## Why

Start at login is the default, and upgrading with the same one command is the only upgrade path non-technical
users have. Found on 2026-11-24 while upgrading the operator's machine to gateway 0.23.0.

## Current code reality (audited 2026-11-24, root `main` at e3bc201, gateway 0.22.0 and 0.23.0)

- Since the compact Windows login registration (gateway 0.21.1), the Run entry starts the gateway as
  `pythonw.exe %LOCALAPPDATA%\AbstractGateway\AbstractGateway.pyw`; `serve` and its arguments live in the JSON
  next to it (`abstractgateway/os_service.py`, `launch_main`). The process's command line has no `serve`.
- `scripts/install.ps1` `Test-GatewayCommandLine` (line 329 on `main`) requires `abstractgateway` AND the word
  `serve` on the command line. `Test-OwnGatewayPid`, `Test-RecordNamesThisGateway` and `Test-PidFileGateway`
  all go through it, so `Find-OwnGateway` returns 0, `$ours` is false, and the preflight calls `Stop-Install`
  (line 1895) because the port comes from the stored Network setting.
- Fix on the local branch `windows-command-sandbox`, commit 1195485 (worktree
  `C:\abstractframework\worktrees\abstractframework-windows-sandbox`, not pushed): `Test-GatewayCommandLine`
  also accepts the login launcher (`...\AbstractGateway\<name>.pyw`); the gateway is then identified by the
  serve record (pid, data dir, start time), as for a plain `serve`. Proven on Windows 10: `install.ps1 -Pin
  latest` recognised the gateway ("this install's gateway is already running"), stopped it, upgraded 0.22.0 ->
  0.23.0, restarted it through the login service, health check passed, start at login stayed on.
- No automated test covers install.ps1's own-gateway detection (`scripts/tests/` has shell tests for
  install.sh only). `install.sh` is not affected: launchd and systemd units keep `serve` on the command line.

## Scope

### In scope

- Push the fix (branch `windows-command-sandbox`), with a regression test for `Test-GatewayCommandLine` and
  `Find-OwnGateway` against the launcher form (a PowerShell test that dot-sources the functions, run by root CI
  `bootstrap-smoke` on Windows).
- Check the other readers of a gateway command line in install.ps1 (`Get-DeclaredDataDir`,
  `Test-GatewayPidStillOurs`, the "started by hand" branch) against the launcher form, and a named instance
  (a Run value other than `AbstractGateway`).
- Changelog entry (already on the branch).

### Out of scope

- Changing how the gateway registers at login.

## Acceptance criteria

- [x] On Windows, with the gateway running from its login item, `install.ps1` prints "this install's gateway
      is already running" at the preflight and completes; the gateway is healthy afterwards and
      `abstractgateway service status` says start at login is on. (Real run with `-Pin latest` on the operator
      machine, 0.22.0 -> 0.23.0. With no flags: the public one-liner's dry run on the same machine prints the
      line and plans the upgrade; the real no-flags run was not repeated there, it restarts a gateway in use.)
- [x] A process that is not this install's gateway on the same port still stops the installer with the
      "already in use by another process" message. (`tests/test_install_ps1_own_gateway.py`: another program,
      a stale serve record, another instance's launcher.)
- [x] The regression tests fail without the fix (the 4 new tests, with the launcher check removed) and pass
      with it, in root CI on Windows (`bootstrap-smoke`, step "Own-gateway detection").

## Testing

- `powershell -ExecutionPolicy ByPass -File scripts/install.ps1 -Pin latest -Print` on a machine whose gateway
  runs from the login item: the preflight line for port 8080 says "this install's gateway is already running".
- `python -m pytest -q tests/test_install_ps1_own_gateway.py` (Windows; the file already drove install.ps1's
  functions through PowerShell, so the new cases went there instead of a separate `.ps1` test).

## Receipts

- Commit 1195485 on local branch `windows-command-sandbox`.
- Install log: `%LOCALAPPDATA%\AbstractGateway\logs\install-20261124-100322.log` (operator machine, 2026-11-24).
- Shipped in AbstractFramework 0.14.3: root PR lpalbou/AbstractFramework#77, merge commit 999f9d6 (the fix is
  commit e7b7f59 there, the tests dceb908). `Get-DeclaredDataDir` and `Test-GatewayPidStillOurs` needed no
  change; the "started by hand" messages now say "started at login" for the launcher.
