# Installer Strategy (Recommended)

AbstractFramework is modular, gateway-first, and spans Python packages plus browser UIs.
The current install flow (pip + npx + env vars) is powerful but not accessible to
non-technical users. The recommended approach is a two-tier installer system that
matches the framework architecture while minimizing user friction.

## Recommendation in one sentence
Ship a cross-platform Installer Manager (one codebase, OS-specific builds) that
installs signed per-app packages and guides configuration, with a manifest-driven
pipeline and gateway-first defaults.

## Why this fits AbstractFramework
- **Gateway-first is the default path**: a central installer can set up the gateway
  and make the thin clients (Observer, Flow, Code Web, AbstractAssistant, SmartNote)
  immediately usable.
- **Modular packages**: users should be able to install one app or the full stack.
- **Mixed stacks (Python + web UIs)**: a manager can orchestrate the right runtime
  without requiring users to install Python or Node manually.

## "One installer for all OS" - what is feasible
You can have one installer **product** and one codebase, but you still need separate
builds per OS because of signing, notarization, and packaging conventions:
- macOS: notarized `.dmg` or `.pkg`
- Windows: signed `.msi` or `.exe`
- Linux: AppImage or Flatpak (and optional `.deb` / `.rpm`)

The manager presents a unified experience; the distribution artifacts are OS-specific.

## The two-tier model
1. **Installer Manager (GUI)**
   - Installs the framework or individual apps.
   - Guides configuration (provider choice, gateway token, data directory).
   - Runs health checks (equivalent to `abstractcore --install`).
   - Manages updates, rollback, and uninstall.
2. **Per-app packages**
   - Each app is distributed as a signed artifact.
   - Apps declare dependencies (gateway, plugins, models) in the manifest.
   - The manager installs only what the user selects.

## Configuration principles
- **No manual env vars**: use a guided wizard that writes config files
  (e.g., `~/.abstractcore/config/abstractcore.json`).
- **Gateway-first defaults**: install and run AbstractGateway as a service and
  connect browser UIs to it by default.
- **Explicit fallbacks**: any degraded behavior must log `#FALLBACK` with a reason.
- **No silent truncation**: if truncation is required for UI display, tag with
  `#TRUNCATION` and explain why.

## Large model assets
Voice, vision, and music backends require large assets. The manager should:
- Show download size and storage location up front.
- Offer "download now" vs "download on demand".
- Verify checksums and allow resume.

## Summary of SOTA practices applied
- Manifest-driven installers with signed artifacts and checksum verification.
- Separate update channels (stable/beta).
- OS-native signing and notarization to avoid installation blocks.
- Per-app packaging with a central manager for orchestration.
