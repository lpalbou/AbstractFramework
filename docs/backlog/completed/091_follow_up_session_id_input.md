## Task
Add explicit session id input to the run preflight and wire Follow Up to reuse it.

## Summary
Expose a Session ID field on the run start screen, use it to set the gateway
`session_id`, and ensure Follow Up reuses the same session id.

## Reason
Follow Up must continue the same execution context. The UI needs an explicit
session id field to make reuse visible and controllable.

## Scope
- Do: add Session ID input in the run form, pass it as `session_id`, and bind
  Follow Up/New Run behavior to it.
- Do not: change runtime policy or gateway behavior.

## Dependencies
- None (frontend-only changes).

## Expected Outcomes
- Session ID appears on the run start screen.
- Follow Up reuses the same session id.
- New Run clears session id and generates a fresh one.

## Full Report
- **Session field**: added a Session ID input to the run preflight screen when
  the flow does not already define a `session_id` pin.
- **Session propagation**: run submissions include `input_data.sessionId` and
  `session_id` is set on the gateway start call (explicit override wins).
- **Follow Up**: sets the Session ID field to the previous run’s session id and
  keeps the stable session id in the UI so follow-up runs use the same context.
- **New Run**: clears the Session ID field and resets the stable session id to
  start a fresh context.
