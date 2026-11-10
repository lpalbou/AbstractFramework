# 1198 — Communities (topics) follow-ups after castor's first three nights

> Package: AbstractRuntime (authoring briefing, topics tool prelude), AbstractMemory (communities pass wording, merged_into: its item 0064), AbstractEntity (topics panel)
> Type: enhancement
> Status: planned
> Created: 2026-11-10
> Priority: P2
> Labels: entities, topics, communities, memory, next-wave

## Summary

Three topics nights on a live home (2026-11-10, `untracked/finish-plan-2026-11-09/castor-topics-night{,-2,-3}/`) proved
the pass (night 3: 11/11 topics titled, summaries name the entity). Four small follow-ups were seen and deferred on the
record; none blocks 0.14.0.

## Scope

1. **Display-name capitalization in the authoring briefing** (runtime `authoring_system_prompt(entity_name)`): the
   briefing passes the spark name as stored; a lower-case id (`castor`) yields "castor is the entity…" and summaries
   that follow it. Use the display name as the entity writes it.
2. **Unchanged topics keep their old wording until revised**: when a topic's members did not change, the pass keeps the
   previous title/summary; when they changed slightly, the author rewrites from scratch and the wording drifts. Give the
   author the previous title/summary as context and ask for a revision, not a new text.
3. **`merged_into` on dissolved topics**: AbstractMemory proposed 0064; the runtime's night line and the app's panel
   should say where a dissolved topic's members went.
4. **First-sleep prelude line for the `topics` tool** ("you have N topics; closest …", ≤120 tokens): deferred
   2026-11-10 (recommendation: not now). The self-knowledge brief (1197) covers discoverability; build the prelude only
   if the brief proves insufficient.

## Validation

Each point: one red test before (briefing text, kept wording, dissolved receipt, prelude absence) and a fourth night on
the same home whose line reads as expected.
