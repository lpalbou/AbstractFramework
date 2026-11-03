# 1030 — iPhone read and sent email collections

> Package: abstractassistant
> Type: task
> Created: 2026-10-18
> Status: Completed
> Completed: 2026-10-18
> Priority: P1
> Labels: iphone, email, ux, observability

## Summary

Split answer email actions into read and sent counts with directional envelope icons.
Make each modal a compact multi-message collection with individual message details,
so several long messages can be browsed without scrolling through every body.

## Why

The operator explicitly requests support for multiple messages and separate read/sent
visibility. Counts must describe confirmed actions in the originating answer.

## Current code reality

- 1029 added `RunActivity.sentEmails`, confirmed send/reply projection and a sent-only
  envelope count. Its modal stacks full message cards, which scales poorly to many bodies.
- Core `read_email` returns success, account/mailbox, UID/UIDVALIDITY, message ID,
  sender/recipients/subject/date, body_text/body_html, attachment metadata and body_skipped.
  Listing/searching mail is distinct from opening a message and must not inflate reads.
- Existing answer replay and account isolation can own both collections. No new mail
  requests or Gateway endpoints are necessary.

## Scope

### In scope

- Successful read projection, deduplication, read/message timestamps, attachment names,
  body skip visibility and restored per-answer isolation.
- Separate directional read/sent buttons, compact searchable message lists, individual
  readable details; multiple messages, recipients, long subjects/bodies and empty states.
- Package/native tests and inspected screenshots, read-only existing-history verification,
  docs and guarded normal iPhone installation.

### Out of scope

- Sending mail, fetching/marking additional mailbox messages, active HTML/external resource
  loading, changing server policy/endpoints, Watch edits, package publication or commits.

## Acceptance criteria

- [x] Read and sent counts are separate, directional and scoped to the answer.
- [x] Only confirmed actions count; retries/replay do not duplicate the same read message.
- [x] Several read/sent messages can be browsed as compact rows and opened independently.
- [x] Message metadata/body/time/attachments are readable; limited/missing bodies are explicit.
- [x] Package/native checks and screenshot inspection pass; normal app installed on iPhone.

## Validation

Successful/failed/list/search reads, JSON-string results, mailbox identity, deduplication,
body limits/skips, replay isolation; native multi-read/multi-send lists, search and detail
navigation with long fields; existing approval/compact row regressions; saved-history only.

## Receipts

- Intake before implementation, 2026-10-18. Related [1029](../completed/1029_iphone_sent_email_receipts.md).
- ADR impact: None; client projection of existing authorized tool-ledger results.

## Completion report

Completed 2026-10-18. Normal iPhone **0.6.12 (20)** installed and launched. Changes
remain uncommitted. No mailbox action, remote package deployment or publication occurred.

### Result and code

- `AnswerActivityButtons` shows separate inward/outward arrow envelope icons for read
  and sent messages. Both counts appear once either direction has confirmed activity;
  zero directions have an explicit empty view. The `ChatScreen` action strip can scroll
  horizontally when large text/counts need extra room.
- `EmailActivityView` replaces stacked full sent-message cards with compact searchable
  read/sent collections. Rows show subject, sender/recipients, preview and recorded time;
  each navigates independently to full metadata/body details. Long subjects/addresses
  wrap in detail. Search covers subjects, sender and To/Cc/Bcc. Back returns to the list;
  Done closes the modal from either level. Existing send/reply/refusal/body limits remain.
- `ReadEmail` and `RunActivity` project successful `read_email` results, excluding failed,
  pending, inbox listing and search operations. Account/mailbox/UIDVALIDITY/UID identity
  deduplicates reads and replay; message ID is used when UID is absent. Repeated reads
  can improve a headers-only receipt without increasing the count. Each answer/account
  retains existing replay/snapshot/reset ownership. HTML stays inert; body-skipped results
  explicitly say headers only. Read action time and original Date header are distinct.
- New/extended files: `ReadEmail.swift`, `RunActivity.swift`, `EmailActivityView.swift`
  (renamed from sent-only view), `AnswerActivityView.swift`, `ChatScreen.swift`, mock
  fixtures, `ReadEmailTests`, send replay test, native and opt-in live tests. Phone README,
  architecture and Assistant `llms-full.txt` updated. No Watch files changed.

### Validation and evidence

- Full Swift package: **201 passed** (125 AssistantKit, 76 Gateway client), including six
  new read tests: fields/JSON-string outputs/inert HTML, read/replay deduplication and
  mailbox/UIDVALIDITY distinction, pending/failure/list/search exclusion, headers-only
  improvement, retained limit/cumulative count, and isolated multi-read/multi-send replay.
- Native UI: **four passed**, zero failed/skipped. Fixture has three read + three sent
  messages, long subject, multiple recipients, HTML-only/headers-only reads, independent
  detail/back navigation and recipient search. Existing no-email compact actions and
  child approval UI pass. Six screenshots inspected visually, including both collections,
  directional icons, read body, long subject/recipients and searched detail.
- Physical iPhone read-only existing-history replay: **one passed**. Actual saved session
  contains one confirmed send with complete fields, **zero confirmed read_email actions**,
  no issues. This proves current history replay; successful reads are proven by fixtures
  matching the inspected Core contract, not by new mailbox reads.
- Normal signed app verified **0.6.12 (20)**, no test plugins; installed/launched successfully.
  Guarded one-job builds respected Watch priority. Only stale phone device build products
  were cleared before the live build to avoid the known package-framework cache problem.
- `git diff --check` and both Assistant/root documentation aggregate checks passed.

Durable summaries, filtered live proof, inspected screenshots and commands:
[1030 evidence](../evidence/1030/README.md).

### Post-completion insight and follow-up triage

ADR impact: **None**; existing authorized ledger/workspace boundaries remain unchanged.
A compact collection with independent details scales better than stacking full bodies;
this is implemented for both directions. Read counts represent unique opened messages
within the answer's mailbox identities, not the mailbox Seen flag, search hits or unseen
inbox totals. Headers-only actions are disclosed in list/detail. Existing 100-message
retention and 50,000-character body display caps have visible notices; older missing
metadata remains explicit. These are documented limits, with no new urgent follow-up.
General replay convergence remains [0993](../planned/0993_one_ledger_replay_many_views.md),
remote multimodal work stays [1027](../planned/1027_restore_media_endpoint_resolution_and_verify_remote_iphone_images.md).
No priority changes or new backlog item needed.
