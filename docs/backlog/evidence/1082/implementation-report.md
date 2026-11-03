# 1082 — source-aware content selection and explicit Code draft actions

Status: COMPLETE for the mapped Feed/Code scope, with the final candidate green. Refreshed TUI all-targets:2569 passed /89 ignored across137 successful result summaries; exit0. No release, commit, push, live service restart or Apple-source edit.

## Implemented scope

- AbstractTUI parser emits original UTF-8 source runs; private boxed Row sidecars carry them through the ordinary rich wrap and shared table-column solver. Existing public Span literals remain compatible. Mapping is lazy per interacted Feed item.
- Public ContentHit, ContentSelection, SelectedContent and ContentContext APIs support Unicode word/sentence/paragraph units, wrapped drag spans, table row/column/header relation and code language/source lines. Original click origin survives unit round trips. Same-unit drags retain whole-unit context; cross-unit spans do not falsely claim one table cell.
- A point-sensitive Element::drag_hit_test preserves legacy screen-copy fallback for unmapped rows. Generic ContentSelection::bind preserves the existing draw callback, normal clicks, links and drag owners. Cancellation, invalid source and teardown release only the binding's capture. Mutated invalid UTF-8/out-of-range public hits are refused on click and drag.
- Scoped logical follow-tail holds compose with existing screen/manual freezes, retain the armed follow state and resume normal pinning when the last hold ends.
- Code reuses its existing one-row breathing spacer for Explain / Use as context / Change / Cancel and unit controls. Narrow layouts use the existing ContextMenu. Standard ActionHost handles Tab, Left/Right, Enter/Space; normal composer focus returns after staging or cancellation.
- Actions quote selected data plus bounded, centered local context and human table/code provenance into the existing draft. Opaque producer/session/item/block/byte identities stay internal. Slash-command drafts refuse context append and remain unchanged. Actions never send, run tools or approve anything; explicit normal Enter retains existing send/steer routing.
- Host pointer Down feeds AvatarPointer::pressed without consuming the actual host action.
- Selection Escape also invokes the existing urgent voice cancellation, resets the cancel arm and preserves the coding draft.

## Explicit boundary

Assistant Markdown/Text/Rich/Code Feed content and streamed Markdown have logical mapping. Code UserCard, custom tool previews and custom JSON renderers retain screen-copy fallback; there is no invented source mapping from rendered glyphs. Standalone reader bindings and producer-authored custom geometry remain 0160 / proposed root1086 follow-up. No filesystem path is inferred from a code fence.

## Focus and structural fixes

- Tab traversal skips zero-area views, preventing the empty live Feed from becoming a blank stop. Explicit set_focus still accepts a zero-area live node; the regression test verifies this authority remains unchanged.
- Existing adv_reactive::shortcut_disposing_focused_subtree_keeps_focus_sane used an unmeasured zero-size focusable fixture. It now supplies Style::line(1), preserving every focus/disposal safety assertion while exercising a real visible tab target. This is a fixture correction for the stated traversal policy, not removal of a safety assertion.
- Strict Clippy prompted private type aliases for mapped runs/emitters, a SourceDocument argument bundle, and boxed private DragOwner storage. The public DragZoneFn alias remains unchanged; boxing keeps ViewNode within its existing size budget. No lint was weakened.

## Final validation

All dependency overrides are per command, never committed/global:

TUI working directory: abstracttui
- cargo test --all-targets --features avatar --config 'patch.crates-io.abstractavatar.path="../abstractavatar"' --quiet: final current-candidate exit0;2569 passed /89 ignored across137 successful result summaries, including library1844 passed /23 ignored. Log: /tmp/abstracttui-final-all-targets.log.
- cargo test --lib --no-default-features --config 'patch.crates-io.abstractavatar.path="../abstractavatar"' --quiet: exit0;1822 passed /23 ignored. Log: /tmp/abstracttui-final-base.log.
- cargo clippy --all-targets --features avatar --config 'patch.crates-io.abstractavatar.path="../abstractavatar"' -- -D warnings: exit0.
- cargo +1.87.0 check --all-targets --features avatar --locked --config 'patch.crates-io.abstractavatar.path="../abstractavatar"' --quiet: final current-candidate exit0 after private structural fixes.
- cargo fmt --all -- --check: exit0.
- Focused source tests:9 pass, including malformed custom resolver bind→Down→Drag, source offset/Unicode/table/code, centered excerpt, original-word unit round trip and same-unit drag expansion.
- Real CaptureTerm/Driver selection acceptance:8 pass. Existing screen-selection integration:24 pass. Coverage includes real highlight glyphs, no release-copy for logical selection, buttons/scrollbar, reflow/current coordinates, outside-viewport clamping, replacement/capture invalidation, closed/open stream provenance, composed freezes and fallback screen-copy of a custom row.

Code working directory: abstractcode/tui
- cargo test --workspace --config 'patch.crates-io.abstracttui.path="../../abstracttui"' --config 'patch.crates-io.abstractavatar.path="../../abstractavatar"' --quiet: exit0. Sum of captured test-result summaries:1246 passed /23 ignored; no live ignored token-spending gates were enabled.
- cargo clippy --workspace --all-targets --config 'patch.crates-io.abstracttui.path="../../abstracttui"' --config 'patch.crates-io.abstractavatar.path="../../abstractavatar"' -- -D warnings: exit0.
- cargo +1.87.0 check --workspace --all-targets --locked --config 'patch.crates-io.abstracttui.path="../../abstracttui"' --config 'patch.crates-io.abstractavatar.path="../../abstractavatar"' --quiet: exit0.
- cargo fmt --all -- --check: exit0.
- Real-root CaptureTerm/Driver content-selection integration:8 pass: draft-preserving Explain + explicit Enter; Cancel; table-header relation; bottom-edge stable row on first click and later messages;38-column Actions menu/composer focus; Tab/Right/Space activation; slash draft refusal and Esc preservation; simultaneous voice/selection cancellation preserving draft.

## Documentation

Updated TUI public API, documentation index, consumer skill, changelog and 0160/overview scope. Updated Code terminal public API/README/changelog, consumer skill and curated indexes. Regenerated TUI and both nested/root Code llms-full files. Root Code generator omits the package-agent skill body while retaining the standalone skill, matching the requested aggregation policy. Existing skills are maintained because both repositories expose multi-step public library/CLI surfaces.

## Limitations and release status

CaptureTerm drives the production terminal parser, UI tree, compositor and presenter without a physical terminal. Its VT model deliberately does not reflow on resize; the resize test uses current source geometry for subsequent hit coordinates instead of treating the old modeled screen as ground truth. No physical terminal pixel-protocol/Swift rendering parity is claimed here.

Source remains unreleased. Plain registry builds require publication/dependency-floor/lock propagation for the separate unpublished AbstractAvatar and new TUI APIs; only explicit local overrides were used for validation. The parent owns release readiness and all publication decisions.

## Final hygiene

Both package consumer skills pass skill-creator quick_validate.py. Both repositories pass git diff --check. Both Cargo workspace format checks and strict all-target Clippy checks pass. Preserved concurrent external SessionCard module, exports and source behavior; only applied format ordering in widgets/mod.rs alongside our own additions. Parent's release binary build/help validation is separate from this report.
