# 0873 — Root launchers stop exporting the legacy backlog environment variables

> Package: abstractframework (scripts/lib/apps_common.sh, scripts/gateway-flow-local.sh)
> Type: improvement
> Created: 2026-09-25
> Priority: low
> Labels: scripts, settings

## Summary

Since abstractgateway 0.4.1 the backlog folder and the exec runner are stored gateway settings
(`abstractgateway config get|set|unset triage_repo_root …`, console backlog-settings card,
Continuum Settings page). The root dev launchers still export `ABSTRACTGATEWAY_TRIAGE_REPO_ROOT`
and `ABSTRACTGATEWAY_BACKLOG_EXEC_RUNNER=1`; the stack works, but Continuum labels both
"environment (legacy)", and the dev stack no longer exercises the path users get.

## Current code reality (root `cfb4926`)

- `scripts/lib/apps_common.sh` l.72–73 and `scripts/gateway-flow-local.sh` l.44 export them.

## Scope

- Replace the exports with a one-time idempotent `abstractgateway config set triage_repo_root
  <checkout>` (and the exec-runner setting) when unset, or document the one-time command in
  `docs/workspace-scripts.md`. Operator's call which (SUMMARY fourth wave, item 9).
- Out of scope: changing gateway behaviour.

## Acceptance criteria

- [ ] No launcher exports the two variables; Continuum Settings shows the stored source.
- [ ] `docs/workspace-scripts.md` says how the dev stack sets the backlog folder.

## Testing

- `grep -rn "TRIAGE_REPO_ROOT\|BACKLOG_EXEC_RUNNER" scripts/` (expect no export)
- `bash scripts/tests/test_repo_scripts.sh`

## ADR status

- ADR impact: None.

## Receipts

- `untracked/missions-2026-09-22/SUMMARY.md` (fourth wave, operator item 9); mission II.
