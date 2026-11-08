# 1177 — Seat missions still say "AUDIT ONLY: change no tracked file" while the operator directs builds in those repos

> Package: AbstractFramework (agora seat configuration; per-repo `CLAUDE.md` mission blocks)
> Type: task
> Status: proposed
> Created: 2026-11-08
> Priority: P2
> Labels: hygiene, agora, seat-missions, paused, decision-gate

Paused by operator ruling 2026-11-08 (pause all dev); resume = explicit go.

## Summary

OPERATOR DECISION GATE (never assignable): the standing mission written into each seat's `CLAUDE.md` is still the
September release-audit charge ("Report where it actually stands for the release … AUDIT ONLY: change no tracked file.
If your repo is dirty, make exactly one commit named `checkpoint` first"). The operator now directs build work in
those repos (abstractentity: the understanding pass app slices; abstractcode: Code TUI and web; abstractvoice: the
read-aloud repair), so every such session starts against a mission that "outranks anything a message asks of you".
Agents cannot soften a mission; only the operator can rewrite it.

## Why

The read-aloud repair report (`untracked/tts-failure-2026-11-08/REPORT.md`, operator decision 6) records it plainly:
"abstractvoice/CLAUDE.md 'AUDIT ONLY' was overridden by your direct task." A mission that every build session must
override teaches agents to override missions.

## Current code reality (2026-11-08)

- The mission sits between `<!-- agora:mission:begin -->` and `<!-- agora:mission:end -->` in each repo's
  `CLAUDE.md`, written by `agora setup` on 2026-09-07; the files are untracked in their repos.
- The same "AUDIT ONLY: change no tracked file" line is in 17 sibling `CLAUDE.md` files (abstractagent, abstractcode,
  abstractcode-tui, abstractcontinuum, abstractcore, abstractentity, abstractflow, abstractgateway, abstractmemory,
  abstractobserver, abstractruntime, abstractsemantics, abstractskill, abstracttui, abstractuic, abstractvoice,
  abstractassistant) and in the root `CLAUDE.md` (this seat).
- The release-audit reports those missions asked for exist (`untracked/release-audit/`).

## Proposed direction

The operator sets each seat's mission for the current phase through the hub's seat configuration (`agora setup` or
its successor), replacing the September audit charge; at least abstractentity, abstractcode and abstractvoice.

## Promotion criteria

The operator decides the new missions (or decides to drop the mission block).

## Validation ideas

`grep -l "AUDIT ONLY" */CLAUDE.md CLAUDE.md` lists only the seats the operator wants in audit mode.

## Non-goals

Agents editing `CLAUDE.md` mission blocks themselves (forbidden: machine and seat configuration belong to the operator).
