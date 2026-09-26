# 0912 — AbstractCode TUI: MTP inside `/model`, `/files`, `/about`, the gateway's default workflow, truthful help

> Package: abstractcode (tui crate 0.6.0 proposed, unreleased)
> Type: feature
> Created: 2026-09-26
> Completed: 2026-09-26
> Priority: normal
> Labels: code, tui, mtp, mission-wave-2026-09-25, unreleased

## Summary

Completed record for mission C2 of the 2026-09-25/26 wave plus its E2E fixes (committed locally, not
released; release staged, waiting for the operator's go). Multi-token prediction is now chosen in
the `/model` flow itself, the conversation's folder can be browsed with `/files`, `/about` shows the
framework identity and the gateway's versions, new conversations follow the gateway's default
workflow, and `--help` / notices state the real defaults.

## Why

Operator request, as recorded by the orchestrator (`PLAN.md`, track C2): "Code TUI: `/workflow`
gateway default + `--workflow default`, `/files` modal + preview, skills warning, MTP visibility,
`/about`". Operator correction on 2026-09-26 (C2 report): "MTP must be selectable inside the /model
flow itself (not only a hint line)". Fact found first: MTP existed since 0.5.1 (`/mtp`, `--mtp`);
the operator's `~/.cargo/bin/abstractcode` was a stale 0.5.0.

## What landed (abstractcode `tui/`)

- **MTP in `/model`** (`ebbe6b8`, `ed82471`): the flow is provider → model → reasoning → MTP;
  choices Inherit / Off / Native N draft tokens, depths offered only when the gateway's capability
  answer says MTP is supported; current value pre-selected, saved to `prefs.speculation`, header
  chip; unsupported/failed checks are explicit rows.
- **`/files`** (`40be4a4`, `051ed62`): see [0910](0910_conversation_workspace_browse_preview_one_guard_and_builtin_deny.md).
- **`/about` + `/version`** (`8f1b5b4`): vendored identity JSON via `include_str!`; see
  [0908](0908_framework_identity_about_screens_and_proxy_forwarded_address.md).
- **Gateway default workflow** (`4668256`, `47c39bf`, `051ed62`, `f1330f1`): see
  [0909](0909_default_agent_workflow_gateway_setting_and_clients.md); `/skills` shows shelf, source
  and warnings (`643a79f`).
- **Live replies** (`290fb49`, `bd480d1`, `74eaefc`, `488caf8`): see [0914](0914_token_streaming_end_to_end.md).
- **Help and launch flags** (`68a781a`, `62a6778`): `--help` defaults derive from the code's
  constants (`--replay-turns` 5, not 20; `--timeout` 7200, not 900), `--workspace` wording truthful,
  no ADR references in user text, CONFIG lists `send_local_workspace` and `speculation`; interactive
  sessions honour `--permissions` / `--require-approval` for that launch (not saved; the notice says
  so); the same-machine notice is truthful for `--no-workspace` and a missing launch folder (E2E N1,
  N2). Docs `c1ea668`, `b2806bc`, coredoc `79088a6`, `1597dd5`.

## Completion report

- Tests: 763 → 815 passed / 8 ignored; `cargo fmt` + `clippy -D warnings` clean; mutation checks red
  at every step (9 for the review-04 fixes, 16 for the stream rules).
- E2E (`E2E/REPORT.md` check 3, pty + exec against a hermetic gateway): `/stream on` chip and live
  bubble, `/workflow` gateway default, `/files` list + preview; exec `--stream on|off`.
- Reviews: REVIEW/04 ACCEPT-WITH-FIXES (S1 `o` passed a path built from gateway strings to `open`,
  which launches app bundles; S2 `exec` with a stale saved preference ran the default and exited 0;
  S4/S5 "loopback URL" stood in for "same machine"; S6 malformed listing read as an empty folder; S7
  the exec hint taught an env var) → REVIEW/10 (b) ACCEPT; REVIEW/17 (c) ACCEPT-WITH-FIXES (missing
  orphan-bubble test) → `488caf8`.
- Kept ruling: a same-host LAN URL counts as remote until the first run's verdict; shared-mount users
  use `/workspace send always` (→ [0893](../proposed/0893_same_machine_locality_behind_a_reverse_proxy.md)).
- Not verified: an MTP drafter actually running (the companion is not downloaded on this host;
  E2E check 6 reports `mtp_drafter_load_failed`) → [0896](../proposed/0896_verify_mtp_drafter_eject_on_a_host_with_the_companion.md).
- ADR state: none.

## Receipts

- `untracked/missions-2026-09-25/C2/REPORT.md`, `S/REPORT.md` (S-tui entries), `E2E/REPORT.md` (checks 3, 6; N1, N2), `CD/REPORT.md` (abstractcode rows)
- `untracked/missions-2026-09-25/REVIEW/04-code-tui.md`, `10-recheck-clients-flow.md`, `17-streaming-clients-flow.md`
