# Backlog: Enforce AbstractVoice as default dependency

## Summary
Make AbstractVoice a required default dependency for AbstractAssistant and remove documentation implying optional voice.

## Why
- Voice is a core part of the assistant experience.
- Missing AbstractVoice should be treated as a misconfiguration, not a normal state.

## Scope
### In scope
- Update docs to remove optional voice install paths.
- Add a test that fails if AbstractVoice is not importable.

### Out of scope
- Changing AbstractVoice internals.
- Redesigning voice UX.

## Dependencies
- AbstractVoice package available in the environment.

## Expected outcomes
- Default installs include AbstractVoice.
- Tests fail fast if AbstractVoice is missing.

## Full report
### What changed
- Removed “optional voice” language from docs and install instructions.
- Added a basic test that asserts AbstractVoice is importable.
- Fixed `VoiceManager.is_available()` to be a true static availability check and ensured tests resolve the local abstractvoice package in the monorepo.
- Clarified AbstractAssistant docs that AbstractVoice is installed by default.

### Files touched
- `docs/getting-started.md`
- `abstractassistant/README.md`
- `abstractassistant/llms-full.txt`
- `abstractassistant/docs/getting-started.md`
- `abstractassistant/tests/basic/test_voice_dependency.py`
- `abstractassistant/tests/conftest.py`
- `abstractassistant/core/tts_manager.py`

### Tests
- `python -m pytest abstractassistant/tests`
- Gateway E2E run (gpt-5-mini) `f7f894cf-5583-419a-a48e-a78af674790a`
