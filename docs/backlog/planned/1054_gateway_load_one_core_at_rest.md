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

## In flight (2026-10-26 night)
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
