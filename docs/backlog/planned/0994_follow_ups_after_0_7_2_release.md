# 0994 — Follow-ups after the 0.7.2 release (gateway 0.9.0, core 2.21.0, runtime 0.8.1, root 0.7.2)

> Package: abstractframework, abstractcore, abstractgateway, abstractruntime, abstractentity, abstractuic, abstractcode, abstractflow
> Type: task
> Created: 2026-09-30
> Priority: normal
> Labels: follow-up, release, installer, upgrade-safety, email, responsive, ci

## Summary

Findings from the 2026-09-30 end-to-end proofs (Mac + Linux GPU), the Mac mini upgrade-safety
audit and the evening requirements sweep that are not recorded in 0987 (which ends at item 28).
Numbering continues 0987 so the sweep's draft numbers (29–41) stay valid references. Items
marked **fix on branch ... pending release** have a branch with a red-first test but are not
merged or published; close them only when the release ships. Split any item into its own file
when it is picked up.

## Current code reality (2026-09-30)

Released: root 0.7.2 (9ac3bff), abstractgateway 0.9.0, abstractcore 2.21.0, abstractruntime
0.8.1; npm code 0.8.0, flow 0.5.0, observer 0.4.0, continuum 0.5.0, entity 0.4.0; ui-kit 0.3.2.
Branches opened today and not merged: root `fix/installer-never-fail`, core
`fix/config-keep-unknown-keys` (1c32560, 748bf5c), gateway `fix/email-safety-followups`,
gateway `fix/apps-install-and-shutdown`, entity `fix/flaky-test`, the kit type-scale work on
orchestrator A's AbstractUIC branch.

## Status after the 0.8.0 wave (2026-10-01)

