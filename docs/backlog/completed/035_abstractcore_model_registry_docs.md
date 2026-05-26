# Backlog Item 035: AbstractCore model registry docs

## Summary
Clarify in AbstractCore documentation that model capabilities and architecture
formats are sourced from the canonical JSON registries.

## Reason
Capability routing, media policies, and prompt formatting depend on these
registries. When new models or architectures ship, maintainers need a clear,
explicit source-of-truth to update so behavior stays correct.

## Scope
### In scope
- Add explicit "source of truth" guidance in AbstractCore docs.
- Point to the canonical JSON files and the assets README for field rules.

### Out of scope
- Changing registry contents or provider logic.
- Adding new models/architectures.
- Modifying tests or tooling.

## Dependencies
- `abstractcore/assets/model_capabilities.json`
- `abstractcore/assets/architecture_formats.json`
- `abstractcore/assets/README.md`

## Expected Outcomes
- AbstractCore docs explicitly name the canonical registries.
- Maintainers know where to edit when new models/architectures arrive.

## Full Report
- **Summary**: Clarified in AbstractCore docs that model capability and architecture registries are the canonical source of truth and must be updated when new models/architectures ship.
- **Docs updated**: `abstractcore/docs/architecture.md`, `abstractcore/docs/vision-capabilities.md`, `abstractcore/docs/README.md`.
- **Knowledge base**: Added an Agent Notes entry pointing to the canonical registries.
- **Tests**: `python -m pytest abstractcore/tests/token_terminology/test_max_tokens_migration.py`
