# Backlog: SmartNote tray quick note UI

## Summary
Refine the SmartNote tray capture dialog into a top-right quick note panel with drag-and-drop attachments.

## Why
- The capture window must feel fast, lightweight, and visually polished.
- Drag-and-drop makes file attachment effortless for quick notes.

## Scope
### In scope
- Redesign the tray note dialog to be top-right and always-on-top.
- Add a drop zone and drag-and-drop attachment handling.
- Improve visual styling for a more graphic, lightweight feel.

### Out of scope
- Backend ingestion or workflow changes.
- New features beyond the capture dialog.

## Dependencies
- Existing SmartNote tray client (PyQt5).

## Expected outcomes
- Quick note panel opens at the top-right under the menu bar.
- Notes can be created with drag-and-drop attachments.

## Full Report
- **Summary**: Reworked the tray note dialog into a top-right quick note panel with drag-and-drop attachments and more visual styling.
- **Implementation**:
  - Updated `smartnote/src/smartnote/ui/note_dialog.py` with a frameless, always-on-top panel, styled card layout, and quick note header.
  - Added drag-and-drop support with a drop zone, attachment list, and remove controls.
  - Implemented top-right positioning below the menu bar and keyboard shortcuts for save/close.
  - Recorded the UX decision in `AGENTS.md`.
- **Tests**: Not run (not requested).
