# 0911 — AbstractAssistant: signed-in hand-over from the gateway, session-switch overlap fix, window defaults, workflow selector, raw-HTML fix

> Package: abstractassistant (0.6.0 proposed, unreleased); abstractgateway (desktop hand-over route)
> Type: feature
> Created: 2026-09-26
> Completed: 2026-09-26
> Priority: high
> Labels: assistant, auth, handover, ui, security, mission-wave-2026-09-25, unreleased

## Summary

Completed record for mission A of the 2026-09-25/26 wave plus the gateway half (G1 A1) and the
Assistant's streaming follow-ups (committed locally, not released; release staged, waiting for the
operator's go). The Assistant now opens from the console or tray already signed in, no longer
paints two sessions on top of each other (and no longer writes one session's messages into
another's transcript), uses the requested window defaults, follows the gateway's default workflow,
and never renders model text as raw HTML. Closes planned
[0875](0875_assistant_one_time_sign_in_handover.md).

## Why

Operator request, as recorded by the orchestrator (`PLAN.md`, track A): "Assistant: handover flag,
overlap bug, 650/28 defaults, workflow selector, About page + tray item".

## What landed

- **Hand-over** (gateway `8d50758`, `7c0b485`; Assistant `b4de208`, `6756a5a`, `30037ec`,
  `06eba33`): the gateway writes a 0600 file `<data>/handover/<random>.json` (schema
  `abstractgateway.desktop_handover.v1`, 2 min, once, carries `user_id`) and launches the Assistant
  with `--gateway-url <url> --gateway-handover-file <path>`; nothing on argv or in the environment
  is a credential. `POST /api/gateway/apps/desktop-handover` is public but direct-loopback only
  (proxy/session headers → 403 without burning the code; used/expired → 410); 30-day session. The
  Assistant opens the file with `O_NOFOLLOW`, requires a regular 0600 file it owns under 4 KiB with
  the right schema, deletes it, keeps an existing session only for the same gateway AND user, and
  otherwise logs the old one out with a banner naming both.
- **Overlap and data corruption** (`ce827ca`, `4d11c01`): widgets hidden and detached before
  `deleteLater` during a session switch; a late attachment refresh for session A no longer writes A's
  messages into B's transcript on disk (save and redraw check session and last run; merged under the
  lock).
- **Window defaults** (`451a961`, `f783129`): width 650, gap 28; old caps removed, only
  screen-based clamps; saved 0 stays 0; layout v2 migrates exact old defaults once.
- **Workflow selector**: see [0909](0909_default_agent_workflow_gateway_setting_and_clients.md)
  (`91a5a5f`, `e0b6acf`, `e64a86e`).
- **About**: see [0908](0908_framework_identity_about_screens_and_proxy_forwarded_address.md).
- **Live replies**: see [0914](0914_token_streaming_end_to_end.md).
- **Raw HTML** (`6bff0f9`): the Markdown renderer had markdown-it `html: True`, so model text with
  `<img onerror>`, `<a href="javascript:">` or `<script>` reached Qt rich text as markup. Raw HTML is
  now off; Mermaid diagrams are inserted through random-token placeholders after rendering.
- CLI `run` without a token → how to sign in, exit 2 (`bb2d381`).

## Completion report

- Tests: suite 810 → 887 passed offscreen with a scratch HOME (15 hand-over tests against a fake
  loopback server; 3 offscreen overlap tests on a real palette; 3 parser-based raw-HTML tests; breaks
  red).
- E2E (`E2E/REPORT.md` check 5, spawner replaced by a recorder): hand-over minted via
  `POST /apps/assistant/launch`, argv carries only the URL and the file path, no gateway key in the
  environment, file 0600 in a 0700 folder with `user_id`; redeem with a scratch HOME deletes the file
  and saves a 0600 session; a second redeem → 410. The real `open -a /Applications/AbstractAssistant.app`
  was not exercised (N7).
- Reviews: REVIEW/00 P0-3 (a code on argv is readable by every local user for 120 s and yields a
  30-day admin session) → file-based hand-over; REVIEW/05 ACCEPT-WITH-FIXES (B1 route missing; S1 the
  flag deleted ANY path it was given; S2 a hand-over silently replaced an existing sign-in; S4 silent
  first-flow fallback; S7 a cap survived) → REVIEW/10 (c) ACCEPT-WITH-FIXES (another user's session
  kept) → `06eba33`; REVIEW/17 (d) ACCEPT.
- Release notes: `abstractcore` floor must be the real released number (placeholder `>=2.15.4`,
  STAGING step 12).
- ADR state: none (reuses the gateway's single-use hand-over pattern).

## Receipts

- `untracked/missions-2026-09-25/A/REPORT.md`, `G1/REPORT.md` (8d50758, 7c0b485), `S/REPORT.md` (S-assistant), `E2E/REPORT.md` (check 5), `CD/REPORT.md`
- `untracked/missions-2026-09-25/REVIEW/00-contracts-review.md` (P0-3), `05-assistant.md`, `10-recheck-clients-flow.md`, `17-streaming-clients-flow.md`
