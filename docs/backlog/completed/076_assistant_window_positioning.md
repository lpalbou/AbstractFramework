# Backlog: Fix AbstractAssistant window positioning

## Summary
Align AbstractAssistant windows to the top-right below the menu bar and clamp them to the visible screen to avoid off-screen clipping.

## Why
- Current windows open with extra offsets and can render partially off-screen.
- Consistent top-right positioning improves usability and matches the tray-first UX.

## Scope
### In scope
- Tray bubble positioning.
- Dialogs, popups, and toast windows created by AbstractAssistant.
- Screen bounds clamping based on available geometry.

### Out of scope
- Cross-app window management outside AbstractAssistant.
- OS-native positioning policies for third-party dialogs.

## Dependencies
- Qt available screen geometry reporting.

## Expected outcomes
- All AbstractAssistant windows appear directly below the system tray bar.
- Popups never render off-screen on the right.

## Full Report
- **Summary**: Aligned all AbstractAssistant windows to the top-right below the menu bar and clamped them to the available screen to avoid right-edge clipping.
- **Implementation**:
  - Added shared screen-geometry helpers and top-right positioning/clamping utilities in `abstractassistant/ui/qt_bubble.py`.
  - Updated tray bubble, tool dialogs, message boxes, input dialogs, history dialog, and toast windows to use top-right positioning and clamping.
  - Adjusted history dialog and toast window positioning to use available screen geometry with zero margins.
- **Tests**: Not run (not requested).
