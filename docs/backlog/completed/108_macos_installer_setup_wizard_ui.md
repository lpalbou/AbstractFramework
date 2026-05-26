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

## Report
### Decision summary
- Consolidated install progress and logging into a single panel and implemented an in‑app setup wizard that calls `abstractcore --set-*` commands directly from the installer.

### Implementation
- `src/index.html` removes the duplicate progress log panel, adds progress UI inside the Install panel, and introduces a full setup wizard panel.
- `src/app.css` updates layout for unified progress display and wizard sections.
- `src/app.js` routes all logs to a single output, shows progress in the Install panel, and applies setup via a new `start_setup` backend command.
- `src-tauri/src/main.rs` adds `start_setup` + `run_setup`, plus helpers for CLI execution and env var persistence.

### Tests
- `cargo tauri build` (release) in `abstractinstallers/abstractframework-macos/src-tauri`.

### Results
- Install UI now shows a single log with progress bar + component list.
- Configuration wizard is available after install and applies settings without opening a terminal.

### Follow-ups
- Validate wizard defaults and any optional fields on a clean machine.
