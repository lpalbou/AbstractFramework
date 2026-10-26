# 1054 — The gateway burns a core at rest: scans, pile-ups and the one-process model

> Package: gateway, runtime
> Type: performance / architecture
> Created: 2026-10-26 01:40:00 +0200
> Priority: P0
> Labels: performance, concurrency, runner, artifacts, automations, tray

## Summary

On the operator's gateway (11,500 runs, 106k artifacts, 13 automations, 23 mail watchers, a 27B model in-process) the serve process burns ~100% of a core with nothing happening, trivial requests take seconds, heavy ones minutes, the watchdog restarted it twice in one night, the tray shows "unreachable" and the watch sticks on "Connecting…". Investigation with thread samples and the watchdog dumps: `untracked/gateway-load-2026-10-26.md` (evidence under `untracked/gateway-load-scratch/`). The immediate fixes are in flight (below); the structural change is the planned work here.

## Findings (2026-10-26)

| Cause | Where | Cost |
|---|---|---|
| `GET /sessions/{id}/artifacts` reads all 105,979 artifacts on the event loop | gateway `routes/gateway.py:6303-6309`, `:11116` | both watchdog restarts; the watch's "Connecting…" |
| `GET /automations` walks each automation's whole history (942 runs, 192 MB, every past prompt) | `automations/attention.py:216-238`, `automations/service.py:236-249`, `routes/automations.py:387/427` | 10 s to > 240 s; 14 copies piled up (tray 10 s timeout + retry, no cancel) |
| Runner change check reads all 11,500 run files every 0.5 s | `runner.py:214-241`, `:1653` | 3–12 s per pass, never catches up; most of the kernel time |
| Mail check re-reads all automations + 13 ledgers every 15 s | `mail/notifications.py:1051-1121` | steady background |
| `_active_consumers` full pass per feed/mail poll | runtime `email/automations.py:70-88` | ~5–7% of a core (fixed: runtime 4cb816b, consumer index) |
| One process: API + 5 runners + 23 watchers + the model on one GIL; 408 `async def` routes, some doing file work on the loop; one 22-thread pool for 236 call sites | `service.py`, `routes/*` | a 1 ms request waits behind a 240 s one |

## Done (2026-10-26 night, rounds 1–2; live since the 03:33 restart)
- Round 1: session artifacts by session through the index, off-loop (2,148 ms → 16 ms; gateway c51f6c0f, runtime 22e6047); runner change token instead of the 0.5 s directory scan (runtime 1dbd19b, gateway 22263c2e); mail check skips when unchanged (966 → 1.2 ms; runtime e517daa, gateway 8e3d2884); automations list from the waiting-runs index + ledger tail, single-flight + 3 s cache, tray back-off (2.4 s → 0.25 s cold / 20 ms warm; runtime 4d33890, gateway 73b6fe85); consumer index (runtime 4cb816b, gateway 77d0a463); clone fixture + `scripts/perf/bench_gateway.sh` + `--gc-tuning` (317f276d).
- Round 2: trusted in-memory run index (runtime 09d3b63; listing 110 ms → 0.3 ms, 77 s → 0.5 ms beside a busy thread), shipped in `verify` (shadow) mode by `serve --run-index` (f88c3d8e; counters in `/api/health` run_index); lockless service lookup (8ce6b488), pools by kind of work `--pool-light/heavy/watchers` (429dfcf5), sessions in memory (101c37b6); mail check index-only (640cf5ab), host-status caches (ae5325e9: tray polls 55 → 1.5 ms), on-loop scan routes off-loop with mtime caches (396f197c).
- Clone bench before → after rounds: artifacts 2.24 s → 3 ms, automations 1.04 s → 36 ms p99, `/runs` 172 → 35 ms p99, CPU at rest 24% → 11%; `/me` p99 under load 231 → 56 ms.
- Live (02:15–03:30, A/B/C only, under five benchmark loads): CPU p50 27%, `/me` 3 ms, connections 3 ms, artifacts 3 ms, automations 26 ms p50; no watchdog restart since 02:07.

## Incidents log (2026-10-26)
- 00:46, 01:17: `GET /sessions/{id}/artifacts` read all artifacts on the loop (fixed c51f6c0f).
- 02:05–02:07 (×2): `service.py:170 principal_service_cached` took `_service_lock` on the loop while a boot built services (fixed 8ce6b488).
- 04:07: the loop blocked in the import lock (`importlib._bootstrap` via `core_config.py:1159 _local_core_payload`, lazy abstractcore config imports) while serving `GET /me/events/stream`, with the machine at load 140 (round 3 worker 2: eager imports at boot + the miss path off the loop).
- Also: a draft test run hidden from listings raised a wait nobody could see (phantom phone/watch badge): fixed 0196916f, the stale run cancelled.

