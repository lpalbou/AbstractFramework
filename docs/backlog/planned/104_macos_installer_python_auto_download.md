# Backlog Item: 104_macos_installer_python_auto_download

## Task
Add an automated Python installer download flow for macOS when Python 3.10+ is missing.

## Summary
The installer should offer a “Download & Install Python” action that retrieves the official python.org macOS installer, launches it, and guides the user to retry.

## Reason
Non‑technical users need a guided, automated path to satisfy the Python prerequisite without hunting for installers manually.

## Scope
### In scope
- Download the official python.org macOS installer to a safe local cache.
- Open the installer package and guide the user to retry.
- Provide explicit fallback logging if download or launch fails.

### Out of scope
- Silent installation or privilege escalation.
- Bundling a Python runtime inside the app.
- Cross‑platform prerequisite handling.

## Dependencies
- macOS `open` command for launching the `.pkg`.
- `curl` for downloading the installer.

## Expected Outcomes
- Python prerequisite modal offers “Download & Install Python”.
- Installer download is automated and the `.pkg` is opened.
- Failures are explicit and recoverable.

## Status
Completed. Full report is in `docs/backlog/completed/104_macos_installer_python_auto_download.md`.
