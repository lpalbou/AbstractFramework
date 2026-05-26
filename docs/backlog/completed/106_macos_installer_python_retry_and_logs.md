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

## Report
### Decision summary
- Implemented PATH‑independent Python selection with patch-level parsing and a preference order, and added streaming command output to make failures actionable.

### Implementation
- `src-tauri/src/main.rs` now parses Python versions with patch numbers and selects the newest eligible version with a preference for python.org frameworks.
- `run_command` now streams stdout/stderr into the UI log so pip failures show full diagnostics.

### Tests
- `cargo tauri build` (release) in `abstractinstallers/abstractframework-macos/src-tauri`.

### Results
- Retry should pick the new python.org installation instead of the old system Python.
- pip/npm/curl errors now appear in the installer log for debugging.

### Follow-ups
- Confirm detection order on machines with multiple Python 3.12 installs (python.org + Homebrew).
