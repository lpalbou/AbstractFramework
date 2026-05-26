# Backlog: Gateway‑first assistant docs + ADR

## Summary
Document the gateway‑first assistant architecture and update core docs to reflect the migration.

## Why
- Users need clear guidance on gateway configuration, workflow selection, and behavior.
- A formal ADR makes the gateway‑first decision durable and discoverable.

## Scope
### In scope
- Create an ADR covering the gateway‑first assistant decision and constraints.
- Update the documentation core set:
  - `README.md`
  - `docs/README.md`
  - `docs/getting-started.md`
  - `docs/architecture.md`
  - `docs/api.md`
  - `docs/faq.md`
- Add troubleshooting for gateway offline status and workflow selection.

### Out of scope
- Marketing content or release notes.

## Dependencies
- Finalized gateway mode behavior and configuration defaults.

## Expected outcomes
- Clear user‑facing docs for gateway‑first operation.
- ADR provides long‑term decision context.

## Full report
### What changed
- Added ADR `docs/adr/2026-02-21_gateway-first-assistant.md`.
- Updated core docs to reflect gateway‑first assistant, workflow picker, and offline reconnect.

### Files touched
- `README.md`
- `docs/README.md`
- `docs/getting-started.md`
- `docs/architecture.md`
- `docs/api.md`
- `docs/faq.md`
- `docs/adr/2026-02-21_gateway-first-assistant.md`

### Tests
- `python -m pytest abstractassistant/tests`
- Gateway E2E run (gpt-5-mini) `05182488-e11b-4dee-91e5-add41c98e910`
