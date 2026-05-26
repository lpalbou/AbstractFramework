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

## Report
### Decision summary
- Rebuilt the setup UI as a wizard and tightened provider inputs to remove ambiguity.

### Implementation
- `src/index.html` now uses card-based steps with Back/Next navigation and a single Base URL field.
- `src/app.js` wires step navigation and binds Base URL to the default provider; wizard panels show one card at a time.
- `src-tauri/src/main.rs` now maps HF tokens to `HF_TOKEN` and applies Base URL using the default provider when no explicit provider is given.
- Embeddings and Logging are now separate steps.

### Tests
- `cargo tauri build` (release) in `abstractinstallers/abstractframework-macos/src-tauri`.

### Results
- The setup flow is step-by-step and avoids long scrolling.
- Gemini/HF tokens are handled correctly.

### Follow-ups
- Validate the wizard UX on smaller screens and older macOS versions.