The 0.8.0 release wave (abstractframework 0.8.0 with abstractgateway 0.10.0, abstractcore 2.22.0,
AbstractRuntime 0.8.2, abstractassistant 0.11.0 and the apps code 0.9.0, flow 0.6.0, observer
0.5.0, continuum 0.6.0, entity 0.5.0) carries the branches named below. Items marked **Completed
in 0.8.0** close when that wave is published (cite the tags then). Still open: 36 (Windows lag CI
job), 39 (operator token rotation), 42 (Update job log token redaction), 46
(`apps.adopt_external`), 47 (`--no-print-token` for the service), 48 (admin boundary around a
user's sealed mailbox), 50 (Apps page npm retry), and 51–54 (recorded during the 0.8.0 preparation: Assistant test
segfault, Telegram bridge setting, llms copies refresh, site screenshots), and 67–71 (recorded in round 3: thin-client principle, no-env
settings and shared pickers, contract-test probes, session-bleed patch releases, future features). Gateway-native TLS (item 45's last part) is
[0995](../proposed/0995_gateway_native_tls_for_remote_browsers.md); the console and app UI notes
of the round-1 rework are
[0996](../proposed/0996_console_and_app_ui_follow_ups_after_the_round_1_rework.md).

## Items

**Root installers**
29. Transient non-lag failures (network error, 5xx, a reset wheel download, a wheel build
    interrupted) still take the "retrying without it" voice fallback (`scripts/install.sh` ~2162,
    `scripts/install.ps1` ~1532) and finish an install with less. Operator: "the upgrade should
    never fail; if there is a lag or delay, it should auto retry." Retry transient errors like
    index lag, then stop with the cause; only a deterministic build failure may take the fallback,
    and the summary says in red what was dropped. The crates (`abstractgateway-console`,
    `abstractcode`) and the npm apps get the same wait through their registries' lag.
    **Fix on branch `fix/installer-never-fail` (root) merged into the 0.8.0 wave.** Owner: root.
    **Completed in 0.8.0** (release wave 2026-10-01; close with the published tag).
30. (upgrade-safety D-A) `PORT="${ST_PORT:-8080}"` (`install.sh` ~1980) with
    `seed_network_setting` (~985-1011) and `service install --port` (~2659) silently revert a
    Network port changed in a console or through the API, and restart the gateway on the old
    port. Default-port installs are unaffected. Keep the stored port unless `--port` was given;
    red-first test with a stubbed `network status --json` (stored 18094 vs bootstrap 18095 → no
    `network set --port 18095`). **Fix on branch `fix/installer-never-fail` (root) merged into the 0.8.0 wave.** Owner: root.
    **Completed in 0.8.0** (release wave 2026-10-01; close with the published tag).
31. (upgrade-safety D-C) Installs older than 0.6.2 read never-recorded options as opted out
    (`install.sh` ~1776-1812: a 0.4.0 install stays without the core CLI). Infer "off" only
    when the option existed at the recorded `GATEWAY_VERSION`. **Fix on branch
    `fix/installer-never-fail` (root) merged into the 0.8.0 wave.** Owner: root.
    **Completed in 0.8.0** (release wave 2026-10-01; close with the published tag).
36. The Windows index-lag retry path is covered by pwsh unit tests only. Add a CI job on
    `windows-latest` that injects a lag (a local index answering 404 for one pin, then serving it)
    and asserts the same full install succeeds with voice. Owner: root CI.

**AbstractCore**
32. (upgrade-safety D-B) Unknown keys in the user's `abstractcore.json` are dropped at the first
    settings save (`config/manager.py` ~697-702 filters at load, `_save_config` ~1071-1178 writes
    without them); pre-existing since core 2.19.0. Keep the raw document and merge known sections;
    test: a top-level custom key and `vision.user_note` survive a setter. **Fix on branch
    `fix/config-keep-unknown-keys` (core, 1c32560) merged into the 0.8.0 wave.** Owner: core.
    **Completed in 0.8.0** (release wave 2026-10-01; close with the published tag).
38. The Docker docs still name 2.13.x `abstractcore-server` image tags. **Fix on branch
    `fix/config-keep-unknown-keys` (core, 748bf5c: examples name 2.21.0) merged into the 0.8.0 wave.**
    Regenerate the tag with every release. Owner: core.
    **Completed in 0.8.0** (release wave 2026-10-01; close with the published tag).
**AbstractGateway / AbstractRuntime**
33. Resuming a paused `email.received` automation does not nudge the mail worker, so mail in the
    first ≤15 s after the resume can be missed (0.9.0 fixed creation only). **Fix on branch
    `fix/email-safety-followups` (gateway) merged into the 0.8.0 wave.** Owner: gateway.
    **Completed in 0.8.0** (release wave 2026-10-01; close with the published tag).
34. A Node.js runtime install started while another one runs fails on the shared `.part`
    download (a retry works). Serialize with a lock or a per-request temp file. **Fix on branch
    `fix/apps-install-and-shutdown` (gateway) merged into the 0.8.0 wave.** Owner: gateway.
    **Completed in 0.8.0** (release wave 2026-10-01; close with the published tag).
35. A stop that lands while gateway startup is in progress does not wait for it (product side; the
    test side was fixed 2026-09-30). **Fix on branch `fix/apps-install-and-shutdown` (gateway)
    merged into the 0.8.0 wave.** Owner: gateway.
    **Completed in 0.8.0** (release wave 2026-10-01; close with the published tag).
40. (upgrade-safety N3) Pausing an automation does not stop an occurrence already in retry
    backoff (pre-existing). **Fix on branch `fix/email-safety-followups` (gateway) merged into the 0.8.0 wave**; the runtime side ships as AbstractRuntime 0.8.2 (pausing cancels the occurrence in backoff). Owner: gateway /
    runtime.
    **Completed in 0.8.0** (release wave 2026-10-01; close with the published tag).
42. (upgrade-safety N1) The Update job log (admin-only, held in memory) contains the installer
    summary, whose Terminal line carries the admin token. Redact the token in the captured log
    (keep it in the operator's own terminal output only), and test that the job log served by the
    API never contains the token. Owner: gateway (Update job) with root (installer summary).

**CI flakes**
37. Two timing-dependent tests, one in AbstractEntity and one in the gateway automations suite
    (names in `untracked/wave-071/drive/STATUS.md`). Make them deterministic (fake clock) or
    quarantine with an issue. **Fix on branches `fix/flaky-test` (entity) and
    `fix/apps-install-and-shutdown` (gateway) merged into the 0.8.0 wave.** Owner: entity / gateway.
    **Completed in 0.8.0** (release wave 2026-10-01; close with the published tag).
**Responsive typography (published Code 0.8.0, Flow 0.5.0, Observer 0.4.0)**
41. Dominant body text is 11–12px on phone and tablet in Code and Flow, and on the Observer
    Launch list (harness threshold 14–17px); Flow library tap targets are below 44px (7/54 and
    45/75 on phone). Fix in the kit's touch type scale (`--af-font-body` ≥ 14px under
    `(pointer: coarse)`) plus the apps' dense lists; re-render the published packages with the
    same harness. **Fix on AbstractUIC `feat/state-toggles` (ui-kit 0.3.3) merged into the 0.8.0 wave** (then patch
    releases of Code, Flow, Observer after the operator's validation). Owner: kit + Code + Flow +
    Observer.
    **Completed in 0.8.0** (release wave 2026-10-01; close with the published tag).
**Remote access over http (operator P1, 2026-09-30 20:30)**
43. The browser apps (Code 0.8.0, Flow 0.5.0, Observer 0.4.0, Continuum 0.5.0, Entity 0.4.0), the
    consoles and the Assistant's web views call secure-context-only APIs (`crypto.randomUUID`,
    `navigator.clipboard`, `getUserMedia`, `Notification`, `serviceWorker`, `navigator.share`);
    over plain http on a LAN/Tailscale address (not localhost) Code dies before rendering
    ("crypto.randomUUID is not a function"). Every id comes from a kit `randomId()` (v4 from
    `getRandomValues` when `randomUUID` is absent), clipboard falls back with visible feedback,
    mic/camera show one honest sentence ("Voice and camera need an https address"). Tests run the
    code path with `crypto.randomUUID` undefined; proof over a non-localhost origin in Chromium and
    WebKit. **Fix on `fix/secure-context` (apps, panel-chat, Assistant) + the kit helper on AbstractUIC
    `feat/state-toggles`, merged into the 0.8.0 wave.** Owner: kit + apps.
    **Completed in 0.8.0** (release wave 2026-10-01; close with the published tag).
44. `/apps/<id>/manifest.webmanifest` answers 401: the app proxy gates every request on the app
    session cookie, and browsers fetch a manifest without cookies unless the link carries
    `crossorigin="use-credentials"`. Apps set `use-credentials` (and relative `start_url`/`scope`);
    the gateway serves manifest, icons and favicon without the session gate (API paths stay gated).
    **Fix on apps `fix/secure-context` + gateway `fix/apps-behind-proxy`, merged into the 0.8.0 wave.** Owner:
    apps + gateway.
    **Completed in 0.8.0** (release wave 2026-10-01; close with the published tag).
45. HTTPS for remote use. Documented path: on the gateway machine `tailscale serve --bg
    http://127.0.0.1:<port>` → `https://<host>.<tailnet>.ts.net/` (TLS by Tailscale; `tailscale serve
    reset` undoes it); gateway 0.9.0 already trusts a same-machine proxy's `X-Forwarded-*`
    (uvicorn `forwarded_allow_ips` = loopback), so sign-in, cookies (`Secure`) and the app handover
    work behind it (receipt: `untracked/day-review/https-proxy/B-self-proof.md`). Real blocker found later the same night: the console SIGN-IN behind the proxy answers 403
    (origin not allowed) on 0.9.0 — workaround `abstractgateway network set --allowed-origins
    https://<host>.ts.net`; **fixed on gateway `fix/apps-behind-proxy` @df1f257** (forwarded-origin
    check, manifest/icons served without the session gate, `browser_gateway_url` / `browser_url`
    fields, Tailscale paragraph in the docs, 23 tests). The console's top-bar address and first-run
    tile still show the plain-http address (console seam, orchestrator A). Gateway-native
    TLS (`network set --https-cert/--https-key`, automatic `tailscale cert`) only if contained —
    see [0995](../proposed/0995_gateway_native_tls_for_remote_browsers.md). Owner: gateway docs + network.
    **Completed in 0.8.0** for the sign-in 403, manifest and docs (release wave 2026-10-01; close with
    the published tag); verify the console's top-bar address and first-run tile at the final gateway head.
46. A gateway adopts any app server it finds on ports 3001–3005/3000/3007 as "running"
    (`apps_manager.py:113-125`, `:1350`) with no way to turn that off, so a second or scratch gateway
    on the same machine serves another gateway's apps at `/apps/<id>/`. Keep the default (the dev
    flow `scripts/start-local.sh` relies on it) but add a documented `apps.adopt_external` setting
    (console + CLI flag `serve --no-adopt-apps`, never an env var) and a test. Owner: gateway.

