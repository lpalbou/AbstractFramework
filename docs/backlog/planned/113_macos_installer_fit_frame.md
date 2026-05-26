# Backlog Item: 113_macos_installer_fit_frame

## Task
Ensure the step-by-step installer fits the window frame without overflow by using a flex layout and internal scrolling.

## Summary
The wizard steps overflow the window height. Make the main container height-aware and allow the active step card to scroll within the frame.

## Reason
The installer should feel native and contained; overflowing content makes it look broken on smaller windows.

## Scope
### In scope
- Convert the main layout to a flex column.
- Hide body overflow and scroll only the active step.
- Remove extra top margins and rely on consistent gaps.

### Out of scope
- Changing window size defaults.
- Redesigning the visual theme.

## Dependencies
- Existing wizard-step structure.

## Expected Outcomes
- The current step always fits the frame.
- Long content scrolls inside the step panel.

## Status
Completed. Full report is in `docs/backlog/completed/113_macos_installer_fit_frame.md`.
