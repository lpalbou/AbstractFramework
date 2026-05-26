# Build a Clickable Installer App (test)

This document explains how to package the GUI installer into a clickable app
for local testing. This is not a production-ready distribution process.

## Prerequisites
- Python 3.10+
- `pip` access to install PyInstaller

## Build with PyInstaller
From the `abstractinstallers/abstractcore` directory:

```bash
python -m pip install pyinstaller
pyinstaller --noconfirm --windowed --name "AbstractCore Installer" installer_gui.py
```

Build outputs:
- macOS: `dist/AbstractCore Installer.app`
- Windows: `dist/AbstractCore Installer/AbstractCore Installer.exe`
- Linux: `dist/AbstractCore Installer/AbstractCore Installer`

## Notes
- This is a prototype build path for testing the UX.
- Production builds should be code-signed and notarized on macOS, signed on
  Windows, and packaged using a native Linux format (AppImage or Flatpak).
