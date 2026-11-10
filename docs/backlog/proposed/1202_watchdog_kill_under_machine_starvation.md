# 1202 — The event-loop watchdog kills a healthy gateway when the whole machine is starved

> Package: AbstractGateway (loop_watchdog.py, af-stack supervisor), AbstractFramework root (scripts/ci_local.sh parallelism, 1192)
> Type: bug
> Status: proposed
> Created: 2026-11-10
> Priority: P2
> Labels: gateway, watchdog, self-healing, load

## Summary

2026-11-10 18:32 and 18:38 UTC, the live dev gateway was killed twice by its own event-loop watchdog (49 s stall, exit
-9; 31.5 s stall, exit 75) and respawned by the af-stack supervisor within 15 s each time, with no agent involved: the
self-healing works. But the gateway was not sick: the machine was (load average 292 on a 16-core Mac: the root gate's
16 parallel test jobs each running `uv` installs at >100 % CPU, fseventsd at 148 % from the venv churn, three Playwright
Chrome runs, 20 node and 24 python processes, 5,485 threads). The loop thread simply did not get scheduled. The kill
dropped the in-flight requests (two long replay SSE streams aged 230–245 s) for nothing.

## Scope

1. Load-aware grace: before exiting, the watchdog compares the loop lag with the system's run-queue (os.getloadavg()
   against the core count); when the whole machine is starved, log the incident and keep running (a kill cannot help),
   and only exit when the loop is blocked while the machine is not. Keep the dump either way.
2. The incident record already names the request the loop was serving (app_proxy body, replay/stream): keep it, add the
   load average and the thread count.
3. Root 1192: the gate's default `--jobs` cap, so a gate on a developer's machine never does this.

## Validation

A synthetic 40 s block of the loop at load 0 exits 75 (today's behaviour); the same block with a simulated load of
10 × cores logs the incident and keeps serving; the supervisor behaviour unchanged.
