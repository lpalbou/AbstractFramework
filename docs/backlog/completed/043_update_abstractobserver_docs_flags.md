# 043 — Update AbstractObserver Docs for Runtime UI Flags

**Status**: Completed  
**Created**: 2026-02-20  
**Completed**: 2026-02-20  
**Priority**: Medium (docs accuracy)  
**Components**: docs, abstractobserver/docs

## Summary

Update framework and observer documentation to reflect that the Backlog/Inbox
triage flags are runtime-injected UI config (not Vite build-time flags).

## Reason

We changed the feature gating from `VITE_` env vars to CLI-injected
`window.__ABSTRACT_UI_CONFIG__` flags. Docs must align with the new runtime
configuration approach and variable names.

## Scope

### In scope

- Update root `docs/configuration.md` quick reference table and AbstractObserver
  section to mention `ABSTRACTOBSERVER_ENABLE_BACKLOG` and
  `ABSTRACTOBSERVER_ENABLE_INBOX_TRIAGE`.
- Ensure observer docs reference runtime config injection semantics.

### Out of scope

- Backend enforcement of these flags.
- Additional UI behavior changes.

## Expected outcomes

- Documentation reflects current env var names and runtime injection behavior.

## Report

### Summary

Updated framework + observer docs to reflect runtime UI config flags and their
CLI-injected environment variables.

### Changes

- Updated the root `docs/configuration.md` quick reference table and
  AbstractObserver section to list `ABSTRACTOBSERVER_ENABLE_BACKLOG` and
  `ABSTRACTOBSERVER_ENABLE_INBOX_TRIAGE`, with a note on runtime injection.
- Added an AbstractObserver FAQ entry describing how to enable Backlog and
  Inbox triage, pointing to the runtime config injection path.

### Files modified

- `docs/configuration.md`
- `abstractobserver/docs/faq.md`

### Verification

- Documentation-only changes (no runtime tests required).
