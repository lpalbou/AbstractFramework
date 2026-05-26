# AbstractCore Installer (test)

This is a test installer for **AbstractCore**. It installs AbstractCore into an
isolated virtual environment and optionally runs the AbstractCore configuration
wizard and readiness checks.

## Requirements
- Python 3.10+ available on PATH
- Internet access to PyPI (unless using a custom index)

## Quick start (macOS / Linux)
```bash
./install.sh
```

## Quick start (Windows PowerShell)
```powershell
.\install.ps1
```

## GUI installer (test)
```bash
python installer_gui.py
```

To build a clickable app bundle, see `BUILDING.md`.

## Install types
- **Full**: everything for your hardware.
- **Standard**: common features with a light footprint.
- **Custom**: choose modules and providers manually.

The installer maps your choices to AbstractCore configuration (provider/model/API keys)
and stores provider base URLs in a helper env file. The GUI wizard mirrors the
`abstractcore --config` flow: default model, vision fallback, API keys, audio
strategy, video strategy, embeddings, logging, and readiness checks.

## Advanced usage
```bash
python installer.py --help
```

Examples:
```bash
# Install latest AbstractCore with the full extras profile
python installer.py install --profile full

# Install a specific version with minimal extras
python installer.py install --version 2.12.0 --profile minimal

# Run the interactive config wizard after install
python installer.py install --configure

# Run readiness checks (downloads may occur)
python installer.py install --install-check --yes
```

## What this installer does
- Creates an isolated virtual environment in a user-local directory.
- Installs AbstractCore from PyPI with the selected extras profile.
- Writes an install state file in the install prefix.
- Optionally runs `abstractcore --config` and `abstractcore --install`.

## Default install location
- macOS / Linux: `~/.abstractframework/abstractcore`
- Windows: `%LOCALAPPDATA%\AbstractFramework\abstractcore`

## Uninstall
```bash
python installer.py uninstall --yes
```

This removes the virtual environment but keeps user data by default. Use
`--remove-all` to delete the entire install directory.
