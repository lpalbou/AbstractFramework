# Backlog Item: 109_macos_installer_log_dedup

## Task
Fix duplicate installer log lines caused by double appends in the UI.

## Summary
Installer log messages are duplicated because the UI appends each event twice. Update the event handler to only append once while keeping the unified log pipeline.

## Reason
Duplicate logs make the install flow noisy and confusing; the UI should show a single, consistent stream.

## Scope
### In scope
- Remove the redundant log append in the installer event handler.

### Out of scope
- Changing backend log emission or streaming behavior.
- Altering the log formatting or verbosity.

## Dependencies
- Existing `installer-log` event stream.

## Expected Outcomes
- Each installer log entry appears once.

## Report
### Decision summary
- Removed the duplicate append call so each `installer-log` event is rendered once.

### Implementation
- `src/app.js` now appends `payload.message` only once in the event handler.

### Tests
- `cargo tauri build` (release) in `abstractinstallers/abstractframework-macos/src-tauri`.

### Results
- Installer log no longer duplicates entries.
