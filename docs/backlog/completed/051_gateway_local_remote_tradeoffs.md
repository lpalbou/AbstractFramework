# 051 — Gateway local vs remote tradeoffs for AbstractAssistant

## Summary

Assess the local‑gateway vs remote‑gateway implications for a thin‑client
AbstractAssistant, and recommend repo placement and direction.

## Why

- Resolve confusion about “offline/local‑first” with a local gateway.
- Decide where the gateway‑first assistant should live.

## Scope

### In scope

- Clarify local gateway behavior vs remote gateway behavior.
- Weigh pros/cons for an all‑thin‑clients strategy.
- Recommend repo placement (same repo vs new repo).

### Out of scope

- Implementing the refactor.
- Changing gateway/core/runtime behavior.
- Running tests.

## Dependencies

- `docs/scenarios/gateway-first-local-dev.md`
- `docs/scenarios/phone-thin-client.md`
- AbstractAssistant/AbstractCode docs

## Expected Outcomes

- Clear answer on local‑gateway “offline” behavior.
- Confirmation on cross‑device continuity with remote gateway.
- Final recommendation with justification.

## Implementation Plan (analysis)

- Review gateway‑first local dev and phone thin‑client scenarios.
- Reconcile thin‑client model with local gateway deployment.
- Provide final recommendation and repo placement.

---

## Report

### Local gateway ≠ loss of “local‑first”

- Running the gateway locally **keeps execution local**. The thin client still works; it just talks to a local HTTP/SSE control plane.
- The “offline/local‑first” tradeoff only applies if the gateway is remote and providers are remote.
- Local gateway is explicitly supported and recommended for thin‑client development.

### Remote gateway = cross‑device continuity

- A remote gateway allows multiple clients to attach to the same durable runs and session memory.
- This enables a consistent assistant across computers/phones, as long as the same `session_id` is used.

### Recommendation

- If the strategic goal is “all apps are thin clients,” move AbstractAssistant to **gateway‑first** in the same repo.
- Keep a **minimal local‑only example** (e.g., `abstractcore.utils.cli`) to demonstrate AbstractCore‑only usage.
- Do **not** modify AbstractCore/Runtime/Gateway for baseline functionality; the web client already proves the contract.

### Repo placement

- **Same repo (preferred)** if AbstractAssistant remains the flagship tray app.
- If you need a long‑lived local‑host product, split that into a **separate legacy repo** to avoid mixed semantics.

### Tests

- Not run (analysis‑only).
