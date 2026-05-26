# Backlog Item: 102_macos_installer_event_acl

## Task
Allow the installer UI to listen for backend progress events by enabling Tauri v2 event permissions via capabilities.

## Summary
The UI fails with `plugin:event|listen not allowed by ACL`, which prevents the installer from loading. Add a capability that grants `core:event:default` permissions and wire it into the app security configuration.

## Reason
Tauri v2 requires explicit permissions for core plugins. Without the event permission, the UI cannot subscribe to `installer-log` events and aborts during initialization.

## Scope
### In scope
- Add a capability file granting `core:event:default` to the main window.
- Reference the capability from `tauri.conf.json`.
- Rebuild the macOS `.app` bundle.

### Out of scope
- Frontend bundling changes or replacing the bridge implementation.
- Modifying installer logic, manifest content, or UX.
- Cross-platform packaging/signing/notarization.

## Dependencies
- Tauri v2 permissions/capabilities system.
- Existing installer event stream (`installer-log`).

## Expected Outcomes
- UI loads without ACL errors.
- Event listening works, allowing progress and logs to render.
- Installer bundle builds successfully.

## Report
### Decision summary
- Added a Tauri v2 capability granting `core:event:default` to resolve the ACL error on `plugin:event|listen` without changing the installer UI logic.

### Implementation
- Added `src-tauri/capabilities/main.json` with `core:event:default`.
- Referenced the capability in `src-tauri/tauri.conf.json` under `app.security.capabilities`.

### Tests
- `cargo tauri build` (release) in `abstractinstallers/abstractframework-macos/src-tauri`.

### Results
- Build succeeded and produced `AbstractFramework Installer.app`.

### Follow-ups
- Run the bundled app on a target machine and confirm the log no longer shows `plugin:event|listen not allowed by ACL`.
