# 0915 — Adversarial review programme of the 2026-09-25/26 wave (23 reviews)

> Package: all packages touched by the wave (abstractgateway, abstractruntime, abstractcore, abstractagent, abstractskill, abstractuic, abstractflow, abstractcode, abstractassistant, abstractobserver, abstractcontinuum, abstractentity, root)
> Type: task
> Created: 2026-09-26
> Completed: 2026-09-26
> Priority: high
> Labels: review, security, quality, mission-wave-2026-09-25, process

## Summary

Completed record for the review seat of the 2026-09-25/26 wave. One long-lived adversarial reviewer
read the cross-repo contracts before anyone coded, then every track's diff and tests before the
orchestrator accepted it, re-ran its own probes against the fixes, and wrote 23 reviews
(`REVIEW/00` … `REVIEW/22`). A track was accepted only after its blocking items were fixed and
re-verified; an independent E2E pass (`E2E/REPORT.md`, 23/23 PASS on hermetic gateways with real
local models) closed the wave.

## Why

PLAN.md: "Adversarial reviewer: one long-lived Opus agent reviewing each track's diff + tests before
I accept it." The wave touched security seams (file serving, hand-over, forwarded addresses) and
shared hot files edited by several agents at once.

## The reviews

| # | subject | verdict |
|---|---|---|
| 00 | CONTRACTS.md (D, W, X, A1, B, S) | 4 × P0 settled before coding |
| 01 | abstractskill `bed8410` | ACCEPT-WITH-FIXES → 07 ACCEPT |
| 02 | About / identity, app-server A-2 | ACCEPT-WITH-FIXES (all repos) → 07 |
| 03 | Code web (C1) | ACCEPT-WITH-FIXES → 10 ACCEPT |
| 04 | Code TUI (C2) | ACCEPT-WITH-FIXES → 10 ACCEPT |
| 05 | Assistant (A) | ACCEPT-WITH-FIXES → 10, 17 ACCEPT |
| 06 | Flow (F) | ACCEPT-WITH-FIXES → 10 ACCEPT |
| 07 | re-check skill + About consolidation | ACCEPT (ui-kit/core parity fixes) |
| 08 | memory (M2) | ACCEPT-WITH-FIXES → 16, 20 |
| 09 | gateway D / same machine / W | W **REJECT** until B1 fixed |
| 10 | re-check 03/04/05/06 | ACCEPT (Assistant with fixes) |
| 11 | streaming design | GO-WITH-CHANGES |
| 12 | app proxies (forwarded address, marker) | ACCEPT |
| 13 | panel-chat 0.1.17 live replies | ACCEPT-WITH-FIXES |
| 14 | Flow edges on load | ACCEPT-WITH-FIXES → 17 ACCEPT |
| 15 | Code web streaming | ACCEPT-WITH-FIXES → 17 ACCEPT |
| 16 | memory re-check + latency regression | gateway built-in deny **REJECT**; runtime **BLOCKING** |
| 17 | streaming clients, runtime, agent, Flow | ACCEPT (TUI with fixes) |
| 18 | G2 console/tray/console-tui + core streaming | ACCEPT-WITH-FIXES → 20 |
| 19 | gateway streaming hub + deny prefixes | ACCEPT-WITH-FIXES |
| 20 | eject vs locks, core JSON/harmony, gateway JS tests | ACCEPT (core with fixes → 22) |
| 21 | runtime built-in protection + usage re-probe | ACCEPT |
| 22 | core harmony + docstrings, runtime usage | ACCEPT (docstrings with fixes → 0905) |

## Defects that mattered (found by review, fixed before acceptance)

- **Gateway secrets served over HTTP** (00 P0-1, 09 B1, proven): a run whose launch folder contained
  the gateway data folder served `runtime/config/runtime_config.json` and `.workflow_policy_secret`
  through the new workspace routes; with launch-folder trust on by default a remote non-admin could
  read `~/.ssh` (09 B2) → data-folder rule + built-in deny ([0910](0910_conversation_workspace_browse_preview_one_guard_and_builtin_deny.md)).
