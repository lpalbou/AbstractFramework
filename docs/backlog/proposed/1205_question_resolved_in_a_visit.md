# 1205 — A question the entity asked is marked resolved when the visit answers it, with a badge and the card moving it

> Package: AbstractRuntime (identity/visit_workflow.py look-back + reflection.py prompt; act_only.py meta; chat.py diary_notice), AbstractGateway (entity_visits.py close_notices; entity_replay.py operator diary display), AbstractMemory (replay.py diary block carries `resolves`), AbstractUIC panel-chat (ChatNoticeKind `question_resolved`), AbstractEntity (badge, Questions lens, record-detail words)
> Type: bug
> Status: proposed
> Created: 2026-11-11
> Priority: P1
> Labels: entities, questions, visits, cross-seat

## Summary

Operator, 2026-11-11 02:00: an entity asked him a question during a visit; he answered; nothing marked the question
resolved, no "question resolved" badge appeared under the reply, and the question still shows under OPEN QUESTIONS in
the card. "it's important as if unresolved, this is probably looked back into its memory."

## Facts (code, 2026-11-11)

- Memory already has the verb: a question is a diary record `diary_type=question`; it is OPEN while no believed diary
  entry references it through `attributes.resolves` / `answers` (`diary.py:163-234 _open_unresolved`,
  `entity_card.py:353-390` splits open/resolved). No flag, no closure, nothing else to add in storage.
- The turn contract tells the entity "If an entry ANSWERS one of your open questions, add resolves=<entry id>"
  (`chat.py:427-430`), parsed at `chat.py:1117-1122`, checked by `diary.py:439-483` (`resolves_status`).
- GAPS: the visit look-back prompt (`reflection.py:84-199`) never lists the entity's open questions nor invites
  `resolves=`; the visit lane passes no resolutions into the prompt (`visit_workflow.py:1246`) while the chat lane does
  (`chat.py:3787`); the visit lane's diary meta carries neither `resolves` nor `resolves_status`
  (`act_only.py:183-199`) so the ELECT reply notice cannot say it; `close_notices` lists only interest/lesson/
  realization (`entity_visits.py:368-404`); the replay diary block carries no `resolves` (`replay.py:156-190`);
  the kit's `ChatNoticeKind` has no `question_resolved`; the app's Questions lens tests only `closed`
  (`graph_lenses.ts:42-44, 115-121`); the night's `resolve_questions_pass` proposals (`candidate_miner.py:209-300`)
  have no reader anywhere.

## Minimal design

1. Runtime: the visit look-back lists the open questions this visit asked or touched (entry id + title) and invites a
   diary block with `resolves=<id>` and an `evidence=` line naming the turn (a ```resolve``` election beside
   ```realize```, same DIARY_WRITE); visit resolutions passed into `build_reflection_prompt`; act_only meta carries
   `resolves` + `resolves_status`; `diary_notice` emits kind `question_resolved` {graph_id, title} when the status is
   `resolved_open_question`.
2. Gateway: `close_notices` emits `question_resolved` from the close's DIARY_WRITE rows with that status; the operator
   diary display carries `resolves`.
3. Memory: the replay diary block carries `resolves` (a key, like `entry_id`).
4. Kit: `ChatNoticeKind` + badge "question resolved: <title>" (panel-chat 0.9.14).
5. App: the badge opens the question; the Questions lens and record-detail words use `resolves`, not closure; the card
   needs no change (memory folds the resolution into "Questions he resolved").

## Owners

Runtime + gateway halves: framework seat. Memory, kit, app halves: Entity/memory seat (after the 0.12.0 tags; Entity
0.12.1 + panel-chat 0.9.14 + memory 0.5.2).
