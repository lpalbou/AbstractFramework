## Summary
- Fix gateway voice state after stop to avoid stale “speaking/paused”.
- Keep UI click behavior aligned with actual playback state.

## Why
- After stopping TTS, the app still treated voice as active, blocking UI open.
- The stop path returned early when no playback process was tracked.

## Scope
- Always clear `_speaking/_paused` on stop, even if no process exists.
- Sync state with process termination on state queries.

## Out of Scope
- Gateway API changes.
- AbstractVoice local TTS changes.

## Dependencies
- `abstractassistant/core/gateway_voice_manager.py`

## Expected Outcomes
- Clicking after stop opens the app (no phantom pause/stop).
- `#FALLBACK` warnings only when truly unsupported.

## Plan
- Update stop logic and state sync helpers.
- Run tests.

## Report
- **Root cause**: `stop_speaking()` returned early when no playback process was tracked, leaving `_speaking/_paused` stale; tray clicks continued to treat voice as active.
- **Fix**: always clear `_speaking/_paused` on stop and sync state on `is_speaking/is_paused/get_state` by checking the player process; this prevents phantom “speaking” states after interruption.
- **Warnings**: no warnings were silenced; `#FALLBACK` remains for true unsupported cases.

## Tests
- `python -m pytest abstractassistant`
