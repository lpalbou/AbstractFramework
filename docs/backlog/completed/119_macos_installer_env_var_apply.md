# Backlog Item: 119_macos_installer_env_var_apply

## Task
Let the wizard apply Base URL environment variables for GUI apps and terminal shells.

## Summary
Environment variables are process-scoped on macOS, so the wizard must explicitly write them into persistent locations. Add optional checkboxes to apply Base URL values via launchd (GUI apps) and `.zprofile` (terminal shells).

## Reason
Users expect Base URL settings to work across apps without manual export commands.

## Scope
### In scope
- Add wizard options for launchd and shell env application.
- Write a LaunchAgent plist for GUI apps.
- Update `~/.zprofile` for terminal shells.
- Log `#FALLBACK` when env application fails.

### Out of scope
- Modifying existing running processes’ environments.
- Cross-platform env variable handling.

## Dependencies
- launchd (`launchctl`) availability on macOS.
- User write access to `~/Library/LaunchAgents` and `~/.zprofile`.

## Expected Outcomes
- Base URL env vars can be applied persistently via the wizard.

## Report
### Decision summary
- Added explicit options for applying Base URL env vars to GUI apps and terminal shells to ensure persistence.

### Implementation
- `src/index.html` adds checkboxes for launchd and shell env application.
- `src/app.js` passes the selected options to the backend.
- `src-tauri/src/main.rs` writes a LaunchAgent plist, calls `launchctl`, and updates `~/.zprofile` as requested.
- Failures emit `#FALLBACK` logs instead of silently ignoring.

### Tests
- `cargo tauri build` (release) in `abstractinstallers/abstractframework-macos/src-tauri`.

### Results
- Base URL env variables can be applied persistently from the wizard.
