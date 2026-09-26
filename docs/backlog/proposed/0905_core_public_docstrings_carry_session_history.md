# 0905 — AbstractCore public docstrings still carry session history

- **Status:** proposed
- **Created:** 2026-09-26
- **Area:** abstractcore (docs hygiene)

## Summary
About 63 help()-visible docstrings under `abstractcore/abstractcore` (module, public class and function docstrings) still carry
session history: thread ids such as `c5053` / `dm#244`, and words like "operator directive" / "adversary" (examples in
`tools/risk_facts.py`, `tools/comms_tools.py`). Mission names and dates were removed in a0f0377 and pdf_routing; the remaining
narrative needs one pass.

## Why
`help()` and IDE tooltips show these docstrings to users; they must describe behaviour, not the conversation that produced it.

## Current code reality
Evidence: untracked/missions-2026-09-25/REVIEW/22-core-harmony-runtime-polish.md (a′). Scan: grep public docstrings for
thread-id patterns, "operator", "adversary", "mission".

## Scope / non-goals
Rewrite the docstrings as plain descriptions; keep measured facts. No behaviour change. Not the CHANGELOG (history belongs there).

## Validation
A repository test that scans public docstrings for the patterns and fails on a hit; suite green.
