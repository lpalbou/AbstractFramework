# 1201 — Topic versions churn: a busy entity rewrites all its topics at every self-elected rest

> Package: AbstractRuntime (identity/topics.py sleep_communities trigger; identity/life.py self-elected rest → consolidator), AbstractMemory (communities_pass writes a whole new version: every topic record re-created, the previous closed, link rows per version)
> Type: bug
> Status: planned
> Created: 2026-11-10
> Priority: P2
> Labels: entities, topics, performance, memory-growth, next-wave

## Summary

Found 2026-11-10 by the Entity session's count of a one-day-old live home: 64 topic versions in 8 h 43 min (castor: 4 the
same day). Each version re-creates all 7 topic records (the previous 7 closed) and ~4 `refines` link rows; after one
day the home holds 268 topic records (7 current, 261 closed) and 247 closed link rows, which the graph had to learn to
hide. Causes, read from the code and the own-time log: (1) the runtime runs the FULL night (repair, topics stage) at
every self-elected rest, and a busy entity rests every ~8 minutes (68 "rest elected" lines, 156 sleeps in a day); (2)
memory skips a version only when NOTHING moved; a rest that follows a few new memories moves 8–12 of them and gets a
whole new version. Neither is wrong alone; together they turn every short rest into a topic rewrite.

## Scope

1. Runtime: the topics stage runs at a sleep only when there is enough new to place: a threshold on records formed
   since the last version (count or share, e.g. the `sleep.after_fragmented_share` setting reused, or ≥ 20 records),
   always at the first sleep and at an operator sleep; otherwise the night line says "topics: unchanged (N new since the
   last version, below the threshold)". Short self-elected rests then place nothing and cost nothing.
2. Memory: incremental versions: an unchanged topic keeps its record (no new record, no close), only changed topics get
   new records and link rows; the version row still advances. This also keeps the unchanged topics' wording (root 1198
   #2) and makes `community_keys_of` and the graph lighter.
3. Both measured on the same home: versions per day, topic records per day, before and after.

## Validation

A home that forms 3 memories then rests: no new version; 25 memories then rests: one version with only the changed
topics re-created; the counts in the own-time line; the app's "closed memories" toggle stops growing with rests.
