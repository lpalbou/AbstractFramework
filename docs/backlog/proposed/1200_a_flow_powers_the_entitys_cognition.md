# 1200 — A Flow powers the entity's cognition; the static blueprint page goes

> Package: AbstractEntity (remove the blueprint page), AbstractFlow + AbstractRuntime (a visual workflow as the cognition of an entity), AbstractGateway (the per-entity workflow binding)
> Type: feature
> Status: proposed
> Created: 2026-11-10
> Priority: P2
> Labels: entities, flow, cognition, design

## Summary

Operator, 2026-11-10 17:45, on the Entity app's "Entity blueprint" page (a static map of the memory-cognition machine):
"the idea was to be able to control the AI cognition directly from a diagram... but in effect, that's more what
abstractflow does... so I wonder if we should remove that page here, and later enable a workflow to power the actual
cognition of an entity." Recommendation given: remove the page now (it documents, it does not control; the diagram
lives in the runtime docs), and design the Flow-powered cognition as its own track, in line with ADR-0041 (the
operator's own workflows as visual flows).

## Scope

1. Remove the blueprint page from the Entity app (0.12.x); keep the diagram in `docs/entity-runtime.md`.
2. Design: an entity's visit turn / own-time tick as a Flow (the lane's steps as nodes: recall, reason, tools, formation,
   close), authored in AbstractFlow, bound per entity by the gateway, replayed in the ledger like today; the default flow
   reproduces the current lane exactly (parity test), and a custom flow changes the cognition without code.

## Non-goals

No change to the ledger contract; no second execution engine: Flow runs on the runtime as every workflow does.

## Validation

Parity: the default cognition flow and the coded lane produce the same ledger for a scripted visit; a custom flow with
one added node shows that node's record in the live activity panel.
