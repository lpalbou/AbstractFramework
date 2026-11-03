# Governance backlog track — runtime as the owned isolation layer

## Status
Planned, 2026-10-15. Every item below carries operator decision gates (listed in the item) and
needs an adversarial review before build. Nothing has been changed in any repo: the track was
created from a read-only audit of abstractgateway and abstractruntime against the operator's
governance model (the operator's words, 2026-10-15), with a live read of the gateway on :8080.

## Purpose
Make the runtime the owned isolation layer of what a user (human or digital) does, make "admin" a
power rather than an identity, keep admins read-only outside their own runtime, treat entities as
digital users with their own runtime and owner-side operational control, and make authorizations
(folders AND tools) a per-(run, workflow) subset of the user's default, itself within the admin's
realm.

## The operator's model (verbatim, 2026-10-15)
- M1 "we only allow one admin per gateway at the moment"
- M2 "one admin should have its own runtime"
- M3 "if we have multiple admins, they should each have their own runtimes, as the goal is to
  differentiate the actions of different admins and to consider 'admin' more based on the power they
  are given"
- M4 "admins should only use their own runtime. no admin should probably be able to run something on
  any other runtime, but they should be able to have read-only access, as well as the possibility to
  change account parameters, and unlock certain situations. but i do not think an admin should be
  allowed to alter anyone's data, for traceability and auditability reasons."
- M5 "runtime should be owned and should be the isolation layer of what a user do"
- M6 "an entity is a digital user, and should behave / be treated mostly like a human user. so the
  owner of an entity should not be able to alter the entity runtime, but it should have read-only
  access to everything the entity has + have operational control over the entity (… the ability to
  suspend, elevate or decrease privileges to its entities, to start, pause, stop processes)"
- M7 "a user is a user. it has nothing to do with the OS since the gateway & runtime are virtualizing
  both digital and human users … there is the realm of things authorized by the admin (eg can read &
  write there, but only read there, and deny there, etc), within which, each user can define subsets
  of authorizations for different processes (… by default, probably the same as admin; but they will
  want, for different runs, to be able to select different authorizations …). authorizations are
  given per (run, workflow). And authorization here is in the broader sense: both the folders and the
  tools"

## Items
| ID | Item | Rows | Severity |
|---|---|---|---|
| 1019 | [Admin identity and the gateway home](1019_admin_identity_and_gateway_home.md) | 1–5, 15 | P1 |
| 1020 | [Admins are read-only outside their runtime](1020_admin_read_only_outside_own_runtime.md) | 6–12 | P0 |
| 1021 | [Plane isolation that cannot be switched off](1021_plane_isolation_cannot_be_switched_off.md) | 13, 14, 16–18, 29 | P0 (conditional) |
| 1022 | [Entities are digital users with their own runtime](1022_entities_are_digital_users.md) | 19–24 | P0 |
| 1023 | [Authorization per (run, workflow) within the admin realm](1023_authorization_per_run_workflow.md) | 25–28 | P1 |
| 1024 | [Requester attribution on every run](../../proposed/1024_requester_attribution.md) (proposed) | — | P1 |
| 1025 | [Cross-user read as a principal privilege](../../proposed/1025_cross_user_read_as_principal_privilege.md) (proposed) | 13 (read side) | decision |

Evidence copies: `evidence/REQUESTER-proposal.md`, `evidence/REQUESTER-adversary.md` (the
who-requested-a-run proposal and its adversarial review, 2026-10-14).

## Audit table (2026-10-15; GW = abstractgateway/src/abstractgateway, RT = abstractruntime/src/abstractruntime; "plane" = one account's data folder, its runtime)

| # | Principle | Case (what the code does) | Evidence | Sev | Recommendation |
|---|---|---|---|---|---|
| 1 | M1 | Any number of admins can exist: `POST /admin/users` accepts `roles:["admin"]`, no cap; the last-admin guard says "create or enable another admin account first". Live: one human admin. | GW routes/gateway.py:663-701, 634-660; users.py:529-575 | P1 | GW: refuse a second enabled human admin (409 `one_admin`), or drop M1 explicitly. |
| 2 | M1/M3 | A second admin gets its own plane, but every cross-plane admin view is computed from the caller's own data folder, so it sees only its own subtree (`/admin/runtimes`, drill-in, `/host/runs`); the `/host/runs` cache key is `(limit, window)` only, so two admins can be served each other's payload. | GW routes/gateway.py:1700-1711, 1733-1745, 29027-29073; admin_runtimes.py:148-162 | P2 | GW: build admin views from `gateway_data_dir_from_env()`; add the principal to the cache key. |
| 3 | M2 | The admin has no runtime of its own: `admin@default` with runtime `admin`/`default` is routed to the gateway ROOT folder, which also holds `users/` (every plane), `entities/`, `auth/users.json`, sessions, `audit_log.jsonl`, the backlog queue. Static token, tray token and the registry admin resolve to the same principal. Live: stranded plane `users/default/admin` (no owner). | GW service.py:259-271, 280-284; security/principal.py:66-90; security/gateway_security.py:930-941, 958-959 | P1 | GW: default `ABSTRACTGATEWAY_ADMIN_USES_DEFAULT_RUNTIME` to false; migrate the root's runs into `users/default/admin/runtime`; the root becomes a gateway home with no run store. |
| 4 | M3 | With user accounts off there is one service: every admin plus the static token share one plane; admins cannot be told apart. | GW security/sessions.py:193-219; service.py:105-114; entity_access.py:57-64 | P1 | GW: single-user mode allows exactly one admin identity. |
| 5 | M3 | Admin power is not limited to a tenant: `is_admin()` returns before the tenant check; catalog writes accept any `?tenant_id`. | GW security/authorization.py:354-357; routes/gateway.py:1985-2006 | P2 | GW: once the realm's scope is ruled (Q3), compare tenants in `_require_admin_principal`. |
| 6 | M4 | An admin can impersonate anyone: `PATCH /admin/users/{id}` with `rotate_token`/`token` works on any account (other admins included) and RETURNS the new token; the admin then acts inside that plane as that user. Changing `email` redirects recovery codes and the "self" auto-send recipient. | GW routes/gateway.py:716-786 (735-737, 751-760); users.py:613-616; mail/recovery.py:373-374 | **P0** | GW: never return another account's token (deliver to the user, or require `_same_account`); audit and notify on email change. |
| 7 | M4/M5 | Planes on disk with no reservation can be adopted: create/rebind check live records and reservations, never the disk. Live: `users/default/admin` and `users/local/local-admin` (19 MB, 12 ledgers of the old static-token identity) have no owner and no reservation; a new account bound to either inherits its runs. | GW users.py:460-482, 565-573, 634-643; live `/admin/runtimes`, `/admin/runtime-reservations` | **P0** | GW: treat every existing `users/<t>/<rid>` folder as reserved; backfill reservations for the two live folders. |
| 8 | M4 | An admin can rebind a plane's data to another account: `PATCH runtime_id` moves an account onto a free plane; `POST /admin/runtime-reservations/{id}/transfer` hands a former account's runs, sessions and memory to another account. | GW users.py:577-646, 690-758; routes/gateway.py:1436-1471 | **P0** | GW: refuse `runtime_id` edits on accounts whose plane exists; make transfer an archive mount, or gate it on a ruling. |
| 9 | M4 | Turning a workflow's availability off WRITES into every non-admin plane: starts each user's service and runner, appends `automation.pause` commands to their command store, writes `automation_pause_reasons.json` in their folder. | GW routes/gateway.py:8320-8344; automation_pause_reasons.py:76-90, 128-149 | **P0** (P1 if ruled an account parameter) | GW: enforce availability when an occurrence is admitted (refuse with a reason) instead of pausing users' automations. |
| 10 | M4 | `PUT /sessions/{id}/workspaces?account=` (admin) rewrites another account's `session_workspaces.json` in their plane, changing what their next runs can reach. | GW routes/gateway.py:29531-29609; session_workspaces.py:5-8, 30-44 | **P0** (P1 if ruled an account parameter) | GW: `?account=` read-only for admins; admins change account DEFAULTS only (`/workspace/policy/{account}`, stored at the root). |
| 11 | M4 | What "unlock" covers today: account Active switch and archive, token rotation, process-wide `/host/pause`/`/host/resume`, entity maintenance hold, `/models/unlock`. No admin path cancels/resumes a stuck run in another plane or answers its wait (every `/runs/*` and `/commands` route resolves the caller's plane). Admin reads of other planes are summaries only; `observer_path` carries no plane. | GW routes/gateway.py:29007-29024, 29059-29073; admin_runtimes.py:507-511, 666-722 | P2 | GW: after the ruling, a read-only `…/runs/{id}/ledger` for admins and an audited, closed list of unlock verbs. |
| 12 | M4 | An admin can purge registered data homes (logs, caches) of any plane. | GW routes/gateway.py:1403-1426; data_homes.py:114-118 | P2 | GW: limit purge to the root's own homes. |
| 13 | M5/M7 | Isolation between planes for tools rests on one admin switch: with `workspace_builtin_deny` off the built-in refusals list is empty; under "Allow everything" any path with no row gets the default mode, so a run reaches `users/*`, `entities/*`, `auth/users.json`, the audit log. Live posture: "Allow everything rw" with `/Users/albou/tmp/abstractframework` rw, which contains the data folder. | GW run_workspace_guard.py:76-82; workspace_policy.py:756-764, 829-836; runtime_config.py:1983-1990, 2127-2129; live `GET /workspace/policy` | **P0** (conditional on the switch) | GW: other planes, `auth/` and the audit log are a deny that cannot be switched off; the switch lifts only credential folders. |
| 14 | M5 | The prompt-cache key ignores the plane and can be set by the client: derived from session id (client-minted), provider, model, workflow, node; a client `_runtime.prompt_cache.key`/`namespace` wins (only `workflow_policy` is stripped). Two planes can share or poison one provider cache entry. | RT integrations/abstractcore/effect_handlers.py:907-921, 1060-1068; GW hosts/bundle_host.py:2580-2584; routes/gateway.py:4046-4053 | P1 | RT: add tenant and runtime to the derived key. GW: strip client `prompt_cache.key`/`namespace`. |
| 15 | M5 | Gateway-wide state lives inside the admin's plane: the single audit file, the user registry and sessions, the default tool grant, the MCP registry, skills. | GW security/gateway_security.py:201-215; users.py:85-89; tool_grants.py:83-93; mcp_run_tools.py:1-20 | P1 | GW: separate the gateway home from the admin's plane (same fix as #3). |
| 16 | M5 | The KG store is per plane by default, but `ABSTRACTGATEWAY_MEMORY_STORE_PATH` makes every plane share one file, and `/kg/query` accepts `scope=all`, `owner_id`, `all_owners`. | GW memory_store.py:88-96; routes/gateway.py:14931-14946 | P2 | GW: refuse a shared path in multi-user mode, or add tenant+runtime to owner ids. |
| 17 | M5 | MCP servers the admin registers are offered to runs in every plane and called with the admin's stored headers (credentials); stdio servers run outside the command sandbox. | GW mcp_run_tools.py:1-20, 249-262 | P1 | GW: per-account credentials or a per-server list of accounts; sandbox stdio servers. |
| 18 | M5 | A run with no requester tells the model the host's OS account (`USER`/`LOGNAME`). | RT integrations/abstractcore/llm_client.py:1164-1177 | P2 | RT: drop the environment fallback. |
| 19 | M6 | Entities have no plane of their own: the home and `runtime_<slug>.sqlite3` sit under the creator's folder, reached only through the caller's service; the registry's `runtime_id=<slug>` never exists on disk; an admin gets 404 on entities in user planes, so Accounts "suspend" only switches off the credential; `/admin/runtimes` lists only entities in the root. | GW entity_access.py:205-230; routes/entities.py:61-66, 3016-3018; entity_accounts.py:95; admin_accounts.py:398-421, 528-537; admin_runtimes.py:200-208 | P1 | GW: each entity gets its own plane (`entities/<slug>` at the gateway level with an `owner` pointer), resolved by slug, not by caller. |
| 20 | M6 | The owner cannot exercise operational control: state, tool policy, substrate, loop start/stop, personal grant, mounts and tasks are admin-only by route pattern; a non-admin creator can archive but not suspend or unarchive. Live: all 16 homes have `created_by: null` — no entity has an owner. | GW security/authorization.py:272-277; admin_accounts.py:54, 539-591; live manifests | P1 | GW: operational verbs to "admin OR creator"; data verbs stay closed (#21, #22). |
| 21 | M6 | Admins alter entity data directly: `PUT /prompt` (overlay on the composed system prompt), `POST /candidates/{id}/promote|reject` (writes memory store and journal), `POST /tasks/{id}/status`, `PUT /spec/phases` (the shared cognition rules). | GW routes/entities.py:4839-4860, 4567-4592, 5550-5570, 791 | **P0** | Rule which are privileges and which are the entity's mind; for mind writes: the entity proposes, the owner approves, the entity applies. |
| 22 | M6 | The creator writes files into the entity's workspace with `POST /entities/{name}/workspace/file`: no admin gate (the pattern covers only `workspace/mounts`), no check beyond visibility. | GW routes/entities.py:4183-4229; authorization.py:275 | **P0** | GW: an inbox drop the entity moves itself, or a ruling. |
| 23 | M6/M4 | Visit turn and close do not check that the caller is the stamped visitor; a mismatching speaker claim is replaced by the stamped visitor, so an admin's words are recorded as `person:<creator>`. | GW entity_visits.py:1083-1135, 1201-1232, 1515-1535; routes/entities.py:1722-1735 | P1 | GW: refuse unless `principal.user_id` is among the stamped participants. |
| 24 | M6 | An entity does not act under its own principal: summon runs live in the summoner's plane with actor `"gateway"`, the summoner's workspace policy and the client's `_runtime.tool_policy`; visit runs also actor `"gateway"`; nothing applies the entity account's own workspace policy to entity runs. | GW routes/entities.py:3210-3222, 3520-3563; entity_visits.py:1017-1021; routes/gateway.py:29363-29378 | P1 | GW: run summons in the entity's plane as the entity, record the summoner as requester, apply the entity's account policy. |
| 25 | M7 | A client's `_runtime.tool_policy` is not clamped: any `auto_approve_tools` list or `auto_approve_max_risk_rank: 4` (destroy) is honoured; the default grant is injected only when the key is absent (the code defers the clamp to a later "enforcement wave"). | GW routes/gateway.py:4046-4053, 8853-8868; tool_grants.py:248-261; hosts/bundle_host.py:2645-2662; RT effect_handlers.py:3025-3087 | P1 | RT: clamp each run's policy to the lower of the admin ceiling and the account default; GW stores both. |
| 26 | M7 | Automations default to `tool_approval: "auto"`, pre-approving every tool the runtime knows except messaging, ignoring the gateway grant. Live d18e1757 #13/#14: 64 tools auto-approved incl. `execute_command`, `shell_exec`, `execute_python`, `delegate_agent`, `self_improve`, `camera_capture_*`, `channel_fs_write`, while the shown default is `act`. | RT automations/controller.py:347-442, 542-551; automations/models.py:63; live `run_f66b78f7….json` | P1 | RT: intersect the automation grant with the owner's ceiling; destroy-tier tools default to `ask`. |
| 27 | M7 | Automation workspaces are not a fixed per-(run, workflow) subset: a definition with no workspace object or "Use my default" is re-resolved at each run from the owner's CURRENT default; "Use my default" is stored with a `workspace_only` placeholder the resolver overrides. Live #13/#14 ran `all_except_ignored` with the framework folder rw. | GW routes/automations.py:484-489, 557-566; automation_workspace_resolver.py:58-122; run_workspace_guard.py:203-209 | P1 | GW: show the resolved set on the definition, offer "freeze at creation", never present the placeholder as the policy. |
| 28 | M7 | The backlog runner is one process-wide runner at the root: saves its RunState directly (actor `backlog_exec_runner`) and runs codex with its own sandbox (env default `workspace-write`, approvals `never`) on the repo root — outside the workspace policy and command sandbox. | GW maintenance/backlog_exec_runner.py:825-839, 885-886, 925-931; service.py:800-826, 1182-1187 | P1 | GW: pass the admin realm's folders as codex's writable roots; record which admin requested the run. |
| 29 | M7 | Host-level switches apply to every plane (`--unsandboxed-commands`, the built-in deny switch); one gateway-wide tool default, no per-account default or ceiling. | GW command_sandbox.py:1-30, 78-104; tool_grants.py:83-93 | P2 | GW: per-account ceiling and default; refuse unsandboxed mode in multi-user. |

## What already respects the model (do not touch)
- Run, ledger, artifact, command, event-inbox and email stores are per plane, one runner per plane (GW service.py:280-301, 333-350).
- The signed workflow policy is bound to the plane through `host_tenant_id`/`host_runtime_id` (bundle_host.py:346-363).
- Workspace nesting holds: gateway caps ⊇ account ⊇ session ⊇ one-off, clamped at every door; rows inside the data folder count only in the account's own plane (workspace_policy.py:805-858; run_workspace_guard.py:139-282).
- Email binding is set by the host and client keys are stripped (bundle_host.py:2568); automations on untrusted input are re-gated (RT controller.py:347-442); session artifacts are isolated (bundle_host.py:2726-2733).
- Accounts are archived, never deleted; last-admin and no-self-deactivation guards exist; entity principals' token, roles and `runtime_id` are guarded at the registry (users.py:597-608, 716-729).
- Visit and summon participants are derived by the door and speaker claims are checked (routes/entities.py:1706-1712); the gateway's own session prompt-cache controls are scoped to the principal (routes/gateway.py:26491-26546).
- Cross-plane reads are admin-only and return summaries; turning availability back on does not resume users' automations.

## Build state (2026-10-15)
Branch `governance-security-1` in abstractgateway (uncommitted, not released): R3 runtimes bound forever (owner files + startup backfill, create/update refusals, archive/unarchive instead of transfer/purge), R4 claim-code tokens (`POST /auth/claim`, 24 h hold on admin-set addresses, old-address notice, console rendering), the unliftable plane deny (hard list stamped on every run incl. listener children and occurrences; entity runs reach their own `workspace/` only). Gate 1: NO-GO (1 P0, 4 P1) → fixed; Gate 2: GO-with-fixes → fixed (N1 TUI claim surfacing, N4 docs, lock-out backfill pass). Reports: `abstractgateway/untracked/governance/{LANE-ACCOUNTS,LANE-DENY,GATE-1,FIX-ACCOUNTS,FIX-DENY,GATE-2}.md`. Follow-ups: terminal console claim modal + archive controls; `docs/security.md` recovery disclosure (GATE-2 N3); runtime door message (abstractruntime workspace_scoped_tools.py:278-281).

## Operator rulings taken (2026-10-15)
- R1 **Admin is a user with admin powers and its own runtime** (1019): the gateway folder keeps only gateway files; one admin, one runtime.
- R2 **Privileges are a strict chain** (1023): "a run must never get more privileges than its user's default, and the user must never have more privileges than what the admin allows."
- R3 **A runtime folder stays bound to its account forever** (1020 rows 7–8): never adoptable, never re-bindable; archive (read-only) is the admin's only option when a user leaves; the two ownerless live folders get reserved to their original identity.
- R5 **Nothing is deleted, ever** (2026-10-15): "we never delete anything (we deprecate/archive), for auditability and interoperability / search accessibility of the data, both for human users and digital users. So a user never really disappears, it loses his access, but the history of everything that happened does not." Archived runtimes stay readable through the gateway's read paths (1020, 1021); cross-user READ is under study (`evidence/CROSS-USER-READ-best-practices.md`).
- R4 **Tokens: the claim-code design** (1020 row 6), adopted 2026-10-15 after `evidence/TOKEN-RESET-best-practices.md` (NIST SP 800-63B §4.1.2.2/4.2, Vault response wrapping, Entra Temporary Access Pass, Keycloak/Okta/Auth0 reset links, GitHub/Stripe show-once tokens): an admin can only invalidate or regenerate a token and never sees it; regeneration issues a one-time, short-TTL (1 h default, 24 h max), hashed claim code — mailed when SMTP is configured, else shown once to the admin to hand over — that the user exchanges at sign-in for the real token; every issue/claim/revoke audited; the user sees claimed-at/from; a new code invalidates the previous; entities and scripts bootstrap the same way.

## Operator rulings needed (the model is ambiguous here)
1. "Unlock": which acts — suspend/resume an account, rotate a token, host pause, cancel or resume another plane's stuck run, answer someone's tool-approval wait, clear an entity's seat or maintenance hold? Is writing a pause command into a user's automation (#9) an unlock or an alteration?
2. Is a conversation's workspace choice (#10) an account parameter or the user's data?
3. Is the admin realm per gateway or per tenant (today an admin in one tenant has powers over every tenant)?
4. May an owner archive or delete their entity (today: archive yes, suspend/unarchive no)?
5. Which entity writes are privileges and which are mind: tool policy, substrate, skills, work order, tasks, prompt overlay, memory-candidate promotion, the shared phase spec?
6. Where should an entity's plane live, and should summon runs be stored in the entity's plane (summoner recorded as requester) or the summoner's?
7. Are the static operator token and the tray a distinct admin with its own plane, or "system"? Where do gateway-wide files (users, audit, catalog, MCP) live if not in an admin's plane?
8. Should "Use my default" follow the live default, or freeze per (run, workflow) at creation?
9. Is tool authorization a strict chain (admin ceiling ≥ user default ≥ run), and may `tool_approval: auto` exceed the user default?
10. Is "one admin" a hard cap?
11. May an admin read run CONTENT in other planes, or summaries only?
12. Is single-user mode covered by this model at all?
