# Backlog Item: 120_macos_installer_env_defaults

## Task
Default the Base URL environment persistence options to enabled.

## Summary
The wizard should proactively apply Base URL environment variables for future processes. Set the GUI (launchd) and terminal (.zprofile) options to enabled by default and warn if the user disables both.

## Reason
Users expect the wizard to complete configuration for future processes without extra manual steps.

## Scope
### In scope
- Pre-check launchd and shell env options in the wizard.
- Warn when Base URL is provided but persistence is disabled.

### Out of scope
- Forcing env changes when the user explicitly opts out.
- Cross-platform env handling.

## Dependencies
- Wizard UI and backend setup flow.

## Expected Outcomes
- Base URL env persistence is enabled by default.

## Report
### Decision summary
- Enabled env persistence options by default and added explicit warning when disabled.

### Implementation
- `src/index.html` pre-checks launchd and shell env options.
- `src-tauri/src/main.rs` emits a warning when Base URL is provided but persistence is disabled.

### Tests
- `cargo tauri build` (release) in `abstractinstallers/abstractframework-macos/src-tauri`.

### Results
- Base URL env persistence is on by default for future processes.
