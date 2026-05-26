# 056 — Tray click activation fix (Qt)

## Summary

Ensure the tray icon click reliably opens the UI on macOS.

## Why

- On macOS, tray activation can arrive as `Context` rather than `Trigger`.
- Current logic ignores `Context`, so clicks sometimes do nothing.

## Scope

### In scope

- Map Qt activation reasons to a robust click handler.
- Treat macOS `Context` activation as a single click.
- Add safe fallbacks when click timer isn't initialized.

### Out of scope

- Redesign of tray UI or context menu behavior.
- Voice mode behavior changes.

## Dependencies

- PyQt5 `QSystemTrayIcon` activation reasons.

## Expected Outcomes

- Clicking the tray icon reliably opens the UI on macOS.
- Double-click handling remains intact.

## Implementation Plan

- Resolve ActivationReason enums and handle `Context` on macOS.
- Fallback to single-click if timer isn't initialized.

---

## Report

### Work completed

- Updated Qt tray activation handling to use ActivationReason enums with fallbacks.
- Treated `Context` activation as a single click on macOS.
- Added fallback to single-click when the click timer is unavailable.
- Added context-menu hook on macOS to treat menu activation as a click when Qt does not emit `activated`.

### Tests

- `python -m pytest abstractassistant/tests` (61 passed, 7 skipped; warnings remain for legacy tests and optional AbstractVoice)
