# Backlog Item: 111_macos_installer_provider_cleanup

## Task
Remove unsupported providers from the setup wizard and align API key handling with what the framework actually supports.

## Summary
The setup wizard was exposing Gemini and Hugging Face tokens even though those providers are not supported. Clean up the UI and backend to only surface supported provider keys and a single Base URL field.

## Reason
Unsupported provider inputs create confusion and erode trust in the installer. The wizard must reflect actual capabilities.

## Scope
### In scope
- Remove Gemini and HF token fields from the wizard.
- Keep Hugging Face as a local provider option without token input.
- Restrict API key application to OpenAI, Anthropic, OpenRouter, and Portkey.
- Keep a single Base URL field tied to the default provider.

### Out of scope
- Adding new providers or online HF support.
- Changing AbstractCore’s internal provider registry.

## Dependencies
- Installer setup wizard UI.
- AbstractCore CLI `--set-api-key`.

## Expected Outcomes
- Wizard no longer suggests unsupported Gemini/HF online flows.
- API keys are applied only for supported providers.

## Status
Completed. Full report is in `docs/backlog/completed/111_macos_installer_provider_cleanup.md`.
