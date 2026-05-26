# 049 — AbstractAssistant React/TS tray rewrite assessment

## Summary

Assess whether a complete React/TS system-tray rewrite of AbstractAssistant would
be simpler than porting gateway-first logic into the current Qt/Python host.

## Why

- Clarify if a full rewrite reduces overall effort or only shifts complexity.
- Provide a decision frame for gateway-first strategy.

## Scope

### In scope

- Compare Qt/Python host vs React/TS tray approaches.
- Identify reuse opportunities from `abstractcode/web`.
- Highlight platform/packaging/voice implications.

### Out of scope

- Implementing the rewrite.
- Updating build pipelines.
- Benchmarking performance.

## Dependencies

- AbstractAssistant architecture docs.
- AbstractCode Web gateway-first contract/docs.

## Expected Outcomes

- Answer: when a React/TS tray rewrite is simpler vs not.
- Concrete recommendation with tradeoffs and risks.

## Implementation Plan (analysis)

- Review AbstractAssistant architecture and UX scope.
- Review AbstractCode Web gateway-first surface.
- Compare with a React/TS tray host (Electron/Tauri/WebView).
- Summarize recommendation and ADR suggestion.

---

## Report

### Work completed

- Reviewed AbstractAssistant architecture/README for local-host scope.
- Reviewed AbstractCode Web gateway-first contract.
- Mapped reuse vs rewrite areas for a React/TS tray rewrite.

### Findings

- AbstractAssistant is a **local host** with tray UI, durable local runtime, and optional voice; it is not a thin client.
- AbstractCode Web is explicitly **gateway-first** and already implements ledger replay, SSE streaming, and durable commands.
- A React/TS tray rewrite is simpler **only** if the product becomes a thin client and can reuse the web UI/logic.
- A rewrite does **not** eliminate complexity around tray integration, packaging, audio capture, and OS features; it shifts that complexity into Electron/Tauri or native bridges.

### Recommendation

- Prefer **embedding or porting the web gateway client** if you want a fast gateway-first transition without a platform rewrite.
- Choose a **React/TS tray rewrite** only if you intentionally want a unified UI stack and are willing to rebuild system tray, voice, and packaging in a new runtime.

### Tests

- Not run (analysis-only).