- **Every proxied browser counted as "this machine"** (00 P0-2, 02 X1/X2, 03 B2): both app proxies
  deleted `X-Forwarded-For`, and Code web's sign-in calls sent none → one rule, overwrite never
  append, app-proxy marker ([0908](0908_framework_identity_about_screens_and_proxy_forwarded_address.md)).
- **Hand-over code on argv** (00 P0-3): readable by every local user for 120 s, redeemable for a
  30-day admin session → 0600 file hand-over; then 05 S1 (the flag deleted any path given) and S2
  (silently replaced a sign-in) ([0911](0911_assistant_handover_overlap_window_defaults_workflow_selector_raw_html.md)).
- **Streaming transport contradiction** (00 P0-4) and the design gaps of 11 (children invisible,
  frame order, reconnect orphans, cleanup tied to `delta_end`) → hub keyed by root run, record
  before `delta_end`, snapshot on reconnect; 19 G1 kill-switched runs leaked hub state and live files
  ([0914](0914_token_streaming_end_to_end.md)).
- **Skill shelf corruption** (01 B1/B2): concurrent seeds failed 15/15 and froze truncated skills as
  operator content; a failed swap deleted the skill ([0907](0907_skills_shipped_with_abstractskill_and_seeded_by_the_gateway.md)).
- **Locked models ejected** (08 S1/S2, proven): a differently spelled unload bypassed the guard;
  one client's default switch ejected another client's locked model ([0913](0913_clean_model_eject_across_backends_and_default_switch_leak.md)).
- **Latency regression root cause** (16): the built-in deny enumerated the data folder into the
  system prompt (+~950 tokens per turn, cache cold every turn, other sessions' paths disclosed);
  measured by a single-toggle A/B ([0900](0900_chat_turn_latency_regression_in_switch_v3.md)).
- **Fixes silently reverted** (16): runtime `079c0fc`, committed from a stale tree, removed the
  claims registry and its tests; caught by `git grep` across commits, repaired `46590e9`.
- **Silent data loss in Flow** (14 F1/F2): load→save still deleted 9 type-refused connections;
  imports showed no notice ([0906](0906_flow_interface_pins_edge_preservation_and_deep_research_wiring.md)).
- **Silent client fallbacks**: 04 S2 (stale saved workflow ran the default and exited 0), 05 S4
  (first-flow fallback), 15 S2 (Off overridden by the gateway default when capabilities failed)
  ([0909](0909_default_agent_workflow_gateway_setting_and_clients.md), 0914).
- **Stale same-version artifacts** (07 R1, 15 S1): two different ui-kit 0.1.12 and panel-chat
  0.1.17 tarballs; FINAL sha256 fixed in CONTRACTS S-3 (f) → release step
  [0899](0899_npm_relock_and_kit_floors_after_the_kit_publishes.md); `npm ci` could not
  pass (03 B1).
- **Answers swallowed or mislabelled** (18 C1, 20 H1/H2): a ```json answer became a tool call; a
  truncated gpt-oss analysis was presented as the answer; `<|return|>` leaked.

## Completion report

- Every REJECT/BLOCKING verdict (09, 16) was re-verified after its fix (10, 17, 19, 21) before the
  track was accepted; the E2E pass re-ran the user-visible paths (streaming, hand-over, Files,
  default workflow, About, eject, latency) on committed trees: 23/23 PASS; minor findings N1, N2, N4
  fixed (`62a6778`, `e64a86e`), N5/N7 environment-only.
- Not yet on disk: a review of the gateway commits after REVIEW/19 (`3d3eac3` … `288f29f`, which
  carry the REVIEW/19 fixes; the planned "reviewer job 23"). The E2E pass ran on gateway `273902e`;
  `1b6b548` and `288f29f` (one workspace guard) are covered by their own tests only.
- Follow-ups created from reviews: 0891–0898, 0900–0905 (see overview).
- ADR state: none. Candidate process rule (not written): "agents sharing a hot file rebase, never
  commit from a stale tree; every mission ships a deliberate-break check".

## Receipts

- `untracked/missions-2026-09-25/REVIEW/00-contracts-review.md` … `REVIEW/22-core-harmony-runtime-polish.md`
- `untracked/missions-2026-09-25/E2E/REPORT.md` (+ `E2E/evidence/`), `PLAN.md` (status 04:40 CEST)
