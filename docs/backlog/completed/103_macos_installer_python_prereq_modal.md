# Backlog Item: 103_macos_installer_python_prereq_modal

## Task
Handle missing Python 3.10+ by prompting users with a clear modal and a guided install path.

## Summary
When Python is missing or too old, the installer currently fails with a log message. Add a prerequisite event flow and a modal that asks the user to install Python 3.10+ and retry, so the failure is actionable for non‑technical users.

## Reason
Users need a guided, friendly remediation path when prerequisites are missing. This prevents confusing failures and improves installation success rates.

## Scope
### In scope
- Emit a structured prerequisite event when Python 3.10+ is unavailable.
- Show a modal with a Python download action and retry flow.
- Keep the UI responsive and log a clear fallback if the browser cannot open.

### Out of scope
- Auto‑installing Python or elevating privileges.
- Adding new package managers or system‑level installers.
- Changing the install manifest or component logic.

## Dependencies
- Existing installer event stream (`installer-log`).
- macOS `open` command for launching the download page.

## Expected Outcomes
- Missing Python triggers a modal with clear instructions.
- Users can open the official download page and retry the install.
- UI does not appear stuck when prerequisites are missing.

## Report
### Decision summary
- Implemented a prerequisite event and modal flow instead of auto‑installing Python, keeping the installer safe and user‑driven while providing a clear remediation path.

### Implementation
- `src-tauri/src/main.rs` emits a `prereq` event with a `python` code and download URL when Python 3.10+ is missing or too old.
- `src/app.js` listens for `prereq` events and displays a modal with “Open Python download” and “Retry install” actions.
- `src/app.css` and `src/index.html` add the modal UI and styling consistent with the existing theme.
- A fallback log with `#FALLBACK` is emitted when automatic browser opening fails.

### Tests
- `cargo tauri build` (release) in `abstractinstallers/abstractframework-macos/src-tauri`.

### Results
- The installer no longer fails silently when Python is missing; it prompts users with a clear, actionable modal.

### Follow-ups
- Verify the modal flow on multiple macOS versions and ensure retry succeeds after Python is installed.
