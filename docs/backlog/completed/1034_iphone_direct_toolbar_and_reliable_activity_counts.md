# 1034 — iPhone direct toolbar and reliable activity counts

> Package: abstractassistant
> Type: bug
> Created: 2026-10-18
> Status: Completed
> Completed: 2026-10-18
> Priority: P1
> Labels: iphone, ux, activity, lifecycle

## Summary

Expose the existing Conversation files, New conversation and Settings actions directly in
the Assistant toolbar, with a settings gear farthest right. Make historical activity counts
reliable across scrolling/reload and render optional counters only for recorded positive counts.

## Why

Operator IMG_1352/1353 show persistent ellipsis counters, absent mail/file counters and a
zero-tool icon. The operator requests direct toolbar actions instead of the overflow menu.

## Current code reality

ChatScreen has three existing actions inside an ellipsis Menu. AnswerActivityButtons renders
cycle/tool counters unconditionally, including zero and unresolved ellipses. Its view-owned
task loads through AssistantStore's loading-ID set; cancellation discards results, overlapping
callers return without awaiting, and a cancelled view task does not reliably retrigger while
the replacement is visible. Failures also remain cached with an empty projection.

## Scope

### In scope

- Direct accessible toolbar icons preserving action safeguards; Settings gear farthest right.
- Store-owned, coalesced activity loads with account/session invalidation and explicit retry;
  meaningful loading/unavailable states without pretending unknown counts are zero.
- Positive-only optional counters, package/native/visual checks, one existing adversary,
  guarded normal device installation, documentation and evidence.

### Out of scope

- Watch changes, rewriting historical chat content, generating new media or new endpoints.

## Acceptance criteria

- [x] All former overflow actions are direct and Settings is rightmost.
- [x] Cancelling/scrolled-away rows cannot strand later historical activity counts.
- [x] Zero-count optional actions and ellipsis count placeholders do not render.
- [x] Failure/retry and context isolation are tested; layout inspected and app installed.

## Receipts

- Intake before implementation; baseline iPhone 0.6.14 (22).
- Related completed 1031–1033; existing adversarial reviewer tools_astra.
- ADR impact: none intended; existing toolbar actions and authorized ledgers remain canonical.


## Implementation receipts

- Replaced view-owned load/set with store-owned shared tasks. Independent activity epoch
  and per-task UUID guard publication/deferred cleanup; all three reset paths invalidate.
  Live completion invalidates old replay before publishing its fresher snapshot.
- Positive-only compact badges, one unnumbered accessible activity/retry action for absent
  or incomplete history. No unresolved ellipsis count placeholders. Tool-zero summary hidden.
- Former overflow actions are direct folder/new/gear buttons. Initial visual pass found
  crowded spacing; refined native widths. Long entity-name test then reproduced intrinsic
  title overflow; explicitly bounded the title text while preserving its full accessible value.
- 147 AssistantKit + 76 client tests passed. Five new gated lifecycle tests cover cancelled
  overlapping waiters, stale reconnect, stale authentication, explicit retry and late replay
  losing to live completion. Initial three UI scenarios and two refined UI cases passed.
- One long-name UI failure retained as iteration evidence; final rerun/physical proof pending.
- Native guard has repeatedly yielded with exit75 to concurrent Watch builds; no overrides
  or Watch source/build-output changes made.


## Completion report

Completed 2026-10-18. Files/New conversation/Settings are direct toolbar actions, with gear
farthest right and existing safeguards preserved. Bounded title Text prevents long entity
names from hiding/overlapping actions; full name remains accessible. Activity cache now
owns/coalesces tasks, publishes despite cancelled row waiters, invalidates all reset paths
and guards stale completion/cleanup. Live completed snapshots take precedence over replay.
Compact counters are positive-only; missing/failed/all-zero history retains accessible
Activity/retry without unresolved ellipsis or invented zero counts.

Validation: **223 package tests** passed; five new gated lifecycle cases. Three initial,
two refined and two final native test cases passed across their runs. One earlier long-name
failure exposed actual overflow and was fixed/retested. One physical read-only test passed:
all **nine saved answers** resolved despite row cancellation, confirmed sent email 1/changed
file 1, zero issues. One adversarial reviewer inspected source and four final screenshots,
verdict Approved. Normal signed **0.6.15 (23)** installed/launched without test plugins.
Guard repeatedly yielded to Watch; no Watch source/products were changed. Changes remain
uncommitted. README/architecture and Assistant aggregate updated.

[Evidence, screenshots, review and commands](../evidence/1034/README.md).

### Insight and follow-up triage

ADR impact: None. Store-owned projection tasks and explicit unknown states correct the
existing lifecycle/UI contract. Partial history stays labeled with + and retry access;
missing counts are never claimed to be zero. Existing bounded replay/retention and legacy
field limitations remain explicit. No new urgent follow-up, priority change or backend
release needed. Historical failed voice-plan text is preserved, not silently rewritten;
1033 already records the generation repair independently.
