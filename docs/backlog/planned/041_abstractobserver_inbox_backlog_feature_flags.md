# 041 — AbstractObserver: Backlog + Inbox Feature Flags

**Status**: Completed  
**Created**: 2026-02-20  
**Completed**: 2026-02-20  
**Priority**: Medium (UX focus + role clarity)  
**Components**: abstractobserver/src/ui

## Summary

Disable Backlog by default and expose it via an env flag. Default Inbox to a
simple mailbox view (email only), with triage/reporting gated behind an env
flag.

## Reason

Backlog and triage workflows are power-user capabilities. The default UI should
be focused on the mailbox experience and avoid presenting actions that are not
expected in a lightweight inbox workflow.

## Scope

### In scope

- Add Vite env flags to opt into Backlog and Inbox triage/reporting.
- Hide Backlog tab/page and backlog-only settings when disabled.
- Default Inbox to email-only view; hide triage tabs and file bug/feature
  actions when disabled.
- Add env flag parsing with explicit `#FALLBACK` warnings on invalid values.
- Update agent notes for the new flags.

### Out of scope

- Backend permission enforcement or API changes.
- Changes to email send/receive behavior.
- UI redesign beyond gating existing functionality.

## Dependencies

- Deployment config must set the new `VITE_` env flags to enable features.
- Gateway endpoints for triage/report filing must remain available when enabled.

## Expected outcomes

- Backlog is not visible unless explicitly enabled.
- Inbox defaults to a simple mailbox experience.
- Triage/reporting UI appears only when the env flag is enabled.

## Report

### Summary

Implemented opt-in UI feature flags so Backlog and Inbox triage/reporting are
hidden by default. Inbox now defaults to email-only unless explicitly enabled
via env flags.

### Implementation details

- Added a Vite env-flag reader with explicit `#FALLBACK` warnings for invalid
  values, and wired new flags into the top-level UI.
- Hid the Backlog nav tab and page rendering unless enabled.
- Gated backlog-specific settings (advisor agent) behind the Backlog flag.
- Added Inbox triage gating: email-only tabs and actions when disabled, and a
  safe fallback to the email tab if triage is off.
- Documented the new env flags in the shared configuration docs and agent notes.

### Env flags

- `VITE_ABSTRACTOBSERVER_ENABLE_BACKLOG` → shows Backlog tab/page.
- `VITE_ABSTRACTOBSERVER_ENABLE_INBOX_TRIAGE` → enables triage/reporting UI.

### Files modified

- `abstractobserver/src/ui/app.tsx`
- `abstractobserver/src/ui/report_inbox.tsx`
- `docs/configuration.md`
- `AGENTS.md`

### Verification

- `npx tsc --noEmit`
- `npx vite build`
- `npx vitest run`
