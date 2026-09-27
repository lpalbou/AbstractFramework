# 0943 — Local gateway pointer file: hand-started Rust, Node and frozen clients find a gateway that is not on 8080

> Package: abstractgateway, abstractframework (installers), abstractcode-tui, abstractgateway-console, abstractuic (app-server), abstractassistant (.app)
> Type: task
> Created: 2026-09-27
> Priority: normal
> Labels: installer, discovery, cross-language, contract

## Summary

The gateway does not always listen on 8080. The installer moves it to the next free port when 8080 is busy
("! port 8080 is in use by another process; using 8081 (kept for future runs)"), and an admin can change the
port at any time (`POST /api/gateway/network` + `POST /network/restart`, or `abstractgateway network set --port`).
Python clients follow it through `abstractgateway.first_run.local_gateway()`. Clients in other languages cannot
call that function, so when started by hand they still default to `http://127.0.0.1:8080`: the two Rust TUIs,
the five Node web apps run with `npx`, and the frozen `AbstractAssistant.app`. They then talk to whatever else owns
8080 and may send it their bearer token or the browser sign-in password.

This item adds ONE small, documented file that records where this computer's installed gateway listens:
`~/.abstractframework/gateway.json`. The installer and `serve` write it; each non-Python client reads it with
about 15 lines of code. There is no liveness check and no token in it.

## Why

Operator, 2026-09-27: "assistant should follow exactly the same rule and auto configure to the port the gateway is
installed to / configured to … ensure all apps that would be installed following that setup … will target the right
url/port by default", "it seems the centralized files to help the 3 languages is a good idea", and
"an admin should be able to change that port."

An adversarial review (2026-09-27) compared five options: each client re-implementing the rule, a pointer written
by every `serve`, reading only the serve record, doing nothing, and a narrowed pointer. It chose the narrowed
pointer, with these reasons:
- **Re-implementing `local_gateway()` in Rust and Node** drifts across three languages: four tiers, per-OS data-dir
  paths, three env names and the legacy `./runtime` rule. It also cannot know a custom installer `--data-dir`,
  because the installer exports `ABSTRACTGATEWAY_DATA_DIR` only to its own process and the service unit.
- **A pointer written by every `serve`** lets a test gateway take it over. The operator runs a hermetic one on :18850
  with its own data dir, so real clients would send credentials to it.
- **Reading only the serve record** fails for a client started before the gateway (login items).
- **Doing nothing** leaves the frozen `.app` and the TUIs' first run on 8080.

## Current code reality (2026-09-27)

**Python side (uncommitted, 2026-09-27; to land before this item):**
- `abstractgateway/src/abstractgateway/first_run.py` `local_gateway(data_dir=None)` resolves, in order:
  1. the running gateway's serve record (`<data>/run/gateway-serve.json`, with a pid check);
  2. a pinned OS service record;
  3. the stored Network setting port;
  4. `127.0.0.1:8080`.
- `firstrun_cli._claim_base_url` delegates to it, so `claim-url`, `apps` and every `models` verb follow it.
  `cli.py` `models loaded|load|unload` no longer hard-code 8080.
- `abstractassistant/abstractassistant/config.py` computes `DEFAULT_GATEWAY_URL` with it when abstractgateway shares
  the Assistant's Python (the console's install path).
- `preferences.GatewayConnectionStore.load` re-points a saved sign-in equal to the old built-in 8080.

**Installers (uncommitted):** `scripts/install.sh` / `install.ps1` print `ABSTRACTGATEWAY_URL=$BASE_URL npx -y …` and
`abstractcode --gateway $BASE_URL`, instead of a comment or nothing.

**Apps the gateway launches already get the URL:** the web apps via `apps_manager.app_launch_config` / `_spawn`, the
Code TUI via its launcher script, and the Assistant via `--gateway-url` from `launch_desktop`. This item does not
change them.

**Admin port change today:**
- `routes/network.py` `POST /network` is admin-only (`_require_admin_principal`). It stores the port, and the change
  applies at `POST /network/restart` (409 when it cannot) or at the next start.
- A service registered with `--pin-command-line` binds its recorded port and ignores the setting.

