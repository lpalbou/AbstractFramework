# 0892 — Gateway run tool deny list: close the gaps, and decide launch-folder trust for non-admins on non-localhost gateways

> Package: abstractgateway (routes/gateway.py, workspace_browse.py, runtime_config.py); abstractruntime (tool sandbox); related 0232
> Type: improvement
> Created: 2026-09-26
> Priority: high
> Labels: security, workspace, deny-list, decision-gate

## Summary

Gateway `0ccbe73` (2026-09-26) added a built-in deny list (credential folders under HOME, the
`~/.abstract*` config folders and the gateway data folder) to workspace browsing for everyone and
to each run's own tool sandbox (`workspace_ignored_paths`), with an admin setting
`workspace_builtin_deny` to turn the run half off. Three gaps remain: (1) the data-folder part of
the run list is a snapshot of the sibling folders that exist at run start, so a folder created later
is not covered; (2) shell tools are not confined by the list at all; (3) `/runs/schedule` child runs
did not get the list — the uncommitted S-gw working tree now applies it (verify once committed).
Plus the operator ruling asked for by REVIEW/09 B2: with launch-folder trust ON by default, a remote
non-admin user can point a run at `$HOME`; consider trust OFF by default for non-admin principals on
a non-localhost gateway.

## Why

- G1 report "Open (backlog)": "tool deny list = snapshot of sibling folders at run start; shell not
  confined (runtime design); /runs/schedule child runs lack the built-in list (→ S-gw)".
- REVIEW/09 B2: "make launch-folder trust default to OFF for non-admin principals on a non-localhost
  exposure. That is an operator decision". The built-in list shipped; the trust default did not change.

## Current code reality (2026-09-26; abstractgateway `1172686` + uncommitted S-gw edits in 9 files)

- `routes/gateway.py` l.4081–4110 `_apply_builtin_tool_deny`: merges `BUILTIN_DENY_HOME_RELPATHS`
  and `data_dir_tool_deny(data_root, keep)` into `workspace_ignored_paths`; called for `/runs/start`
  at l.8112.
- `workspace_browse.py` l.334–337 `BUILTIN_DENY_HOME_RELPATHS` (.ssh, .aws, .gnupg, .config/gcloud,
  .kube, Library/Keychains, .abstractgateway/.abstractcode/.abstractassistant/.abstractcontinuum/
  .abstractcore); l.372–389 `data_dir_tool_deny` lists siblings via `os.scandir` — its docstring
  says "A snapshot of what exists now". `.netrc` and `.docker` (named in REVIEW/09 B2) are absent.
- `/runs/schedule` (`start_scheduled_run`, l.8173): the call `_apply_builtin_tool_deny(input_data, …)`
  at l.8394–8396 exists ONLY in the uncommitted working tree (`git diff` of routes/gateway.py).
- `runtime_config.py` l.622–629 `_trust_client_launch_folder_payload`: default `True`; per-user
  override `user_workspace_policies[...].trust_client_launch_folder` (l.518–523).
- Shell/`execute_command` containment is the open P0 `planned/0232_execute_command_sandboxing_and_workspace_path_containment.md`.

## Scope

### In scope

- Replace the data-folder snapshot with a rule the tool sandbox evaluates per call ("inside the data
  folder and not inside the run's own folder"), or re-derive the list per tool call.
- Confirm the schedule path after S-gw commits (test: a scheduled child run's `read_file` on
  `~/.ssh/x` is refused).
- Decide whether `.netrc`, `.docker` join the built-in list.
- Put to the operator: default `trust_client_launch_folder` to OFF for non-admin principals when the
  gateway is exposed beyond localhost (network mode), with the admin able to grant it per user.

### Out of scope

- Shell sandboxing itself (0232). Roles/RBAC (0862/0870). Per-run uuid folders shared in single-user
  mode and "rotating the operator token signs out a tray-launched Assistant" (other G1 opens; triage
  separately if they matter).

## Dependencies

- 0232 (shell), 0870 (operator rulings on roles), S-gw commit in abstractgateway.

## Expected outcomes

- No gateway-data or credential folder is reachable by a run's file tools, whatever was created after
  the run started, on every start path.
- A recorded operator ruling on launch-folder trust for remote non-admins.

## Acceptance criteria

- [ ] Test: a folder created in the data dir after run start is refused to the run's `read_file`.
- [ ] Test: `/runs/schedule` target runs carry the built-in list (committed code, not working tree).
- [ ] Operator ruling recorded (verbatim) in this item; if "off", a test for a non-admin on a LAN
      exposure getting no launch-folder trust by default.

## Validation

- `python -P -m pytest abstractgateway/tests -k "workspace or deny or schedule"` with a scratch HOME.
- Deliberate break: remove the schedule-path call; the new test must go red.

## Evidence

- `untracked/missions-2026-09-25/G1/REPORT.md` (Final section, "Open (backlog)")
- `untracked/missions-2026-09-25/REVIEW/09-gateway-early.md` (B1, B2)
- `untracked/missions-2026-09-25/CONTRACTS.md` (A-1)

## ADR status

- ADR impact: likely. "Built-in deny list binds browse and runs" and the trust default for remote
  non-admins are cross-task security rules; write or revise an ADR when the ruling lands.

## Receipts

- None yet.

## Status note (2026-09-26, after gateway `288f29f`, runtime `9818cad`)

- Gap (1) closed: the data-folder snapshot was replaced by deny PREFIXES plus one allow (the run's
  own folder), evaluated per call by the runtime (`6567ed4`); the enumeration helper is deleted
  (gateway `609806d`). It was also the cause of the latency regression 0900 (closed).
- Gap (3) closed: one workspace guard (`run_workspace_guard.py`, gateway `288f29f`) runs on every
  start path, `/runs/schedule`, bridges and entity summons included; a child run can only add to the
  host's deny list (runtime `9818cad`).
- Still open: shell confinement (0232); `.netrc` / `.docker` in the built-in list; the operator
  ruling on launch-folder trust for remote non-admins. Record: `completed/0910_conversation_workspace_browse_preview_one_guard_and_builtin_deny.md`.
