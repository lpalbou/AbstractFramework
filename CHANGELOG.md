# Changelog

All notable changes to AbstractFramework will be documented in this file.

## [Unreleased]

*No unreleased changes.*

## [0.1.2] - 2026-02-12

### Changed

- **Bumped `abstractcore` pin from `2.11.8` to `2.11.9`**
- **Fixed `abstractgateway` pin from `0.2.1` to `0.1.0`** (aligned with actual repo version)
- **Bumped framework version from `0.1.1` to `0.1.2`**

### Documentation

- **Comprehensive documentation overhaul** surfacing 21 previously hidden capabilities:
  - Added "What Can You Build?" section to README with 12 concrete use cases
  - Added "Key Capabilities in Depth" section with code examples (MCP, structured output, streaming, voice, vision, glyph compression, embeddings, server, scheduling, event bridges, CLI apps, evidence/provenance)
  - Enhanced docs/README.md as a welcoming hub with "What's Possible" capability overview
  - Updated docs/architecture.md with MCP integration, evidence/provenance, scheduled workflows, split API/runner, and media pipeline architectures
  - Added 3 new getting-started paths: MCP Integration (Path 13), Structured Output (Path 14), OpenAI-Compatible Server (Path 15)
  - Added 17 new FAQ entries covering MCP, structured output, streaming, async, glyph compression, embeddings, server mode, CLI apps, snapshots, interaction tracing, voice cloning, GGUF models, scheduled workflows, event bridges, split API/runner, SQLite backend
  - Enhanced docs/api.md with "Where to Find Specific APIs" navigation table
  - Updated docs/glossary.md with 9 new terms (Snapshot, History bundle, Provenance, Evidence, MCP, Event bridge, Structured output, Glyph compression, Interaction trace)
  - Updated llms.txt with full ecosystem repo list and enriched descriptions

## [0.1.1] - 2026-02-04

### Added

- **Unified release profile API metadata** in `abstractframework/__init__.py`:
  - `RELEASE_VERSIONS` (pinned package versions for global profile)
  - `CORE_DEFAULT_EXTRAS` (default AbstractCore extras installed by this release)
  - `get_release_profile()` helper

### Changed

- **Global `abstractframework==0.1.1` profile is now full-stack by default**:
  - Pins and installs all ecosystem Python packages together:
    - `abstractcore==2.11.8`
    - `abstractruntime==0.4.2`
    - `abstractagent==0.3.1`
    - `abstractflow==0.3.7`
    - `abstractcode==0.3.6`
    - `abstractgateway==0.2.1`
    - `abstractmemory==0.0.2`
    - `abstractsemantics==0.0.2`
    - `abstractvoice==0.6.3`
    - `abstractvision==0.2.1`
    - `abstractassistant==0.4.2`
  - Installs `abstractcore` with `openai,anthropic,huggingface,embeddings,tokens,tools,media,compression,server`
  - Installs `abstractflow` with `editor`
- **Docs repositioned to a single-entrypoint experience**:
  - `README.md` now leads with one-command install and pinned version table
  - `docs/README.md`, `docs/getting-started.md`, and `docs/faq.md` now describe the full-release install path first
  - Added a dedicated "create more solutions" section in `README.md` for `.flow`-based specialized agent deployment
- Updated `scripts/install.sh` to install `abstractframework==0.1.1` directly
- Updated status output in `abstractframework.print_status()` to point to one-command full install

### Technical (not user-facing)

- Switched `pyproject.toml` dependency strategy from open-ended/minimal constraints to pinned ecosystem versions for deterministic global installs

## [0.1.1] - 2026-02-04

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