47. The admin token banner prints on every loopback start of `serve`, so each OS-service start
    writes the token into the service's error log (`~/Library/Logs/AbstractGateway/gateway.err.log`
    on macOS). The "never hide the admin token at first launch" rule covers the first run only:
    `service install` should register the LaunchAgent/systemd unit with `--no-print-token` (the
    console and tray keep showing the token file's path). Owner: gateway.
48. "Admin never reads mail" holds for every read route (verified 2026-09-30, receipt
    `untracked/day-review/W3-email-safety.md`), but an admin can rotate a user's token or transfer
    the user's runtime to an account the admin controls, which carries the sealed mailbox
    credentials. Document this boundary in docs/email.md and evaluate binding the mailbox seal to a
    user-held secret (password / OS keychain of the user's own session). Owner: gateway.
49. Gateway 0.9.0: an admin could read another user's `event_inbox` and ledger files (email
    subject and body) through `GET /files/read` because the server workspace root defaults to the
    gateway's working directory — the data dir under launchd. **Fixed on gateway
    `fix/email-safety-followups` @141ba50 (data dir and credential folders refused on every server
    file route), merged into the 0.8.0 wave.** Owner: gateway.
    **Completed in 0.8.0** (release wave 2026-10-01; close with the published tag).
50. The gateway's Apps page installs the npm apps at their latest version with no retry through
    npm registry lag or a transient network error; it asks the user to try again. Give it the same
    bounded retry ladder as the installer (`scripts/install.sh` `AF_INDEX_RETRY_DELAYS`), with the
    cause shown when the ladder runs out. Owner: gateway.

**Recorded during the 0.8.0 release preparation (2026-10-01)**
51. AbstractAssistant: an intermittent local segfault in the setup of `tests/test_live_replies.py`
    (a Qt callback in `abstractassistant/ui/session_switcher.py`), 3 of 7 local full runs, never seen
    in CI. Reproduce headless, find the callback that outlives its widget, fix with a test that
    crashes without the fix. Owner: assistant.
52. The Telegram bridge can only be switched on with an environment variable. Settings are never
    environment variables: give it a console setting (web + terminal) and a CLI flag, with the
    variable imported once like the email variables. Owner: gateway.
53. The per-package llms copies (each package's `llms.txt` / `llms-full.txt` as vendored or quoted
    elsewhere, e.g. the docs assistant's corpus and the site) need a refresh after the 0.8.0 docs
    passes. Owner: root + each package.
54. Site screenshots to recapture for 0.8.0: the Accounts page (desktop), the Apps page with the
    grouped sidebar, the terminal console shots, Code web (desktop and phone), the Assistant's and
    the Observer's Active switch. Owner: site.

55. The AbstractGateway 0.10.0 wheel carries `console_islands.py` stamped with ui-kit 0.3.3 and the
    0.3.3 islands bundle hash, while ui-kit 0.4.0's islands differ by one comment line (no
    functional drift; the 2026-10-01 local deploy re-synced on its build branch only). Re-sync from
    the released kit at the next gateway release; the drift test passes only with
    `ABSTRACTUIC_SRC` pointing at the kit the sync used, so pin that in CI. Owner: gateway.
56. `abstractcore.testing.mailserver.free_port()` picks a free port and binds it later, so parallel
    suites can collide (Errno 48); the gateway's SMTP test fixture retries on EADDRINUSE since
    0.10.0. Bind port 0 inside the server instead and return the bound port. Owner: core.
57. AbstractCore `tests/.../test_mlx_residency_eject_leak_unit` fails on a Mac where the real `mlx`
    package is installed (also at v2.21.0; Linux CI has no `mlx`). Make it independent of an
    installed `mlx`. Owner: core.
58. Gateway docs (README, getting-started, api, automations, security) build curl examples with
    `$(cat …/bootstrap-admin-token)`; the convention is the token as a direct `--token <value>` /
    `Authorization: Bearer <admin token>` placeholder. Owner: gateway.
59. ui-kit `theme.css` still carries "0.3.3" comments (copied verbatim into the consoles, so a change
    needs a console re-sync), and `monitor-memory/README.md` keeps an incident-history sentence;
    fix both with the next kit release that bumps those packages. Owner: kit.

64. Agent runs ignore the default text route's `base_url`: `PUT
    /api/gateway/config/capability-defaults/input/text` with `base_url` is stored and read back, but
    `abstractgateway/core_config.py` `text_default()` returns provider, model and reasoning only, so the
    run's `llm_call` goes to the provider's default address (a remote LM Studio set as the default text
    route is bypassed for the local one). Present in 0.7.2 and 0.8.0 (macOS verification 2026-10-01,
    `untracked/release-r2/reports/verify.md` B1). Fix with a red-first test through a real run start.
    Owner: gateway (+ runtime if the payload drops it). Priority: high for remote-model setups.
65. The default workspace root is the folder the installer was run from, so an upgrade run from
    another folder moves it. Record it at first install and keep it. Owner: root installers + gateway.
66. A light install does not build `abstractcore-console` (the gateway console and `abstractcode` are
    built); decide whether light installs it too and make the installer summary say which consoles
    were built. Owner: root.

**Recorded during round 3 (2026-10-01)**
67. Thin clients hold no run-input state (operator principle, 2026-10-01): execution and its
    inputs live in gateway/runtime and the replayable ledger; clients read and forward. Recorded
    as a use case of [0993](0993_one_ledger_replay_many_views.md) with the clients to audit (Code
    web, Code TUI, Assistant, Observer Discuss, Entity, Flow run panel). Owner: 0993.
68. No environment variables for settings (rule reminder, fixed in round 3): the entity "mind
    substrate" fallback `ABSTRACTGATEWAY_ENTITY_CHAT_PROVIDER` / `_MODEL`
    (`abstractgateway/entity_chat.py`, `env_registry.py` `entities.substrate`) is removed in favour
    of the gateway text route default plus a per-entity override set in the console and the Entity
    app. General rule: **apps use the shared AbstractUIC pickers (route, voice); no bespoke
    provider/model/voice forms** — the Entity app moves onto the kit pickers. ADR state: the rule
    belongs in ADR-0032 (gateway-first apps) or a new ADR; record it there before closing. Owner:
    gateway + entity + kit. Close with the round-3 release, citing the tags.
69. A contract test must never trigger remote provider probes: the abstractflow editor contract
    test reached `api.acemusic.ai` and `api.elevenlabs.io` during setup on flow 0.10.0 (round-3
    gates). Product fix: provider probes run only on an explicit request (never on load/setup);
    test fix: refuse network in the contract suite so a probe goes RED. Owner: flow (+ gateway if
    the probe is server-side). See [0849](0849_test_suites_must_not_reach_the_operators_live_stack.md).
70. Release impact of the session bleed: AbstractCode web 0.9.1 (round 3 @53b36ae) and
    abstractgateway 0.10.1 (@9c7475c, `artifact_not_in_session`) patch releases. Release notes and
    docs must not claim the fix before both are published; close citing both tags. Owner: root
    release sequence.
71. Future features recorded from the same discussion:
    [0997](../proposed/0997_cross_session_references_under_user_supervision.md) (reference other
    sessions and their attachments under a ledger-recorded user grant; today a session sees only
    its own) and [0998](../proposed/0998_at_mentions_of_agents_and_entities_in_a_session.md)
    (@-mentions of agents and entities; agora/collaborative workspaces, with 0212/0213/008).

**Recorded during the 0.9.0 release (round 3, 2026-10-01/02)**
67. MCP tools in entity (AI user) runs and plain `llm_call` nodes: an entity run and an `llm_call` node can call `mcp::<server>::<tool>` under the same Ask gate; red-first tests. Owner: runtime + gateway.
68. MCP client pooling: `abstractruntime` `mcp_facade` starts a stdio server once per run (not per call) and closes it at run end. Owner: runtime.
69. Gateway terminal console: an "Enabled for agents" switch for MCP servers, parity with the web switch and its note. Owner: gateway.
70. Code web tool picker labels MCP tools `Mcp:<server>`; use `MCP · <server>` as the console does. Owner: code.
71. Cold boot under load: `abstractcore` `mlx_provider.py` imports `outlines` eagerly (lines 24-30); constructing MLXProvider must leave outlines, transformers and torch out of `sys.modules` (test). Owner: core.
72. Cold boot: `abstractruntime` `llm_client.py` (~10247, 10281, 10424) builds the default client eagerly; build it on first use (counting-factory test). Owner: runtime.
73. `tests/test_abstractflow_editor_gateway_contract.py` triggers remote provider probes (acemusic, elevenlabs) caught by the network guard at teardown; loading the editor contract makes no outbound call. Owner: gateway.
74. Code web e2e timing at load (automation occurrence lag, 15 s event wait, cold first sign-in): bind waits to gateway readiness; 3 consecutive green runs at load ≥ 30. Owner: code.
75. Code sidebar: sticky section headers need an opaque background so both stay visible while scrolling. Owner: code.
76. Observer: dead CSS from the removed Story view (`.run_overview`, `.timeline_event`, `.lc*`, `.produced_row`, `.subrun_chip` in styles.css/observe.css/space.css); and no obvious way from the Board into a run view. Owner: observer.
77. Kit sign-in form: confirm the "Keychain Not Found" toast is gone on the operator's Mac (token field autoComplete=off + password-manager ignore attributes; the user field keeps autoComplete="username"). Owner: kit.
78. Entity Settings after-shots (1440/834/390, Mind/Voice) and their report were not captured (worker died at the capture step). Owner: gateway/entity.
79. Console warm-up: pages that wait on the warm-up say so inline (today only a pill). Owner: gateway.
80. Operator dev flow `multiagent-coding` 0.0.19 (imported into runtime/) fails to compile: `text_of` shadows a sandbox helper since runtime 0.4.32; rename it in the flow. Owner: operator flow.
81. Islands/theme re-sync after every kit change is manual; the deploy build and gateway CI fail loudly when the drift pin is stale (the 0.10.0/0.11.0 wheels carry islands stamped with an older kit). Owner: gateway (see 55).
82. Kit WorkflowPicker shots: fixtures carry basic-agent so the "Gateway default" entry is realistic. Owner: kit.
83. Console Accounts head has a dead zero-size duplicate `#open-create-entity`; keep one element with that id. Owner: gateway.
84. `POST /runs/start` with a crafted ref to a NONEXISTENT artifact of another session starts the run (the guard fires only for existing session-private artifacts; no leak): answer 400 too. Owner: gateway.
85. Entity own-time loop ignores the MTP setting (visits and summons honour it). Owner: gateway.
86. Kit AfSelect: Enter in its search box does not pick the highlighted option (click works). Owner: kit.
87. Console entity voice picker lost the per-provider "needs an API key" labels after the move to the kit VoiceSettings. Owner: gateway + kit.
88. `ABSTRACTGATEWAY_ENTITY_MAX_OUTPUT_TOKENS` is still an env var: move it to a gateway setting (settings are never env vars); root `scripts/plan_walkthrough.py` (~125-135, ~1149-1151) still documents/exports `ABSTRACTGATEWAY_ENTITY_*` variables the gateway no longer reads. Owner: gateway + root.
89. The round-3 adversary skipped WebKit, the light theme and the wide-width matrix (budget) and the release-content check of the 0.9.0 branches: re-run before the next UI release. Owner: release.
90. Release-prep checklist (0.9.0 wave needed fixes at publish time): bump EVERY version source — AbstractUIC root `package.json` (the tag validates it), `abstractassistant/_version.py`, the gateway FastAPI `app.py` version and `live_deltas.ABSTRACTRUNTIME_FLOOR` with the install-profile tests, Code's CHANGELOG heading `[web X]`; widen panel-chat's ui-kit peer range with every kit minor (0.2.3 shipped without `^0.5.0` → 0.2.4). Add a pre-tag script per repo that greps these. Owner: release. (2026-10-04: applied by hand for the 0.10.0 preparation; the script is carried as 0999 item 11.)

**Operator decisions (raised 2026-10-01, round 2)**
60. Light installs include local voice (Supertonic, faster-whisper) although "light" reads as
    external providers only: keep or strip?
61. The display name on mail the runtime sends: the part before the @, or none?
62. Entities have no permanent end, so Delete is unavailable for them (greyed out with the reason):
    add one?
63. Bundles that ship with the gateway can be deleted (with a warning that only a reinstall brings
    them back): keep deletable?

**Operator actions**
39. Rotate the Linux GPU box's gateway admin token: it sat unredacted in local evidence logs until
    13:53 on 2026-09-30 (the logs were redacted then; the token itself was not changed). Owner:
    operator (never assignable).

## Acceptance criteria

- [ ] Each branch-fixed item closed only when its release ships, citing the tag and the red-first
      test.
- [ ] Items 36, 42, 43 and 44 fixed with a test that goes RED without the change.
- [ ] Item 45: the Tailscale paragraph is in the gateway docs and the console's Network page hint.
- [ ] Item 39: operator confirms the rotation.

## Receipts

`untracked/sweep-2026-09-30/SWEEP.md` (drafts 29–41, rows 2, 3b, 7, 9),
`untracked/upgrade-safety/REPORT.md` (D-A, D-B, D-C, N1, N3),
`untracked/wave-071/drive/STATUS.md` (Linux/Mac end-to-end, CI flakes),
`untracked/sweep-2026-09-30/rerender/` (published-app re-render).
