# 1028 — Compact iPhone answer actions and browse session files

> Package: abstractassistant
> Type: bug
> Created: 2026-10-18
> Status: Completed
> Completed: 2026-10-18
> Priority: P1
> Labels: iphone, files, workspace, observability, ux

## Summary

Make completed answer activity and session files compact, discoverable and useful on
iPhone. Put cycle/tool/file counts after the speaker in the answer action row. Preserve
the clear live execution/approval panel. Replace the artifact-only conversation file list
with a browser that includes the session's actual workspace documents and hierarchy,
previews files, and hides conversational voice artifacts by default with an explicit toggle.

## Why

The operator's screenshots show a large completed-activity card, a separate file-count
line, a missing generated `discussion-summary.md`, anonymous “Attachment” rows, and a
flat list dominated by `ask.wav`/read-aloud WAV files. The goal is to see and preview the
files of the session using existing Gateway capabilities.

## Code reality at intake

- `phone/iphone/Sources/App/ChatScreen.swift` shows `RunActivityPanel` for terminal
  activity and a separate “View conversation files” button below the last AI answer.
- `AttachmentsController.refresh` calls only `client.artifacts(sessionId:)`; it does
  not browse workspace files. `PhoneArtifact.parse` falls back to “Attachment” and does
  not preserve the full provenance needed to distinguish dictation/read-aloud from
  deliberately generated voice files.
- Gateway already exposes run workspace metadata/list/content routes and session
  workspace configuration. Reuse those authorized surfaces; verify their live contracts
  and capability/404 handling before implementation. Session artifacts and workspace
  documents are different sources; a tool-created file need not be an artifact.
- The existing live activity projection and per-message media previews should remain.

## Scope

### In scope

- Per-answer cycle/tool counts with a detail sheet; compact session file count/action.
- Existing Gateway run/workspace browsing and authenticated file download/preview.
- Meaningful labels, directory navigation, artifact provenance, conversational voice
  toggle, pagination/limits, and visible failures instead of silently missing files.
- Tests for actual HTTP contracts, history/account/session isolation, file filtering,
  source identity, preview cleanup, and native screenshots checked visually.
- One adversarial reviewer. Watch builds keep priority; changes stay in phone scope.

### Out of scope

- New Gateway endpoints without a demonstrated missing contract, remote package upgrades,
  arbitrary host paths, deletion of user/server files, or credentials in reports/logs.
- Hiding intentionally generated audio simply because it is WAV, or losing live approval
  visibility to make the completed UI smaller.
- Runtime media deployment work tracked separately by [1027](../planned/1027_restore_media_endpoint_resolution_and_verify_remote_iphone_images.md).

## Acceptance criteria

- [x] Completed replies have cycle/tool/file icon counts in their action row and no bulky completed-activity card or separate file-count paragraph.
- [x] Count actions open the correct turn's activity or session file browser; older replies never show a newer run's statistics.
- [x] Live running/waiting/failed state remains visible, including actionable approvals.
- [x] Session workspace directories and generated Markdown documents are discoverable and previewable using existing Gateway routes.
- [x] Conversational dictation/read-aloud files are hidden by default and revealed with a toggle; deliberately generated voice remains available.
- [x] Ambiguous artifacts have meaningful provenance/type labels and preview or a clear supported-action error.
- [x] Relevant package/native tests pass; screenshots are inspected and the completed normal app is installed on the iPhone when Watch resources permit.

## Testing

`swift test --package-path abstractassistant/phone/iphone/Packages/AssistantKit --jobs 1`

Use the guarded iPhone native-test/build helper in `phone/iphone/BUILD.md`; add targeted
HTTP fixtures covering artifact metadata, run workspace list/content, nested folders and
permission failures. Record exact commands, test counts and final screenshot evidence here.

## Receipts

- Intake: 2026-10-18, before production code changes for this item; screenshots IMG_1345,
  IMG_1344 and Screenshot 15.16.50 supplied by the operator.
- Baseline: Assistant `8f4f646` (iPhone 0.6.9 build 17).
- Adversarial reviewer: existing `tools_astra` agent, read-only API/UX audit requested.
- ADR impact: none intended; reuse the existing Gateway-owned authorization, workspace
  and artifact contracts. Any discovered ownership/security change needs separate review.

## Completion report

Completed 2026-10-18; implemented and installed iPhone **0.6.10 (18)**. Changes are
currently uncommitted; no package release or remote Gateway update is implied.

