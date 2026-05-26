# 042 — AbstractObserver: Header + Observe Toolbar Cleanup

**Status**: Completed  
**Created**: 2026-02-20  
**Completed**: 2026-02-20  
**Priority**: Medium (UX clarity)  
**Components**: abstractobserver/src/ui

## Summary

Remove the redundant Launch button from the Observe toolbar, move the gateway
connection LED to the far right, and drop the uninformative run/cursor pills.

## Reason

The Observe header is visually busy and includes controls and status labels that
do not provide actionable value. The connection state should read as a right-
aligned status indicator.

## Scope

### In scope

- Remove Observe toolbar "Launch…" button.
- Move gateway connection LED to the far right of the header.
- Remove run/cursor status pills from the header.

### Out of scope

- Additional header layout redesigns.
- Changes to Launch page access (nav tab remains).
- Backend or API changes.

## Dependencies

- None.

## Expected outcomes

- Observe toolbar ends with run controls only.
- Connection LED is aligned to the right edge of the header.
- Header is simpler without run/cursor pills.

## Report

### Summary

Removed the Observe toolbar Launch button, moved the gateway LED to the far
right of the header, and dropped the run/cursor status pills.

### Implementation details

- Header: removed run/cursor pills, moved the gateway LED to the right side.
- Observe toolbar: removed the “Launch…” button (Launch remains in nav).
- Cleaned unused cursor state now that the pills are gone.

### Files modified

- `abstractobserver/src/ui/app.tsx`

### Verification

- `npx tsc --noEmit`
- `npx vite build`
- `npx vitest run`
