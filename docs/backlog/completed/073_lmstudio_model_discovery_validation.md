# Backlog Item: LMStudio discovery should not validate missing model

## Summary
- Prevent LMStudio model discovery from failing when the configured default model is not present.
- Ensure provider discovery returns available models without requiring a live model match.

## Reason
- Provider discovery should be resilient and reflect what the backend exposes, not fail on a missing default model.
- LMStudio environments often vary by installed models; discovery must remain robust.

## Scope
### In scope
- Adjust provider discovery to avoid OpenAI-compatible model validation during model listing.
- Validate with targeted provider registry tests.

### Out of scope
- Changing runtime behavior for generation when an invalid model is selected.
- Altering LMStudio server configuration or model management.

## Dependencies
- AbstractCore provider registry and OpenAI-compatible provider base.

## Expected Outcomes
- `/api/gateway/discovery/providers/lmstudio/models` returns available models even if the default model is absent.
- No ModelNotFoundError during provider discovery for LMStudio.

## Report
### Work completed
- Updated provider discovery to instantiate OpenAI-compatible providers with `model="default"` during model listing to avoid validation on missing defaults.
- Kept discovery behavior consistent for non-OpenAI-compatible providers.

### Tests
- `pytest abstractcore/tests/providers/test_registry_core.py -q`
