# 0848 — The supervisor must not blame "model inference" for a blocked gateway

> Package: abstractframework (scripts/lib/af_supervisor.sh)
> Type: task
> Created: 2026-09-18
> Priority: normal
> Labels: operability, diagnosis-honesty

## Summary

When `/api/health` stops answering, `scripts/lib/af_supervisor.sh` tells the operator the
gateway is "likely busy (in-process model inference)" and points at `gateway.log`. On
2026-09-17 that message was wrong four times out of four: no run was executing in any of
the four windows, and the real cause was a workflow publish/promote rebuilding the host on
the gateway's event loop. The message sent the operator to a log that says nothing about
it, and it reads as "this is normal" for a state that is not.

## Why

Operator, after reading the banner and the four warnings:

> "investigate why the gateway becomes sometimes inaccessible"

The supervisor is the first thing anyone reads when the stack misbehaves. A confident wrong
diagnosis costs more than no diagnosis: it names a cause the operator cannot act on and
hides one they can (`runtime/audit_log.jsonl` records every mutating request with its
duration, which identified the cause in one query).

## Scope

### In scope

- Replace the asserted cause with what the supervisor actually knows: the port answers TCP
  but `/api/health` did not respond within the probe timeout for N probes.
- Point at the evidence that identifies the cause, in order:
  1. `runtime/audit_log.jsonl` — the slowest requests overlapping the window
     (`method`, `path`, `duration_ms`), which distinguishes a blocked event loop from a
     busy model;
  2. the run ledgers (`runtime/ledger_*.jsonl`) — whether any LLM call was in flight at all;
  3. `runtime/logs/gateway.log`.
- Name the two states the probe cannot tell apart, so the operator knows what to look for:
  event loop blocked (nothing is served, including health) vs worker/threadpool saturated
  (health answers, other routes stall — the class already documented at
  `routes/gateway.py::_discovery_max_concurrency`).
- Review the comment at `af_supervisor.sh:67` and the messages at `:542`/`:564` for the same
  assertion, and the "it was busy, not dead" recovery line (it asserts the same cause).
- Optional: have the probe record the failing window's slowest audit-log entry into
  `af-stack.log` so the diagnosis is in the log the operator is already reading.

### Out of scope

- Changing probe cadence, timeout, or the restart policy (`SUP_HANG_KILL` semantics stay).
- Fixing the underlying stall (abstractgateway 0846).

## Acceptance criteria

- [ ] No supervisor message asserts a cause the supervisor cannot observe.
- [ ] The unhealthy banner names the audit log and the ledgers, in that order, with a
      copy-pasteable command for each.
- [ ] Re-running the 2026-09-17 scenario (publish + promote against a gateway without the
      off-loop fix) produces a banner that leads to the publish within one command.

## Receipts

- `runtime/logs/af-stack.log` 2026-09-17 21:49–22:06, 2026-09-18 00:05–00:06.
- `runtime/audit_log.jsonl` same windows: publish 9–22 s, promote 27–65 s.
- Cross-package: abstractgateway `docs/backlog/planned/0846_publish_promote_must_not_rebuild_every_service.md`.
