# Backlog Item: 110_macos_installer_setup_wizard_steps

## Task
Refine the macOS installer setup wizard: single base URL, Gemini/HF handling, and step-by-step cards.

## Summary
The setup panel was too long, mixed unrelated fields, and exposed two base‑URL inputs. Convert it into a step‑by‑step wizard, remove the duplicate base‑URL selector, and ensure Gemini + HF tokens are applied correctly.

## Reason
Users need a clean, guided configuration flow without overwhelming scroll or confusing inputs.

## Scope
### In scope
- Step‑by‑step setup cards with Back/Next navigation.
- Single Base URL input bound to the default provider.
- Proper handling of Gemini (Google) API keys and HF tokens.
- Separate Embeddings and Logging steps.

### Out of scope
- Changing AbstractCore config schema or CLI contracts.
- Adding new provider types beyond the current list.

## Dependencies
- AbstractCore CLI for `--set-*` operations.
- Env var persistence for HF token and base URLs.

## Expected Outcomes
- Setup wizard is card-based with Back/Next.
- Only one Base URL field is visible.
- Gemini + HF tokens are correctly applied.

## Status
Completed. Full report is in `docs/backlog/completed/110_macos_installer_setup_wizard_steps.md`.
