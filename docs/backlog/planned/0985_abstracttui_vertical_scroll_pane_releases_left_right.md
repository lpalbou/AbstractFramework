# 0985 — AbstractTUI: a focused vertical scroll pane releases Left/Right to the global tab switch

> Package: abstracttui (key routing); abstractgateway-console, abstractcore-console (adopt)
> Type: task
> Created: 2026-09-29
> Priority: low
> Labels: tui, console, keyboard, follow-up

## Summary

Follow-up of [0984](../completed/0984_console_tuis_left_right_arrows_switch_global_tab.md). In both
terminal consoles Left/Right switch the global screen unless the focused element uses the arrows.
A focused vertical scrolling pane consumes them too, although it only scrolls up and down, so on
such a screen the arrows do nothing visible and the global switch does not fire.

## Scope

- AbstractTUI: a scroll pane that cannot scroll horizontally leaves Left/Right unconsumed, so the
  host's global handling sees them; a horizontally scrollable pane keeps them.
- Both consoles adopt the AbstractTUI release; the footers stay as they are.

## Acceptance criteria

- [ ] With a vertical-only scroll pane focused, Left/Right switch the global screen in both
      consoles (headless UI test in each crate, RED before).
- [ ] A horizontally scrollable pane, text fields, radio lists, tabs bars and dialogs keep the
      arrows (existing tests stay green).

## Receipts

- abstractgateway-console 0.11.1 CHANGELOG (a focused scrolling pane scrolls); 0984 resolution.
