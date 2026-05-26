# 067 — SmartNote systray note capture + self-organizing knowledge

**Status**: Completed  
**Date**: 2026-02-21  
**Priority**: High  
**Components**: smartnote (new), abstractruntime, abstractcore, abstractmemory, abstractsemantics

## Summary
Build a new **SmartNote** application: a macOS systray client that captures notes (with attachments),
routes them to a thin backend, and **self-organizes** the note corpus using durable workflows,
semantic memory, and similarity links. Provide an initial "idea traveler" API to browse topics
and see how ideas evolve over time.

## Reason
Personal notes accumulate quickly and become hard to search, leading to duplicated ideas and
lost context. SmartNote keeps notes unified and organized by topic, similarity, and time,
so knowledge remains discoverable and coherent as it grows to thousands of entries.

## Scope
### In scope
- Create a **new `smartnote/` package** with core docs (README + docs set).
- Implement a **thin systray client** (single-click note capture + attachments).
- Implement a **backend service** with durable ingestion (AbstractRuntime + AbstractCore).
- Automatic classification: summary, topics, entities, and semantic triples.
- Similarity linking (semantic embeddings) for “related notes.”
- Knowledge graph storage via AbstractMemory + AbstractSemantics validation.
- Initial **idea traveler** endpoints: list topics, topic timelines, topic summary.
- Minimal tests (unit-level) for chunking, storage, and topic indexing.

### Out of scope
- Multi-user auth/roles, shared workspaces, cloud sync.
- Full-featured UI browsing (web app) beyond initial topic endpoints.
- Mobile clients.
- Proprietary connectors (Evernote/Notion import).

## Dependencies
- AbstractRuntime (`abstractruntime[abstractcore]`) for durable workflows.
- AbstractCore for LLM calls + embeddings.
- AbstractMemory + AbstractSemantics for KG assertions.
- FastAPI + Uvicorn for the backend HTTP API.
- PyQt5 + pystray + Pillow for the macOS tray client.

## Expected outcomes
- A working SmartNote package with user-oriented docs.
- Durable note ingestion with automatic summaries, topics, and related links.
- Idea traveler API for topic exploration and time-based navigation.
- Tests executed with clear outputs and no silent fallbacks.

## Full Report
- **Summary**: Added a new SmartNote package with a thin systray UI, a durable ingestion server, automatic classification, similarity links, and topic browsing APIs.
- **Implementation**:
  - Added `smartnote/` package with docs, CLI, server, tray UI, runtime workflow, and storage layers.
  - Implemented a chunked LLM ingestion workflow (no truncation) and AbstractMemory assertions.
  - Added note storage, embeddings-based similarity, and topic index for idea browsing.
  - Updated framework docs to reference SmartNote and added ADR 004 for thin-client architecture.
  - Updated `AGENTS.md` with SmartNote architectural notes.
- **Tests**: `python -m pytest smartnote/tests -q`

