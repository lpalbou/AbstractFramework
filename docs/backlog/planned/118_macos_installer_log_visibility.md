# Backlog Item: 118_macos_installer_log_visibility

## Task
Ensure the install log area stays visible and spacious within the install step.

## Summary
The install log collapsed to a tiny viewport, making the UI unusable during installs. Update the install panel layout so the log expands to fill available space.

## Reason
Users must be able to see progress and errors without resizing the window.

## Scope
### In scope
- Make the install panel a flex column with a larger log region.
- Ensure actions/progress remain fixed-size.

### Out of scope
- Changing log content or verbosity.
- Altering window size.

## Dependencies
- Install panel layout.

## Expected Outcomes
- Install log is visibly large by default.
- Progress elements remain above the log.

## Status
Completed. Full report is in `docs/backlog/completed/118_macos_installer_log_visibility.md`.
