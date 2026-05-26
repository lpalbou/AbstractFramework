# 077 — Installer Wizard Clarity + Defaults

**Status**: Completed  
**Date**: 2026-02-21  
**Priority**: High (UX + configuration trust)  
**Components**: abstractinstallers/abstractcore

## Summary

Improve the AbstractCore GUI wizard clarity by showing current settings when
“keep” options are presented, explaining advanced fields (STT backend id),
offering a language dropdown for STT hints, and aligning logging defaults with
AbstractCore.

## Reason

Users cannot make informed choices when “keep current” is shown without the
current values. The STT backend field is unclear, and free‑form language input
is error‑prone. Defaults must match AbstractCore to avoid confusion.

## Scope

### In scope

- Show current config values for vision/audio/video/embeddings/logging steps.
- Replace free‑text STT language input with a dropdown of supported codes.
- Explain the STT backend id field (advanced, optional).
- Align logging defaults with AbstractCore (ERROR).
- Rebuild the GUI app bundle after changes.

### Out of scope

- New configuration surface for music (AbstractMusic).
- Additional advanced video tuning controls.

## Dependencies

- AbstractCore config file (`~/.abstractcore/config/abstractcore.json`)
- AbstractVoice STT language list

## Expected outcomes

- Wizard steps show current settings clearly.
- STT fields are understandable and safer to use.
- Logging defaults match AbstractCore behavior.

## Report

### Summary

- Added current‑value summaries for vision/audio/video/embeddings/logging.
- Replaced STT language entry with a dropdown and clarified STT backend usage.
- Aligned logging defaults to AbstractCore and removed confusing “keep” option.

### Build

- `pyinstaller --noconfirm --windowed --name "AbstractCore Installer" installer_gui.py`

### Tests

- `python -m py_compile abstractinstallers/abstractcore/installer_gui.py`

### Notes

- Build output: `abstractinstallers/abstractcore/dist/AbstractCore Installer.app`.
- Uses `~/.abstractcore/config/abstractcore.json` for current values.
