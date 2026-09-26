# 0910 — Conversation workspace: browse and preview from every client, one guard for every run start, a built-in deny list

> Package: abstractgateway (workspace routes, `run_workspace_guard.py`, built-in deny); abstractruntime (`WorkspaceScope`); abstractcode (web Files tab, TUI `/files`)
> Type: feature
> Created: 2026-09-26
> Completed: 2026-09-26
> Priority: high
> Labels: workspace, security, gateway, runtime, clients, mission-wave-2026-09-25, unreleased

## Summary

Completed record for track W of the 2026-09-25/26 wave (G1, S-gw, S-rt, C1, C2; committed locally,
not released; release staged, waiting for the operator's go). A user can see the folder a
conversation works in — absolute path and gateway host name — list it, and preview files, from Code
web and the Code TUI. Getting there safely forced two security changes: every run start now goes
through one workspace guard, and a built-in deny list (credential folders, `~/.abstract*`, the
gateway data folder) binds both browsing and the run's own file tools.

## Why

Operator request, as recorded by the orchestrator (`PLAN.md`): Code WUI "Files tab + preview + open
folder"; Code TUI "`/files` modal + preview"; gateway "W (workspace routes)". CONTRACTS §W: "Showing
the absolute path + hostname is REQUIRED by the operator (it is the feature) — keep it."

## What landed

- **Routes** (gateway `93bba5d`): `GET /runs/{id}/workspace` {path, kind, host{hostname,
  caller_is_this_machine}, open_supported}, `/files` (entries, `truncated`, `hidden` counts),
  `/content` (CSP sandbox, nosniff, Range 206/416); `..`/absolute → 400; symlink escape → 403; other
  user → 404; deny lists re-checked on every call.
- **Data-folder rule and built-in deny** (`0ccbe73`, then rewritten): the data folder is refused on
  every entry and read even when a launch folder contains it; built-in deny for `~/.ssh`, `~/.aws`,
  `~/.gnupg`, `~/.config/gcloud`, `~/.kube`, `~/Library/Keychains`, `~/.abstract{gateway,code,
  assistant,continuum,core}` and the data folder, for browse (everyone) and runs (admin setting
  `workspace_builtin_deny` to disable); `O_NOFOLLOW` + verified fd. After REVIEW/16 the run half is
  expressed as deny PREFIXES plus one allow (the run's own folder), never an enumeration and never
  rendered into the prompt (gateway `609806d` deletes the enumeration helper; runtime `6567ed4`
  enforces `workspace_builtin_deny_prefixes`/`workspace_builtin_allow` on every file tool,
  list/search and shell cwd; `9818cad` a child run can only add to the parent's deny, never remove).
- **One guard** (gateway `288f29f`): `run_workspace_guard.py` is called from `host.start_run` for
  every start path — Telegram/email/agora bridges, entity summons, sandbox routes, schedules; assigns
  the conversation's gateway-made folder when none is named; `/runs/schedule` runs the same policy
  check (data-folder root → 400). Behaviour change: bridge/summon/schedule runs that never named a
  folder are now confined to their conversation folder.
- **Clients**: Code web `6e5c46b`, `ac05c59` (Files tab, path + "on the gateway host <name>", Open
  folder only when same machine and admin, previews for Markdown/JSON/images/HTML source/text,
  Range-bounded 1 MiB text preview, images only from this workspace); Code TUI `40be4a4`, `051ed62`
  (`/files` modal with preview, `o` reveals only the gateway's absolute root, same-machine = the
  gateway's verdict, `/workspace send auto|always|never`; remote gateways no longer receive the
  local cwd).

## Completion report

- Tests: gateway 2350 → 2401 passed / 7 skipped at `288f29f` (+3 browse; 5 breaks red); runtime
  2580 passed (37 workspace tests incl. "prompt byte-identical while the data folder grows by 50
  files"); Code web 226, TUI 775 (9 breaks red).
- E2E (`E2E/REPORT.md`): check 3 TUI `/files` lists and previews a file the agent wrote; check 4
  Code web Files tab lists and previews; check 6 system prompt byte-identical across turns while the
  data folder grew 474 → 493 files, no "Excluded paths" line.
- Reviews: REVIEW/00 P0-1 (launch-folder trust made the routes a one-call read of any host file,
  gateway secrets included); REVIEW/09 **REJECT** of `93bba5d` until B1 was fixed (proven: a launch
  folder that CONTAINS the data folder served `runtime/config/runtime_config.json`) and B2 (non-admin
  reads `~/.ssh` with trust on by default) → fixed by `0ccbe73`; REVIEW/16 **REJECT** of `0ccbe73`
  (the enumeration grew the system prompt ~950 tokens per turn — see
  [0900](0900_chat_turn_latency_regression_in_switch_v3.md)) → fixed by the prefix rewrite;
  REVIEW/19 and REVIEW/21 ACCEPT.
- Follow-ups: operator ruling on launch-folder trust for remote non-admins, `.netrc`/`.docker`, and
  shell confinement (0232) → [0892](../proposed/0892_gateway_tool_deny_list_gaps_and_launch_folder_trust_for_non_admins.md);
  a same-host LAN URL counts as remote until the first run's verdict →
  [0893](../proposed/0893_same_machine_locality_behind_a_reverse_proxy.md). Open G1 notes kept in
  0892's out-of-scope list (per-run uuid folders shared in single-user mode; rotating the operator
  token signs out a tray-launched Assistant).
- ADR state: not written. 0892 carries the ADR candidate ("the built-in deny list binds browse and
  runs; host protection is authoritative for the run tree").

## Receipts

- `untracked/missions-2026-09-25/CONTRACTS.md` (§W, A-1), `G1/REPORT.md` (Final), `S/GW-REPORT.md` (288f29f), `S/REPORT.md` (S-rt final, 9818cad), `C1/REPORT.md`, `C2/REPORT.md`, `E2E/REPORT.md` (checks 3, 4, 6)
- `untracked/missions-2026-09-25/REVIEW/00-contracts-review.md`, `09-gateway-early.md`, `16-memory-recheck-latency.md`, `19-gateway-streaming.md`, `21-runtime-recheck.md`
