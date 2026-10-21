# 1037 — iPhone rich conversation sharing with original files

> Package: abstractassistant
> Type: task
> Created: 2026-10-18
> Status: Completed
> Completed: 2026-10-18
> Priority: P1
> Labels: iphone, sharing, files, rich-text, ux

## Summary

Accent New conversation for recognition. Share formatted conversation content together with
original attached media and files produced by the linked answers; preserve inline placement
where native destinations support rich content.

## Why

Operator screenshot 21:35 shows the New action blending into history. Operator requests actual
file attachments in discussion sharing and formatted Mail/Notes content instead of raw Markdown.
Completed1036 deliberately exported loaded text only; this item extends that scope.

## Current code reality

ConversationShareSnapshot/Sheet wrap a String in UIActivityViewController. ConversationTranscript
retains Markdown source and filenames, not bytes. Public messages carry artifact owners; existing
GatewayClient downloads artifacts and workspace content. AnswerActivity.access records successful
file writes/edits with owning child run. PhoneTemporaryStorage supports owned UUID directories and
startup cleanup; export needs its own lifetime. Apple supports rich messageBody metadata and
NSAttributedString item providers, while receiving apps control final inline rendering.

## Scope

### In scope

- Colored New action with existing navigation/run guards.
- Immutable loaded-message snapshot; real artifact and positively identified written-file downloads.
- Ordered rich text with inline image copies, formatted lists/headings/code/links and original files.
- Rich/plain alternatives on one transcript item and attributed message-body metadata.
- Dedicated owned export storage, cancellation/context invalidation, explicit download/limit errors,
  deduplication, filename collisions and cleanup after activity completion/cancellation.
- Focused package/native/provider tests, inspected UI/screenshots, one existing adversary,
  normal guarded iPhone installation and documentation/evidence.

### Out of scope

- Exporting arbitrary unrelated host-workspace content, private runtime details or credentials;
  changing Gateway APIs, sending test email/saving personal Notes, Watch changes or publication.

## Acceptance criteria

- [x] New conversation is visually distinct and reachable.
- [x] Original attached files and produced documents accompany formatted loaded conversation.
- [x] Image/message positions and write provenance are preserved without fabricated ordering.
- [x] Mail/Notes receive rich alternatives and message-body metadata; raw Markdown is not the default.
- [x] Failures/cancellation/context changes cannot expose partial or cross-account exports; temporary
      copies survive receiver reads and are cleaned after sharing.
- [x] Tests, native evidence, adversarial review and normal phone installation are recorded.

## Receipts

- Intake before implementation, baseline installed0.6.17(25), completed1036.
- Existing tools_astra adversarial source/platform-contract review requested; ignore Agora.
- Apple primary reference: developer.apple.com/documentation/uikit/uiactivityitemsconfigurationmetadatakey/messagebody
- ADR impact: None intended; local export using existing public run/file contracts.


## Completion report

Completed 2026-10-18; moved from
`planned/1037_iphone_rich_conversation_sharing_with_original_files.md` to the same filename
in `completed/`. Original intent preserved above; all work remains local/uncommitted.

ChatScreen accents New in mint. ConversationExport downloads original artifacts and positively
recorded write/edit files through existing public routes. RichConversation renders ordered
attributed/HTML/RTFD text with image previews and separate original-file providers, including
messageBody metadata. ConversationShareSheet owns cancellation/context guards and cleanup via
PhoneTemporaryStorage.exports. Project version is **0.6.18 (26)**.

**235 package + five native + one physical saved-session export test passed.**
Native screenshots directly inspected by parent and existing tools_astra adversary; independent
review approved source/provider/rendered-artifact scope. Physical export included 18 messages,
one image and one document, then verified cleanup. Initial fixture URL assertion, Plain Text
preview title and optional-prompt device compilation issues were corrected; evidence retained.
Native final has no runtime warnings; device startup reports an existing AVAudioSession
main-thread warning. Normal signed build installed/launched with no test PlugIns. Watch priority
preserved; no server mutation/publication. Phone README, architecture, validation and LLM
aggregate updated. [Evidence/reproduction](../evidence/1037/README.md).

Residual limits: actual configured Mail/Notes destination rendering is unverified; rich content
and original-file providers are offered, receiver chooses final layout. Export covers loaded
messages, explicit media and recorded writes/edits, not unobservable shell side effects.
Workspace files use current saved versions. Limits: 100 originals/200 MB and 12 inline image
previews. Missing files/incomplete activity fail explicitly. No test email/personal note sent.
Follow-up triage: receiver verification remains a documented validation note; no new speculative
item needed. ADR impact None: existing public reads and local native share lifetime, no new
cross-package policy. No priority impact. No backlog/code drift remains in this item.
