# ADR: macOS installer manager (Rust/Tauri)

## Status
Proposed — 2026-02-21

## Context
- AbstractFramework needs a non‑technical, customizable install experience.
- The current Python GUI installer is a prototype and not a macOS‑native product.
- The installer strategy calls for a GUI manager + manifest‑driven components.
- macOS distribution requires a signed, notarized `.app` or `.pkg`.

## Decision
- Build a macOS installer manager prototype in **Rust + Tauri**.
- Use a **manifest‑driven** component list with dependencies and OS gating.
- Install components via **PyPI/pip** into an isolated venv (no Git clone).
- Detect prerequisites (Python/Node) and emit explicit `#FALLBACK` warnings when missing.
- Keep signing/notarization out of scope for the prototype, but design for it.

## Consequences
- Adds a new Rust/Tauri codebase to maintain.
- Requires Node + Rust toolchains for local builds.
- Enables a future path to a production‑grade installer with proper signing.
