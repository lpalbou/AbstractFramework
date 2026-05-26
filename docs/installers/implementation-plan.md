# Implementation Plan (Phased)

This plan turns the installer strategy into an incremental, shippable roadmap.

## Phase 0 - Design and alignment
- Finalize installer strategy and manifest schema.
- Record an ADR for the installer approach.
- Identify OS support constraints for each app.

## Phase 1 - Manager MVP (gateway-first)
- Build a minimal cross-platform manager.
- Install and run AbstractGateway as a service.
- Package Observer, Flow, and Code Web as local apps or embedded web UIs.
- Provide a basic configuration wizard (provider, gateway token, data dir).

## Phase 2 - Core app coverage
- Add AbstractCode installation and launch support.
- Add health checks (provider reachability, gateway status).
- Add a reliable update and rollback mechanism.

## Phase 3 - OS-native apps
- Integrate AbstractAssistant and SmartNote where supported.
- Enforce OS-specific packaging (macOS, Windows, Linux).
- Add explicit "unsupported on this OS" messaging.

## Phase 4 - Optional capability plugins
- Add Voice/Vision/Music plugin installs.
- Provide model download management with size and storage controls.
- Enforce explicit `#FALLBACK` warnings for CPU-only or degraded modes.

## Phase 5 - Enterprise hardening
- Offline bundles and airgapped install support.
- Signed manifests and audit logs.
- Policy-driven configuration and deployment automation.
