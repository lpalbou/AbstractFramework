# Backlog Item: 107_macos_installer_pypi_version_fallback

## Task
Prevent pip failures from stale pinned versions by validating PyPI availability and falling back to latest with explicit warnings.

## Summary
The full framework install failed because the manifest pinned `abstractframework==0.1.2`, which is not on PyPI. Add a preflight check that verifies a pinned version exists on PyPI and falls back to latest when missing, with a `#FALLBACK` warning.

## Reason
Manifests can drift ahead of published PyPI versions, and the installer must handle that gracefully without leaving users blocked.

## Scope
### In scope
- Validate pinned PyPI versions via the PyPI JSON API.
- Fall back to latest when a pinned version is missing.
- Keep existing install behavior for valid pins.

### Out of scope
- Modifying PyPI publishing workflows.
- Adding a full version resolver or lockfile system.
- Offline-first install support.

## Dependencies
- `curl` for retrieving PyPI metadata.

## Expected Outcomes
- Installer no longer fails when a pinned version is missing from PyPI.
- Fallback behavior is explicit and logged.

## Status
Completed. Full report is in `docs/backlog/completed/107_macos_installer_pypi_version_fallback.md`.
