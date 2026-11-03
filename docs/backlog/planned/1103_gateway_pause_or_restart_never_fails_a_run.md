# 1103 — A gateway pause or restart never fails a run: it suspends and resumes

> Package: AbstractGateway, AbstractRuntime
> Type: task
> Created: 2026-11-03
> Priority: high
> Labels: runs, restart, ledger, release-blocker

## Summary

Stopping or restarting the gateway (launchd kickstart, tray Restart, upgrade) must leave every in-flight run suspended at its last durable step and resume it on boot; an interrupted model call is re-issued; no retry is consumed; no failure notification. Occurrence 24 of 2026-11-02 (run 973e7ef1) was recorded as failed because a polite restart made the model host exit 0 and the attempt was classified as a failure (`untracked/council-2026-11-02/automation-failure-973e7ef1.md`). Release blocker for abstractgateway 0.20.0 / AbstractRuntime 0.17.0.

## Why

Operator 2026-11-03: "we can pause or interrupt the gateway, it doesn't mean in any way that a run has failed, just that it is suspended and will resume with the gateway. it was already the case before, i fear opus did something very wrong here as indeed i started to see 'failed' sessions for no reason recently … normally the absence of a gateway prevents the ledger (runtime) to continue its actions.. so nothing 'fails', it just doesn't execute the next steps anymore." ADR 0002 §7 wording to amend accordingly.

## Scope

### In scope

- Find the commit that changed suspend-and-resume into failed (architect report `untracked/release-2026-11-03/architect-restart-suspend.md`); reproduce on scratch gateways for current main and the last released matrix (`repro-restart-suspend.md`).
- Fix at the owning layer (runtime shutdown/host-exit classification, gateway lifecycle, attention) with tests that go red today; `attention.py` writing "completed" as an error text (P4).
- Watch/iPhone/web card copy for a suspended run ("paused with the gateway", not failed).

### Out of scope

- A new restart policy UI; reclassifying historical ledgers (report the count, decide separately).

## Acceptance criteria

- [ ] SIGTERM mid-step → ledger shows the run suspended, boot resumes it, final status completed; no retry consumed; no notification; test red on main.
- [ ] Automation occurrence through the same path: not failed, no attention item.

## Receipts

- Investigation running 2026-11-03 03:05 (architect + Fable repro).
