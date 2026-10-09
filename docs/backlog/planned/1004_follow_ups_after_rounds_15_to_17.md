# 1004 — Follow-ups after rounds 15 to 17

> Package: abstractframework (root), abstracttui, abstractgateway, abstractcore, abstractcode, abstractvoice
> Type: task
> Created: 2026-10-09
> Priority: normal
> Labels: release-follow-up, tui, engine, code-tui, voice, docs

## Summary

Rounds 15 (gateway terminal console redesign), 16 (round-16 wave staged as root 0.10.2) and 17
(AbstractCode TUI automation parity) left work that did not block their gates. This item collects
those leftovers in one place so a later agent can pick each one up without the round notes.
Item 1003 keeps what it already tracks (console 0.16.0 release, Code TUI default workflow and
Mailbox step, Flow, Windows, and the rest); nothing here repeats it.

## Why

The round drafts (`untracked/round15/BACKLOG-R15.md`, `untracked/round16/BACKLOG-R16.md`) and the
adversary's non-blocking notes are scratch files; the root backlog is the durable record.

## Current code reality (2026-10-09, staged, not published)

- abstractgateway-console crate 0.16.0 on abstractgateway branches `round15/2026-10-07` and
  `round16/...`; engine abstracttui 0.3.8 on `maint/0.3` and 0.6.1 on main (both staged).
- Root `release-prep/0.10.2` at f3e011b (round-16 pins: gateway 0.14.0, runtime 0.10.0, core
  2.26.0, voice 0.15.0, assistant 0.13.2, ui-kit 0.8.7, …), not published.
- AbstractCode TUI crate 0.9.2 on abstractcode `round16/2026-10-08` with round 17 merged
  (CODE-TUI-GAPS tasks 1–5, 10, 12, 13: attention chip, `/schedule` inputs, tools, email trigger and
  Mailbox, account default workflow, `/sessions` search, Read aloud in automations). Not released.
- Two engine lines stay live: gateway console and abstractcore-console on abstracttui 0.3.x, Code
  TUI on 0.6.x. Every engine fix ships twice.

## Scope

### In scope

1. **One engine line (R15-B1).** Move abstractcore-console, then the gateway console, from
   abstracttui 0.3.x to 0.6.x (API inventory 0.3.7 → 0.6.x in BACKLOG-R15), release bottom-up
   (core console → gateway console → root pins), then lift the console widget layer
   (`console-tui/src/ui/w/**`: action, toggle, segmented, table, form, confirm, notify, tip, caret)
   into abstracttui as a shared module; retire `maint/0.3` once no published consumer pins 0.3.
2. **Code TUI persistent sidebar** (gaps #6): left drawer with Conversations and Automations lists
   (cards, `Archived · N`), key and mouse toggle, on the engine's `drawer_dock`.
3. **Code TUI mouse-first model** (gaps #7): the round-15 interaction model (clickable actions with
   tooltips, state toggles, segmented choices, form modals) after item 1; covers the round-17
   key-only inventory (status chip Enter, `/` search in `/sessions`, account-default picker + `d`,
   Ctrl+P, every `/schedule` row, pickers, switches, text fields, definition-panel rows).
4. **`/schedule` as one form** (gaps #8): the kit dialog's sections on one scrollable form modal
   instead of a 7-step wizard; on a gateway 422 keep the form open with the sentence inline (today it
   closes and shows the sentence as the list notice).
5. **Code TUI rich file preview** (gaps #9): rendered Markdown and highlighted code in `/files` and the
   automation folder; name PDF and audio honestly; "save to this machine" when local.
6. **Code TUI docs assistant** (gaps #11): `/docs` overlay through the gateway docs-qa with
   `app=code`, same grounding footer as the web.
7. **NVIDIA CUDA speech-to-text manual check.** The CUDA path (cuDNN 9 + cuBLAS 12, capability
   compute type, recorded CPU fallback) is proven only with mocked CTranslate2/CUDA; run the manual
   check on the 0989 NVIDIA host per abstractvoice `docs/installation.md` and record it.
8. **`af_supervisor.sh` busy banner (0848).** The "likely busy (in-process model inference)" banner in
   `scripts/lib/af_supervisor.sh` should point at the audit line's `reload` block.
9. **Last "viewer" wording.** `docs/guide/summoned-entities.md:401` diagram text "observer / viewer";
   roles are admin + member (ruling 2026-10-08, 0870).
10. **API refuses an email automation without a prompt.** The API accepts an email automation created
    without a task/prompt and every occurrence then fails at run time (identical on released 0.13.1);
    refuse at creation with a sentence, as the web dialog already requires the field.
11. **Code web served speech-input hint.** Shows only once ui-kit 0.8.7 is published and Code bumps
    its kit (AfVoiceSection); verify after the 0.10.2 publish.
12. **Cross-plane admin access to entities in a member's plane (W6 F1).** Confirm the round-16 fix
    passed its re-gate; otherwise document the limit.
13. **Code TUI automation detail at 80x24** (round 17 notes): the detail shows no run rows at 80x24,
    so the run Ctrl+P reads is not visible; the run selection is colour-only (add a text marker).
14. **abstracttui select-mode test gaps (AV5, both branches):** the "a click never selects" test is
    masked (click a cell away from the anchor); no test that ↓ at the bottom edge stays the
    scroller's.
15. **Gateway console round-15/16 SHOULD notes** (ADVERSARY lines 1128–1208): tooltip left over a
    modal, "Saved." vs "Saved", missing title ✕ on Create user and Retained runtimes, "HTTP 400:"
    prefix on inline refusals, caret placement past the text, status-bar hints for drawers and
    confirms, Sandbox refusals inline, Setup card tooltips, Mind/Voice "save by themselves" next to a
    Save button, duplicated Tools-per-phase sentence.

### Out of scope

- Anything item 1003 already tracks; new features beyond the list.

## Acceptance criteria

- [ ] `cargo tree -i abstracttui` shows one 0.6.x for the gateway console; all three console suites green; `maint/0.3` retired.
- [ ] The console widget layer lives in abstracttui and is used by both consoles and the Code TUI.
- [ ] Code TUI has the persistent sidebar, the mouse-first model (every key-only control in the round-17 inventory has a mouse path), `/schedule` as one form that stays open on a gateway refusal, rich file preview and `/docs`.
- [ ] NVIDIA CUDA STT check recorded from the 0989 host.
- [ ] `af_supervisor.sh` banner points at the `reload` block.
- [ ] No "viewer" role wording left in root docs.
- [ ] Gateway API refuses an email automation without a prompt (test red without the fix).
- [ ] Code web shows the served speech-input hint on the published kit.
- [ ] W6 F1 fixed or documented as a limit.
- [ ] Automation detail shows runs at 80x24 with a non-colour selection marker.
- [ ] Both abstracttui select-mode test gaps closed (mutants go red).
- [ ] Console SHOULD notes fixed or explicitly declined on the record.

## Receipts

- Predecessor still open: [1003](1003_follow_ups_after_the_0_10_1_release.md).
- `untracked/round15/BACKLOG-R15.md` (R15-B1 and API inventory).
- `untracked/round15/CODE-TUI-GAPS.md` §3 (tasks 6–13).
- `untracked/round16/BACKLOG-R16.md`; adversary email evidence `untracked/round16/adv/final/email/`.
- `untracked/round4/ADVERSARY.md` — AV5 verdict (line ~1166), console SHOULD notes (~1128–1208),
  Round 17 section (~1239) with the AY/AZ verdicts and the "Open (non-blocking)" line.
- Root staged release: `release-prep/0.10.2` f3e011b.
