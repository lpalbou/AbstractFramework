# 055 — Smooth tray animation (green ready state)

## Summary

Increase tray icon animation frame rate to make the ready-state animation smooth.

## Why

- Current 20 FPS animation looks choppy on macOS menu bar.
- Smooth animation improves perceived quality and UX.

## Scope

### In scope

- Increase animation FPS for tray icon updates (cap at 30 FPS).
- Add configurable `system_tray.animation_fps` with validation (10-30).
- Document the new config option.

### Out of scope

- Redesign of icon visuals.
- Changes to gateway or model behavior.

## Dependencies

- Qt/pystray tray icon update paths.

## Expected Outcomes

- Smoother ready-state animation in the system tray.
- Configurable FPS with safe bounds (10-30 FPS).

## Implementation Plan

- Add `animation_fps` to `SystemTrayConfig`.
- Use the configured FPS for Qt and threading animation timers.
- Update docs and config template.

---

## Report

### Work completed

- Added `system_tray.animation_fps` config with safe parsing and validation (10-30 FPS).
- Updated tray animation timers to use the configured FPS for smoother updates.
- Documented the new config option and updated `config.toml`.

### Tests

- `python - <<'PY' ...` (manual smoke: verified animation interval computed from config)
