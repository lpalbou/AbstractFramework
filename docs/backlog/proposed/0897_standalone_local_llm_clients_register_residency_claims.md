# 0897 — Standalone LocalAbstractCoreLLMClient instances do not register residency claims

> Package: abstractruntime (integrations/abstractcore/llm_client.py); abstractcore (providers/process_residency.py)
> Type: bug
> Created: 2026-09-26
> Priority: normal
> Labels: memory, residency, multi-client

## Summary

After REVIEW/08 S2, a default-model switch ejects only models that no client claims
(`eject_unclaimed`), and every `MultiLocalAbstractCoreLLMClient` registers its pools, overrides,
locks and default as claims. A plain `LocalAbstractCoreLLMClient` built on its own does not register,
so another client's switch (or a server unload) can eject the model it is using; its next call then
reloads the weights, and an in-flight call is protected only by the provider's own busy refusal.

## Why

M2 report, Review 08 fixes: "Open: standalone Local clients do not register claims (backlog)".

## Current code reality (2026-09-26; abstractruntime `bdebd0c` + staged edits; abstractcore `3c6e5ea`)

- `abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py`: `class
  LocalAbstractCoreLLMClient` l.7364 has no `register_claimant` call; `class
  MultiLocalAbstractCoreLLMClient` l.9745 calls `_pr.register_claimant(self)` at l.9794.
- `abstractcore/abstractcore/providers/process_residency.py`: `register_claimant` l.142,
  `claims_for` l.173, `eject_unclaimed` l.198.

## Scope

### In scope

- Register standalone Local clients as claimants (weakly referenced, released on close/GC), with the
  same claim shape as MultiLocal; audit other in-process holders (summarizer, embeddings clients,
  entity runtimes) for the same gap.
- Two-client test: a standalone Local client's model survives a MultiLocal default switch.

### Out of scope

- Remote clients (no in-process weights).

## Dependencies

- None; 0895 (idle unload) depends on this.

## Expected outcomes

- No process-wide eject removes a model any in-process client still claims.

## Acceptance criteria

- [ ] Test above green; deliberate break (skip registration) red.
- [ ] `list_model_residency()` diagnostics show the standalone client as a claimant.

## Validation

- `python -P -m pytest abstractruntime/tests -k "residency or claim or switch"` (scratch HOME).

## Evidence

- `untracked/missions-2026-09-25/M2/REPORT.md` (Review 08 fixes, Open)
- `untracked/missions-2026-09-25/REVIEW/08-memory.md` (S2)

## ADR status

- ADR impact: None.

## Receipts

- None yet.
