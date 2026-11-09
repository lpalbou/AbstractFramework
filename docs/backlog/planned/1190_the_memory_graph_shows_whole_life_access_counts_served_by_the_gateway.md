# 1190 — The memory graph's grey-to-green scale counts the entity's whole life, served by the gateway

> Package: AbstractGateway (a read route serving per-record and per-pair activation), AbstractRuntime (the memory facade re-exports what the gateway needs), AbstractMemory (`compute_activation` exists), AbstractEntity (the graph switches to the served values)
> Type: feature
> Status: planned — next wave (the app half shipped in this wave)
> Created: 2026-11-10
> Priority: P2
> Labels: entities, memory, graph, attention, next-wave

## Summary

The Entity app's memory graph now draws one grey-to-green usage scale (rarely used → dark grey, often used → green,
normalised) — but from the replay window the app has loaded, not from the entity's whole life. The operator's reading
of the graph needs counts over the whole life. The gateway serves the engine's own activation per record and per
pair, and the app reads it instead of folding the loaded replay.

## Why

Operator, 2026-11-09 21:25 (running log `untracked/release-2026-11-07/RESUME.md`): the gradient was "not working to my
eyes": the whole graph uniformly green; he wants dark grey (rarely visited) to green (highly visited), normalised.
Earlier (20:40, finding d): "edge gradient = temporal access count".

## Current code reality (2026-11-10)

- App half built this wave: AbstractEntity `a35e8f1` (one grey-to-green usage scale, the Context view's travelled
  paths, the Context legend) and `2c9a7ba`; the scale is computed in the app (`temporal_activation.ts`, an
  engine-parity port of abstractmemory attention) from the replay's `selected` / `co_selected` events of the loaded
  window (castor's window: 1644 `co_selected`, 87 `selected`).
- The gateway serves no graph route and no `access_count` / `last_recalled` / `activation` field
  (`untracked/finish-plan-2026-11-09/operator-test/FINDINGS.md` section 5).
- AbstractMemory already has the pure function: `abstractmemory/src/abstractmemory/attention.py:288`
  `compute_activation(events, *, config, at_seq, include_prior, selected_counts)`.
- The gateway reaches memory names through the runtime's facade
  (`abstractruntime/src/abstractruntime/integrations/abstractmemory/memory_facade.py`; a direct import breaks the
  gateway's import-boundary test, as `bffa4959` did on 2026-11-09).

## Scope

### In scope

1. Gateway (3–5 h): `GET /entities/{name}/attention` → `{records: {id: {temporal, global, last_selected_seq}},
   pairs: {...}}`, principal-scoped like the other entity reads, computed by the engine's own function over the home's
   whole event stream, paged or bounded explicitly (never a silent cut).
2. Runtime facade + memory (1–2 h): re-export what the route needs; a memory helper if the whole-life fold is too slow
   to compute per request (then cached per home, invalidated on new events).
3. App (2 h): the graph reads the served values; the loaded-window fold stays only as the offline fallback the app
   already labels.
4. Tests: the route's numbers equal `compute_activation` over the same stream; a record used once long ago reads grey,
   one used often recently reads green; removing the route turns the app test red.

### Out of scope

- The graph's other views (Context paths, legend: done in `a35e8f1`).
- Changing the attention model itself.

## Acceptance criteria

- [ ] The scale is the same whatever replay window the app has loaded.
- [ ] Route numbers match the engine function; bounded with the bound stated.
- [ ] 400 px screenshot of the graph with the scale and its legend.

## Receipts

- `untracked/finish-plan-2026-11-09/operator-test/FINDINGS.md` (5); running log `RESUME.md` 20:40, 21:00, 21:25.
