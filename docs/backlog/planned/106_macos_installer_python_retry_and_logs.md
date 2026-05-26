# Backlog Item: 106_macos_installer_python_retry_and_logs

## Task
Fix retry behavior after Python install and surface detailed pip failure logs in the installer UI.

## Summary
The installer still detects an older Python after the `.pkg` install and fails pip installs without actionable output. Improve Python detection to select the highest available version and stream command output to the UI log for debugging.

## Reason
macOS GUI apps do not inherit user shell PATH, so retry logic must use absolute-path detection. Additionally, pip failures need full output to diagnose dependency or network issues.

## Scope
### In scope
- Use full version parsing (major/minor/patch) and preference rules for Python selection.
- Stream stdout/stderr from pip/npm/curl into the installer log.
- Keep the existing UX while improving diagnostics.

### Out of scope
- Changing package versions in the manifest.
- Adding new dependency managers.
- System‑level configuration changes.

## Dependencies
- Tauri backend log emission pipeline.

## Expected Outcomes
- Retry uses the newly installed Python instead of the old system one.
- pip errors show real diagnostic output in the UI log.

## Status
Completed. Full report is in `docs/backlog/completed/106_macos_installer_python_retry_and_logs.md`.
