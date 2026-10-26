# ADR-0041: No Hidden Effects After a Flow

On Flow End records the outcome; Notify nodes act; nothing acts after the end node.

## Status
Accepted (2026-10-26)

## Dates
- Proposed: 2026-10-26
- Accepted: 2026-10-26

## Context

A triggered flow's `On Flow End` had a `notify` pin (`{title, body}`). After the run, the
automation layer read it: a non-empty title raised an attention item (AbstractRuntime
`automations/controller.py` `complete_occurrence`, `notify_payload`), and the tray, the console,
the email outbox and push to the watch and the phone delivered it (AbstractGateway
`automation_attention.py`, `push/dispatcher.py`, `mail/notifications.py`), each delivery recorded
as `notification.sent|failed` in the person's event stream (`events_stream.py`). None of it was
on the canvas. The operator's complaint, 2026-10-26, on the Gmail judge ("Judge what arrived",
visualflow 8ee07990): "all of that is happening outside of the workflow, so I have no visibility
on what is happening after the execution of that workflow… how am I supposed to know what is that
notify? and whom it will notify and how? If it's in a workflow, I can see it, if not it's hidden
somewhere in code."

Flow already had the explicit form: **Notify me** (a Publish to channel preset: channel `me`,
Alert on), which raises the same kind of alert from a node the person can see.

## Decision

1. **On Flow End records the outcome; it is not an effect.** For a triggered flow it carries
   `response` (what Observer shows as the answer), `success` (the run's own verdict: false = the
   run failed, retried, then a failure item) and `note` (a short line of what happened and why,
   kept with the run, shown in Observer and in After the run). Nothing on it reaches a person.
2. **Every effect toward a person is an explicit node on the canvas.** Today: **Notify me** (the
   recipient is the person; the channel set is all of theirs) and **Publish to channel** with Alert
   on. The node says on its card whom it reaches and how ("You: tray · watch and phone ·
   Assistant"). Its inputs leave room for what comes next without a new node: a recipient that
   defaults to me (later another account: "Notify someone") and a channel set (later tray only,
   phone and watch only, email only, app channels).
3. **The implicit `notify` pin is a compatibility path.** Flows saved before keep it and it keeps
   working; the node says in words what it does ("Older flows: a title here notifies you on every
   channel you have: tray, watch and phone, email when on. Empty: nothing rings. New flows use
   Notify me."). Flow never adds it to a flow again: a new triggered flow is `On Flow Start →
   (empty) → On Flow End` with `response`, `success`, `note`, and the canvas note says "Add Notify
   me to reach yourself".
4. **Every run exposes what happened after it.** `GET /api/gateway/runs/{run_id}/after` answers,
   from records only: what arrived, when the run started and ended, its note, every alert the run
   or one of its sub-runs raised (On Flow End's notify of an older flow, the automation's failure
   item, Notify me, Publish with Alert on, a wait parked on the person, "Email me when done") or
   why nothing rang (`quiet_reason`), and each delivery with its channel, route (`push`, `stream`,
   `outbox`), device and time. Flow's run window and Observer's run card show it as **After the
   run**. A delivery that is not recorded with its channel does not exist for the person.

## Consequences

### Positive
- The person reads, on the canvas, everything a flow does to reach them; After the run shows what
  actually happened, delivery by delivery, and says why when nothing rang.
- One mechanism for reaching the person (a node), testable with "Run as if triggered" like any
  other step; the outcome record (`response`, `success`, `note`) is plain data.

### Negative
- Two paths coexist until older flows are rewritten: an older flow's `notify` still acts after the
  end node. Flow labels it; the operator rewrites their flows in Flow (ADR-0040: agents only draft).
- The channel choice and the recipient are designed but not built: the runtime's visual executor
  passes only `channel, type, title, body, subject, data, alert` to the gateway
  (`visualflow_compiler/visual/executor.py`), the gateway's published alert carries no channel
  set, and the tray, push and email deliverers do not filter by one. Flow shows the choices and
  offers "All my channels" only until those three seams exist. Email is not sent for Notify me
  today (the outbox mails automation results, failures and approvals).

### Neutral
- `success` keeps its retry and failure-item semantics; a failure item is the automation's own
  record of a failed run, not a flow effect, and After the run lists it.
- Interactive waits (an approval, a question) stay what they are: a step that parks the run on the
  person, visible on the canvas as that step; After the run lists them with their deliveries.

## Enforcement
- **Flow's new-flow template** (`abstractflow/src/utils/triggerPins.ts` `AUTOMATION_END_PINS`,
  `useFlow.createFlow`): a triggered flow is created and saved with `response`, `success`, `note`
  and never `notify`; tested in `src/components/automation/after_the_run.test.tsx` and
  `src/utils/trigger_pins.test.ts`.
- **Gateway test that every delivery is recorded with its channel**
  (`abstractgateway/tests/test_run_after.py::test_every_delivery_writer_names_its_channel`):
  `record_notification` refuses an unknown channel, and every writer in the gateway passes one;
  the same file checks that After the run answers each recorded delivery (tray and push on an
  occurrence, an approval on a sub-run, email by its outbox key) and `quiet_reason` for an empty
  title.
- Code review: a change that makes a flow, the runtime or the gateway reach a person after the end
  node (a new implicit pin, a post-run hook, a notifier reading run output) is refused; the effect
  becomes a node. A new deliverer records `notification.sent|failed` with its channel or it does
  not ship.
- Docs: `abstractflow/docs/web-editor.md` "What happens after On Flow End" lists every pin and node
  that reaches a person; a new one is added there in the same change.

## Validation
- `abstractgateway`: `tests/test_run_after.py` (6 tests).
- `abstractflow`: `src/components/automation/after_the_run.test.tsx` (On Flow End pins, the
  older notify pin's line, Notify me's words, After the run in every state).
- `abstractobserver`: `src/ui/after_the_run.test.tsx` (the section under a run's answer).
- Live, read-only, 2026-10-26: After the run for the Gmail watch occurrence `ce98246c` (4 new
  emails, "Suspicious credential emails received" from an older flow's notify, delivered to the
  console, the phone, the tray and the watch) and for run `7abde419` (an approval raised on its
  agent sub-run, delivered to the tray, the phone, the watch by push and email).

## Backlog links
- Originating: the operator's review of 2026-10-26 (Gmail judge, run `7abde419`).
- Related: 1046 (per-user event stream), 1049 (push for the watch and the phone), 1050 (events and
  attention follow-ups).
- Follow-up (not filed here): Notify me's channel set and recipient end to end (runtime executor
  pins, gateway published-alert channel set, tray/push/email filtering, email for Notify me).

## Related
- ADR-0040 (the operator edits and publishes library flows; agents draft), ADR-0039 (loading
  states).
- `abstractflow/docs/web-editor.md` (What happens after On Flow End, Publish),
  `abstractgateway/docs/api.md` (After the run).
