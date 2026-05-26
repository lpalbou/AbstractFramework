# Backlog Item: 108_macos_installer_setup_wizard_ui

## Task
Unify installer logging/progress UI and add a post‑install AbstractCore configuration wizard inside the macOS installer.

## Summary
The installer currently shows duplicate logs and lacks the promised configuration wizard. Consolidate progress + logs into the Install panel and add a built‑in setup wizard that applies AbstractCore configuration directly.

## Reason
Users need a single, clear progress/log view during install and an in‑app configuration flow without falling back to CLI commands.

## Scope
### In scope
- Single installer log area with progress bar + component list.
- Post‑install wizard UI with AbstractCore config options.
- Backend command to apply config via `abstractcore --set-*` flags.

### Out of scope
- Replacing the installer runtime or changing the packaging model.
- Automatically configuring provider credentials without user input.
- Cross‑platform installer changes.

## Dependencies
- Installed AbstractCore CLI in the installer venv.
- Existing Tauri event log pipeline.

## Expected Outcomes
- Only one installer log is visible.
- Progress bar and component list show in the Install panel.
- Configuration wizard runs after install and applies settings without terminal use.

## Status
Completed. Full report is in `docs/backlog/completed/108_macos_installer_setup_wizard_ui.md`.
