# 0856 — Validate the Windows bootstrap and gateway service on real machines

> Package: abstractframework (scripts/install.ps1), abstractgateway (service install on Windows)
> Type: task
> Created: 2026-09-23
> Priority: high
> Labels: install, windows, validation

## Summary

`install.ps1` is parsed and dry-run tested under pwsh 7 on Linux containers and exercised by the
`bootstrap-smoke` CI job on `windows-latest` with `-NoService`, but it has never run on a physical
or VM Windows 10 22H2 / Windows 11 machine (x64 and ARM64), and the gateway's Windows login entry
(`abstractgateway service install`, a Startup shortcut) is marked experimental.

## Scope

### In scope

- Real runs under Windows PowerShell 5.1 and PowerShell 7: one-liner, scriptblock form with
  flags, re-run, `-Uninstall -Purge`.
- `Invoke-Native` stderr handling, `Start-Process -WindowStyle Hidden` with redirects (window
  hidden, PID correct), child-process `irm | iex` for uv, Ollama and LM Studio.
- `uv tool update-shell` editing the user PATH.
- `abstractgateway service install|status|uninstall`: the Startup entry starts the gateway at
  sign-in with no console flash; quoting with spaces in `%LOCALAPPDATA%`; uninstall stops a
  running gateway (it does not today).
- `winget install … --scope user` for Ollama and LM Studio without UAC; Group Policy
  AllSigned/Restricted detection; firewall prompt on the loopback bind.
- NTFS permissions for the token and claim files (0600 is not enforced on NTFS).

### Out of scope

- MSI/enterprise packaging.

## Acceptance criteria

- [ ] Evidence (logs, screenshots) for Windows 10 22H2 x64 and Windows 11 x64/ARM64.
- [ ] A `bootstrap-smoke` Windows leg that runs without `-NoService`, or a documented reason why not.
- [ ] Windows service support no longer marked experimental, or the limits documented.
