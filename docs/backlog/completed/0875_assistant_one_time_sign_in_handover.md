# 0875 — AbstractAssistant opens from the gateway already signed in

> Package: abstractassistant (controller.py, CLI); abstractgateway (apps_manager.py `launch_desktop`, tray)
> Type: feature
> Created: 2026-09-25
> Completed: 2026-09-26 (committed locally, unreleased)
> Priority: normal
> Labels: apps, auth, assistant

## Summary

Since abstractgateway 0.4.2 the console and the tray install and open AbstractAssistant (a
desktop-kind app card), but the Assistant has no sign-in handover: it opens with whatever sign-in it
saved, and passing a gateway address would drop that saved sign-in. Browser apps and Code's terminal
app open signed in through a single-use code; the Assistant should too.

## Current code reality

- abstractassistant 0.5.0: `controller.py` l.1379–1417 handle gateway URL / saved sign-in; no
  one-time-code intake.
- abstractgateway 0.4.2: `apps_manager.py` `launch_desktop` refuses other computers (409
  `not_on_gateway_machine`), strips tokens from the child environment; `POST /apps/tui-handover`
  (same machine only) trades a one-time code for a launch-scoped token — the pattern to reuse.

## Scope

### In scope

- An Assistant entry (flag or URL scheme) that accepts a one-time code from the gateway and trades
  it for a token, never on argv or in a file readable by others.
- The gateway passes the code when it opens the Assistant; a running Assistant receives it without a
  second copy.

### Out of scope

- Remote (other-computer) launches; Assistant UI redesign.

## Acceptance criteria

- [x] Open from the console on a fresh profile lands signed in as the clicking admin (E2E check 5; the real `open -a` launch was stubbed by a recorder).
- [x] No token on argv or in the environment; the single-use code sits in a 0600 file (0700 folder) that the Assistant deletes on read; the session it gets is saved 0600 like any sign-in.
- [x] A saved sign-in is kept for the same gateway and user; otherwise it is logged out with a banner naming both (not silent).

## Testing

- `python -m pytest abstractgateway/tests/test_gateway_apps_install_and_assistant.py -q`
- `python -m pytest abstractassistant/tests -q -k handover`

## ADR status

- ADR impact: None (reuses the existing handover contract).

## Receipts

- `untracked/missionLL/REPORT.md` ("Open" list); 0864.

## Completion report

- Completed 2026-09-26 by the 2026-09-25/26 mission wave (gateway G1 A1 + mission A); full record in
  [0911](0911_assistant_handover_overlap_window_defaults_workflow_selector_raw_html.md). Original
  path: `planned/app-surfaces/0875_assistant_one_time_sign_in_handover.md`.
- Shape chosen: a file, not a URL scheme or argv code (REVIEW/00 P0-3: argv is readable by every
  local user through `ps`). Gateway `8d50758` writes `<data>/handover/<random>.json` (schema
  `abstractgateway.desktop_handover.v1`, 2 min, single use, `user_id` from `7c0b485`) and launches
  `--gateway-url <url> --gateway-handover-file <path>`; `POST /api/gateway/apps/desktop-handover`
  is direct-loopback only (proxy/session headers → 403 without burning the code; used/expired →
  410). Assistant `b4de208`, `6756a5a`, `30037ec`, `06eba33`: file checks (regular, owned, 0600,
  < 4 KiB, schema), deleted after reading, session kept only for the same gateway and user.
- Validation: Assistant hand-over tests against a fake loopback server (15 → suite 887 passed);
  `E2E/REPORT.md` check 5 (argv, env, file modes, redeem, second redeem 410). Reviews REVIEW/05,
  REVIEW/10 (c), REVIEW/17 (d) ACCEPT.
- Residual: the scope item "a running Assistant receives it without a second copy" is handled by
  the gateway's "already running" message, not by passing the code to the running instance; rotating
  the operator token signs out a tray-launched Assistant (G1 open note, listed in 0892's
  out-of-scope). Not released: waits for the operator's go (abstractassistant 0.6.0, gateway 0.5.0
  proposed in STAGING).
