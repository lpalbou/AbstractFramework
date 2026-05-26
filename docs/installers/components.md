# Components and Packaging Matrix

This guide maps AbstractFramework components to installer-friendly packages and
highlights OS availability and dependencies.

## Core services (gateway-first defaults)
| Component | Type | Packaging target | Default dependencies | Notes |
|---|---|---|---|---|
| AbstractGateway | Background service | Signed OS package | AbstractCore + AbstractRuntime | Installs a gateway service with a data dir and auth token. |
| AbstractCore | Library | Bundled with Gateway and apps | Provider config | Installed implicitly; users should not install it manually. |
| AbstractRuntime | Library | Bundled with Gateway and apps | Storage backend | Installed implicitly; provides durability/ledger. |

## User-facing apps
| Component | Type | Packaging target | Default dependencies | Notes |
|---|---|---|---|---|
| AbstractObserver | Browser UI | Desktop wrapper or local web server | Gateway | Should auto-connect to local gateway. |
| AbstractFlow (Editor) | Browser UI | Desktop wrapper or local web server | Gateway | Requires gateway URL + token. |
| AbstractCode Web | Browser UI | Desktop wrapper or local web server | Gateway | Requires gateway URL + token. |
| AbstractCode (terminal) | CLI app | Bundled runtime + launcher | Local LLM or gateway | Provide a GUI launcher for non-technical users. |
| AbstractAssistant | Tray app | OS-native desktop app | Gateway (default) | Currently macOS-focused; show availability per OS. |
| SmartNote | Tray app | OS-native desktop app | Gateway + SmartNote bundle | Currently macOS-focused; show availability per OS. |

## Optional capability plugins (large models)
| Component | Type | Packaging target | Default dependencies | Notes |
|---|---|---|---|---|
| AbstractVoice | Plugin | Optional add-on | STT/TTS models | Show download sizes; support offline prefetch. |
| AbstractVision | Plugin | Optional add-on | Vision models | Large assets; allow deferred downloads. |
| AbstractMusic | Plugin | Optional add-on | ACE-Step assets | Very large downloads; allow on-demand. |

## External dependencies (detected, not bundled)
| Dependency | Role | Installer behavior |
|---|---|---|
| Ollama | Local LLM server | Detect and link; offer install link if missing. |
| LM Studio | Local LLM server | Detect and link; guide setup if missing. |
| GPU drivers | Acceleration | Preflight checks; show clear warnings if missing. |

## Availability rules
- The manager should only list components that are supported on the current OS.
- Unsupported components must show a clear reason and a roadmap link.
- Any fallback (e.g., CPU-only) must emit a `#FALLBACK` warning.
