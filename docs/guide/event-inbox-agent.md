# Event-inbox resident agent — an open channel anyone can interleave into

This guide covers `abstractflow/examples/flows/event-inbox-react-agent.json`
and the gateway's durable event delivery. Together they implement a **resident
ReAct agent driven by an open event channel**: not agora-specific, not
Telegram-specific — any producer that can POST a gateway command can drop an
event into the agent's mailbox, *including while the agent is mid-burst*, and
the event folds into the very next loop cycle.

## Why this design

The first cut of hub-connected agents (see `agora-workflow-agent.md`) pulled
its inbox from one specific hub at loop start. That works, but couples the
agent to a transport and only reads mail when the loop decides to. The general
primitive underneath is:

> a durable mailbox with a name, drained at every loop boundary, that anyone
> can post into at any time — plus a doorbell that wakes the agent when it
> sleeps.

With that in place, agora, Telegram, cron, a human at a terminal, or another
agent are all just producers. And crucially, **you can steer an agent while it
works** — post a correction during a burst and the next cycle sees it, without
waiting for the run to finish or cancelling it. (The Agent-node ReAct loop
already has this property internally via `inject_guidance` and its
`_runtime.inbox`; this brings the same durable-mailbox pattern to hand-built
workflow agents with a public, structured event envelope.)

## The pieces

### 1. Durable event delivery (AbstractGateway)

`emit_event` was wake-only: it resumed runs *currently parked* on the matching
wait key; events sent while a listener was busy were silently dropped
(`delivered: 0`). The gateway command now accepts **`durable: true`**:

- parked listeners are resumed (unchanged), and
- the envelope is appended to the **`events_inbox` run var** of every
  non-terminal run that *declares the mailbox*: `events_mailbox` var equal to
  the event name (string, or list of names to listen on several channels).

Envelopes carry a per-run monotonic `seq`, so readers drain with a cursor —
append-only on the runner side, cursor-only on the reader side, no
read-then-clear race. The inbox is capped (500; oldest dropped with an
`events_inbox_dropped` counter). Same concurrency posture as
`inject_guidance`: best-effort append on the runner thread.

### 2. The resident flow (AbstractFlow example)

```text
on_flow_start (mailbox, task, tools, max_burst_cycles)
  └─ declare events_mailbox = <mailbox>   ← makes durable delivery target this run
  └─ while not stopped:
       DRAIN (code node): events with seq > cursor → mode
         ├─ park  (no mail, no burst)  → wait_event on evt:global:global:<mailbox>
         ├─ work  (fresh mail OR burst in progress) → one ReAct cycle:
         │        prompt = task + NEW EVENTS + burst trace → llm_call
         │          ├─ tool_calls → execute → append trace → next iteration re-drains
         │          └─ plain text → burst report (answer_user) → back toward park
         ├─ flush (burst budget exhausted) → #FALLBACK report → park
         └─ stop  (payload kind == "stop") → exit loop → flow ends
```

The load-bearing property: **every cycle starts with a drain**. Events that
arrive mid-burst are queued durably by the gateway and appear under
`NEW EVENTS` in the next cycle's prompt — the system prompt tells the model to
read them first because they may redirect the work.

When idle the run parks on `wait_event` — a durable, zero-cost wait that
survives gateway restarts. The wait key is `evt:global:global:<mailbox>`
(global scope), so producers need to know only the mailbox name — no run ids,
no session ids.

### 3. The producer contract

Anyone posts through the gateway command endpoint:

```bash
curl -X POST $GATEWAY/api/gateway/commands -H "Content-Type: application/json" -d '{
  "command_id": "'$(uuidgen)'",
  "run_id": "my-room",
  "type": "emit_event",
  "payload": {
    "name": "my-room",
    "scope": "global",
    "durable": true,
    "payload": {"kind": "message", "from": "laurent", "priority": "high",
                 "body": "Drop what you are doing and check the failing build first."}
  }
}'
```

- `name` = the mailbox (the open channel). `run_id` on the command is just a
  routing string for emit_event; targeting is by mailbox declaration.
- `payload.payload` is the event body the agent sees: `kind` (`message` |
  `stop` | anything you define), `from`, `priority`, `body`.
- `{"kind": "stop"}` ends the resident gracefully.
- Without `durable: true` an emit only wakes a parked resident (busy runs
  won't see it) — producers for this flow should always set it.

A bridge makes any hub a producer: e.g. an agora subscriber forwarding
envelopes (`agora watch --exec 'curl ...'` or a small `AgentRunner`) turns
agora traffic into channel events, priorities passed through in the payload.

## Verified behavior

Scripted (`abstractruntime/tests/test_visualflow_event_inbox_react_agent.py`,
`abstractgateway/tests/test_runner_emit_event_durable.py`): park key shape,
wake + first-cycle delivery, **mid-burst interleave** (event appended between
ticks appears in the next cycle's prompt and not earlier), cursor advance,
burst reset, stop control, budget-exhaustion flush with `#FALLBACK`, per-run
seq monotonicity, list-declared mailboxes, cap accounting, non-durable emits
unchanged.

Live (`scripts/event_inbox_flow_smoke.py`, real GatewayRunner + LMStudio
`qwen3.5-4b`): resident parked; producer 1 posted a task (write 7*6 to a
file — done: `42`); producer 2 posted a second task *while the first burst ran*
and the resident wrote `Paris is the capital of France.` in the same burst;
re-parked; stop event completed the run.

## Relation to the agora ReAct example

`agora-react-agent.json` remains a valid pattern when you want the agent
itself to own hub-side triage with agora's native signals (escalation,
obligations, acks). The event-inbox resident is the more general shape:
transport-agnostic, interleavable, and idle-cheap. For agora specifically, the
long-term convergence is a thin agora→gateway producer bridging envelopes into
the channel, with hub signals mapped into the event payload.
