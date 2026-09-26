# 0909 — Default agent workflow: one gateway setting, three doors, resolved on the server, followed by every client

> Package: abstractgateway (`agents.default_workflow`, `/runs/start` `@default`); abstractcode (web + TUI); abstractassistant
> Type: feature
> Created: 2026-09-26
> Completed: 2026-09-26
> Priority: high
> Labels: gateway, workflows, settings, clients, mission-wave-2026-09-25, unreleased

## Summary

Completed record for track D of the 2026-09-25/26 wave (mission G1 plus the selector work in C1,
C2 and A; committed locally, not released; release staged, waiting for the operator's go). An admin
chooses, per agent interface, which workflow a new conversation runs; clients list "Gateway default
→ <name> @ver" first and send `flow_id: "@default"`, and the gateway resolves it at run start and
reports what it ran. No client keeps its own fallback chain any more.

## Why

Operator request, as recorded by the orchestrator (`PLAN.md`): gateway "D (default workflow)"; Code
WUI "workflow selector w/ gateway default"; Code TUI "`/workflow` gateway default + `--workflow
default`"; Assistant "workflow selector". Before the wave each client picked its own default
(Code docs even named `coding-agent:coder`, which was wrong).

## What landed

- **Gateway** `4c26658`: setting `agents.default_workflow.<interface>` =
  `[private:|catalog:]bundle[@ver]:flow`; stored > built-in (`basic-agent` for
  `abstractcode.agent.v1`; none for the Assistant → unavailable with a reason); no silent fallback;
  validated writes (unknown key → whole write refused); three doors (CLI `config get|set|unset`,
  console "Make agent default" + Workflows block, console TUI knob ★). `/bundles` and
  `/workflow-catalog` carry `default_agent_workflows` + `default_agent_workflows_unavailable`;
  entrypoints carry `is_agent_default`. `/runs/start` and `/runs/schedule` accept `@default`
  (interface required → 400; bundle fields with it → 400; unresolvable → 409 naming setting, value
  and source) and return `resolved_workflow`, also saved as `input_data.workflow_selection`.
  `950055e`: first-`:` split; the host resolves `@default` so Telegram records `gateway_default`.
  `e670774`: truthful Assistant no-default reason.
- **Code web** `719ad66`, `29372a5`, `4c7e79f`: selector with the gateway default first, persisted
  as `@default`; restored conversations follow `workflow_selection.source`; a default without the
  interface or registry scope is shown unavailable, not repaired.
- **Code TUI** `4668256`, `47c39bf`, `051ed62`, `f1330f1`: client fallback chain removed;
  `--workflow default`; picker row 0 = gateway default; `exec` with a stale saved workflow exits 2
  unless `--workflow default`.
- **Assistant** `91a5a5f`, `e0b6acf`, `e64a86e`: Settings → Models → Workflow lists the gateway
  default first, else "Built-in orchestrator"; a removed workflow blocks with a banner, never
  swapped; the built-in orchestrator is never labelled "@0.0.0".

## Completion report

- Tests: gateway suite 2350 passed at the G1 final; Code web 226, TUI 775 (9 deliberate breaks red),
  Assistant 829 → 887.
- Hermetic/E2E: G1 on 18852 `@default` → `basic-agent@0.0.5 gateway_default`; C2 exec on 18854
  (default; admin sets coder → coder; cleared → basic-agent; bad → exit 2); `E2E/REPORT.md` check 1
  (`/bundles` default + Assistant unavailable reason) and check 3 (TUI `/workflow` "● Gateway
  default → basic-agent @0.0.5").
- Reviews: REVIEW/00 (contract D); REVIEW/09 D ACCEPT-WITH-FIXES (S7 Telegram `@default`, S8 split on
  the first `:`) → fixed `950055e`; REVIEW/04 S2/S3 (a stale saved pick silently ran the default and
  exited 0) and REVIEW/05 S4 (a silent first-flow fallback survived in the Assistant) → closed,
  REVIEW/10 ACCEPT for Code web and TUI, ACCEPT-WITH-FIXES for the Assistant (hand-over only).
- Behaviour change for the release notes: clients no longer fall back on their own; a gateway with
  no resolvable default refuses with 409.
- ADR state: none. Settings follow the three-doors rule (web console, terminal console, CLI).

## Receipts

- `untracked/missions-2026-09-25/CONTRACTS.md` (§D), `G1/REPORT.md`, `C1/REPORT.md`, `C2/REPORT.md`, `A/REPORT.md`, `E2E/REPORT.md` (checks 1, 3)
- `untracked/missions-2026-09-25/REVIEW/00-contracts-review.md`, `03-code-web.md`, `04-code-tui.md`, `05-assistant.md`, `09-gateway-early.md`, `10-recheck-clients-flow.md`
