# 0952 — Configure npm trusted publishing for `@abstractframework/monitor-memory` (operator action)

> Package: abstractuic (npm)
> Type: task
> Created: 2026-09-28
> Priority: normal
> Completed: 2026-09-28
> Labels: operator-action, npm, release, trusted-publishing

## Summary

OPERATOR ACTION: the AbstractUIC v0.1.14 release published ui-kit 0.1.14, panel-chat 0.1.19, app-server 0.1.11 and monitor-gpu 0.1.10, but `@abstractframework/monitor-memory` 0.1.10 failed with npm E404 on PUT: npm has no trusted publisher configured for that package. The package stays at 0.1.9 on npm. No app depends on it through npm, so the wave is not blocked.

## Why

Ledger: "monitor-memory 0.1.10 FAILED (npm E404 on PUT = no trusted publisher for that package) -> operator action".

## Current code reality (2026-09-28)

- npm shows `@abstractframework/monitor-memory@0.1.9` as latest; the repository's `release.yml` skips already-published packages on a re-run.

## Scope

### In scope

- On npmjs.com, add a trusted publisher for `@abstractframework/monitor-memory`: repository `lpalbou/AbstractUIC`, workflow `release.yml`, environment `npm`.
- Re-run the AbstractUIC release workflow for the next tag (it skips published packages), or publish 0.1.10 once with an OTP.

### Out of scope

- Any code change.

## Acceptance criteria

- [x] `npm view @abstractframework/monitor-memory version` returns the version of the latest AbstractUIC release.

## Validation

`npm view @abstractframework/monitor-memory@0.1.10 version`.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.

## Completion report (2026-09-28)

- The operator added the trusted publisher on npmjs.com (repository `lpalbou/AbstractUIC`, workflow `release.yml`, environment `npm`, permissions npm publish + stage publish).
- Re-ran the failed job of the AbstractUIC `v0.1.15` release run (36389121418); it skipped the already-published packages and published `@abstractframework/monitor-memory@0.1.10` with provenance.
- Validation: `npm view @abstractframework/monitor-memory versions` ends with `"0.1.9","0.1.10"`.
- Not a duplicate of `@abstractframework/monitor-active-memory` (checked at the operator's request): monitor-memory is the dependency-free host RAM + GPU meter custom element (`<monitor-memory>`, polls `GET /api/gateway/host/metrics/memory`; embedded by the gateway console); monitor-active-memory is the React/ReactFlow Knowledge-Graph + Active Memory explorer used by Flow/Observer/Code. Only the names are close.
