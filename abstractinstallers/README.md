# AbstractInstallers (test sandbox)

This directory is a sandbox for installer experiments. It is intentionally separate
from the production packages to avoid polluting the main repositories.

## Current prototypes
- `abstractcore/` contains a cross-platform installer prototype for AbstractCore,
  including a GUI test app (`installer_gui.py`).
- `abstractframework-macos/` contains a macOS installer manager prototype using
  Rust/Tauri with manifest-driven component selection.

## Constraints
- These prototypes are proofs of concept and do not replace official installs.
- Production-grade builds require signing/notarization and a release pipeline.
