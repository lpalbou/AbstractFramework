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

## Status
Completed. Full report is in `docs/backlog/completed/109_macos_installer_log_dedup.md`.
