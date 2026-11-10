# 1196 — The live activity panel shows what the entity is doing, in real time, actionably

> Package: AbstractEntity (activity panel), AbstractGateway (ledger stream fields), AbstractUIC (shared activity row)
> Type: feature
> Status: planned
> Created: 2026-11-10
> Priority: P2
> Labels: entities, observability, ledger, next-wave

## Summary

Operator, 2026-11-10 10:30, on the Entity app's activity strip ("turns 1 · recall ··· · recall~tk ···"): "ideally, make
that more actionable. this should be realtime feedback on what the entity is doing, the memory passively retrieved, the
tools it uses with the key parameters, the memory actively retrieved, the number of iterations etc."

## Scope

Replay of the run ledger (the ledger is the authority; every app shows the same): per turn, live: the current step
(thinking / tool / answer), passive recall (how many memories came to mind, which topics), active recall (search_memory
/ topics / read_memory calls with their key parameters), tools used with their key parameters, iteration n of max, time
per step; each row opens the ledger event. Same component in Code web for agent runs (tool rows exist there already).

## Related

abstractentity backlog 0010 points here.

## Validation

A visit with two tool calls and a topics lookup shows all rows live and identical after a reload; 400 px layout.
