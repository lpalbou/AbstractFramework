# 0981 — Follow-ups after root 0.6.1 (gate findings, doc contradictions, small product bugs)

> Package: abstractgateway, abstractcode, abstractflow, abstractassistant, abstractcore, abstractcontinuum, abstractvoice
> Type: task
> Created: 2026-09-28
> Priority: normal
> Labels: follow-up, docs, ux, gateway, release

## Summary

Non-blocking findings from the 0.6.1 patch tag gates and from the website refresh (screenshots taken on a hermetic 0.7.0 gateway). Each line is small; split into its own item when picked up.

## Why

Recorded so nothing found during the release is lost. Sources: `untracked/patch-wave/gate/` (tag-gate reports), `untracked/site-refresh/` (site refresh report and screenshots).

## Current code reality (2026-09-28)

Released: gateway 0.7.1 (7fcf33a), abstractcode 0.7.1 / web 0.6.1, Observer 0.2.1, Assistant 0.9.1, ui-kit 0.1.16, root 0.6.1.

## Scope

### In scope

**Gateway (0.7.1 gate, non-blocking)**
- CHANGELOG says "`foreign_binary` (409)"; the install request is accepted and the job then fails with reason `foreign_binary`. Fix the wording.
- A timed-out `--help` probe is cached as "not ours" until the file changes, so a slow first launch of our own binary can block updates. Do not cache a timeout as foreign.
- Updating through a symlink to our binary leaves the linked target (e.g. in `~/.cargo/bin`) as a second copy. Say so, or offer to remove it.
- Windows: updating a running `abstractcode.exe` fails with a raw `PermissionError`; say "close AbstractCode and retry".

**AbstractCode (0.7.1 gate, non-blocking)**
- The sign-in hint's `abstractgateway-config bootstrap-admin --print-token` / `apps tui-command code` lack `--data-dir` for a gateway with a custom data dir (`signin.rs:37`); "rotates nothing" comment is loose; `<value>` should read `<token>`.
- A 403 on history alone with ping 200 reloads every 30 s (`runner.rs:807-812`, `ui/mod.rs:2508`).
- Login store: fsync the directory after the rename; a crash can leave a 0600 temp file with the token; `~/.abstractcode` is created 0755.

**Kit / Observer / Assistant (accessibility, non-blocking)**
- Kit Discuss button (`AutomationPanel.tsx:993`) disabled tooltip lacks the reason first.
- Observer rows: no visible disabled reason; native `disabled` buttons are not focusable, so keyboard users never see the hint; `aria-description` is the only accessible hint.
- Assistant accessible description omits the disabled reason.
- CHANGELOG wording: Observer "every row control has a tooltip" (legacy rows have none); Assistant "every control uses the shared hint" (Discuss keeps its own).

**Docs that contradict the code (found by the site refresh)**
- AbstractCode README says the gateway binds 0.0.0.0 (it binds 127.0.0.1).
- Assistant README starts the gateway with `ABSTRACTGATEWAY_AUTH_TOKEN` (token is a launch flag / direct parameter).
- Gateway first-run doc uses `--url --token-file` (should be `--gateway-url` and `--token <value>`).
- basic-agent version: docs say 0.0.4, the packaged file is 0.0.5.
- Voice and 3D READMEs show old version numbers; AbstractCore Docker docs show old image tags.

**Small product bugs seen in screenshots**
- Web console Welcome step shows Memory "Unknown" until a workflow bundle loads.
- Start-at-login text duplicated ("Off — Off — …").
- Flow footer says "v0.1.0" on the 0.4.0 package.
- Code web sidebar says "Automations 2" while listing three.
- A file attached in Code web did not appear in its Files panel.
- Continuum and the Code web client both default to port 3002 when run standalone (see also app-surfaces 0879).

**Release process**
- Root CI's abstractcode build step is soft, so green CI does not prove the crate is on crates.io; the root release workflow does not check sibling pins are visible on their registries.
- `test_inventory.sh` fails against the real siblings: `packages.txt` misses three dependency edges.
- The gateway py3.10 live-deltas flake (0933) failed CI three times on 2026-09-28; raise 0933's priority.

### Out of scope

- New features.

## Acceptance criteria

- [ ] Each line is fixed or split into its own item with an owner.

## Validation

Per line; docs lines verified against the code they describe.
