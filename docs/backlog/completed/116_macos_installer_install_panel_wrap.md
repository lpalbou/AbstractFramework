# Backlog Item: 116_macos_installer_install_panel_wrap

## Task
Prevent install log text from overflowing the install card.

## Summary
Long pip output lines were overflowing the install panel. Wrap log lines and ensure the log area flexes within the install step.

## Reason
Overflowing text makes the UI look broken and reduces readability during installation.

## Scope
### In scope
- Enable line wrapping for the install log.
- Ensure the log panel flexes and scrolls within the install step.

### Out of scope
- Changing log content or verbosity.

## Dependencies
- Install panel layout.

## Expected Outcomes
- Log text stays inside the install card.
- The install panel remains frame-safe.

## Report
### Decision summary
- Wrapped log text and adjusted flex settings to keep long lines inside the install panel.

### Implementation
- `src/app.css` sets wrapping for `#install-panel #log-output` and keeps the log container flexed.

### Tests
- `cargo tauri build` (release) in `abstractinstallers/abstractframework-macos/src-tauri`.

### Results
- Log lines no longer overflow the install card.
