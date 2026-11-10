# 1187 — A mention becomes a job by the entity's own judgment; it reports back; a job button in the Entity app

> Package: AbstractRuntime (visit/mention lane: `take_as_job` tool, job queue, report-back), AbstractGateway (mention dispatch, job queue routes, back channel into the conversation), AbstractEntity (job button, badge action), AbstractUIC panel-chat (mention badge "leave as task"), AbstractCode / AbstractAssistant (consume the badge)
> Type: feature
> Status: planned
> Created: 2026-11-09
> Priority: P1
> Labels: entities, mentions, work, job-queue, free-will, next-wave

Agreed by the operator on 2026-11-09 21:30 ("agreed"). Scheduled right after the 0.14.0 release unless he moves it in.

## Summary

Today an entity gets a job only through the Console web "Work order" card or the TUI `/task` command; a mention in a
conversation is a question inside a visit, never work. The operator finds that "too complex and clanky" and wants:
"hey @castor work on this, @ephemeral control the network". Design, agreed:

1. **A mention stays a question by default.** The entity answers in the conversation (today's behaviour).
2. **The entity decides whether it is a job.** When mentioned, it reads the request and, if it cannot finish it in one
   answer, it says so in its reply and queues the request for itself with a tool (`take_as_job`). No text heuristics on
   our side (operator rule: never regex/NLP on model text): the entity's own judgment, in line with the free-will ruling
   (1186: "the entity should grow enough experience to decide").
3. **It reports back into the same conversation** when the job is done or when it is stuck (the guardian back channel
   noted in 1186), as a turn authored by the entity (author.kind entity), replayable from the ledger like every turn.
4. **An override for the guardian:** a small action on the mention badge, "leave as task", that queues the request
   as a job when the entity did not take it.
5. **A job button in the Entity app** for the same thing without a conversation (title + text → job queue), replacing
   the Console card and the TUI command as the only ways in (both stay).

## Visit versus work (confirmed semantics)

A visit is a conversation driven turn by turn by the visitor; each answer is bounded (tools within the turn, then the
entity waits). Work is a job in the entity's own loop: it iterates on a defined task across ticks until the job is done,
then returns to own time if still granted, else idle (contract v3, D1/D4). A job queued while idle starts the loop.

## Current code reality (2026-11-09)

- Mentions: `POST /api/gateway/sessions/{sid}/mentions` through the visit door; `author` on every turn; durable
  `mention_id`; mirrors into the visited entity's live visit. No job path.
- Jobs: `read_job_queue` (runtime), work orders (`work_order.md`, Console web card), tasks (`task_inbox.jsonl`, TUI
  `/task`), agent summons counted as work but not as queued jobs; person summons open a visit. Automations never reach
  an entity (kind reserved).
- The composer shows a mention as a chip above the text; inline mentions in free text are a separate item (kit, 19–27 h).

## Scope

- Runtime: a `take_as_job` tool available in the mention/visit lane (and own-time chat), writing to the same job queue
  the day gate reads; the job carries the conversation (session id, mention id, requester) so the report-back knows
  where to go; the report-back turn when the job completes or parks (stuck = a gated decision for the guardian).
- Gateway: dispatch the report-back into the originating conversation as an entity-authored turn (history, replay view,
  stream); `POST /entities/{name}/jobs` (title, text, from: conversation|button); mention badge action calls it.
- Entity app: job button; badge action "leave as task" in the shared mention badge (kit).
- Code / Assistant web: render the badge action (kit); nothing else.

## Non-goals

No heuristic deciding "this is a task"; no automatic job from every mention; no change to the visit semantics.

## Validation

- A mention the entity cannot finish in one answer: its reply says it takes the job; the job appears in its queue; the
  entity moves idle → work (or personal → work); when done, a turn authored by the entity appears in the originating
  conversation; the ledger replays it in every app.
- "Leave as task" on a badge queues the job without a new answer; the job button does the same from the Entity app.
- A mention the entity answers fully queues nothing. Tests red with each piece removed; one real-model E2E.

## Known limits shipped in AbstractGateway 0.21.0 (2026-11-10; this item absorbs them)

- A turn the session agent did not answer (`agent:"not_addressed"`) carries a `turn_id`, not a run id: `GET /runs/{id}/input_data`
  answers 404 for it. Decision 2026-11-10: the route stays run-only; clients (Assistant web first) read the turn row's
  own fields on reload. The job queue of this item gives such turns a real record.
- Messages sent mid-reply through steer/guidance reach the session agent regardless of mentions (they do not go through
  `/runs/start`). Out of scope for 0.21.0; the job dispatch of this item must cover that path too. Client rule shipped with it: while a
  reply is running, an entity-only message still steers the agent, so the clients hide the "stays out" hint then; and
  every client (Code web 4beb02f, Code TUI a602c4c, Assistant web 78a5eb6, Entity 8b86d00) refuses a skipped start that
  lacks `turn_id`: the gateway's `turn_id` on `agent:"not_addressed"` is a hard contract.

## Related

1111/1112 (mentions), 1138, 1175 (guardian rights), 1186 (guardian, back channel), inline mentions composer (kit item to
file), 1185.
