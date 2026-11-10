# 1201 — Topic versions churn: a busy entity rewrites all its topics at every self-elected rest

> Package: AbstractRuntime (identity/topics.py sleep_communities trigger; identity/life.py self-elected rest → consolidator), AbstractMemory (communities_pass writes a whole new version: every topic record re-created, the previous closed, link rows per version)
> Type: bug
> Status: planned
> Created: 2026-11-10
> Priority: P2
> Labels: entities, topics, performance, memory-growth, next-wave

## Summary

Found 2026-11-10 by the Entity session's count of a one-day-old live home: 64 topic versions in 8 h 43 min (castor: 4 the
same day). Each version re-creates the CHANGED topics (~4 of 7, the previous records closed) and one `refines` link row each; after one
day the home holds 268 topic records (7 current, 261 closed) and 247 closed link rows, which the graph had to learn to
hide. Causes, read from the code and the own-time log: (1) the runtime runs the FULL night (repair, topics stage) at
every self-elected rest, and a busy entity rests every ~8 minutes (68 "rest elected" lines, 156 sleeps in a day); (2)
memory's `changed` rule is too fine (communities.py 0.5.1 :1508-1513): membership is compared as (id, via) pairs, so
a `via` promotion alone, or one new record, rewrites the topic; a rest after a few new memories rewrites ~4 topics. Neither is wrong alone; together they turn every short rest into a topic rewrite.

## Scope

1. Runtime: the topics stage runs at a sleep only when there is enough new to place: a threshold on records formed
   since the last version (count or share, e.g. the `sleep.after_fragmented_share` setting reused, or ≥ 20 records),
   always at the first sleep and at an operator sleep; otherwise the night line says "topics: unchanged (N new since the
   last version, below the threshold)". Short self-elected rests then place nothing and cost nothing.
2. Memory (versions are already incremental: unchanged topics keep record, layout and title): a coarser `changed` rule,
   AbstractMemory proposed 0070 (50ec71f): ids-only compare with the promotion recorded in place, a rewrite floor
   (e.g. < 3 new ids, no move-out, jaccard >= 0.9 → the topic stands, new ids stay provisional, receipt says
   deferred_members), receipt counts for the own-time line ("topics: 7 stand, 9 placed, 0 rewritten").
3. Both measured on the same home: versions per day, topic records per day, before and after.

## Validation

A home that forms 3 memories then rests: no new version; 25 memories then rests: one version with only the changed
topics re-created; the counts in the own-time line; the app's "closed memories" toggle stops growing with rests.
