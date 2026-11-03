# 1029 — iPhone sent-email receipts beside answer actions

> Package: abstractassistant
> Type: task
> Created: 2026-10-18
> Status: Completed
> Completed: 2026-10-18
> Priority: P1
> Labels: iphone, email, observability, ux

## Summary

Add an envelope icon and confirmed sent-email count to each AI answer's compact action
row. Open a clean receipt modal showing recipients, sender, subject, message, time and
send confirmation using the existing authorized run ledger.

## Why

The operator wants to inspect what an agent actually emailed without digging through
raw tool activity. Count completed confirmed sends rather than intentions or failures.

## Current code reality

- `AnswerActivityButtons` already loads isolated per-answer `RunActivity` through the
  existing root/child ledger APIs. Its generic tool rows truncate public output and omit
  call arguments; a separate typed receipt projection is required for email bodies.
- Core `comms_tools._send_result` returns success, message_id, from, to/cc/bcc, subject,
  accepted/refused recipients. Bodies and attachment paths exist in `send_email` and
  `reply_email` call arguments. Successful SMTP submission does not prove delivery.
- Existing live snapshots and restored answer replay use the same reducer. Reuse it so
  receipts survive restart and stay scoped to the originating answer/account/session.

## Scope

### In scope

- Typed send/reply receipts, conservative success matching and replay deduplication.
- Envelope/count only when a send is confirmed; readable subject/address/time/body sheet.
- Partial refusal visibility and explicit missing-body/time handling; safe HTML source
  handling without external resource loads.
- Package tests, native interaction/screenshots, a read-only existing remote-send check,
  documentation and normal guarded iPhone installation.

### Out of scope

- Sending test emails, changing recipient policy, fetching mailbox content, new Gateway
  endpoints, editing Watch code, remote upgrades or commits without a requested commit.

## Acceptance criteria

- [x] Confirmed sends/replies display an envelope count beside existing answer controls.
- [x] Sheet shows available recipients, sender, subject, body and recorded time clearly.
- [x] Pending/denied/failed sends do not count; repeated ledger rows do not duplicate sends.
- [x] Receipts remain isolated by answer and account through replay; generic activity stays lean.
- [x] Tests/screenshots/live read-only check pass and normal build is installed on iPhone.

## Validation

Targeted receipt reducer tests plus full Swift package; native receipt and no-mail UI checks,
existing compact actions/approval regression; read-only saved-session replay on physical phone.

## Receipts

- Intake recorded before implementation, 2026-10-18; baseline normal phone 0.6.10 (18).
- Related completed work: [1028](../completed/1028_iphone_compact_answer_actions_and_session_file_browser.md).
- ADR impact: None; this is a client projection of existing authorized ledger data.

## Completion report

Completed 2026-10-18. Normal iPhone **0.6.11 (19)** installed and launched. Changes
remain uncommitted; no remote package update or new endpoint was required.

### Result

`SentEmail` and `RunActivity` project confirmed sends/replies from the existing authorized
ledger. The envelope appears only when confirmed count is positive. Runtime identities
match results first; conflicting identities cannot be replaced by positional or model-ID
fallbacks. Explicit success plus message ID/accepted recipients confirms submission.
Pending/denied/failed sends do not count. Replayed rows/message IDs are deduplicated.
Earlier whitelisted mail arguments survive approval and partial completion records.

`AnswerActivityButtons` opens `SentEmailsView`: subject, sender, To/Cc/Bcc, recorded time,
plain message body, recipient refusal notices, attachment names and optional message ID.
Technical details stay collapsed. Missing bodies/time are explicit. HTML-only messages
are inert optional source, without remote-resource loading. Per-answer replay/snapshots
and account/session reset already provide receipt ownership and isolation.

Generic activity never retains the mail body/headers as a rendered tool argument; the
receipt projection whitelists fields and keeps no authorization headers. Bodies/HTML
are bounded at 50,000 characters with visible truncation; the latest 100 receipts are
retained with a cumulative count and a visible limit notice. A receipt confirms SMTP
submission, not delivery. Time uses the tool record timestamp; it is not a delivery time.

### Validation

- Final full Swift package: **195 passed** (119 AssistantKit + 76 client tests), including
  ten receipt tests: success fields, pending/failure/nonmail exclusion, replay/message-ID
  deduplication, approval/partial arguments, JSON-string result/reply/partial refusal,
  conflicting runtime identities, answer isolation, body limits, inert HTML/attachment
  basenames, and cumulative counts beyond the retained receipt limit.
- Native UI: **three cases passed** (receipt/count, no-email compact actions, child approval)
  and final visual-refinement receipt recheck **one passed**. Three final demo screenshots
  inspected: envelope row, sent-message card and reply card.
- Physical iPhone read-only replay: **one passed**, actual saved conversation has one
  confirmed send, one complete receipt (sender/recipients/subject/body/time), zero issues.
  No email was sent for testing and no private email fields were exported.
- Normal signed app metadata verified **0.6.11 (19)**, no test plugins, installation and
  launch succeeded. One-job guard preserved Watch priority. A stale phone-only package
  framework cache caused the initial device compile to fail; removed only phone device
  build products and rebuilt successfully. Final validation follows that correction.
- `git diff --check`, Assistant documentation aggregate freshness and root aggregate
  freshness passed. Updated phone README/architecture and Assistant `llms-full.txt`.

Evidence and exact commands: [1029 evidence](../evidence/1029/README.md).

### Post-completion review and follow-up triage

ADR impact: **None**. Client receipt projection reuses authorized ledger contracts and
existing ownership boundaries. Submission/delivery distinction and old histories with
missing fields are documented limits, not additional planned work. The general replay
convergence item [0993](../planned/0993_one_ledger_replay_many_views.md) remains applicable;
remote multimodal deployment stays in [1027](../planned/1027_restore_media_endpoint_resolution_and_verify_remote_iphone_images.md).
No additional backlog item or priority change needed. Watch files, remote packages and
recipient policy were untouched.
