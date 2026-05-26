# 050 — AbstractAssistant thin-client strategy assessment

## Summary

Assess whether it is worth spending time to make AbstractAssistant a gateway-first
thin client, and whether AbstractCore/Runtime/Gateway changes are required.

## Why

- Clarify the strategic direction for "all apps = thin clients".
- Remove confusion about required backend changes.

## Scope

### In scope

- Evaluate thin-client value from external-user and solution-architect views.
- Determine whether AbstractCore/Runtime/Gateway need changes for this shift.
- Provide a recommendation and tradeoffs.

### Out of scope

- Implementing the refactor.
- Changing gateway endpoints or runtime behavior.
- Running tests (analysis only).

## Dependencies

- AbstractAssistant docs (README, architecture).
- AbstractCode Web gateway-first docs.

## Expected Outcomes

- Clear recommendation with rationale.
- Explicit statement on backend changes required (if any).
- ADR suggestion if the decision is strategic.

## Implementation Plan (analysis)

- Review AbstractAssistant’s local-host scope.
- Review AbstractCode Web’s gateway-first contract.
- Compare goals vs tradeoffs (thin client vs local host).
- Summarize recommendation and next steps.

---

## Report

### Findings

- AbstractAssistant is a **local host** today: it runs AbstractAgent + AbstractRuntime locally and owns tool execution and voice integrations.
- AbstractCode Web is a **gateway-first thin client** and already exercises the gateway contract (runs, ledger streaming, commands, attachments, voice).
- Therefore, making AbstractAssistant a thin client does **not** require changes to AbstractCore/Runtime/Gateway for baseline functionality.

### Do we need to alter AbstractCore/Runtime/Gateway?

- **No for baseline thin-client behavior.** The gateway already exposes the endpoints used by `abstractcode/web`.
- **Only optional enhancements** if you want assistant-specific ergonomics (e.g., tray notifications or custom discovery UX). Those are not required for correctness.

### Critical assessment (external user vs solution architect)

- **External user (impression + convenience):**
  - A gateway-first AbstractAssistant is more impressive because it demonstrates durable runs, multi-device continuity, and shared workflows without local setup.
  - It makes “thin client” a repeatable product story, aligning with AbstractCode Web.
- **Solution architect (strategy + operations):**
  - Consolidates runtime governance in one place (gateway), reducing duplication and compliance risks.
  - Enables any AbstractFlow workflow to run in the tray app without shipping flow logic locally.
  - Costs: loss of offline/local-first behavior and reliance on gateway availability/latency.

### Recommendation

- **Yes, it is worth it** if the product goal is “all apps are thin clients” and the gateway is the canonical runtime surface.
- Keep **one local-first example** (CLI or a separate “local host” variant) if you still want to demonstrate AbstractCore-only usage patterns.
- Otherwise, prioritize the gateway-first path and retire/rename the local-host positioning to avoid mixed signals.

### ADR suggestion

Create an ADR for “AbstractAssistant = gateway-first thin client” that documents:

- Decision intent and scope.
- The loss of offline/local-first behavior.
- The compatibility story with AbstractCode Web and AbstractFlow workflows.

### Tests

- Not run (analysis-only).
