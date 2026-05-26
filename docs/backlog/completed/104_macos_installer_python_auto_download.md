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

## Report
### Decision summary
- Implemented a guided download‑and‑open flow using the official python.org macOS installer, keeping installation explicit and user‑approved.

### Implementation
- `src-tauri/src/main.rs` adds `download_python_installer` to download the Python 3.12.10 macOS installer, cache it, and open the `.pkg`.
- `src-tauri/src/main.rs` enforces macOS version checks, validates `curl` availability, and emits explicit errors for unsupported systems.
- `src/app.js` routes the prerequisite modal action to `download_python_installer` and falls back to opening the python.org downloads page on failure.
- `src/index.html` updates modal copy to reflect the automated install flow.

### Tests
- `cargo tauri build` (release) in `abstractinstallers/abstractframework-macos/src-tauri`.

### Results
- Users can download and launch the Python installer directly from the prerequisite modal.
- Failures are surfaced with `#FALLBACK` logs and a manual download path.

### Follow-ups
- Confirm the cached installer path and launch behavior on multiple macOS versions.
