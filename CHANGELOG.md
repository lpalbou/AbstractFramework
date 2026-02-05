# Changelog

All notable changes to AbstractFramework will be documented in this file.

## [Unreleased]

### Changed

- **Repositioned as documentation-only hub** — This repo is now a documentation index; not published to PyPI
  - Removed all references to `pip install "abstractframework[all]"` from docs
  - Users install individual packages directly from PyPI (e.g., `pip install abstractcode`)
  - Updated `scripts/install.sh` to install individual packages instead of meta-package
  - Updated `abstractframework/__init__.py` to reflect documentation-only purpose
- **Added durability notes** throughout documentation:
  - `README.md` Quick Start section explains session persistence
  - `docs/getting-started.md` Path 2 (Terminal Agent) includes durability note with `/clear` instruction
- Rewrote gateway docs to match the implemented ecosystem (current package names, quickstarts, and commands)
- Updated installer script to use the correct browser UI entrypoint (`npx abstractobserver`)
- Fixed `abstractframework` convenience re-export to expose `abstractcore.create_llm` reliably
- Clarified that AbstractVoice and AbstractVision are **capability plugins** for AbstractCore:
  - Updated `docs/getting-started.md` Path 6 (Voice I/O) and Path 7 (Image Generation) to show integration with AbstractCore via `llm.voice`, `llm.audio`, and `llm.vision` APIs
  - Updated intro table to show these as `abstractcore + plugin` combinations
  - Updated `README.md` Modalities section to explain the capability plugin architecture
  - Updated `docs/README.md` package table with plugin clarification
  - Path 7 now recommends HuggingFace for local image generation (Ollama/LM Studio do not support image generation models)

### Technical (not user-facing)

- Fixed package structure for potential PyPI publishing (`abstractframework/` subdirectory with `__init__.py`)
- Fixed ruff config syntax (`select` moved to `[tool.ruff.lint]`)
- Added `py.typed` marker for PEP 561 type checking support
- Added `Typing :: Typed` and `Operating System :: OS Independent` classifiers

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
