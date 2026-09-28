# 0967 — AbstractAssistant: SIGSEGV flake constructing the palette in tests

> Package: abstractassistant (tests, Qt palette)
> Type: task
> Created: 2026-09-28
> Priority: low
> Labels: flaky-test, qt, crash

## Summary

During the 0.9.0 staging, one full test run crashed with SIGSEGV in `tests/.../test_live_replies.py`'s `palette` fixture (`AssistantPalette` construction) while two full suites ran in parallel on the same machine. Five isolated reruns of the file and four further full runs were green. A crash in Qt construction is worth understanding before it hits a user.

## Why

stage-assistant.md (wave 2): "Flake seen once: a SIGSEGV in test_live_replies.py palette fixture ... worth a backlog note, not a blocker."

## Current code reality (2026-09-28)

- abstractassistant 0.9.0 (`e981344`); offscreen Qt with the traffic-light bridge and hotkey disabled is the known-safe setup.

## Scope

### In scope

- Reproduce under parallel load (two suites, `QT_QPA_PLATFORM=offscreen`), capture a native stack, fix or isolate the cause.

### Out of scope

- Palette features.

## Acceptance criteria

- [ ] Root cause recorded; the fixture is stable under parallel runs.

## Validation

A stress loop of the fixture under parallel suites.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
