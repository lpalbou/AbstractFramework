# Backlog: Inline Follow Up Resume Modal

## Summary
- Replace the current follow-up flow with an inline modal that captures a follow-up message (and optional attachments) without leaving the run results page.
- Resume execution by starting a new run in the same session and threading it into the existing execution timeline as a follow-up step.

## Why
- The current follow-up path loses context and forces users back to the input form.
- The requested UX requires inline follow-up, session continuity, and visible steps in the execution timeline.

## Strategy (options + choice)
- Option A: Reopen the preflight form and reuse session/context (current design).
  - Reject: breaks UX requirement, loses flow continuity.
- Option B: Inline follow-up modal that starts a new run but renders it as a continuation thread.
  - Accept: matches UX (stay on results page), keeps context via session and messages, shows follow-up step.
- Option C: Reopen a completed run and append a new wait/step in runtime.
  - Reject for now: requires runtime support for post-completion continuation; larger scope.

## Scope
- In scope:
  - Inline follow-up modal (4-line textarea).
  - Optional drag & drop attachments via gateway upload.
  - Threaded execution timeline (follow-up step + subsequent events).
  - Keep workspace/settings from prior run inputs when available.
- Out of scope:
  - Runtime changes to truly resume a completed run.
  - New backend APIs for post-completion continuation.

## Dependencies
- Gateway attachments upload endpoint (`/api/gateway/attachments/upload`).
- Existing run input_data retrieval for workspace/settings.

## Expected outcomes
- Follow Up stays on the results page.
- User can input a follow-up message + optional attachment.
- A new step appears in the execution timeline with the user’s follow-up.
- Execution resumes as a new run in the same session with prior context.

## Implementation Report
- Delivered an inline follow-up modal (text + drag/drop attachments) inside the run results UI.
- Threaded follow-up runs into a single execution timeline using a display thread id.
- Preserved original input settings (workspace + inputs) while overriding prompt/context for follow-up.
- Added session-scoped attachment uploads to `context.attachments` for follow-up runs.
- Added a synthetic "Follow Up" step to the timeline before the new run starts.

## Tests
- `npm run build` (abstractflow/web/frontend)

## Notes
- Follow-up is modeled as a new run in the same session/thread (UI continuity + context), not a true post-completion runtime resume.

