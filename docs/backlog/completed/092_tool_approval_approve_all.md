## Task
Add Approve All option for tool approvals to disable prompts per session.

## Summary
Provide an Approve All button in the approval footer and auto-approve all
future tool waits for the current session.

## Reason
Users want to avoid repeated approval prompts once they have opted in for a
session.

## Scope
- Do: add Approve All button, persist auto-approve per session, and auto-resume
  approval waits without prompting.
- Do not: change gateway policy defaults or runtime tool policy defaults.

## Dependencies
- None (frontend-only changes).

## Expected Outcomes
- Footer shows Approve All | Approve | Deny in that order.
- Approve All prevents further approval prompts for the session.

## Full Report
- **Button order**: Approval footer now renders Approve All, then Approve, then Deny.
- **Session auto-approve**: Approve All records the current session id in sessionStorage
  and enables automatic approvals for subsequent tool waits in the same session.
- **Auto-resume**: When a tool approval wait appears for an auto-approved session,
  the client immediately resumes with `{ approved: true }` and skips the prompt.
