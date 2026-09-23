# 008-abstractagent: [FEATURE] Adopt the headless fleet bridge as abstractagent's ready-to-use collaborative agent

> Package: abstractagent
> Type: feature
> Created: 2026-07-14 05:55:55 +0200
> Priority: P2
> Labels:

## Summary
Move scripts/headless_fleet_bridge.py's resident contract (hub reception, task dispatch, steer forwarding, approval policy, artifact publication, driver-owned delivery) into abstractagent as a first-class documented entry point for swarm seats.

## Why

Operator (2026-07-13 19:47): "i may like the idea of a very lightweight skilled agent capable to work in a swarm and leverage the agora protocol. i even wonder then, if that should not be owned by abstractagent, as a simple, ready-to-go ready-to-use collaborative agent?" Adversary verdict (agency-run fable5): ADOPT.

## Scope

### In scope

- Bridge entry point (CLI or module) inside abstractagent with tests
- Thin shim or pointer left at scripts/headless_fleet_bridge.py
- docs/guide/headless-swarm.md updated to name the adopted owner

### Out of scope

- Changing abstractcode's serve protocol (consumer contract stays frozen)
- Gateway-hosted resident shape (separate, existing lane)

## Acceptance criteria

- [ ] 3-seat swarm bench passes against the adopted entry point
- [ ] agent seat SHIP post with evidence; agency re-runs the bench as verifier

## Receipts

- Adversary verdict + dispatch: commons (fleet adoption lane, 2026-07-13)
- Bench evidence: plan_proof_out/promoted-bench-20260714T022221Z/ (8/9 green)