**Hard-coded 8080 in hand-started clients:**
- `abstractcode-tui/src/config.rs:15`: flag > env > login store > 8080.
- `abstractgateway/console-tui/src/lib.rs` ~l.133 and ~l.163: `--url` or 8080. It does NOT read
  `ABSTRACTGATEWAY_URL`, unlike every other client; that is a bug in its own right.
- The Node apps: `abstractflow/bin/cli.js:29`, `abstractcode/web/bin/server.js:10`, `abstractobserver/bin/cli.js:22`,
  `abstractcontinuum/bin/settings.js:54`, `abstractentity/bin/cli.js:30`, and the shared
  `abstractuic/app-server/src/gateway_session_proxy.js` (~l.203; the URL cookie is honoured only when it equals that
  default, ~l.330).
- The frozen `.app`: `packaging/macos/AbstractAssistant.spec` excludes abstractgateway, so the `.app` falls back to
  8080 or its saved sign-in.

**Existing files:**
- `~/.abstractframework/` already exists (`data_registry.json`, `kill-receipts.log`). The installer's uninstall keeps
  that directory on purpose (install.sh ~l.900).
- Clients already keep per-home files: `~/.abstractcode/gateway.json`, `~/.abstractflow/gateway_connection.json`.
- No discovery or pointer file exists today.

## The contract (decided here; record it in docs/architecture.md and as an ADR before closure)

**Path:** `~/.abstractframework/gateway.json` on every OS (`%USERPROFILE%\.abstractframework\gateway.json` on Windows).

**Content:**
```json
{"schema": 1, "url": "http://127.0.0.1:8081", "port": 8081,
 "data_dir": "/home/me/.local/share/abstractgateway",
 "updated_at": "2026-09-27T12:00:00Z", "written_by": "installer|serve"}
```
- `url` is where the gateway LISTENS, or will listen at its first start (installer). It is NOT the configured-but-not-
  yet-applied port: after an admin changes the port, clients keep the old URL until the restart binds the new one.
- It holds no token, no pid and no liveness information.

**Writers.** Write atomically (tmp file + replace, like `write_serve_record`), mode 0600.
1. **The installer** (`install.sh`, `install.ps1`), right after it picks the port and before it starts the gateway.
   It knows the custom `--data-dir` and the chosen port. It also rewrites the file on a re-run.
2. **`abstractgateway serve`**, once bound, with the port it actually bound. This covers:
   - an admin port change: the console restart or `network restart` re-runs serve;
   - `service install --port`, where the service's serve writes;
   - a pinned service;
   - a manual edit of the runtime config.

   `network set` does NOT write the file: clients must not move before the gateway does.

**Ownership rule (serve only).** Serve writes only when:
- the file is absent and the serve's data dir is the OS default data dir (`host_paths.user_data_dir()`); or
- the file's `data_dir` equals the serve's own data dir.

Compare resolved paths, never `data_dir_source`: the service unit always exports `ABSTRACTGATEWAY_DATA_DIR`, so the
source reads `env` even for the default. The installer is the owner, so it always writes. As a result, test gateways,
the hermetic :18850 console and pytest runs never touch the real file.

**Deleter.** The installer's uninstall deletes this single file, purge or not; the rest of `~/.abstractframework` stays
as today. `serve` never deletes it on stop: the port stays valid while the gateway is stopped.

**Readers.** The Rust TUIs, the shared Node proxy/app servers, and the frozen `.app`. Order:
1. explicit flag;
2. app-specific env, then `ABSTRACTGATEWAY_URL`;
3. the client's saved login or connection, except a saved URL equal to the old built-in `http://127.0.0.1:8080`,
   which is replaced by the pointer's URL (the rule `GatewayConnectionStore.load` already applies);
4. the pointer's `url`;
5. `http://127.0.0.1:8080`.

A reader re-reads the file when a connection to the resolved URL fails, so a long-running client follows a restart
onto a new port without being restarted itself.

**Security rule (readers).**
- Ignore the file unless: `schema` is known, the `url` host is `127.0.0.1`, `::1` or `localhost`, and (on POSIX) the
  file is owned by the current uid.
- A malformed or refused file is ignored with ONE visible warning. It never crashes the client.

