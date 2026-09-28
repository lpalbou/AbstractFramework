# 0980 — Patch 0.6.1: every command on PATH, AbstractCode terminal sign-in, one shared Run now hint

> Package: abstractframework (installers, docs, identity sync); abstractgateway 0.7.1; abstractcode 0.7.1 / web 0.6.1; abstractuic ui-kit 0.1.16; abstractobserver 0.2.1; abstractassistant 0.9.1
> Type: task
> Created: 2026-09-28
> Priority: normal
> Labels: installer, cli, tui, sign-in, automations, patch-wave
> Status: completed 2026-09-28. Staged on root `wave3/root` for root 0.6.1; it ships when the patch wave publishes (operator GO for this patch wave)

## Summary

This is the implementation record for the 2026-09-28 patch wave's root part. Before it, a fresh
install left `abstractcode` and the library commands off PATH; a directly launched AbstractCode
terminal client showed "no workflow yet" and retried forever against a 401; and Run now meant
something different in each client.

## What shipped (root)

- **fix/installer-clis** (`01fa951` … `39b1838`, merged in `wave3/root`):
  - `abstractcode` is built by default next to `abstractgateway`, in uv's tool bin folder;
  - the library commands (abstractcore, abstractvoice, abstractvision, abstractmusic) are exposed
    by default, all-or-nothing per package, and a package with a taken command name is skipped;
  - opt-outs `--no-code-cli` / `--no-core-cli`, with the `--with-*` flags kept as aliases;
  - the summary lists every command with what it does, and prints the sign-in lines
    (`abstractcode login --token <token>`, or `abstractgateway apps tui-command code`); the token is
    never saved;
  - a re-run keeps an `abstractcode` newer than the pin;
  - install.ps1 builds both crates into `%USERPROFILE%\.local\bin`;
  - uninstall removes `abstractcode` and the stale `<data>/apps/bin` copy.
  - Evidence: `untracked/installer-clis-note.md`; the RED evidence for each round is recorded there.
- **fix/run-now-hint** (`cfc24a2`): `scripts/check_identity_sync.py` gains the
  `automation_controls.json` group (canonical in the ui-kit; copies in the Assistant and the
  AbstractCode TUI). Docs state Run now's effect on the schedule. Evidence:
  `untracked/run-now-note.md`, including runtime-probe semantics 4/4.
- **Release 0.6.1:** pins gateway 0.7.1, assistant 0.9.1, npm code 0.6.1 and observer 0.2.1, crate
  abstractcode 0.7.1; the manifest regenerated; CHANGELOG `[0.6.1]`.

## Validation

- Root pytest 46 passed, 5 skipped (3 need pwsh; 2 need sibling checkouts, run separately against
  the real siblings: see the staging note).
- Shell suites: install/uninstall paths 144/144, inventory 12/12, repo scripts 28/28, supervisor 28/28.
- `install.sh --print` and `--print --uninstall --yes` under `/bin/sh` and `dash` give identical
  output and write nothing.
- The manifest check and the llms-full check are current.

## Follow-ups

- [0979](../planned/0979_abstracttui_clear_screen_before_leaving_the_alternate_screen.md): abstracttui
  clears the screen before leaving the alternate screen (the duplicated header in a phone's SSH
  scrollback).
- abstractcore declares generic unprefixed commands (`summarizer`, `extractor`, `judge`, `intent`,
  `deepsearch`), which are now on PATH by default. Suggestion for the core seat: keep only the
  `abstractcore-*` names in a future release (installer note, Findings).
- AbstractCode web: raise the ui-kit floor to `^0.1.16` so the kit's Run now hint reaches the web
  panel (run-now note).
- `abstractcode exec` could reuse the sign-in report wording; the gateway's `apps list` wording
  "installed by the gateway" also covers an installer-built copy (tui-signin note, follow-ups).

## Receipts

- Root staging note `untracked/patch-wave/STAGE-root.md`; notes `untracked/installer-clis-note.md`,
  `untracked/run-now-note.md`, `untracked/tui-signin-note.md`.
