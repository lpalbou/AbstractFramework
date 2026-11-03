# 1104 — Decision capability (output=decision) works end to end from AbstractCore to AbstractFlow

> Package: AbstractCore
> Type: task
> Created: 2026-11-03
> Priority: high
> Labels: decision, jev, kev, e2e
> Status: Completed
> Completed: 2026-11-03 (recorded; shipped in abstractcore 2.33.0)

## Summary

Verify with real calls that the decision modality (Kev/Lev/Laya local engines, hosted Jev via the `typesafe` provider, `POST /v1/decisions`) works at every level — abstractcore generate, gateway route, AbstractRuntime node, AbstractFlow node in a saved and run flow — and fix every AbstractCore defect found. Background: `docs/decision-models.md`, backlog 0877 (AbstractCore), memory of 2026-11-01.

## Why

Operator 2026-11-03: "one of the key modification of abstractcore recently was to introduce jev-like 'decision' capabilities. when we tested it, up to abstractflow, it was working. so make sure it is working end to end, up to abstractflow. and fix any issues you might find at the level of abstractcore".

## Scope

### In scope

- Pass/fail table per level with real request/response (key redacted); Core fixes with tests + changelog fragment.
- Issues above Core reported with file:line and filed per repo.

### Out of scope

- New engines or quantizations; publishing weights.

## Acceptance criteria

- [x] Local Kev and hosted Jev decisions succeed through generate, `/v1/decisions`, the runtime node and a Flow run; `/v1/models` carries `capabilities` + `decision.endpoint`; chat on a decision model → 400 decision_model.

## Receipts

- W4 running 2026-11-03 03:10.

## Completion report (2026-11-03)

- AbstractCore PR #41 (`fix/decision-e2e`, merged 2026-11-03 as `57081f51`, in tag `v2.33.0`).
- Two Core defects found by real calls and fixed: hosted decision models were listed as text models under every
  filter; a `typesafe` + `jev-latest` decision default ran the most recently loaded local Kev instead.
- Per-level proof in the PR body (scratch HOME and gateway, Kev-0.8B MLX 8-bit + hosted Jev): Core
  `generate(output="decision")`; gateway `POST /v1/decisions`, `/v1/models` decision rows, chat on a decision
  model -> 400 `decision_model`; AbstractRuntime `decision-triage.json` run COMPLETED; AbstractFlow Decision node
  saved, loaded and run from the Run dialog.
- Tests: `tests/server/test_decisions_endpoint.py`, `tests/decision/test_decision_generate.py` (each red with its fix
  removed, per the PR).
