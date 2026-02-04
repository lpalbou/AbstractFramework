# Changelog

All notable changes to AbstractFramework will be documented in this file.

## [Unreleased]

### Changed

- Rewrote gateway docs to match the implemented ecosystem (current package names, quickstarts, and commands).
- Updated installer script (`scripts/install.sh`) to use the correct browser UI entrypoint (`npx abstractobserver`).
- Fixed `abstractframework` convenience re-export to expose `abstractcore.create_llm` reliably.

## [0.1.0] - 2026-02-04

### Added

- Initial release of AbstractFramework as an **Agentic OS** — an open-source operating system for AI agents
- Positioned as a complete, end-to-end infrastructure with no black boxes and no external dependencies
- Comprehensive documentation:
  - `README.md` - Main entry point and overview
  - `docs/getting-started.md` - Installation and setup guide
  - `docs/architecture.md` - System design and components
  - `docs/configuration.md` - Environment variables reference
  - `docs/faq.md` - Frequently asked questions
- Installation script (`scripts/install.sh`)
- Meta-package with optional dependencies:
  - `abstractframework[all]` - Full installation
  - `abstractframework[backend]` - Backend services only
  - Individual component extras

### Components

Python packages (PyPI):
- abstractcore - LLM abstraction layer
- abstractruntime - Durable execution engine
- abstractagent - Agent framework
- abstractflow - Workflow orchestration
- abstractcode - AI coding assistant backend
- abstractgateway - HTTP API gateway
- abstractmemory - Temporal triple store (KG substrate)
- abstractsemantics - Semantics registry + KG assertion schema helpers
- abstractvoice - Speech-to-text & TTS
- abstractvision - Image & video processing
- abstractassistant - High-level assistant API

JavaScript packages (npm):
- abstractobserver - Gateway-only observability UI (Web/PWA)
- @abstractframework/ui-kit - Shared UI components
- @abstractframework/panel-chat - Chat panel components
- @abstractframework/monitor-flow - Flow monitoring components
- @abstractframework/monitor-gpu - GPU monitoring widget
- @abstractframework/monitor-active-memory - Memory explorer components
