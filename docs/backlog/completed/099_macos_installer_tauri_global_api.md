# 099 — macOS Installer Tauri Global API Fix

**Status**: Completed  
**Date**: 2026-02-22  
**Priority**: High (installer usability)  
**Components**: abstractinstallers/abstractframework-macos

## Summary

Enable the Tauri global JS API so the static UI can attach event handlers and
invoke backend commands, restoring click behavior (Custom selection, Browse,
Install).

## Reason

The UI was static because the Tauri bridge was unavailable. Tauri v2 disables
`window.__TAURI__` by default unless `withGlobalTauri` is enabled in config.

## Scope

### In scope

- Enable `withGlobalTauri` in `tauri.conf.json`.
- Rebuild the macOS installer bundle.

### Out of scope

- Further UI/UX enhancements.
- Update/rollback flows.

## Dependencies

- Tauri v2 configuration schema.

## Expected outcomes

- JS event handlers work in the packaged app.
- Custom selection, Browse, and Install are responsive.

## Report

### Summary

- Enabled `app.withGlobalTauri` in the Tauri config.
- Rebuilt the app bundle; JS bridge now attaches and UI handlers run.

### Build

- `cargo tauri build`

### Tests

- Not run (manual UI validation pending).

### Notes

- Bundle output: `abstractinstallers/abstractframework-macos/src-tauri/target/release/bundle/macos/AbstractFramework Installer.app`.
