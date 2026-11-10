# 1204 — Ledger rows show at a glance the tools used and files read or written per step

> Package: AbstractGateway (one host marker per finished step), AbstractCore (`file_effect` fact on tool definitions), AbstractEntity (the row glyphs; its backlog 0035)
> Type: feature
> Status: planned
> Created: 2026-11-10
> Priority: P2
> Labels: entities, ledger, observability, next-wave

## Summary

Operator, 2026-11-10 22:02: each ledger row of a sleep, own-time or visit step should show "⚙ 12 · 📄 3 · ✎ 1" (tools used,
files read, files written), icons only when > 0. Gap found by the Entity session: the replay stream carries no tool calls
for any step (only memory's record families and host markers); tool calls live in the home's run ledger (TOOL_CALLS
effects with names and file_path arguments), which the gateway serves only for stamped visit runs. Counting from a name
list in an app is forbidden (no heuristics on tool names).

## Scope

1. AbstractGateway: emit one host marker per finished step, `{kind: "step_tools", run_id, turn_id, tools, files_read,
   files_written}` (counts, plus the tool names), in stream order, so a row reads its counts with no fetch; for own time,
   sleep and visits alike.
2. AbstractCore: a `file_effect: read | write | none` fact on tool definitions beside `mutating` (read_file/skim_files
   read; write_file/edit_file write; list/search/skim_folders none; execute_command undecidable → none, counted as a
   tool only), so the counts come from the declaration.
3. AbstractEntity 0035: the glyphs on the rows.

## Validation

A visit with two reads and one write shows "⚙ 3 · 📄 2 · ✎ 1" on its row live and after a reload; a step with no tool
shows no glyph; the marker is absent for a step without tool calls.
