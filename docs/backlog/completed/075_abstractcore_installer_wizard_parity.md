# 075 — AbstractCore Installer Wizard Parity

**Status**: Completed  
**Date**: 2026-02-21  
**Priority**: High (installer UX + config parity)  
**Components**: abstractinstallers/abstractcore, abstractcore

## Summary

Extend the AbstractCore GUI installer wizard to cover the same major setup
phases as `abstractcore --config` (vision fallback, audio/video strategies,
embeddings, logging) so non‑technical users can complete a full configuration
without a terminal.

## Reason

The current GUI wizard only covered provider defaults and API keys, leaving
critical capabilities (vision fallback, audio/video handling, embeddings, and
logging) unconfigured. This creates confusion and incomplete setups compared
to the CLI wizard.

## Scope

### In scope

- Add wizard steps that map to `abstractcore --config` phases.
- Persist vision fallback, audio/video strategy, embeddings, and logging via
  the AbstractCore CLI.
- Expand API key coverage to match the CLI wizard (including Google).
- Provide tooltips and copy that explain each configuration phase.

### Out of scope

- Music fallback configuration (owned by AbstractMusic).
- New installer packaging or signing changes.
- Automated UI tests for Tkinter.

## Dependencies

- `abstractcore` configuration flags (`--set-vision-provider`, `--set-audio-strategy`, etc.).
- Tkinter GUI flow in `abstractinstallers/abstractcore/installer_gui.py`.

## Expected outcomes

- GUI wizard mirrors the major phases of `abstractcore --config`.
- Users can configure defaults, fallbacks, embeddings, and logging in the GUI.
- Configuration is persisted without requiring a terminal.

## Report

### Summary

- Added wizard steps for vision fallback, audio/video strategy, embeddings, and logging.
- Wired GUI choices to new installer configure flags mapped to AbstractCore CLI commands.
- Expanded API key coverage (Google) and refreshed tooltips/microcopy.

### Tests

- `python -m py_compile abstractinstallers/abstractcore/installer_gui.py abstractinstallers/abstractcore/installer.py`

### Notes

- Music fallback remains in AbstractMusic; the wizard surfaces an informational note only.
