# AbstractFramework macOS Installer (prototype)

This is a macOS‑native installer manager prototype for installing the full
AbstractFramework with **customizable component selection**. It follows the
manifest‑driven strategy documented in `docs/installers/`.

## What it does

- Presents a GUI to choose **Full** or **Custom** install.
- Installs selected components via **PyPI/pip** into an isolated venv.
- Optionally installs web UIs via **npm** (user‑local prefix).
- Emits explicit `#FALLBACK` warnings for any degraded path.

## What it does not do (yet)

- Code signing / notarization.
- Updates, rollback, or auto‑repair.
- Native packaging for per‑app desktop UIs.

## Layout

```
abstractinstallers/abstractframework-macos/
├─ BUILDING.md
├─ manifest.local.json
├─ src/                 # HTML/CSS/JS UI
└─ src-tauri/           # Rust/Tauri backend
```

## Notes

- The installer uses `manifest.local.json` as a local manifest.
- It installs **from PyPI** (no Git clones).
- macOS is the only target in this prototype.
