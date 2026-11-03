# 1086 — Logical source geometry for custom transcript blocks

> Package: abstracttui, abstractcode
> Type: interaction extension
> Created: 2026-10-31
> Status: Proposed
> Priority: medium
> Labels: selection, source-provenance, custom-widgets

## Summary and current code reality

1082 implements source-aware Feed Markdown/Text/Rich/Code and streamed Markdown, with generic
ContentSelection.bind for providers that can resolve their own source hits. Custom DrawFn
blocks do not supply cell-to-source geometry. Code user cards, folded tool previews and custom
JSON blocks therefore retain ordinary screen-copy behavior instead of pretending their glyphs
identify exact logical source. Existing whole-message context menus remain separate from the
new explicit selected-passage actions.

## Proposed outcome

Allow custom content producers to publish source hits through a small optional contract derived
from their actual layout. Prefer existing shared rich-wrap/table geometry and immutable source
snapshots. Do not duplicate parsing in Code, guess offsets by searching glyphs, or interpret
alpha/pixel occupancy as semantic regions. Preserve original widget activation, source-kind
metadata, clipping, scrolling and accessibility. Integrate appropriate user/tool/JSON surfaces
only after their source geometry is available; keep explicit draft review and normal Send/steer.

## Validation and promotion criteria

Real Driver cases for wrapped user text, tool arguments/result/error, folded/expanded views,
JSON key/value identity, clipped/nonsquare placement, stale source, Unicode, click/drag and
normal controls. Demonstrate producer-authored hit accuracy and copy fallback for unsupported
parts. Confirm that menu labels distinguish a selected passage from a whole message and that
context staging preserves drafts. Promote when specific producers and the minimal API are chosen.

## Dependencies and ADR state

Follow-up to 1082 and remaining TUI 0160 logical-selection scope. TUI ADR 0007 governs source
provenance and host authority. No universal custom-widget selection or automatic AI action is
promised by this proposal.
