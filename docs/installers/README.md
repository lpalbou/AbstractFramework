# Installers

This directory documents a proposed installer system for AbstractFramework. It is a
design reference that explains how a non-technical, cross-platform install experience
should work for the framework and individual apps.

## Goals
- Provide a simple GUI installer for non-technical users.
- Keep the framework modular: install the full stack or one app at a time.
- Follow the gateway-first architecture as the default deployment path.
- Avoid manual environment variables by using guided configuration.
- Surface all fallbacks and truncation explicitly (`#FALLBACK`, `#TRUNCATION`).

## Document map
- `strategy.md` - Recommended installer architecture and SOTA practices.
- `components.md` - Component packaging matrix for AbstractFramework apps.
- `user-journeys.md` - Step-by-step installation flows (full stack and per-app).
- `security-and-os-blocks.md` - How to avoid OS installation blocks.
- `release-and-manifest.md` - Release pipeline and manifest guidance.
- `operations-and-support.md` - Logs, data locations, troubleshooting.
- `implementation-plan.md` - Phased plan to deliver installers.

## Status
These guides describe a target design. A macOS‑only prototype exists at
`abstractinstallers/abstractframework-macos`, and a GUI prototype for AbstractCore
exists at `abstractinstallers/abstractcore`.
