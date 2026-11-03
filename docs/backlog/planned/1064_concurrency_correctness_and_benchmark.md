# 1064 — Concurrency correctness and benchmark: many sessions, many users, no cross-talk, measured

> Package: abstractgateway (scenarios, harness, benchmark; its 0952), abstractruntime (ledger `seq`, runner, session tool policy), every store backend (JSONL/file, SQLite)
> Type: test + benchmark
> Created: 2026-10-28
> Priority: high
> Labels: concurrency, isolation, ledger, sse, tool-policy, performance, latency, benchmark
> Links: recurrent [1060](../recurrent/1060_gateway_security_resilience_and_latency_standing_duty.md) (security, resilience and latency standing duty), [0993](0993_one_ledger_replay_many_views.md), [1061](1061_session_tool_policy_no_approval_flash.md)

## Summary

Prove, with a real gateway process and scripted clients, that (a) one user running several sessions at
once and (b) several users each running several sessions get every turn, wait, answer and stream event
routed to the right session, with no cross-talk, an intact ledger (`seq` gap-free and monotonic per run),
complete SSE delivery and tool-policy isolation; and give the framework a reproducible benchmark
(p50/p95/p99 latency, throughput, memory) that drives the optimisation of the gateway, the runtime, the
communication layer and the stores.

## Why

Operator, 2026-10-28: concurrency correctness for one user with several sessions and several users with
several sessions, with a benchmark to drive optimisation. 1060 (operator, 2026-10-27): "we have had a
couple of issues with the gateway being unavailable, overloaded or restarting". Every existing test
exercises one of these properties in isolation; none drives N sessions x M users through the real
HTTP/SSE surface and checks them together.

## Current understanding (what exists, origin/main 2026-10-28)

- `abstractgateway/tests/test_r13_gateway_concurrency.py` (R13.1, the 2026-10-04 watchdog incident): a
  REAL uvicorn server with fake CPU-bound engines; health stays fast under generation plus concurrent
  read-aloud; admission bound; TTFA. The starting harness (real server, real client), single user.
- `tests/test_resume_concurrent_same_wait.py`: two answers to one wait.
- Isolation, one request at a time: `test_gateway_principal_isolation_matrix.py`,
  `test_gateway_session_history_isolation.py`, `test_gateway_attachment_session_isolation.py`,
  `test_automations_plane_isolation.py`, `test_gateway_workflow_ownership_isolation.py`.
- Streams: `test_gateway_ledger_stream_cursoring.py`, `..._event_driven.py`, `..._terminal_latency.py`,
  `test_gateway_live_delta_stream.py`, `test_events_stream_*`.
- Benchmarks: `scripts/bench_replay_view.py` (+ `_bench_replay_server.py`: a gateway per store backend,
  a seeded ~3,000-record delegated run tree, server CPU via psutil, bytes on the wire; 0993);
  `scripts/perf/bench_gateway.sh` + `bench_driver.py` (hermetic clone, sequential probes, idle CPU/RSS/GC,
  `--fail-p99` gates used by `scripts/perf/ci.sh`). Both are single-client.

## Chosen route

1. **Scenario harness** (gateway `tests/concurrency/`, real server per backend, a fake deterministic
   LLM with controllable latency and tool calls): users U1..Um, each with sessions S1..Sn started at
   once, each turn carrying a per-session nonce that the fake model echoes, a tool call that waits for
   approval in some sessions and a session tool policy (`approve all`) in others.
2. **Assertions** per run and session: every reply contains only its own nonce (no cross-talk);
   answers to waits resume the right run (a wrong-session answer is refused); ledger `seq` gap-free and
   strictly increasing per run, no duplicate step ids; every SSE subscriber (ledger, view, `/me/events`)
   receives every record once, in order, across a reconnect with `Last-Event-ID`; a session's tool
   policy never applies to another session or user; a user never lists, reads or streams another
   user's run (403/404); health p99 stays under its bound during the burst.
3. **Benchmark** (`scripts/perf/bench_concurrency.py`, same seeded fixtures): matrix 1x1, 1x8, 4x4,
   16x4 (users x sessions) on JSONL and SQLite; reports p50/p95/p99 turn latency, time to first
   SSE event, throughput (turns/s, records/s), server CPU and RSS, open threads/fds, store lock waits;
   JSON output with the commit ids, comparable across runs; a CI smoke size with `--fail-p99` gates
   (same convention as `bench_driver.py`) and a full size run by hand before each release wave (1060).
4. Findings become dated gateway/runtime items; this item tracks the harness and the baseline.

## Open decisions

- D1: CI budget: the smoke size per PR (proposed 1x4 + 2x2, under 2 min) vs nightly full size.
- D2: target numbers (proposed starting gates: health p99 < 50 ms under load; turn overhead p95 over
  the fake model's latency < 150 ms at 4x4) to be set from the first baseline, not guessed.

## Scope

### In scope

- The harness, the assertions above on both store backends, the benchmark script and its baseline report.

### Out of scope

- Real-model load (separate, by hand); multi-process / multi-host gateways (later item if needed).

## Acceptance criteria

- [ ] Gateway 0952: scenario suite green on JSONL and SQLite; each assertion shown red by a deliberate fault (wrong-session routing, dropped SSE record, policy leak).
- [ ] Benchmark baseline committed (JSON + summary) with commit ids; CI smoke gate wired.
- [ ] 1060's next wave check cites this baseline.