**Python clients** keep `local_gateway()`. It reads the gateway's own records and the pointer is written from the same
values, so both agree; `local_gateway()` gains no pointer tier.

## Scope

### In scope

- The gateway: `serve` writes the pointer under the ownership rule; a helper `write_gateway_pointer(url, port,
  data_dir, written_by)`; `abstractgateway network status` shows the pointer's URL and whether it matches the bound
  port.
- The installers: write the pointer after choosing the port; delete it on uninstall (`install.sh`, `install.ps1`); the
  `--print` plan and the "by hand" twins show the write.
- `abstractgateway-console`: read `ABSTRACTGATEWAY_URL` (the standalone bug above), then the pointer.
- `abstractcode-tui`: the pointer as step 4, plus the 8080 re-point of a saved login.
- `abstractuic/app-server` (shared by the five Node apps): the pointer as step 4, then a release of every app that
  vendors it (flow, code web, observer, continuum, entity).
- The frozen `AbstractAssistant.app`: `config._local_gateway_url()` falls back to reading the pointer when
  abstractgateway is not importable. It is about 10 lines and must not import the gateway.
- One shared fixture set (valid file, non-loopback URL, wrong schema, malformed JSON, missing file), checked by every
  reader's tests. It sits next to the existing ui-kit contract fixtures, which `scripts/` already sync-checks.
- The contract text in `docs/architecture.md` and `docs/install.md` (admin port change: "clients follow at the
  restart"), plus an ADR for the file contract.

### Out of scope

- Remote gateways: the pointer is loopback-only. A gateway on another computer is still chosen in each client's
  Settings or with a flag.
- More than one installed gateway per user in the pointer: the first owner wins, and others need `--url`. Document it,
  do not model it.
- Liveness, health or auth in the pointer: no pid, no token.
- Changing how the gateway launches its own apps: they already receive the URL explicitly.
- Rewriting clients' saved logins beyond the old-8080 re-point.

## Acceptance criteria

- [ ] **Installer and a busy 8080.** On a machine with 8080 held by another process, a fresh `install.sh` leaves
      `~/.abstractframework/gateway.json` with the fallback port. Then, with no flags and no env, each of these
      reaches the gateway on that port:
      - `abstractgateway-console`;
      - `abstractcode`;
      - `npx -y @abstractframework/flow`;
      - the frozen `.app` (first sign-in field).

      Proof is a scratch-HOME run log.
- [ ] **Admin port change.** An admin changes the port in the console Network page and restarts. The pointer then
      shows the new port. A running TUI or Node app follows after one failed connection, without a restart. Before
      the restart the pointer still shows the old, working port.
- [ ] **Ownership.** A second gateway with its own data dir (like the :18850 hermetic console) starts and stops
      without changing the pointer. Test: temp HOME, two data dirs.
- [ ] **Uninstall** deletes the pointer and nothing else in `~/.abstractframework`.
- [ ] **Security.** Every reader ignores a pointer with a non-loopback URL, an unknown schema, or (POSIX) another
      owner, and warns once. The shared fixtures pass in Rust, Node and Python. Deleting a fixture turns its check RED.
- [ ] **`abstractgateway-console` honours `ABSTRACTGATEWAY_URL`** (regression test).
- [ ] **No test touches the real `~/.abstractframework/gateway.json`.** Every writer test uses a scratch HOME. After
      each suite, check with `find ~/.abstractframework -newer <stamp>`.
- [ ] **Docs** (`architecture.md`, `install.md`) and the ADR describe the contract.

## Dependencies

- The uncommitted 2026-09-27 Python work above (`local_gateway()`, the Assistant default, the installer hints) lands
  first.
- The release order follows `docs/backlog/overview.md`'s release trace, and every release needs the operator's go:
  1. gateway (writer);
  2. installers (root);
  3. ui-kit/app-server;
  4. the five Node apps;
  5. the two crates;
  6. the Assistant `.app` build.

## Receipts

- Adversarial design review, 2026-09-27 (this session): the narrowed pointer (option E) was recommended over
  re-implementing the rule, a pointer written by every serve, the serve record only, and doing nothing.
- Adversarial review of the Python side, 2026-09-27: the service-record tier is limited to pinned services, the
  installer hints were fixed, and the saved-sign-in re-point was added.
