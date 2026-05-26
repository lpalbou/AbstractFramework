# OS Security and Installation Blocks

Modern operating systems protect users by blocking unsigned or untrusted installers.
To provide a smooth, professional install experience, the AbstractFramework installer
must follow OS-native signing and distribution practices.

## Universal baseline
- All artifacts are signed.
- All downloads are HTTPS with checksum verification.
- The installer validates signatures and checksums before execution.
- Any fallback is explicit (`#FALLBACK`), never silent.

## macOS (Gatekeeper)
**Goal:** No "unidentified developer" warnings.

Best practices:
- Sign the app with a Developer ID certificate.
- Notarize each release with Apple and staple the ticket.
- Distribute via signed `.dmg` or `.pkg`.
- Avoid dynamic code downloads without verification.

If users still see a block:
- Provide a short guide to open **System Settings > Privacy & Security** and allow the app.
- This should be rare if signing and notarization are correct.

## Windows (SmartScreen)
**Goal:** Avoid "Windows protected your PC".

Best practices:
- Use Authenticode signing for all installers and binaries.
- Prefer EV code signing to reduce SmartScreen friction.
- Distribute via `.msi` or signed `.exe`.
- Publish hashes and ensure consistent publisher identity.

If users still see a warning:
- Provide a short guide to click **More info > Run anyway**.
- This should be rare with EV signing and sufficient reputation.

## Linux (distro trust)
**Goal:** Install without manual dependency resolution.

Best practices:
- Prefer AppImage or Flatpak for consistent dependencies.
- Provide `.deb` and `.rpm` for enterprise or server deployments.
- Sign packages and publish repository metadata.

If users encounter permission errors:
- Guide them to install using their OS package manager or Flatpak.
- Avoid asking users to run arbitrary scripts.

## Firmware and GPU drivers
- Run a preflight check for GPU availability.
- If GPU is missing or incompatible, fall back to CPU with `#FALLBACK` and explain
  performance impact.

## Summary
OS blocks are avoidable if we sign, notarize, and verify artifacts. The installer
should make trust visible and never hide degraded behavior.
