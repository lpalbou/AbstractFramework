# 0935 — Windows uninstall: purge fails silently and misses the Assistant and AbstractCode data

- **Status:** planned (not started)
- **Created:** 2026-09-27
- **Area:** root `scripts/install.ps1`

## Summary
`scripts/install.ps1:354-357` runs the purge as `Remove-Item … -ErrorAction SilentlyContinue`, so a failure (the same race with a still-running
gateway as 0934, or a locked file) is never reported, and it removes only the gateway data dir: `%APPDATA%`/`%LOCALAPPDATA%` locations of
the Assistant (`~/.abstractassistant` equivalent) and AbstractCode (`~/.abstractcode`, `~/.abstractcode-tui`) survive. Port the 0934 fix:
stop the gateway process tree (Scheduled Task / Startup entry + `run/gateway-serve.json` pid + descendants), delete each location with
retries and verification, list what remains on failure, exit non-zero with uninstall advice, cover every user-data location, keep model
weights and shared caches.

## Validation
`install.ps1` CI job (`windows-latest`, `-NoService`) gains the purge checks mirrored from `scripts/tests/test_install_user_path.sh`;
real-machine validation stays under 0856.

## Related
0934, 0856 (Windows bootstrap validation on real machines).
