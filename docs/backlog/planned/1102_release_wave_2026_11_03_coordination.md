# 1102 — Release wave 2026-11-03: coordination record (swarm memory)

> Package: AbstractFramework
> Type: task
> Created: 2026-11-03
> Priority: high
> Labels: release, coordination, wave

## Summary

The persistent memory of the 2026-11-03 release wave (root 0.12.0 → 0.12.1): lanes, pull requests, gates and state. The coordinator (Fable) updates this item at every milestone; workers never merge or publish. Plan and audits live under `untracked/release-2026-11-03/` (CONTROL.md, ROADMAP.md, pr-triage.md, audit-*.md).

## Why

Operator 2026-11-03: "resume your entire work / release, be MORE CAREFUL"; "WORK WITH ADVERSARIAL SUB AGENT, ALWAYS"; "use $backlog items for your persistent memory to remember what is being done. make sure to update them". Every change goes through the `review`/`uxreview`/`architect` skills (AbstractSkill) before merge; nothing unrequested; no delete operations of any kind.

## Scope

### In scope

- Tier-0: abstractvoice 0.20.0 (AbstractVoice #26), abstractavatar 0.1.1 (AbstractAvatar #2); vision/memory/semantics skipped (docs-only).
- ui-kit 0.9.13 + panel-chat 0.8.0 → abstractcore 2.33.0 (#36 key probe, #37 GGUF cache, #38 typed ModelNotDownloadedError, 1105) → AbstractRuntime 0.17.0 (1107) → abstractagent 0.6.0 → abstractgateway 0.20.0 (#86, #52, #20, #88, #96, #39, #95 merged 4ee3a13; 1103 blocker; 1106) + console crate → apps (Code web 0.15.0 + CLI 0.14.0, Entity 0.11.0, Flow 0.14.0, Observer 0.12.0, Assistant desktop 0.18.0 + web 0.1.0 on npm) → root 0.12.1.
- Housekeeping: superseded PRs closed (Runtime #19, Gateway #87, Assistant #36, root #32 per AbstractRuntime ADR 0010); supervisor branch merged with `--restart-on-hang` (root #43); dependabot patch bumps.
- Local redeploy (one gateway restart with no runs in flight), TestFlight 0.17.0 (operator rejects stale run 39257198880), website preview (gated).

### Out of scope

- Publishing the website (operator pushes); council R8/R9 leftovers (1102 follow-up item after the wave).

## Acceptance criteria

- [ ] Every package above visible on its registry at the listed version; floors raised with pin tests; root 0.12.1 clean-venv install passes.
- [ ] `./scripts/status.sh`: every repo on main, clean, 0 ahead/0 behind; `./scripts/build.sh` passes.
- [ ] Final report under `untracked/release-2026-11-03/REPORT.md` with the show-me-your-work sections.

## Receipts

- 2026-11-03 02:50: Gateway #95 merged (4ee3a13) after Fable review (review-gateway-95.md).
- State log: untracked/release-2026-11-03/ROADMAP.md
