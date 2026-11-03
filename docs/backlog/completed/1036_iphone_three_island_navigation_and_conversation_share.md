# 1036 — iPhone three-island navigation and conversation sharing

> Package: abstractassistant
> Type: task
> Created: 2026-10-18
> Status: Completed
> Completed: 2026-10-18
> Priority: P1
> Labels: iphone, navigation, sharing, ux

## Summary

Group navigation into Conversations at left, conversation Share/Files/Tools in the middle,
and Settings in a separate bubble at right. Replace the ambiguous per-answer Share action
with explicitly scoped conversation-text sharing, preserving responder selection and New.

## Why

Operator IMG_1356 asks what message Share does and requests three distinct navbar islands:
“(conversations list) (conversation share and config) (settings)”. Current ShareLink exports
only one answer, while the direct New button crowds Files/Settings and Tools sits beside
responder selection.

## Current code reality

ChatScreen owns toolbar actions and per-answer ShareLink(message.text). ConversationsSheet
already exposes New conversation, currently resetting the responder to Assistant. Existing
attachment/import and run guards must remain. Conversation messages contain role, text and
public artifacts; runtime/session/credential data must not be exported accidentally.

## Scope

### In scope

- Three visible toolbar islands; responder selection remains easy to find below the toolbar.
- Conversation-text share with role labels and public attachment names, clear text-only scope.
- New inside Conversations, preserving selected responder; existing guards and Copy/speech.
- Native layout/interaction checks, focused transcript tests, one existing adversary,
  guarded normal iPhone installation and documentation/evidence.

### Out of scope

- Sharing credentials, raw runtime records, pending drafts, fetching hidden context or packaging
  attachment bytes; Watch changes, backend endpoints or release publication.

## Acceptance criteria

- [x] Three islands remain distinct on the native phone, including long responder names.
- [x] Share exports current conversation text in order, not just one answer; scope is explicit.
- [x] Files, Tools, Settings, responder selection and New remain reachable with existing guards.
- [x] Native screenshots inspected, adversary review, tests and normal installation recorded.

## Receipts

- Intake before implementation; baseline installed 0.6.16 (24), completed 1035.
- UX review skill and existing tools_astra adversary; ignore Agora per operator instruction.
- ADR impact: None intended; local navigation and existing visible-message export.


## Implementation receipts

- Three toolbar islands implemented and inspected natively; long responder chooser below
  truncates without overlapping actions. New moved into Conversations and preserves responder.
- Share exports an immutable snapshot of loaded user/assistant text with attachment names;
  text-only/loaded scope is explicit. Empty/open/restoring guards and context dismissal added.
- 230 package tests passed (154 AssistantKit + 76 client); two new transcript cases. Initial
  existing media URLProtocol test race retained in evidence; unchanged suite rerun passed.
- Native long-name/New test passed. Navigation/share test reached native share sheet; test
  selectors corrected to tools.close and the system Copy collection Cell. Final three-case
  native run and copied-transcript assertion remain pending while Watch Xcode testing runs.
- Source and native navbar review by tools_astra: no material blocker. Final share/copy and
  normal 0.6.17 (25) installation remain required before closure.
- [Evidence](../evidence/1036/README.md). Strict queue waits for other Xcode processes; named
  iPhone simulator shut down while waiting, with no Watch process/product changes.


## Completion report

Completed 2026-10-18. ChatScreen has three separate glass islands: Conversations at left,
Share/Files/Tools in the middle and Settings at right. Responder selection stays directly
below, with long-name truncation and full accessible value. New lives inside Conversations
and preserves selected responder. Existing import/attachment/run safeguards remain.

Removed ambiguous per-answer Share; Copy/speech and individual file/media sharing remain.
Conversation Share captures the loaded user/assistant transcript at tap, with role labels,
public filenames and explicit loaded-text/attachment-exclusion scope. Notices, drafts,
statistics, run/artifact IDs and runtime records are not export inputs. Sharing is disabled
for empty/loading history and dismissed when context changes. No backend/API changes.

Validation: **230 package tests** passed, including two focused transcript tests. Three native
UI tests passed (zero failures/skips/runtime warnings), exercising navigation, native Share/
Copy, empty state, long names and preserved responder. Initial native selector failures were
corrected and retained as iteration evidence; an existing media URLProtocol race passed in
the unchanged package rerun. Source and screenshots inspected by one adversary: Approved.
Transcript contents are unit-verified; no independent post-test clipboard inspection is
claimed because the simulator was already shut down. Normal signed **0.6.17 (25)** installed
and launched successfully, without test PlugIns.

Native work yielded repeatedly to Watch. The phone simulator was stopped during strict
waiting; verification resumed only after Watch compilation stopped and its test process
remained idle with normal memory pressure, under the existing dynamic guard. No Watch
source/products or process were changed. README/architecture/validation/llms updated;
changes remain uncommitted. [Evidence and screenshots](../evidence/1036/README.md).

### Insight and follow-up triage

ADR impact: None. This is local navigation and explicit export of already loaded public
conversation values. Complete server-history export and packaging attachment bytes remain
outside scope, clearly stated in the share content and docs. Existing media-test shared-stub
cancellation timing is preserved as validation context; no production transport change was
needed. No urgent follow-up or priority change arose.
