# 1060 — Standing duty: gateway security, resilience under load and failure, and a latency budget

> Package: root (recurrent), abstractgateway first, abstractruntime, every package on the request path
> Type: recurrent / operating policy
> Created: 2026-10-27
> Priority: P1
> Labels: security, resilience, performance, latency, incidents, isolation

## Summary

A persistent, recurring charge for every wave of work: the gateway must be (a) very secure and (b) resilient
to failures and heavy load, and the whole foundation must keep latency as small as the abstractions allow.
Every release wave checks this item; findings become dated gateway items.

## Why

Operator, 2026-10-27: "having abstractions is great, but it has a cost and we need to ensure it remains as
small as possible, especially in terms of latency (any undesirable pause in executing a workflow, retrieving
data or discussions from the ledger/runtime, the right context or accessing the memory graph). we have had a
couple of issues with the gateway being unavailable, overloaded or restarting; this needs further
investigation and any such incidents should be logged, so we can understand/benchmark/report the problems.
the openai endpoint launchable by the framework should probably be spawned as a separate service
(controllable by gateway) so that if it fails (e.g. ddos), it doesn't crash the gateway. consider gateway
security and performance/resilience to heavy load a persistent recurring task."

## The duty, each wave

1. **Incidents are recorded, always.** Unavailability, overload, restarts and watchdog exits land in one
   incident ledger with cause, duration, load at the time and the stack when known; the console and
   `abstractgateway status` show the last incidents. Gateway item 0943.
2. **Blast-radius isolation.** The OpenAI-compatible endpoint (`/v1`, `core_endpoint.py`) and other
   public-facing listeners run as separately supervised processes the gateway starts, watches and restarts;
   their failure never takes the gateway down. Gateway item 0944.
3. **Load and failure drills before release:** a reproducible load test (concurrent runs, SSE subscribers,
   TTS streams, uploads at the caps) with p50/p95 latency and error rates recorded in the release report;
   regressions block the release.
4. **Latency budget:** every new abstraction on the request path (facade, projection, index, cache) ships
   with a before/after measurement; a pause a person can feel in a workflow step, a ledger read or a memory
   lookup is a bug, not a cost of architecture.
5. **Security review** of every new route and listener: authorization contract test
   (`test_gateway_route_authorization_contract.py`), upload caps, signed ingress, secrets never in logs,
   secret-scanning false positives avoided by construction (test vectors assembled at runtime).

## Links

- Existing: `loop_watchdog.py` (incident files `<data dir>/incidents/watchdog-*.json`), `tray_supervisor.py`,
  split mode (`serve --no-runner` + `abstractgateway runner`), `security/`, runtime reliability track
  (`abstractruntime/docs/backlog/planned/runtime_systemic_reliability/`: 0045 crash replay, 0052 event-loop
  tripwire, 0054 health counters), root 1054 (gateway load, one Core at rest).
- Related: 0993 (replay view cache), 1058, 1059.
