# Backlog Item: 114_macos_installer_api_key_explanation

## Task
Explain in the setup wizard what happens when API keys are entered.

## Summary
Users need to understand where API keys are stored and how they are used. Add a short explanation in the API keys step.

## Reason
Clarity and trust: users should know keys are saved locally and only used for provider authentication.

## Scope
### In scope
- Add a brief explanation in the API keys step.

### Out of scope
- Changing key storage behavior or encryption.

## Dependencies
- Setup wizard UI.

## Expected Outcomes
- Users see a clear explanation of where keys are stored and their purpose.

## Report
### Decision summary
- Added a concise note in the API keys step to explain storage location and usage.

### Implementation
- `src/index.html` adds a hint stating keys are stored in `~/.abstractcore/config/abstractcore.json` and used for authenticated provider calls.

### Tests
- `cargo tauri build` (release) in `abstractinstallers/abstractframework-macos/src-tauri`.

### Results
- API key behavior is explicitly described in the UI.