### Result and implementation

- `ChatScreen`, `AnswerActivityView` and `AssistantStore` now put cycles/tool calls/files
  after the answer's speaker action. Counts open an answer activity sheet or the shared
  session file browser. Terminal completion no longer occupies a large card. Live,
  approval, failed, cancelled and lost-connection feedback remain available.
- `AnswerActivity` replays the root and owned descendants, never a different answer's
  activity. It pages ledgers, preserves terminal state and reports partial results.
  Entity visit replay is explicitly labelled **Visit activity** when durable per-turn
  boundaries are unavailable; current visit turns keep isolated cursors/snapshots.
- `SessionFilesController`, `SessionFilesScreen` and Gateway client's `SessionFiles`
  model use existing workspace metadata/list/content APIs, discover descendants even
  when the root has no workspace, deduplicate shared workspace roots, and browse folders.
  Mutable workspace documents are downloaded afresh; artifacts retain their own IDs.
  Labels preserve meaningful source paths and use type plus short ID when unnamed.
- `ArtifactPreview` renders Markdown/text in-app, retains image/audio/native file
  previews and sharing. Preview copies are removed on dismissal/account/session reset;
  cancelling a stale download cannot replace a newer preview. Downloads retain the
  authenticated transport's 256 MiB streaming cap, redirect refusal and partial cleanup.
- `ArtifactProvenance` hides marked read-aloud/dictation and linked transcripts by default.
  New dictation uploads use `voice/dictation/<UUID>.wav` via the existing upload contract.
  On the deployed Gateway older audio lacks purpose markers, so legacy classification
  requires complete conversation input/output hydration, matching source/producer/link
  provenance, and no explicit attachment reference. The browser discloses that inference;
  its toggle restores every hidden item. Intentional voice exports remain visible.

### Validation and adversarial review

- Full Swift package: **185 passed** (109 AssistantKit, 76 Gateway client).
- Final native simulator selection: **17 passed**, zero failed/skipped. Five screenshots
  visually inspected: compact row, file list, nested folder, Markdown, audio toggle.
- Final physical iPhone read-only test: **1 passed**. The actual saved session exposes
  `discussion-summary.md` (769 UTF-8 bytes), one workspace, 20 legacy audio/transcript
  artifacts hidden by default, no remaining attachment rows and no issues. Downloaded
  preview cleanup asserted. This test creates no messages or generation requests.
- Normal signed app installed/launched successfully, verified **0.6.10 (18)** and no test
  plugins. Watch retained resource priority through the guarded one-job build helper.
- One adversarial reviewer (`tools_astra`) reviewed API fidelity, isolation, stale task
  races, pagination, workspace discovery and conservative voice filtering. Findings fixed:
  root-without-workspace blocked descendants; stale download/page tasks could mutate new
  state; old entity replay could misstate per-answer counts; metadata refresh could retain
  a stale missing root; old audio classification needed complete explicit-reference
  protection and upload/LLM source checks. Initial test/compile corrections are retained
  in the evidence README; final runs supersede them.
- `git diff --check` and Assistant `llms-full.txt` freshness passed.

### Documentation, limits and follow-up triage

Updated phone README, BUILD and architecture docs, and regenerated Assistant `llms-full.txt`.
Durable receipts: [evidence/1028](../evidence/1028/README.md).

ADR impact: **None**. Existing Gateway authorization/workspace/artifact contracts remain
canonical; no new endpoints or server-owned policy changes were needed.

Bounded browsing is explicit: artifacts page 500 at a time, workspace inventories 1,000
entries with an option to load the full folder, activity traversal at most 64 runs and
20,000 ledger records per run. Partial counts/errors remain visible. If complete explicit
file-reference history cannot be established (including histories beyond 64 turns), older
ambiguous audio stays visible; nothing is deleted. Text preview is bounded with a visible
truncation notice and whole-file sharing retained. These are documented limits, not hidden
failures.

Post-completion insight/follow-up triage: actual workspace documents and artifacts must be
queried separately; this item now does so. General replay convergence is already planned
in [0993](../planned/0993_one_ledger_replay_many_views.md). Remote media deployment remains
[1027](../planned/1027_restore_media_endpoint_resolution_and_verify_remote_iphone_images.md).
Legacy backlog naming/duplicate IDs remain [0889](../planned/0889_normalize_the_legacy_root_backlog.md).
No additional item or priority change is needed. No Watch edits, publication or remote
package deployment were performed.
