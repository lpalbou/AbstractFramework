## Summary
- Ensure tool approval dialogs are visible even when the bubble is hidden.
- Prevent hidden-parent dialogs from blocking runs without user feedback.

## Why
- Tool approvals can stall runs if the dialog is suppressed behind a hidden parent.
- Users must see approval prompts without opening the main window.

## Scope
- Make tool approval dialogs top-level when the bubble is hidden.
- Force the dialog to the front without showing the chat bubble.

## Out of Scope
- Changing tool policy defaults or gateway backend behavior.
- UI layout redesign.

## Dependencies
- Qt dialog handling in `qt_bubble.py`.

## Expected Outcomes
- Approval prompts appear reliably while runs are active.
- Runs waiting on approval can complete without silent stalls.

## Plan
- Update tool approval dialog creation to avoid hidden parents.
- Ensure the dialog is raised and stays on top.
- Run tests.

## Report
- **Top-level dialog**: tool approval message boxes now use an active window when possible, otherwise no parent, avoiding hidden-parent suppression.
- **Visibility controls**: dialog is marked stay-on-top + application-modal and explicitly raised/activated before exec.
- **No bubble pop**: approval prompts remain independent of the main chat bubble.

## Tests
- `python -m pytest abstractassistant`
