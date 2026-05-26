# Backlog Item: 101_macos_installer_bridge_fallback

## Task
Make the macOS installer UI resilient to missing Tauri global bridge injection by adding a runtime fallback that uses `__TAURI_INTERNALS__` directly.

## Summary
The installer UI can appear "static" when the Tauri global API is unavailable on some machines or WebView configurations. Add a fallback bridge path that uses the internal Tauri IPC surface so UI events and install progress work across a broader range of macOS setups.

## Reason
Users are still seeing "Tauri bridge unavailable" despite CSP and global bridge settings. A runtime fallback is needed to make the app robust on older or stricter environments without requiring a full frontend rewrite.

## Scope
### In scope
- Implement a fallback bridge using `window.__TAURI_INTERNALS__` for `invoke` and `listen`.
- Expose bridge mode in the UI status/logs for debugging.
- Rebuild the `.app` bundle.

### Out of scope
- Replacing the frontend with a bundled `@tauri-apps/api` build.
- Changing installer manifest, component list, or install logic.
- Cross-platform packaging or notarization work.

## Dependencies
- Tauri v2 runtime (provides `__TAURI_INTERNALS__` IPC).
- Existing macOS installer UI in `abstractinstallers/abstractframework-macos/src`.

## Expected Outcomes
- UI event handlers attach reliably across macOS versions.
- "Bridge: ready (global/internal)" is shown in the header.
- Installer bundle builds successfully.

## Report
### Decision summary
- Added a bridge fallback to `__TAURI_INTERNALS__` instead of a full frontend rewrite to remove reliance on global API injection and CSP quirks while keeping the existing UI intact.

### Implementation
- `abstractinstallers/abstractframework-macos/src/app.js` now resolves the bridge via the global API when available and falls back to `__TAURI_INTERNALS__` for `invoke` and `listen`.
- UI status and logs now surface the bridge mode (global or internal) for diagnostic clarity.

### Tests
- `cargo tauri build` (release) in `abstractinstallers/abstractframework-macos/src-tauri`.

### Results
- Build succeeded and produced `AbstractFramework Installer.app`.

### Follow-ups
- Run the bundled app on target macOS machines and confirm the bridge status shows `Bridge: ready (internal)` when global injection is unavailable.
- If any environment still fails to expose `__TAURI_INTERNALS__`, consider bundling `@tauri-apps/api` as a module build.
