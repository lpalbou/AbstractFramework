# Backlog Item: 105_macos_installer_python_detection_paths

## Task
Make Python detection robust on macOS by scanning common install locations and selecting the newest Python 3.10+.

## Summary
After installing Python via the official `.pkg`, the installer still detected the older system Python because the app PATH does not include the new location. Add absolute-path scanning to locate Python in the framework install and common package manager locations.

## Reason
macOS GUI apps often run with a minimal PATH. Without absolute-path detection, the installer incorrectly reports Python 3.9 even after a user installs 3.10+.

## Scope
### In scope
- Scan `/Library/Frameworks/Python.framework/Versions/*/bin/python3`.
- Scan common Homebrew, MacPorts, pyenv, asdf, and conda paths.
- Choose the highest Python version ≥ 3.10.
- Report all detected versions with paths in the error message.

### Out of scope
- Modifying PATH or requiring a restart.
- Installing Python silently.
- Windows/Linux prerequisite handling.

## Dependencies
- Local filesystem access to typical Python install paths.

## Expected Outcomes
- Retry install succeeds after Python is installed via the `.pkg`.
- Error messages show detected versions and paths for debugging.

## Report
### Decision summary
- Implemented absolute-path scanning and best-version selection to avoid PATH dependency in a GUI app context.

### Implementation
- Added `python_candidate_paths()` and `probe_python()` to scan framework and common toolchain locations.
- Updated `detect_python()` to select the highest Python version ≥ 3.10 and include path details in error messages.

### Tests
- `cargo tauri build` (release) in `abstractinstallers/abstractframework-macos/src-tauri`.

### Results
- Python detection no longer relies on shell PATH and should pick up python.org installs reliably.

### Follow-ups
- Verify detection on Intel + Apple Silicon machines with Python installed via python.org, Homebrew, and pyenv.
