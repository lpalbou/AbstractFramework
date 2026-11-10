# 1204 — Ledger rows show at a glance the tools used and files read or written per step

> Package: AbstractGateway (one host marker per finished step), AbstractCore (`file_effect` fact on tool definitions), AbstractEntity (the row glyphs; its backlog 0035)
> Type: feature
> Status: planned (gateway half DONE 2026-11-11, gateway 4fa309e5; core half + app glyphs pending)
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

## Gateway half delivered (2026-11-11 00:10, abstractgateway 4fa309e5, unpublished)

Marker `{kind: "step_tools", session_id, run_id, turn_id, tools, tool_count, files_read, files_written}` right after the
step's rows, in the replay export and the live stream, deduplicated on run_id + turn_id, not listed among the life's
moments. Visits: the tool handler notes each call that ran under the turn id, a wrapper on ANSWER_USER writes the marker
(one per step across tool rounds; refused calls not counted). Own time and work ticks run in the loop process with no
run ledger: the gateway reads new episode records' `tools_used` since a per-home cursor (.host_stream/<slug>.step_tools_cursor.json)
at each /replay read and live poll. Sleep passes run no tools: no marker. No backfill (a full one costs the square of the
history). The one name table FILE_EFFECT_BY_TOOL (entity_step_tools.py) stands in for the core `file_effect` fact until
the core half lands. Follow-ups: the live stream rereads the whole marker file per poll (read only the new tail); each
marker invalidates the recent-moments cache; a turn waiting for tool approval and mention/person turns without a turn
id are untested.
