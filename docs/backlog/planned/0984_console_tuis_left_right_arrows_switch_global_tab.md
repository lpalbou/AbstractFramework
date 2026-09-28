# 0984 — Console TUIs: Left/Right arrows switch the global tab

> Package: abstractgateway (console-tui crate `abstractgateway-console`), abstractcore (console-tui crate `abstractcore-console`)
> Type: task
> Created: 2026-09-29
> Priority: normal
> Labels: tui, console, keyboard, ux

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

- [ ] In both consoles, Left/Right move between global tabs when no focused element uses the arrows.
- [ ] Typing in a field, and Left/Right-driven widgets, behave as before.
- [ ] Help overlay and docs list the keys.

## Validation

Headless UI tests in both crates; manual check over SSH from a phone terminal.
