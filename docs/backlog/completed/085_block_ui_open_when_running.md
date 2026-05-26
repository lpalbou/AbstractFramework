## Summary
- Prevent opening the chat bubble while a run is active.
- Surface running status via tray tooltip/notification.
- Track a lightweight “what’s running” summary for the tray UI.

## Why
- Running state should block the main window entirely.
- Users still need visibility into whether and what is running.

## Scope
- Block `show_chat_bubble` when a run is active.
- Add run activity summaries and expose them via tray tooltip.
- Show a tray notification when the user clicks while running.

## Out of Scope
- Changing gateway reattach behavior or run lifecycle semantics.
- Altering tool execution or approval logic.

## Dependencies
- Qt bubble run state machine.
- System tray tooltip/notification support.

## Expected Outcomes
- Tray clicks do not open the main window while running.
- Users can see a concise running summary from the tray.

## Plan
- Add run activity tracking in the bubble.
- Block open in the app and show notifications.
- Update tray tooltip with running summary.

## Report
- **Run blocking**: tray click and “Show Chat” now refuse to open the bubble while a run is active.
- **Activity summaries**: bubble tracks lightweight run activity (reattach, tool approval, tool execution, ask-user).
- **Tray visibility**: tooltip and notification surface the running summary without opening the UI.

## Tests
- `python -m pytest abstractassistant`
