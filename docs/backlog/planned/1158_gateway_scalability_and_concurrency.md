# 1158 — Gateway scalability and concurrency: investigate, measure, fix

> Package: AbstractGateway (work pools, SSE streams, run listing/index, TTS streams, model host admission), AbstractRuntime (run store reads), AbstractUIC (shared browser connection, root 1140), AbstractCore (model host inflight)
> Type: investigation + engineering track
> Created: 2026-11-08
> Priority: HIGH (operator 2026-11-08: "your tests reveal some concurrency / scalability issues; create a planned backlog item to investigate scalability and improve it")
> Labels: scalability, concurrency, performance, gateway, observability

## What tonight showed (2026-11-08, one MacBook Pro, 128 GB, the operator's live gateway on :8080)

Two automated review workers (Playwright Chromium + WebKit at three viewports; WebKit read-aloud loops) plus a gate run
and several other sessions' tests hit the live gateway while the model host held 19.6 GB and ~68 GB sat wired (Metal);
swap reached 12–15 of 16 GB. Observed, all from read-only probes and logs:

- `GET /api/health` answered in 6–90 ms throughout, but `GET /api/gateway/runs?status=running` took 3–16 s and then
  did not answer within 60 s (01:10) from a 3-hour-old process; a fresh process answered the same in 0.15 s.
- The `watchers` work pool (16 threads; TTS stream setup, app launch/stop, network probes, engine installers) sat at
  **38 queued jobs** across samples; every route that uses it waited. Consoles showed "Loading conversations…" and
  "Discovering your workflows…" for 12–90 s; Code's permission click earlier in the day hung behind 6 browser
  connections (root 1140).
- `voice/tts watchdog fired: synthesis exceeded 300s` at 01:35 (and 25 s at 00:23): the voice engine competing with the
  LLM in one model host under swap. The model host reported `inflight: 4` and no admission control.
- Browser side: 34 established connections to :8080 from four processes; each Code tab holds three long-lived streams.
- The tray's attention badge filled with the failures; the operator asked "what's going on with the gateway? this
  should only rarely happen and only under heavy load".

Related items already filed: gateway 1156 (run listing fast under load; pool observability), root 1140 (one shared
browser connection per origin), root 1152 (inference resource orchestration), gateway 1149 (keep-awake setting).

## Scope

### Investigate (first, 1–2 days)

1. **A load harness on a hermetic gateway** (never :8080): N browser tabs × M apps (Code, Observer, Entity) × K TTS
   streams × automations ticking every 2 min, against a copied run store of ~3,000 runs; record p50/p99 of the list
   routes, stream setup time, watcher queue depth, RSS over 6 h, and the first failure mode as N, M, K grow.
2. **Pool accounting**: which jobs hold `watchers` threads and for how long (TTS setup, app launches, probes); which
   routes block the event loop (the 30 s watchdog) or hold locks across I/O; where the run listing spends its time
   (per-request scans vs an index).
3. **Streams**: how many SSE/fetch streams one tab opens per app and what each costs server-side (a thread? a task?);
   whether `me/events/stream` is counted by the SSE semaphore (it is not today).
4. **Model host admission**: what happens when TTS and LLM requests overlap on one GPU; where the 300 s watchdog
   leaves the stream, the run and the user.

### Improve (then, sized from the measurements)

- Blocking work off the shared pool: TTS setup and long probes on their own bounded executors with backpressure and a
  stated queue limit; a job that waits for a GPU never holds a general-purpose thread.
- Streams as asyncio tasks with per-principal and per-origin caps; the root 1140 shared connection on the client side.
- The run listing reads an index (bounded by `limit`), never the store; the index is maintained at write time.
- Admission at the model host: one generation per engine with a short queue, TTS and LLM interleaved deliberately,
  and the queue depth shown in health (root 1152 decides the cross-engine design; this item covers the local host).
- Observability: `GET /api/health` reports per-pool queued/running with job kinds and ages, open streams per principal,
  run-store size, RSS and event-loop lag; the console's System page shows the same so an operator can see "heavy
  load" before the badge does.
- A documented scalability target (e.g. 10 tabs, 3 apps, 2 TTS streams, 20 automations on one Mac) and the harness
  run in the gate's `perf` job at a fraction of it.

### Out of scope

- Multi-machine gateways; a scheduler across remote engines (1152); the Apple apps.

## Acceptance

- [ ] The harness exists, runs on a hermetic gateway, and its numbers for today's main are recorded in the item.
- [ ] At the target load, list routes stay under 300 ms p99, no route blocks the loop, `watchers` never queues more
      than its size, RSS is flat over 6 h, and a stalled TTS stream ends within its watchdog without holding a thread.
- [ ] Health shows the pool/stream/loop figures; the perf job runs the harness at a fraction of the target.
