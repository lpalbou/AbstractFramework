# Backlog: SmartNote artifact-first graph ingestion

## Summary
Re-architect SmartNote to store notes as gateway artifacts, classify fragments into note cards, and build a KG-based graph for browsing.

## Why
- Artifact + ledger storage is the durable source of truth and supports replay.
- Notes should auto-classify into existing cards or create new cards to reduce chaos.
- Graph links (topics, entities, related cards) enable intuitive exploration.

## Scope
### In scope
- Define artifact schemas for note fragments and note cards.
- Ingest flow: classify fragment → link to card or create new card.
- Store time + optional location metadata on artifacts.
- Assert KG links using SmartNote namespace.
- Maintain derived indexes incrementally (no full rebuild on startup).
- Add query flows for cards, timelines, and graph neighborhood.

### Out of scope
- Rewriting VisualFlow sandbox (trusted imports) for this iteration.
- UI redesign beyond current quick-capture panel.

## Dependencies
- AbstractGateway bundle mode.
- AbstractRuntime artifact store and memory_kg effects.
- AbstractSemantics predicate registry updates.

## Expected outcomes
- SmartNote can ingest chaotic text and attach it to existing cards or create new cards.
- Durable artifacts represent fragments + cards with timestamps and location when available.
- Graph edges make implicit links explicit and enable idea exploration.

## Full Report
- **Summary**: Implemented artifact-first fragments + cards, auto-classification into cards, and KG assertions for graph navigation.
- **Implementation**:
  - Added fragment/card models and artifact storage helpers with SmartNote tagging.
  - Reworked ingestion to classify fragments, update cards, store artifacts, and update a derived CardIndex.
  - Updated query tools to return cards + fragment timelines and to search via card embeddings.
  - Documented the card-based flow, auto-classification, and new configuration knobs; added ADR 005.
- **Tests**:
  - `python -m pytest smartnote/tests/test_card_index.py`
  - `python -m pytest smartnote/tests`
