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

Runtime: committed on main as `0a8fc67` (identity/self_brief.py, `self_brief.md` in the home, prefix section, 14 tests, 487
affected tests passed); full suite running; the refinement above is NOT built yet (next step, recorded in
`changelog.d/self-knowledge-brief.md`). Not published: AbstractRuntime 0.19.1 is the cut that carries it; if the
0.14.0 wave ships on 0.19.0, the brief waits for the next runtime patch and the gateway floor moves then. Gateway: no
code change needed; its prompt-preview route composes without the brief (shows a prefix without the section) — fold into
the gateway's next cut. Entity app: show the brief in the Topics panel header (not built).

## Validation

Brief ≤ 400 tokens with every topic's title and the top trails; byte-identical prefix across turns without a sleep; a
failed author keeps the previous brief + a failure line; a Stop during the author call writes nothing.