## Round 3 done (2026-10-26, 04:30–05:00; live since the 04:52 restart)
- Last on-loop reads to the pools and `promote` off-loop (39bcd30e); every service build off the loop, single-flight, `503 service_starting` + Retry-After on a miss that still reaches the loop; eager abstractcore imports + `/discovery/capabilities` and capability defaults off the loop after the 04:07 import-lock exit (93e1aa9c); CI load test `.github/workflows/perf.yml` + `scripts/perf/ci.sh` + `make_fixture.py` (10k runs / 100k artifacts / 50 automations; local run passed: /me 5 ms, connections 4 ms, artifacts 33 ms, runs 141 ms, automations 7 ms p99, CPU at rest 0.7%) (ca16cd98); health test for pools/run_index/gc_tuning.
- Split mode opt-in (runtime 980f4ab, gateway 0d49d0e7, 1cc40fb5): `abstractgateway runner --data-dir` hosts the model on a loopback port with a per-start secret (`<data>/split/model_host.json`), `/v1` forwarded with streaming, the API process loads no model (`set_default_model_warmup(False)`), event/mailbox indexes follow the other process within 2 s, watchers/outbox/push/bridges only in the runner, health rows carry mode/process. Before default: the API's own model uses (Ask on a run, summaries, sandbox, entity chat), the backlog exec runner placement, top-level `runner.mode`, `/me` during generation, installer support.
- Notify me channels end to end (runtime 9f913ae, gateway 10ce0f1b, flow c14f554) — found and fixed: every compiled Notify me / Publish node had failed with `unknown publish field(s): ['resume_to_node']`.
- Live window after the 04:52 restart (15 min, load 11–30, run index in verify = scan + shadow comparison): CPU p50 67% / p99 90%; `/me` 24 ms p50 / 308 ms p99; connections 8 ms / 0.79 s; artifacts 8 ms / 0.64 s; runs 0.48 s / 7.3 s; automations 26 ms; heartbeat 0.24 s; no non-200, no incident. Shadow: 261 compared, 0 mismatches, 40 reconciles, 0 repairs. The remaining CPU and the runs p99 are the verify-mode scans; the flip to `--run-index trusted` (after a clean night) is the next step toward the ≤5% target.

## Next (round 3)
- Trust the run index after a clean night in verify mode (flip the `--run-index` default), GC report check, the remaining on-loop reads (`promote`, `/runs` and `/host/*` `to_thread` sites), the service build itself off the loop.
- Split runner process opt-in after fixing the `/v1` double model and the cross-process event/mailbox indexes; the CI load test on the clone fixture; the SQLite index only if the in-memory index is not enough.

## In flight (2026-10-26 night) — superseded by the sections above
- Artifacts by session through the index, off-loop; `GET /runs` off-loop; runner change token instead of the directory scan; mail check skips when unchanged (worker A).
- Automations list from the waiting-runs index + latest occurrence, single-flight + short cache + cancel on disconnect; tray back-off and "slow to answer" state (worker B).
- Consumer index (done).

## Planned (structural)
1. SQLite run store as the default (`config.py:322` still `store_backend="file"`): 61 call sites scan every run file today; an index is the only fix that scales.
2. The runner (and the in-process model) in their own process by default (`serve --no-runner` + `abstractgateway runner` exist); the API process must never share the GIL with ticks and model calls.
3. Bounded pools per kind of work (API reads, scans, watchers) with cancel-on-disconnect; no file work inside `async def`.
4. A load test in CI: 10k runs / 100k artifacts fixture; `/me` < 50 ms p99 under the periodic jobs; CPU at rest < 5%.

## Acceptance criteria
- [ ] CPU at rest < 5% on the operator's data; `/me` < 50 ms; `/automations` < 300 ms; `/sessions/{id}/artifacts` < 50 ms; no watchdog restart in 24 h.
- [ ] The runner's idle pass reads no files.
- [ ] The load test runs in CI.

## References
- `untracked/gateway-load-2026-10-26.md`; 1049 (push, blocked by the watch's "Connecting…"); 0991 (admission/model residency), 0993 (session index).
