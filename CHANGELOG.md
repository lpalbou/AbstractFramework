# Changelog

All notable changes to AbstractFramework will be documented in this file.

## [Unreleased]

## [0.1.6] - 2026-05-31

### Changed

- Bumped the pinned framework release set:
  `abstractcore==2.13.31`, `AbstractRuntime==0.4.26`,
  `abstractagent==0.3.10`, `abstractgateway==0.2.23`,
  `abstractflow==0.3.17`, `abstractcode==0.3.8`,
  `abstractassistant==0.4.8`, `AbstractMemory==0.2.6`,
  `abstractsemantics==0.0.4`, `abstractvoice==0.10.17`,
  `abstractvision==0.3.18`, and `abstractmusic==0.1.12`.
- Propagated the MLX-Gen `0.18.8` vision runtime floor through AbstractVision and AbstractCore so Apple Silicon installs can use the latest Wan 2.2 video runtime support.
- Included the Gateway multi-user/session control-plane release boundary, including per-user runtimes, admin user management, provider endpoint profiles, and cross-app hosted Gateway URL/session guards.

## [0.1.5] - 2026-05-29

### Changed

- Refactored the meta-package install profiles to only support:
  `pip install abstractframework` (remote-first),
  `pip install "abstractframework[apple]"`, and
  `pip install "abstractframework[gpu]"`.
  Removed legacy profiles like `all`, `backend`, `all-apple`, and `all-gpu`.
- Aligned the meta-package pins with the current repo package versions and their
  revised profile wiring (Gateway-first stack + Flow + CLI app).
- Bumped the pinned framework release set:
  `abstractcore==2.13.30`, `AbstractRuntime==0.4.25`,
  `abstractagent==0.3.9`, `abstractgateway==0.2.21`,
  `abstractflow==0.3.16`, `abstractcode==0.3.7`,
  `abstractassistant==0.4.7`, `AbstractMemory==0.2.6`,
  `abstractsemantics==0.0.4`, `abstractvoice==0.10.17`,
  `abstractvision==0.3.17`, and `abstractmusic==0.1.12`.
- Installed the full Python ecosystem by default (including `abstractassistant`), and
  upgraded it to hardware-local profiles via `abstractframework[apple]` / `[gpu]`.
- Updated the macOS installer manifest to install `abstractframework[apple]` for the full framework.

### Documentation

- Revised the core documentation set for a clearer “two entry points” mental model (AbstractCore SDK vs AbstractGateway control plane), plus a more practical onboarding flow for authoring/deploying `.flow` bundles and monitoring/scheduling runs with AbstractObserver.
- Removed stale install instructions suggesting `abstractgateway[http]` (and `abstractgateway[http,telegram]`) are required for HTTP/SSE or Telegram bridge support; the base `abstractgateway` install already includes the server stack and these extras are compatibility aliases.

## [0.1.4] - 2026-05-26

### Changed

- Bumped the pinned framework release set:
  `abstractcore==2.13.25`, `abstractruntime==0.4.21`,
  `abstractagent==0.3.7`, `abstractflow==0.3.13`,
  `abstractgateway==0.2.17`, `abstractmemory==0.2.6`,
  `abstractsemantics==0.0.4`, `abstractvoice==0.10.16`,
  `abstractvision==0.3.12`, `abstractmusic==0.1.11`, and
  `abstractassistant==0.4.5`.
- Updated the global install profile wiring (core default extras, Gateway/Memory
  extras, and Apple/GPU aggregate profiles) to match the current gateway-first
  release set.
- Tightened repo hygiene so local-only artefacts and sibling projects (venvs,
  caches, and independent repos like SmartNote / AI-Space) stay out of
  AbstractFramework version control and distribution sources.
- Scoped pytest discovery to the root `tests/` folder to avoid collecting tests
  from sibling checkouts that are present locally for orchestration.

### Added

- Added installer documentation and scaffolding under `abstractinstallers/`,
  including:
  - A macOS Tauri v2 installer-manager prototype (`abstractframework-macos`)
  - An AbstractCore installer script + GUI prototype (`abstractcore`)
  - A Tauri init template for future installers (`tauri-init-template`)
- Added helper scripts for orchestration and local dev:
  `scripts/commit.sh`, `scripts/gateway-flow.sh`, and `scripts/gateway-flow-local.sh`.
- Added a root-level install-profile pin alignment test:
  `tests/test_install_profiles.py`.
- Expanded ecosystem docs (ADRs, guides, scenarios, installers pages, and
  backlog entries) to reflect current gateway-first deployment patterns.

### Removed

- Removed an internal memory summary artefact that should not have been tracked.

## [0.1.3] - 2026-05-08

### Changed

- Bumped the pinned framework release set for the install-profile alignment:
  `abstractcore==2.13.12`, `abstractruntime==0.4.8`,
  `abstractagent==0.3.2`, `abstractgateway==0.2.4`,
  `abstractmemory==0.2.4`, `abstractsemantics==0.0.3`,
  `abstractvoice==0.9.2`, `abstractvision==0.3.3`, and
  `abstractmusic==0.1.1`.
- Added native hardware aggregate extras:
  `abstractframework[apple]`, `abstractframework[gpu]`,
  `abstractframework[all-apple]`, and `abstractframework[all-gpu]`.
  The `apple` and `gpu` root profiles delegate to the matching full Gateway
  deployment profile; the `all-*` profiles pin the whole ecosystem.
- Documented the Python-vs-Docker split: Python installs can use native Apple
  and GPU profiles, while Docker remains the lightweight Gateway server image
  plus the explicit NVIDIA server image.

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
