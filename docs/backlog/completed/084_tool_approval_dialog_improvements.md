## Summary
- Show tool name + key parameters in the approval prompt.
- Replace raw JSON details with structured, readable formatting.
- Prevent tool approval dialogs from opening the main chat window.

## Why
- Users should see which tool is requested at a glance.
- Raw JSON is too noisy for approval decisions.
- Approval dialogs should not force the main UI open.

## Scope
- Improve tool approval message content and formatting.
- Provide structured details on demand.
- Keep approval dialogs independent from chat bubble visibility.

## Out of Scope
- Reworking other modal dialogs (ask-user, error).
- Changing gateway tool execution mode defaults.

## Dependencies
- Qt tool approval dialog in `abstractassistant/ui/qt_bubble.py`.

## Expected Outcomes
- Approval prompt shows tool name + key parameters.
- Details view is readable and structured.
- Main window stays closed during approvals.

## Plan
- Build a structured tool summary and detail formatter.
- Update tool approval dialog message and details.
- Remove chat bubble activation from approval prompts.

## Report
- **Prompt hinting**: approval messages now show tool names plus key parameters (path/query/command) at a glance.
- **Readable details**: details view is structured (tool header + argument list) instead of raw JSON.
- **No UI pop**: tool approval dialogs no longer open/raise the main chat window.

## Tests
- `python -m pytest abstractassistant`
