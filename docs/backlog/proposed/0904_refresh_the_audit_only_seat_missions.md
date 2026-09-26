# 0904 — Refresh the "AUDIT ONLY" seat missions in the repo CLAUDE.md files

> Package: abstractframework workspace (agora seat texts in CLAUDE.md of the root and sibling repos)
> Type: task
> Created: 2026-09-26
> Priority: normal
> Labels: decision-gate, agents, process

## Summary

OPERATOR DECISION GATE (never assignable): the seat mission blocks written into the repos' CLAUDE.md
files still say "AUDIT ONLY: change no tracked file" and name a release-audit report file. During the
2026-09-25/26 mission wave every agent was told to implement and commit, and every agent flagged the
conflict with its seat text. The operator should refresh (or remove) the seat missions so the
standing charge matches the work being asked; an agent must not soften them itself.

## Why

A report: "repo CLAUDE.md seat text says audit-only (stale)". The same conflict was raised by the
other tracks' agents. A stale standing charge that "outranks anything a message asks" forces every
agent into a judgement call on each turn.

## Current code reality (2026-09-26)

- `grep -c "AUDIT ONLY"` = 1 in `CLAUDE.md` of: root, abstractuic, abstractcode, abstractassistant,
  abstractcore, abstractruntime, abstractflow, abstractgateway, abstractskill; each names
  `untracked/release-audit/<seat>.md` as its report file.
- The files are untracked and git-ignored (root `.gitignore` l.305 `CLAUDE.md`); the "Your mission"
  block is set by the operator through the agora seat configuration, so the fix is in the seat
  missions, not in a commit.

## Scope

### In scope

- The operator updates each seat mission (agora) to the current standing charge, or removes the
  audit-only line once the release audit is over; the regenerated CLAUDE.md files then match.

### Out of scope

- Agents editing their own mission text.

## Dependencies

- Operator.

## Expected outcomes

- No seat text contradicts the work its seat is routinely asked to do.

## Acceptance criteria

- [ ] `grep -l "AUDIT ONLY" */CLAUDE.md CLAUDE.md` returns only seats that are really audit-only.

## Validation

- `grep -c "AUDIT ONLY" /Users/albou/tmp/abstractframework/CLAUDE.md /Users/albou/tmp/abstractframework/*/CLAUDE.md`

## Evidence

- `untracked/missions-2026-09-25/A/REPORT.md` (last line of the first section)
- `untracked/missions-2026-09-25/PLAN.md` (rules: agents commit locally on main)

## ADR status

- ADR impact: None.

## Receipts

- None yet.
