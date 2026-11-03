# 1082 contextual interaction evidence and try guide

Implemented locally in AbstractTUI and AbstractCode; no package publication or backend changes.
[Independent review](../1081/adversarial-review.md) approves the current selection/rendering scope.

## Try the application

The optimized local binary is `abstractcode/target/release/abstractcode`. Launch it through your
normal Gateway/login settings, or use its normal `--resume` option to reopen a conversation.
The ordinary installed command may still point to an older binary.

1. Open an assistant response containing prose, a Markdown table or a fenced code block.
2. Click a word: it highlights; while the avatar is Ready and motion is enabled its gaze also
   attends to the actual click. Click attention is bounded to two seconds and consumes no action.
3. Double-click for a sentence, triple-click for a paragraph, or drag across wrapped lines.
   A table cell/code block retains its source context. Unit buttons refine the selection.
4. Choose **Explain**, **Use as context** or **Change** above the composer. The quoted passage,
   bounded surrounding excerpt and human-readable table/code provenance join your existing draft.
5. Inspect/edit the draft and use normal Send. During an active run this uses ordinary steering;
   choosing a selection action alone emits no run command or tool approval.
6. **Cancel** preserves the draft. Esc clears selection and retains normal voice cancellation.
   A slash-command draft must be finished/cleared before inserting selected content.

The action row reuses existing space, so selection does not move the passage under the pointer.
Tab reaches its action host; Left/Right select, Enter or Space activate. Narrow views expose
**More** or **Actions**; Up/Down and Enter operate the overflow menu. Screen-copy remains available
in custom user/tool/JSON blocks; those currently do not expose semantic content actions.

## Public contract and implementation

- TUI `render/content.rs`: producer-authored source runs and optional table/code provenance.
  The Markdown parser, rich-text wrapping and table layout retain actual UTF-8 source ranges.
- TUI `widgets/content_selection.rs`, `feed_content.rs`, `markdown_content.rs`: bounded lazy hit
  mapping, click/drag/unit selection, stable source snapshots and visible highlight overlays.
  Public mutable hits are validated on select and every drag update; no unchecked UTF-8 slicing.
- Additive `Element::drag_hit_test` lets mapped content own only its actual hit region. Links,
  scrollbars, controls and unmapped custom rows retain their own behavior. Pointer capture and
  the scoped follow-tail hold are released on clear, invalidation and unmount.
- Code `tui/src/ui/content_selection.rs`: responsive single-row actions, local draft staging,
  32,768-byte selected-source bound, 2,048-character centered context with omission labels,
  slash-command refusal and normal composer focus. No raw item/session IDs in product drafts.
- Source replacement/removal, conversation/session changes and unmount clear stale selection.
  New transcript appends do not silently change the selected snapshot.

## Validation and documentation

Final package matrix (all commands exit 0):

| Gate | Result |
|---|---|
| TUI all-targets, avatar enabled | 2,569 passed / 89 ignored across 137 successful test binaries |
| TUI base library, avatar disabled | 1,822 passed / 23 ignored |
| Code workspace | 1,246 passed / 23 ignored |
| Both repositories | strict all-target Clippy, format and Rust 1.87 all-target checks pass |
| Fresh Code optimized workspace build | passes; `--help` and `--version` return normally |

Ignored hardware/live-service gates were not enabled. These are package regression totals,
including preexisting tests; they are not counts of newly added tests. See
[full implementation receipt and reproducible commands](implementation-report.md),
[TUI all-target output](tui-all-targets.log) and [base output](tui-base.log).

Focused source tests, actual terminal Driver/CaptureTerm tests and full Code root harness tests
cover Unicode, wrapping, source ranges, table/code context, invalid UTF-8/overflow hit mutation,
keyboard/overflow, bottom-edge click stability, draft preservation and explicit send. Independent
external public-API probes exercise later formatted words, combining marks, emoji/CJK/bidi,
unit round trips and cross-table drag context clearing. The full package matrix is recorded in
the [completion record](../../completed/1082_contextual_content_selection_and_agent_steering.md).

TUI accepted [ADR 0007](../../../../abstracttui/docs/adr/0007-logical-content-selection.md) owns
logical source/selection semantics; Code owns AI-facing actions. TUI API and Code selected-content
API/README/changelog, package agent skills and both Code LLM corpora were updated. Generic engine
APIs are taught by their existing operable package skills; GUI presentation adds no separate skill.

## Follow-up classification

- Custom producer-drawn user/tool/JSON geometry: proposed [1086](../../proposed/1086_logical_source_geometry_for_custom_transcript_blocks.md).
- Registry dependency floors and standalone published installs: existing proposed [1079](../../proposed/1079_abstractavatar_registry_release_and_consumer_distribution.md).
- Arbitrary OCR, file reads from clicked paths and automatic sends/tools: outside this contract.
