# 0984 — Console TUIs: Left/Right arrows switch the global tab

> Package: abstractgateway (console-tui crate `abstractgateway-console`), abstractcore (console-tui crate `abstractcore-console`)
> Type: task
> Created: 2026-09-29
> Priority: normal
> Labels: tui, console, keyboard, ux
> Status: completed 2026-09-29. Ships in abstractgateway-console 0.11.1 (gateway 0.7.2, `219a1d2`) and abstractcore-console 0.4.1 (core 2.18.1, `d820229`); root 0.6.2 pins both

## Summary

In both terminal consoles, the Left and Right arrow keys switch the current global tab (the previous/next top-level screen), as a quick-navigation equivalent of the existing Ctrl+N style tab switching.

## Why

Operator request (2026-09-29): "the left and right arrows should be used to change the current global tab (eg equivalent of control+N but with left/right arrows for quick navigation in the TUIs)." Recorded as a planned item because it needs new crate versions (a new cascading release), per the operator's instruction.

## Current code reality (2026-09-29)

- Gateway terminal console: crate `abstractgateway-console` 0.11.1 (staged with gateway 0.7.2), `console-tui/` in the abstractgateway repo. Global tabs switch with the existing shortcuts (Ctrl+N style / F-keys); check `console-tui/src/ui/mod.rs` key handling.
- AbstractCore terminal console: crate `abstractcore-console` 0.4.0, `console-tui/` in the abstractcore repo.
- Both crates render on AbstractTUI; the key map may be shared there.

## Scope

### In scope

- Left = previous global tab, Right = next global tab, wrapping at the ends, in both consoles.
- The arrows keep their local meaning where a screen needs them: while a text input has focus (cursor movement), and in widgets that use Left/Right (sliders, horizontal choice lists, split panes). The global switch applies only when the focused element does not consume Left/Right; document the rule in each console's help overlay and docs.
- One implementation where possible (AbstractTUI key-routing helper) rather than two copies.
- Tests: headless UI tests for switching, wrapping, and the text-input / widget exceptions.

### Out of scope

- Changing the existing tab shortcuts (they stay).

## Acceptance criteria

- [x] In both consoles, Left/Right move between global tabs (previous/next screen in browse mode,
      wrapping) when no focused element uses the arrows.
- [x] Typing in a field, and Left/Right-driven widgets, behave as before: a text field moves its
      caret, a radio list or tabs bar changes its selection, a dialog keeps every key; the setup
      guide/wizard does not jump screens and says that `Ctrl+N` walks it.
- [x] The footers list the keys (gateway: `←/→ Ctrl+P/N`; core: `1-9,0 ←/→ screens`); both console
      CHANGELOGs describe them.

## Resolution (2026-09-29)

- abstractgateway-console 0.11.1 (`219a1d2`, released with AbstractGateway 0.7.2) and
  abstractcore-console 0.4.1 (`d820229`, released with AbstractCore 2.18.1). Root 0.6.2 pins both
  (`CRATE_RELEASE_VERSIONS`; the installer builds the gateway console at 0.11.1).
- Known limitation: a focused vertical scrolling pane keeps Left/Right (AbstractTUI routes the
  arrows to it), so the global switch does not fire there until focus moves. Follow-up:
  [0985](../planned/0985_abstracttui_vertical_scroll_pane_releases_left_right.md).

## Validation

Headless UI tests in both crates; manual check over SSH from a phone terminal.
