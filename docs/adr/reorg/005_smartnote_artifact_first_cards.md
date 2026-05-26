# ADR 005: SmartNote artifact-first cards + KG graph

**Status**: Accepted  
**Date**: 2026-02-21  
**Scope**: SmartNote application

## Context

SmartNote must tame chaotic input by automatically grouping fragments into durable “cards” while preserving replayability and audit trails. The previous note store was an app-specific file cache that did not act as a durable source of truth.

## Decision

- **Artifact-first storage**: each capture becomes a **fragment artifact**; cards are **artifact snapshots** with stable `card_id`s.
- **Auto-classification**: ingestion routes a fragment to an existing card or creates a new card.
- **Derived indexes**: card embeddings and fast lookup are stored in a derived **CardIndex** that can be rebuilt.
- **Graph namespace**: KG edges use `scope="smartnote"` and `owner_id="smartnote"` for isolation.
- **No silent fallbacks**: any degraded path emits `#FALLBACK`.

## Consequences

- Durability and replay are anchored on artifacts + ledger, not app-specific files.
- Card indexing is incremental and can be repaired without data loss.
- SmartNote gains explicit graph links between cards, topics, and entities.
