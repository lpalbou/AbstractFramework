# 0979 — abstracttui: clear the screen before leaving the alternate screen

> Package: abstracttui (term/options.rs); consumers abstractcode, abstractgateway-console, abstractcore-console
> Type: task
> Created: 2026-09-28
> Priority: low
> Labels: tui, terminal, ssh, scrollback

## Summary

Some terminals do not keep the alternate screen separate from the scrollback. A phone's SSH client
is one example; tmux with `alternate-screen off` is another. In these terminals the last frame of
an abstracttui app stays in the scrollback after it quits. Launch AbstractCode twice and the
scrollback shows two `AbstractCode … acode-<id>` header lines. That looks like two sessions from
one start, but it is two launches. Write `ESC[2J ESC[H` (clear, home) just before `ESC[?1049l` when
leaving. Where the alternate screen works this is harmless; where it does not, it clears the
leftover frame.

## Why

The AbstractCode sign-in investigation (`untracked/tui-signin-note.md`, item 4) traced a user
report of a "duplicated header" in a phone SSH client to this. The TUI mints exactly one session id
per launch (`abstractcode/tui/src/lib.rs:168`). The leftover frame is the previous launch's last
screen.

## Current code reality (2026-09-28, abstracttui v0.6.0-3-g8209d1f)

- `abstracttui/src/term/options.rs:178` appends `\x1b[?1049l` to the leave bytes with no clear
  before it; the test at `:199` asserts that the leave bytes end with it.
- Every consumer (abstractcode 0.7.x, abstractgateway-console 0.11.x, abstractcore-console 0.4.x)
  depends on abstracttui 0.6.0.

## Scope

### In scope

- Emit `ESC[2J ESC[H` before `ESC[?1049l` in the leave sequence when the alternate screen was
  entered; a test on the exact bytes.
- Release abstracttui, then raise the consumers' dependency in their next releases.

### Out of scope

- Changing the inline (non-alternate-screen) mode.

## Acceptance criteria

- [ ] Under tmux `alternate-screen off`, launching and quitting an app twice leaves no app frame in
      the scrollback.
- [ ] The leave-bytes test pins the clear, and it fails when the clear is removed.

## Validation

A tmux reproduction (`set -g alternate-screen off`), plus the unit test on `leave_bytes`.

## Receipts

- Source: `untracked/tui-signin-note.md` (item 4 and follow-ups); root patch staging note
  `untracked/patch-wave/STAGE-root.md`.
