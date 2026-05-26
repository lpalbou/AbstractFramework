# 076 — AbstractCore Installer Rebuild + Docs Refresh

**Status**: Completed  
**Date**: 2026-02-21  
**Priority**: High (UX clarity + installer trust)  
**Components**: abstractinstallers/abstractcore, docs

## Summary

Rebuild the AbstractCore GUI installer bundle and refresh core documentation to
clarify how the installer works (PyPI/pip, no Git clone) and where the prototype
fits in the overall installation story.

## Reason

Users were running outdated app bundles and could not see the full wizard
phases. Documentation did not clearly state that the GUI installer uses PyPI
packages and requires rebuilding to pick up UI changes.

## Scope

### In scope

- Rebuild the PyInstaller bundle for the AbstractCore GUI installer.
- Update `docs/getting-started.md`, `docs/api.md`, `docs/architecture.md`,
  and `docs/faq.md` to reflect the installer prototype behavior.
- Document that the prototype uses PyPI/pip (no Git clone) and requires a
  rebuild for UI updates.

### Out of scope

- Production code signing or notarization.
- A full framework installer or per‑app installers beyond AbstractCore.
- Automated GUI test harnesses.

## Dependencies

- PyInstaller build tooling
- `abstractinstallers/abstractcore` GUI installer prototype

## Expected outcomes

- Fresh app bundle available in `abstractinstallers/abstractcore/dist`.
- Core docs describe the prototype installer accurately.
- Reduced confusion about installer behavior and update cadence.

## Report

### Summary

- Rebuilt the PyInstaller GUI app for AbstractCore.
- Updated core docs to describe the prototype installer, its PyPI/pip install path,
  and the need to rebuild the app bundle for UI changes.
- Captured installer behavior in AGENTS notes.

### Build

- `pyinstaller --noconfirm --windowed --name "AbstractCore Installer" installer_gui.py`

### Tests

- `python -m py_compile abstractinstallers/abstractcore/installer_gui.py abstractinstallers/abstractcore/installer.py`

### Notes

- Build output: `abstractinstallers/abstractcore/dist/AbstractCore Installer.app`.
- PyInstaller emitted a rapidfuzz hook warning; the bundle still built successfully.
