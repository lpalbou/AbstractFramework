# 1197 — The entity's self-knowledge brief in its prompt prefix (written at sleep)

> Package: AbstractRuntime (night stage + prompt composition; 0.19.1), AbstractEntity (show the brief in the Topics panel header)
> Type: feature
> Status: planned (IN PROGRESS 2026-11-10: runtime worker; commit pending)
> Created: 2026-11-10
> Priority: P1
> Labels: entities, topics, memory, discoverability, prompt-cache

## Summary

Operator ruling, 2026-11-10 (verbatim): "that's one of the thing that can truly help the entity actively explore its
memory when relevant. IMO, you should allow at least 200 tokens if not 400 tokens. so that it knows enough about oneself
(the main topics and trails of thoughts), so that it can search its own memories (we have normally tools for that).
accessing a memory first go through discoverability, like in FAIR principles.. it can't search what it doesn't know
exist. so we have to help the entities know what it knows, at least at a very high level. then it can deep dive actively
(consciously) into its memory. i would however be careful with those summaries, so that it doesn't invalidate the prefix
(kv cache prompt). probably one more reason why the title/summaries/trails of thoughts should be better computed at
sleep, so it doesn't bother the ongoing work."

Refinement (10:35): per community: title + one line + memory-type stats ("12 episodes, 3 dreams…") + last formed /
last accessed; then the main trails of thought.

## Design (built)

At the end of the night's topics stage: one summaries-author call over memory's communities payload → a 200-400 token
plain-text brief stored in the home (`self_brief.md`, header with version_seq/written_at/tokens), never in the graph;
placed in the system prefix of every lane right after the identity block and BEFORE anything per-turn, so the KV prefix
stays stable between sleeps; no brief → no section; the `topics` tool's teaching points at it. Runtime 0.19.1.

## State 2026-11-10 ~11:00

Runtime: committed on main as `0a8fc67` + `340b61b` (changelog note) (identity/self_brief.py, `self_brief.md` in the home,
prefix section, 14 tests; FULL SUITE 4925 passed, 32 skipped, 3 xfailed at 0a8fc67; measured on castor's real 11-topic
payload: 2384-token body, a 202-word brief = 348 tokens); NOT pushed; the refinement above is NOT built yet (next step, recorded in
`changelog.d/self-knowledge-brief.md`). Not published: AbstractRuntime 0.19.1 is the cut that carries it; if the
0.14.0 wave ships on 0.19.0, the brief waits for the next runtime patch and the gateway floor moves then. Gateway: no
code change needed; its prompt-preview route composes without the brief (shows a prefix without the section) — fold into
the gateway's next cut. Entity app: show the brief in the Topics panel header (not built).
Memory seam for the refinement: AbstractMemory serves no last-accessed date per topic, only `facts.activity` (recalls over
the last 7 days); "last accessed" needs a `facts.span`-like last-recall stamp in the communities payload (Entity session,
memory backlog) before the runtime can print it.

Blocker found and fixed 2026-11-10 ~11:40: 0a8fc67's `topics` tool description was 249 characters, over AbstractCore's
200-character tool limit (`tools/core.py _MAX_TOOL_DESCRIPTION_CHARS`); AbstractCore refused the definition and the gateway's
mention door answered 500 on this runtime (the gateway worker ran its tests against 8c8a731 for that reason). Fixed in
runtime `9656cee` (195 characters; `tests/test_tool_descriptions_fit_core.py` pins every entity tool under the limit). The
release sweep must include that test; a runtime cut from 0a8fc67 without it ships the 500.

## Test note 2026-11-10 14:50

The operator looked for self_brief.md in the Entity app's Files view and found none: (a) no real night had run since restart
#15 (the two "sleeps" were visit-door restores); castor's first night started 14:51 (idle sweep, 26 % fragmented) and writes
it; (b) the Files view lists the workspace, not the home root, so the brief needs its own place in the app (Entity session:
Topics panel header or Identity page, with written_at).

## Related

abstractentity backlog 0011 (the "what do you know" answer) and 0005 (members by type + last formed, the panel side of the refinement) point here.

## Validation

Brief ≤ 400 tokens with every topic's title and the top trails; byte-identical prefix across turns without a sleep; a
failed author keeps the previous brief + a failure line; a Stop during the author call writes nothing.
