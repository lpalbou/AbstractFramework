## Summary
- Fix tool approval defaults so safe tools show Approve by default.
- Enforce per-run tool approval preferences in gateway runs.
- Align tool policy defaults across AbstractRuntime, AbstractAssistant, and AbstractUIC.

## Why
- Current UI shows all tools as Ask, contradicting desired default behavior.
- Gateway auto-approves safe tools even when UI says Ask; preferences must be enforced.
- Consistent defaults across thin clients prevent confusing policy drift.

## Scope
- Add per-run tool policy overrides to tool execution handling.
- Send tool policy from AbstractAssistant to gateway via run input.
- Ensure UI defaults fall back to safe policies when discovery is missing.

## Out of Scope
- Changing gateway tool execution mode defaults.
- Redesigning tool execution pipelines beyond approval gating.
- Modifying non-tool UI flows.

## Dependencies
- AbstractRuntime tool execution effect handlers.
- AbstractAssistant gateway run input builder.
- AbstractUIC tool policy defaults.

## Expected Outcomes
- Safe tools default to Approve; mutating file/system tools default to Ask.
- Tool approval prompts match UI selections (per-run).
- Thin client UI and backend behavior stay aligned.

## Plan
- Implement per-run tool policy override in tool execution handler.
- Send tool policy in gateway run input and build from session selections.
- Update policy defaults and fallback logic for tool discovery.

## Report
- **UI defaults**: safe tools now default to Approve via explicit fallback logic, even if gateway policy defaults are unavailable.
- **Legacy state fix**: when a session has the old “all ask” state, approvals reset to safe defaults with a `#FALLBACK` warning.
- **Per-run enforcement**: `_runtime.tool_policy` is honored in the tool effect handler, so “Ask” choices produce real approval waits.
- **Policy alignment**: AbstractRuntime + AbstractAssistant defaults now treat read/search + comms as safe; file/system mutations ask.

## Tests
- `python -m pytest abstractruntime/tests/test_tool_approval_resume_executes.py`
- `python -m pytest abstractassistant`
