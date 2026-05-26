# 098 — macOS Installer UI Fixes (Custom + Folder Picker)

**Status**: Completed  
**Date**: 2026-02-22  
**Priority**: High (installer UX)  
**Components**: abstractinstallers/abstractframework-macos

## Summary

Fix the macOS installer UI to enable component selection in Custom mode and
provide a native folder picker for the install directory.

## Reason

Custom install mode did not allow users to select components, and the install
directory field lacked the standard macOS folder picker, making the UX confusing
and error‑prone.

## Scope

### In scope

- Enable component selection in Custom mode.
- Add Select all / Clear all shortcuts.
- Add a native macOS folder picker for the install directory.
- Rebuild the macOS installer bundle.

### Out of scope

- Update/rollback flows.
- Signing/notarization.

## Dependencies

- Rust/Tauri installer prototype

## Expected outcomes

- Custom mode supports selecting components.
- Folder picker uses the system dialog.

## Report

### Summary

- Enabled Custom component selection with toolbar shortcuts.
- Added a native folder picker via `rfd` and a Browse button in the UI.
- Rebuilt the macOS installer bundle.

### Build

- `cargo tauri build`

### Tests

- Not run (UI change only).

### Notes

- Bundle output: `abstractinstallers/abstractframework-macos/src-tauri/target/release/bundle/macos/AbstractFramework Installer.app`.
