# Build the macOS Installer (prototype)

This prototype uses Rust + Tauri. You need the Rust toolchain and the Tauri CLI.

## Prerequisites

- macOS 13+
- Rust (via rustup)
- Tauri CLI
- Node.js (only if you want to install web UI packages)

## Install tools

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
cargo install tauri-cli
```

## Run in dev mode

From `abstractinstallers/abstractframework-macos/src-tauri`:

```bash
cargo tauri dev
```

## Build a macOS app bundle

```bash
cargo tauri build
```

Build output (default):

- `src-tauri/target/release/bundle/macos/AbstractFramework Installer.app`

## DMG packaging

The prototype currently builds the `.app` bundle only. DMG bundling is disabled
(`bundle.targets = ["app"]`) to avoid tooling issues in development environments.
Re-enable DMG once packaging prerequisites are in place.

## Notes

- This is a prototype; signing and notarization are not configured.
- The installer uses `manifest.local.json` for component selection.
