# Runtime artifact observability proposed track

## Status
Proposed

## Purpose
This track preserves Observer and Runtime supervision ideas that are related to artifact observability but are not yet ready for implementation. The completed `0188` through `0194` work made artifacts, activity queues, logs, and waits more visible; the remaining issues need product and contract decisions before more code lands.

## Items
- `0195_observer_wait_replay_chat_session_handoff.md`: investigate whether waiting runs should be resumed through a replayable session chat rather than a narrow response modal.
- `0196_observer_session_turn_runtime_hierarchy.md`: investigate a first-class Session -> Turn -> Run/Subrun -> Artifact/Log hierarchy for Runtime Activity.

## Reading order
Read `0195` before changing wait/resume UX. Read `0196` before changing Runtime Activity navigation, run grouping, or session summaries.

## Governing ADRs
None identified after review. These proposals may require an ADR if they establish durable ownership for cross-app chat replay, session indexing, or Observer resume authority.

## Scope
Observer UX, Gateway session/history contracts, Runtime run/session/turn metadata, and cross-app replay expectations.

## Non-goals
This proposed track does not authorize new wait-chat implementation, session tree implementation, or new Gateway persistence APIs by itself.

## Notes for future agents
Treat these as investigation items. The user explicitly asked to park the wait/replay issue and to make proposals for session hierarchy, not to implement those features in the current pass.
