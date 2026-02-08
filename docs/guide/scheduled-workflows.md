# Scheduled Workflows (Durable Jobs)

This guide explains how scheduled workflows work when using `abstractgateway` + `abstractruntime`.

## What "scheduled workflows" means in AbstractFramework

A scheduled workflow is a durable parent run that triggers a target workflow as child runs over time.

Key properties:
- Durable: schedule state is persisted and survives restarts.
- Replay-first observability: you can attach later and reconstruct what happened from the ledger.
- Single authority: the gateway host owns ticking/resuming.

## Who "runs" the schedule (and why it stops when processes stop)

AbstractRuntime is a library. It can represent "wait until time X", but it does not create OS timers or wake itself up.

Something must keep calling `Runtime.tick(...)` to advance runs. In the gateway topology, the gateway runner loop:
- ticks running runs
- resumes due waits (including "wait until" for scheduled jobs)
- applies durable commands (pause/resume/cancel/emit_event)

If you stop the gateway process, nothing ticks. When it restarts, due waits resume on the next poll cycle.

## Creating a scheduled run (Gateway HTTP API)

Endpoint: `POST /api/gateway/runs/schedule`

Example: start now, repeat every 20 minutes forever:

```bash
curl -sS -X POST "http://127.0.0.1:8080/api/gateway/runs/schedule" \
  -H "Authorization: Bearer $ABSTRACTGATEWAY_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bundle_id": "my-bundle",
    "flow_id": "root",
    "input_data": { "prompt": "write my report" },
    "start_at": "now",
    "interval": "20m",
    "share_context": true
  }'
```

Example: start at a specific time (UTC ISO), run 10 times:

```bash
curl -sS -X POST "http://127.0.0.1:8080/api/gateway/runs/schedule" \
  -H "Authorization: Bearer $ABSTRACTGATEWAY_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bundle_id": "my-bundle",
    "flow_id": "root",
    "input_data": { "prompt": "write my report" },
    "start_at": "2026-01-15T15:06:00+00:00",
    "interval": "20m",
    "repeat_count": 10
  }'
```

Notes:
- Intervals are relative (drift is expected if runs take time or the gateway is down).
- If a child run blocks on a durable wait (ask-user, approvals, wait-event), the schedule blocks too (it waits for the
  child to finish).
- Durable execution is not transactional I/O (at-least-once semantics). Prefer idempotent outputs for scheduled jobs.

## Controlling scheduled runs

Scheduled runs are normal durable runs:
- Pause the parent run to pause the schedule.
- Cancel the parent run to stop the schedule and cancel active children.

This is done via `POST /api/gateway/commands`.

