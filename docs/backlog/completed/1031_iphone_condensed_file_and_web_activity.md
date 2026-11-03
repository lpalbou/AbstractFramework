# 1031 — iPhone condensed file and web activity

> Package: abstractassistant
> Type: task
> Created: 2026-10-18
> Status: Completed
> Completed: 2026-10-18
> Priority: P1
> Labels: iphone, observability, files, web, ux

## Summary

Show only relevant answer activity actions: separate file reads, file writes/edits,
email reads/sends, web searches (skim/full) and page fetches (skim/full). Counts open
compact collections with recorded targets/results, preserving live activity and session
file preview access while avoiding misleading success or provenance claims.

## Why

The operator wants a condensed account of information accessed and files changed during
an agent answer, with quick access to the evidence. Zero-count optional actions clutter it.

## Current code reality

- `AnswerActivityButtons` currently renders both mail directions whenever either is nonzero;
  `ChatScreen` always shows a session-wide folder count on the latest answer. Neither is
  an accurate per-answer file read/change receipt. The session file browser remains in More.
- `RunActivity` already pairs run-scoped runtime tool identities/results and replays owned
  descendants. Core common tools return mixed schemas: read/skim/write/edit file text,
  JSON-string web search, textual skim_url and structured fetch_url. Outer tool success
  alone does not prove success (mixed skim failures, skim HTTP403, preview/no-op edits).
- File listing/searching is discovery, not reading every matching file. Search result URLs
  are discovered links, not fetched pages. Arbitrary shell commands are opaque.

## Scope

### In scope

- Optional positive-only actions; run-scoped file source grouping and successful-operation
  receipts for read_file/skim_files/write_file/edit_file, web_search/skim_websearch,
  skim_url/fetch_url. Record skim/full/range/append/edit/method where available.
- Compact searchable target/result collections; file read excerpts/change receipts and
  quick access to existing session file browser; safe user-initiated web links.
- Mixed failures, previews/no-op, repeated/replayed operations, result pairing, bounded
  retention, per-answer ownership, native screenshots and tests; normal phone installation.
- One adversarial reviewer, Watch priority preserved.

### Out of scope

- Inferring shell side effects, counting list/search matches as full reads, auto-fetching
  sites/files, new Gateway endpoints, Watch edits, remote upgrades/publication or commits.

## Acceptance criteria

- [x] Zero read/sent mail and irrelevant file/web actions are hidden independently.
- [x] File reads and writes/edits, searches and page fetches have separate positive counts.
- [x] Collections identify source/query/URL, mode, time and recorded content/results;
  failed/pending/no-op/preview work is not presented as a successful change/access.
- [x] Multiple targets, mixed skim success/failure, replay and per-answer/run identities work.
- [x] Existing session workspace previews, live activity/approvals remain reachable.
- [x] Package/native/live read-only checks, visual inspection and adversarial review pass;
  normal app installed with Watch resource priority.

## Receipts

- Intake before implementation 2026-10-18, baseline iPhone 0.6.12 (20).
- Reviewer `tools_astra` canonical-tool audit: mixed skim blocks/HTTP403 are false-success
  traps; search results are not fetches; edit preview/no-op is not a modification.
- Related [1030](../completed/1030_iphone_read_and_sent_email_collections.md),
  [1028](../completed/1028_iphone_compact_answer_actions_and_session_file_browser.md).
- ADR impact: None; client evidence projection through existing authorized ledger APIs.

## Completion report

Completed 2026-10-18; normal iPhone **0.6.13 (21)** installed and launched. Changes remain
uncommitted. No Gateway/Runtime changes, remote deployment, publication or Watch edits.

### Result and implementation

- Optional mail directions now hide independently at zero. New positive-only icons/counts
  distinguish files read, files changed (written/appended/edited), web search operations
  and pages fetched. The old session-wide folder count was removed from answer rows;
  More → Conversation files remains available. Share/copy/speech/cycle/tool controls and
  live activity/approval visibility remain.
