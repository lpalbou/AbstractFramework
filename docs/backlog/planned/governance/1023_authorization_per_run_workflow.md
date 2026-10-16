# 1023 — Authorization per (run, workflow) within the admin realm: folders and tools as nested subsets

> Package: abstractgateway, abstractruntime, abstractobserver, abstractflow, abstractcode (web)
> Type: task
> Created: 2026-10-15
> Priority: high
> Labels: governance, security, tools, workspace, decision-gate, adversarial-review-required
> Track: governance (README rows 25–28)

## Summary

OPERATOR DECISION GATE (never assignable) for Q8, Q9; the clamp (row 25) and the automation
intersection (row 26) are buildable once Q9 is ruled. Folders already nest the way the operator
describes (gateway caps ⊇ account ⊇ session ⊇ one-off, clamped at every door — README "what already
respects the model"), but TOOLS do not: a client's `_runtime.tool_policy` is honoured unclamped
(any `auto_approve_tools` list, or `auto_approve_max_risk_rank: 4` = destroy; the gateway default is
injected only when the key is absent and the code defers the clamp to a later "enforcement wave",
row 25); automations default to `tool_approval: "auto"`, pre-approving every tool the runtime knows
except messaging — live d18e1757 #13/#14 auto-approved 64 tools including `execute_command`,
`shell_exec`, `execute_python`, `delegate_agent`, `self_improve`, `camera_capture_*`,
`channel_fs_write`, while the shown default is `act` (row 26). Automation workspaces are not a fixed
per-(run, workflow) subset: "Use my default" and a missing workspace object are re-resolved at every
run from the owner's CURRENT default, and the stored `workspace_only` placeholder is not the policy
(row 27). The backlog exec runner runs codex at the repo root outside both the workspace policy and
the command sandbox (row 28).

## Why

Operator, 2026-10-15: "there is the realm of things authorized by the admin (eg can read & write
there, but only read there, and deny there, etc), within which, each user can define subsets of
authorizations for different processes (eg they can configure a default of what they accept — by
default, probably the same as admin; but they will want, for different runs, to be able to select
different authorizations. for instance, you could imagine to launch run A with workflow A on subset A,
and run B with another workflow B and with authorization subset B. authorizations are given per
(run, workflow). And authorization here is in the broader sense: both the folders and the tools."

## Scope

### In scope
- ONE authorization object per (run, workflow): `{folders: {posture, rows}, tools: {allowed, auto_approve, max_risk_rank}}`,
  resolved at START as the intersection admin realm ∩ account default ∩ run request, stamped into the
  run's vars (signed like the workflow policy), inherited by children, enforced by the runtime from
  the run's vars only — never from the request principal, never from a live default (Q8 decides
  whether "Use my default" freezes at creation; the resolved set is always shown on the definition).
- Row 25 (RT + GW): clamp `_runtime.tool_policy` to the lower of the admin ceiling and the account
  default (1021 introduces the per-account ceiling/default); a request above the ceiling is refused
  with the sentence naming the tool and the ceiling.
- Row 26 (RT): the automation grant is the intersection with the owner's ceiling; destroy-tier tools
  default to `ask`; the Automate form shows the resolved tool set, never `act`.
- Row 27 (GW + clients): the definition stores the RESOLVED workspace set (or an explicit "follow my
  default" marker per Q8) and never a placeholder; the Observer's Agent profile and the Automations
  page show the resolved set per occurrence.
- Row 28 (GW): the backlog exec runner takes the admin realm's folders as codex's writable roots and
  records the requesting admin (1024).
- Clients (Flow, Code web, Observer Launch): one "Authorizations" section per run = folders + tools,
  showing the three nested levels (realm, my default, this run) and refusing above-ceiling choices
  in the form.

### Out of scope
- New tool kinds; MCP credential scoping (1021 row 17).

## Ruling taken (2026-10-15)
- Q9 answered: strict chain — "a run must never get more privileges than its user's default, and the user must never have more privileges than what the admin allows." Rows 25–26 are buildable.

## Decision gates (operator)
- Q8: "Use my default" follows the live default, or freezes per (run, workflow) at creation?
- Q9: strict chain admin ceiling ≥ user default ≥ run, and may `tool_approval: auto` exceed the user default?

## Acceptance criteria
- [ ] A run requesting a tool outside its account default, or a risk rank above the ceiling, is refused at start with the reason; a mutation that removes the clamp turns a test red.
- [ ] An automation created with the defaults cannot auto-approve a destroy-tier tool; the form and the Observer show the same resolved tool list as the occurrence's ledger auto-approvals.
- [ ] The resolved (run, workflow) authorization is readable on the run (Observer Agent profile "Access" names realm, default and run subsets) and identical on every child.
- [ ] Adversarial review with the Alice/Bob matrix extended to tools.

## Receipts
- Audit table: `README.md` rows 25–28 (2026-10-15); live `run_f66b78f7….json` (64 auto-approved tools); automation d18e1757 revision 4 (no workspace object → live default `all_except_ignored`).
