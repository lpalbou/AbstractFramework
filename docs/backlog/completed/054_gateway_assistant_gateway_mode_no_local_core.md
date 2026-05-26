# 054 — Gateway-first Assistant (no local AbstractCore on startup)

## Summary

Ensure AbstractAssistant gateway mode does not import or call local AbstractCore providers,
preventing local model discovery and provider network calls.

## Why

- Gateway-first UX should not hit local providers (OpenAI/LMStudio).
- Avoid noisy debug logs from provider registry/model listing on startup.
- Keep gateway mode lightweight and deterministic.

## Scope

### In scope

- Lazy import of AgentHost/ProviderManager in gateway mode.
- Gateway-mode session storage without AgentHost/runtime init.
- Gateway URL auto-enables gateway mode with explicit `#FALLBACK`.
- Update tests/fixtures to cover gateway mode.

### Out of scope

- UI rewrite or gateway API changes.
- AbstractCore logging defaults.

## Dependencies

- Gateway discovery endpoints already available.
- Existing session store format.

## Expected Outcomes

- No local provider/model discovery in gateway mode.
- Gateway mode uses SessionStore without initializing runtime.
- Tests updated and passing.

## Implementation Plan

- Refactor LLMManager to use SessionStore directly in gateway mode.
- Lazy-import AgentHost/ProviderManager to avoid AbstractCore side effects.
- Add config coercion + `#FALLBACK` warning for gateway URL.
- Update tests/fixtures for gateway mode coverage.

---

## Report

### Work completed

- Refactored gateway mode to use SessionStore directly and avoid AgentHost/runtime init.
- Lazy-imported AgentHost/ProviderManager to prevent local provider discovery side effects.
- Added gateway URL coercion with `#FALLBACK` warning to enable gateway mode automatically.
- Updated tests and fixtures to use gateway mode smoke checks.
- Reinstalled `abstractassistant` in editable mode so the `assistant` entrypoint uses repo code.

### Tests

- `python -m pytest abstractassistant/tests` (60 passed, 7 skipped; warnings remain for legacy tests and optional AbstractVoice)