- `AccessActivity` projects eight canonical Core contracts into grouped `AccessEntry`
  sources and `AccessEvent` evidence. File counts use validated returned path plus run
  identity; requested aliases are preserved, repeated operations are grouped and separate
  child workspaces cannot conflate. Searches count successful query operations (including
  empty results), not result links. Pages group returned URLs with requested URL/method
  evidence. Skim/full/range/append/edit modes and recorded timestamps remain visible.
- File skim errors and HTTP403 textual skims cannot rely on outer executor success.
  Recognizable successful file receipts/HTTP2xx or structured web success are required;
  pending/failed/no-op/preview edits are excluded. URL metadata is parsed only from the
  fixed header, not untrusted page content. Write receipts do not invent file creation.
- `AccessActivityView` offers compact searchable collections and individual excerpts,
  results, diff/receipt details and safe user-initiated web links. File sheets hand off
  after dismissal to the existing session workspace browser and Markdown/file previews.
  Complex action strips scroll horizontally. HTML/code is inert recorded text.
- Whitelisted arguments exclude write/replacement content, HTTP request headers/bodies.
  Public output can include response metadata. Each category retains 100 sources and
  each source's latest five operations; cumulative source counts/visible retention notices
  remain. Excerpts cap at 8,000 characters, search links at 30, title/snippet cuts have
  ellipses. Overlong URLs are explicitly non-navigable rather than altered links.

### Validation and review

- Full Swift package **211 passed** (135 AssistantKit + 76 Gateway client), ten source
  tests covering aliases/replay/run isolation, mixed skim failures and deceptive filenames,
  byte windows, write/append/edit grouping, no-op/preview/failure/shell/discovery exclusions,
  empty searches/no invented fetches, HTTP403/preview URL spoofing, methods/redirects/request
  secret exclusion, long-link disabling, and retained cumulative counts/latest events.
- Six distinct native scenarios passed: initial **5 passed / 1 failed**, corrected web test
  **1 passed**. Failure was solely an accessibility selector expecting Link where SwiftUI
  exposes Button; hierarchy and visible control confirmed it. Workspace handoff/Markdown,
  positive-only counts, file/web collections, overflow and approval regression verified.
- Physical saved-history replay **1 passed**: actual conversation has one changed file,
  one sent email, zero other source categories, zero issues. No new file/mail/web actions
  were created for this proof. Broader read/search/fetch behaviors are fixture-verified.
- One adversarial reviewer `tools_astra` audited source contracts, correctness, ownership
  and seven actual screenshots. Final verdict **Approved for signed install**. Findings
  fixed: aliases counted twice; URL preview text could spoof Final URL; a legitimate edit
  containing No changes applied could be excluded; long destinations must not be truncated
  into clickable links. Native screenshots show clear counts, grouped operations, proper
  read/change distinction, search leads versus fetched pages and accessible overflow.
- Signed normal **0.6.13 (21)** verified without test plugins, installed/launched successfully.
  One-job native build guard repeatedly yielded to Watch; no Watch files/build outputs
  were changed. `git diff --check` and Assistant/root aggregate checks passed.
- Updated phone README/architecture and regenerated Assistant `llms-full.txt`.

Durable tests/screenshots/filtered live proof/install/review and commands:
[1031 evidence](../evidence/1031/README.md).

### Insight and follow-up triage

ADR impact: **None**. Existing authorized ledger and workspace ownership stay canonical.
Receipts describe recognized successful tool operations, not OS-level tracing. Lists and
search matches do not imply file reads; shell commands may access/change extra files and
remain visible in full activity. UI/README disclose that limit rather than infer targets
from shell text. Per-run file identity is deliberately conservative for differing child
workspaces. Retention and preview limits are explicit, with no new urgent follow-up.
General replay convergence is already [0993](../planned/0993_one_ledger_replay_many_views.md);
remote media deployment remains [1027](../planned/1027_restore_media_endpoint_resolution_and_verify_remote_iphone_images.md).
No priority change, extra item or release was introduced.
