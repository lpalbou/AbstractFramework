# 0875 — AbstractAssistant opens from the gateway already signed in

> Package: abstractassistant (controller.py, CLI); abstractgateway (apps_manager.py `launch_desktop`, tray)
> Type: feature
> Created: 2026-09-25
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

- [ ] Open from the console on a fresh profile lands signed in as the clicking admin.
- [ ] No token on argv, in the environment of unrelated processes, or on disk.
- [ ] A saved sign-in to another gateway is not silently lost (asked or kept).

## Testing

- `python -m pytest abstractgateway/tests/test_gateway_apps_install_and_assistant.py -q`
- `python -m pytest abstractassistant/tests -q -k handover`

## ADR status

- ADR impact: None (reuses the existing handover contract).

## Receipts

- `untracked/missionLL/REPORT.md` ("Open" list); 0864.
