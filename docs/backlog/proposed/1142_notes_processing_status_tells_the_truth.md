# 1142 — "Process my notes" reports what really happened

> Package: AbstractNote (automation + status), AbstractRuntime (automation outcome record)
> Type: defect
> Created: 2026-11-07 (found by the Codex root-cause investigation of 2026-11-06, never filed)
> Priority: medium
> Labels: notes, automations, observability

## Summary

The Codex investigation of the 2026-11-06 processing failure (relay reasoning level; fixed in AIRelays 0.22.1) found two
reporting defects that are still open: a "Process my notes" batch reports `completed / success` when 0 notes were
processed and 1 failed, and a note that is re-queued for retry keeps its failure counter at 0, so the failure is
invisible while the retry waits. The operator reads these statuses to decide whether to enable the next automation
("should other automations be on?"); a status that says success on failure defeats that.

## Scope

### In scope

- The batch outcome is `failed` (or `partial`) whenever at least one note failed, with the counts (processed, failed,
  re-queued) in the outcome record (ADR 0041: On Flow End = outcome record).
- A re-queued note carries its failure count and last error until it succeeds; the Notes app shows it.
- A test for each: a batch with one failure never reads as success; a re-queued note shows its failure.

### Out of scope

- The processing pipeline itself (fixed 2026-11-06), the relay, Consolidate.

## Acceptance criteria

- [ ] Reproduce the 2026-11-06 situation (one note failing) and read `failed`/`partial` with counts, not `success`.
- [ ] The re-queued note shows "1 failure, retrying" until it processes.
