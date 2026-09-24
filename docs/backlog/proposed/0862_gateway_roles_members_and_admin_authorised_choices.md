# Proposed: 0862 — Gateway roles: admin, member (and maybe viewer), with admin-authorised choices

> Package: abstractgateway (security, routes, web console, abstractgateway-console); abstractcore (read-only consumer of the allow/deny lists)
> Type: proposal
> Created: 2026-09-24
> Priority: normal (the two authorization bugs listed under "Found while writing this" are higher and do not wait for this item)
> Labels: security, rbac, accounts, network-exposure, console

## Metadata

- Created: 2026-09-24
- Status: Proposed
- Completed: N/A
- Governing ADRs: ADR-0018 (durable run gateway and remote host control plane), ADR-0021 (deployment
  topologies), ADR-0033 (install profiles, config entrypoints, server boundaries)
- ADR impact: needs an ADR revision or a new ADR if promoted. The role set and "members choose only within what
  the admin authorised" are cross-task rules, not task sequencing.
- Builds on: `planned/gateway-control-plane/0146_gateway_rbac_scope_policy_matrix.md` (central route-policy
  table and Alice/Bob isolation, in progress), `0147` (per-principal config/secrets/defaults), `0148`
  (workflow catalog ACLs), `0143` (per-principal runtime router), `0142` (tenant isolation),
  `0232` (sandbox `execute_command`), `0858` (console toggle for `allow_engine_install`).

## Why `proposed/` and not `planned/`

The backlog convention: `planned/` = committed implementation work, `proposed/` = plausible but uncommitted,
with decisions still open. The operator said he is unsure and asked what RBAC would mean in practice. Three
decisions are still open: whether to add a viewer role, whether a member may configure its own entities (the
entity-mutation rows were signed admin-only, see below), and how strongly to push a member account when the
network mode changes. The enforcement substrate this builds on is already `planned/` (0146). Promote this
item once the operator rules on the three questions under "Promotion criteria".

## Origin

Operator, 2026-09-24 (verbatim): "lastly, i wonder if we should not also force the creation of one user
account to protect the admin account... but i am unsure that we have proper RBAC and what that would mean in
practice. we do have a logic of creating users, so maybe we can use that, but in practice, beyond just
providing separated runtimes it doesn't change much i think... so maybe more a docs/backlog/planned/ item on
better RBAC ? (eg only admin can purge, create accounts, define whitelist/blacklist of the gateway as a
whole... from which users can only select amongst what's authorized etc?"

## Summary

The gateway knows two kinds of principal: admin, and everyone else. The admin/else split is enforced by one
route-policy table, and it already holds the host-level acts (engines, models, apps, network, host control,
users, purge) for admins only. What is missing is the other half of the operator's sentence, "users can only
select amongst what's authorized". A non-admin today can use every provider key the operator configured, pick
any model, send its own tool-approval policy past the operator's default, add endpoint URLs that the gateway
host will call, and widen its own filesystem posture. So a second account mostly gives the operator a separate
runtime (runs, workflows, entities, memory), not a smaller set of rights. This item proposes named roles
(`admin`, `member`, optional `viewer`), a gateway-wide allow/deny policy for providers and models that
members choose within, clamps on the three member self-service surfaces that can widen rights today, a
per-role contract test, and a recommendation for the "protect the admin account" question: prompt for a
daily-use member account when the network mode leaves localhost, not at first run.

## Today's state (evidence)

Line numbers are from the live working tree read on 2026-09-24 around 12:55 CEST. abstractgateway HEAD
`7be3e7c` has uncommitted edits by other seats (missions M/O/R/Y/Z), so some numbers may move by a few lines.

### How a request gets a role

- A principal carries free-form `roles` and `scopes` (`abstractgateway/src/abstractgateway/security/principal.py:12-37`).
  `is_admin()` is the only role predicate: `"admin" in roles` (`principal.py:24-25`).
- Roles in use: `admin`; `user` (the default for a new record, `users.py:176`, `users.py:507`); `entity` for
  entity principals (`users.py:205-209`); and `readonly`, used only by the loopback dev-read principal
  (`principal.py:90-105`). No code gives `user`, `readonly` or any scope a meaning in route authorization.
  The middleware always calls `authorize_gateway_principal(..., admin_required=True)`
  (`security/gateway_security.py:1103-1108`), and `require_gateway_authorization` has no caller outside its
  own module (grep). Scopes are therefore inert for route authorization.
- The static operator token and the tray's ephemeral loopback token both resolve to `local_admin_principal()`
  (`principal.py:67-87`, `gateway_security.py:731-771`).
- User auth is on when `ABSTRACTGATEWAY_USER_AUTH` / `AUTH_MODE=users` says so (`users.py:91-106`). A bare
  first-run `serve` on loopback turns it on and bootstraps `default/admin` (`first_run.py:1-27`,
  `first_run.py:154-164`). An explicit token-only environment keeps user auth off and binds `0.0.0.0` by
  default (`first_run.py:128-145`).
- Under user auth, every principal except the bootstrap admin gets its own service and data root
  `<data>/users/<tenant>/<runtime>/` (`service.py:103-111`, `service.py:250-290`). Without user auth there is one
  shared service (`service.py:103-111`, `service.py:246-247`).

### The route classes

- Public, outside `/api/gateway`: `/`, `/console`, `/docs`, `/redoc`, `/openapi.json`, `/api/health`, the
  triage capability URLs and `/apps/handover/{code}`
  (`abstractgateway/tests/test_gateway_route_authorization_contract.py:49-67`).
- Public inside the boundary: `POST /session/login` and `POST /session/claim` only
  (`gateway_security.py` `_public_auth_path`; pinned by `test_gateway_route_authorization_contract.py:250-277`).
- Admin-only: every row of `GATEWAY_ROUTE_POLICIES` (`security/authorization.py:77-296`). Every GET without
  a row is open to any signed-in principal, and so is every write on the `USER_LEVEL_WRITES` allowlist
  (`test_gateway_route_authorization_contract.py:74-186`).
- The contract test pins: every route is behind the middleware or on the public list; every write route has
  exactly one decision (policy row, or on the user-level allowlist); no policy row is dead; a non-admin gets a
  403 on one representative route per row; representative user-level writes pass
  (`test_gateway_route_authorization_contract.py:235-426`). It knows two roles only, and it checks writes
  only. No test pins which GETs a non-admin may call.

### Admin vs. non-admin, area by area (user auth on)

| Area | Admin | Non-admin today | Evidence |
|---|---|---|---|
| Accounts: list/create/edit/disable/delete, rotate tokens | yes | no (403) | `authorization.py:78` (`/api/gateway/admin` prefix); routes `routes/gateway.py:464-588` |
| Own credential (rotate own token) | via admin lane | no self-service route; only `GET /me` | `routes/gateway.py:302-315`; route table (no `/me` write) |
| Last-admin guard | none: an admin can delete/disable/demote the only admin | n/a | `routes/gateway.py:573-588`, `users.py:532-617` (no admin-count check; grep "last admin" finds nothing) |
| Purge / reset: data homes, retained runtimes | yes | no | `authorization.py:78`; `routes/gateway.py:926`, `:998` |
| Purge own drafts | yes | yes (own runtime) | `test_gateway_route_authorization_contract.py:110` |
| Network exposure: change mode, restart to apply | yes | no; `GET /network` yes, `lookup_public` refused | `authorization.py:119-124`; `routes/network.py` `_require_admin_principal` + `lookup_public and not admin` |
| Host control: restart, shutdown, pause, update, tray | yes | no; host state/metrics readable | `authorization.py:97-114` |
| Engines: install/start/stop, job continue/cancel | yes, and install also needs `allow_engine_install` (default on only for a loopback bind) | no; status readable | `authorization.py:161-168`; `routes/engines.py:112-115`, `:147-172` |
| Models: download, delete, load, unload, lock, unlock, cancel download | yes | no; catalog/installed/loaded readable | `authorization.py:134-153`, `:177-182` |
| Browser apps: install, update, launch, stop | yes | no; `POST /apps/{id}/open` for self, app logs readable | `authorization.py:187-192`; `test_...contract.py:94` |
| Provider keys, gateway-wide (Core config rows, gateway-scope endpoint profiles) | yes | no (403 in handler) | `routes/gateway.py:13922-13928` |
| Provider keys, own (user-scope endpoint profile, own URL + key) | yes | yes, any `base_url`; `discover-models` calls that URL from the gateway host | `routes/gateway.py:25000-25050` |
| Use the operator's provider keys | yes | yes: the Core config/env keys are the baseline for every principal | `provider_connections.py:281-292` ("API keys are Core-owned, so the AbstractCore store is the baseline in EVERY mode") |
| Model/provider choice for runs, sandbox, generation | any | any: client `provider`/`model` win, defaults fill only the gaps | `hosts/bundle_host.py:2348-2352`; `routes/gateway.py:25226-25240` |
| Gateway-wide allow/deny list of models/providers | does not exist | n/a | `allowed_models` is stored per endpoint profile (`provider_endpoint_profiles.py:34`) and shown in the console (`console.py:7966-7990`); grep finds no server-side enforcement in abstractgateway |
| Capability defaults | gateway-wide store, and `apply-recommended` | own overlay only | `authorization.py:197-202`; overlay proven by hermetic probe (below) |
| Tool approval: default grant | yes (`PUT /tool-grants/default`) | no, but the client's own `tool_policy` wins over the default and is not clamped | `authorization.py:284-289`; `tool_grants.py:18-21`, `tool_grants.py:248-262`; `hosts/bundle_host.py:2354-2371` |
| Workspace/filesystem posture, gateway-wide | yes (`/admin/user-workspace-policy`, runtime-config) | no | `authorization.py:78` |
| Workspace/filesystem posture, own | yes | yes: may set `mode: blacklist` ("allow everything, refuse the blocked roots") and add any `workspace_allowed_paths`; the paths are "additive", never bounded by the gateway's | `routes/gateway.py:27082-27130`; `runtime_config.py:1378`, `:1484-1490` |
| Server file helpers, artifact import/export | yes | no | `authorization.py:204-210` |
| Workflows: shared registry / catalog | yes | no (403) | `routes/gateway.py:6748-6778`; catalog under `/admin` |
| Workflows: own registry (upload, delete, publish) | yes | yes (own runtime) | `test_...contract.py:134-144` |
| Runs, chat, generation, memory, KG | own world (bootstrap admin = default runtime) | own runtime | `service.py:250-290`; Alice/Bob matrix in 0146 |
| Entities: create, chat, visit, meet | yes | yes (per-root quota) | `routes/entities.py:135-175` |
| Entities: configure (substrate, tool policy, skills, voice, prompt, loop, mounts), templates, phase spec | yes | no, not even for its own entities | `authorization.py:252-295` |
| Audit log, admin logs, processes, email, backlog, triage, reports | yes | no | `authorization.py:78-86` |
| Console tabs | all | Runtimes tab hidden; Users section, reservations, workflow Import, apply-recommended and setup hidden; Models/Engines/Apps/Network render read-only | `console.py:9800-9861` |

The audit log is written by the middleware to `<data>/audit_log.jsonl` (`gateway_security.py:537-547`);
reading it is admin-only (`authorization.py:79`).

### Invitations today

Claim links exist but are admin-only by construction. They are minted by the local CLI for the bootstrap admin
(`first_run.py:279-306`, `firstrun_cli.py:97-102`). They are redeemed only from a loopback socket peer with no
proxy headers (`routes/gateway.py:409-416`), only with user auth on (`:418-425`), and they refuse a non-admin
target (`:439-443`). A member account is created by an admin in the Users tab or with
`POST /api/gateway/admin/users`, which returns the raw token once (`routes/gateway.py:492-532`). There is
no CLI to create a member: `abstractgateway-config` has `bootstrap-admin` only (`config_cli.py:565`).

## The gap

1. **Roles are binary and implicit.** "Member" means "not admin". A new route is admin or everybody, and
   nothing lets the gateway say "members may do X, viewers may not".
2. **Nothing bounds a member's choices.** A member spends the operator's provider keys on any model, adds
   arbitrary endpoints that the gateway host calls, and chooses its own tool approval, workspace mode and
   paths. The admin has no gateway-wide allow/deny list to choose within.
3. **Separated runtimes separate data, not the operating-system account.** Every runtime runs in the same
   gateway process, as the same OS user. With an unclamped `tool_policy` and a self-widened workspace, a
   member's agent run reaches what that OS user reaches (0232: `execute_command` is raw `sh -c` with no
   containment). That is why the operator's instinct is right: a second account "doesn't change much".
4. **A daily user cannot do some ordinary things**: configure its own entity, rotate its own token, see the
   runtime-config posture (the GET docstring says any principal may read it, `routes/gateway.py:597`, but the
   `/admin` prefix row returns 403), or import a workflow from the console (the button is hidden at
   `console.py:9826` although the server accepts own-registry uploads).
5. **The contract test pins two roles and writes only.** Reads that should be admin-only rely on a policy row
   existing. Nothing fails if a new admin-class GET ships without one.

## Proposed roles

- **admin**: the operator. Everything below, plus the host.
- **member** (today's `user`; keep `user` as an alias forever): a daily user with its own runtime, who
  chooses within what the admin authorised.
- **viewer** (optional): signs in, reads its own runtime and the shared catalog, and starts nothing. It is
  cheap in code, because the middleware already classifies every request as read or write
  (`gateway_security.py:1003`). One rule, "viewer and write and not logout → 403", plus one contract-test
  column would do it. No use case has been named yet (a wall display? an observer seat?), so add it only when
  the operator names one.
- **entity** principals keep their own lane (`users.py:153-170`). This item does not change them.

## Permission matrix

"Own" = the caller's runtime (`<data>/users/<tenant>/<runtime>`). "Within policy" = inside the gateway-wide
allow/deny lists and ceilings the admin sets. Today's value is shown where it differs.

| Capability | admin | member | viewer (optional) |
|---|---|---|---|
| Sign in, sign out, read `/me` | yes | yes | yes |
| Rotate own token / set own credential | yes | **yes (new self-service)** | yes |
| Create, disable, delete accounts; reset others' tokens; mint invites | yes | no | no |
| Change roles; last-enabled-admin guard | yes, guarded (**new**) | no | no |
| Purge/reset data homes, retained runtimes, other runtimes | yes | no | no |
| Delete own runs/drafts | yes | yes | no |
| Network exposure (mode, restart), allowed origins, proxy trust | yes | no (status read-only) | no |
| Host control (restart, shutdown, pause, update, tray) | yes | no | no |
| Engines: install, start, stop | yes (+ `allow_engine_install`) | no (read status) | no |
| Models: download, delete, load, unload, lock | yes | no (read); optional later: "request a download" | no |
| **Gateway-wide provider/model allow & deny lists** | **yes (new)** | read the effective list only | read |
| Provider keys, gateway-wide | yes | no; uses them **within policy** (today: all of them) | no |
| Own endpoint profiles (bring your own URL/key) | yes | **only if the admin allows it** (new flag; default off once network mode is not `localhost`, because `discover-models` makes the host call the URL) (today: always) | no |
| Choose provider/model for runs, sandbox, generation, own capability defaults | yes | **within policy** (today: anything) | no |
| Gateway-wide capability defaults, apply-recommended | yes | no | no |
| Tool approval ceiling (default grant) | yes | a run's `tool_policy` is **clamped to the ceiling** (today: client wins) | no |
| Workspace posture, gateway-wide | yes | no | no |
| Workspace posture, own | yes | **narrowing only**: may block paths and choose among admin-allowed roots; `blacklist` mode and new allowed roots need the admin (today: free) | no |
| Server file helpers, artifact import/export | yes | no | no |
| Browser apps: install, update, launch, stop | yes | no; `open` a running app | no |
| Shared workflow catalog: promote, default, ACL, block | yes | no | no |
| Own workflow registry: upload, publish, delete | yes | yes (console Import shown) | no |
| Run workflows, chat, generate, memory/KG | yes | yes, own runtime | read own history only |
| Entities: create, chat, visit, meet | yes | yes (quota) | no |
| Entities: configure own (voice, skills, substrate within policy) | yes | **operator ruling needed** (signed admin-only today, `authorization.py:234-257`) | no |
| Entity templates, shared phase spec | yes | no | no |
| Audit log, admin logs, processes, email, backlog, triage, reports | yes | no | no |
| Runtime-config posture (read) | yes | read-only, secrets redacted (matches the GET docstring) | read-only |

## Admin-authorised choices (the allow/deny lists)

- One gateway-wide store (runtime-config key, admin write, audited like every admin write), for example
  `model_policy: {providers: {allow: [...], deny: [...]}, models: {allow: [...], deny: [...]},
  members_may_add_endpoints: bool}`. Patterns allowed (`openai/*`, `mlx/*-4bit`). Deny wins. An empty
  allow list means "everything the gateway can reach", which is today's behaviour, so existing installs do
  not change on upgrade.
- One enforcement chokepoint in the Gateway, reached before any Core call. It resolves `(provider, model)`
  for every member-reachable door: `runs/start`, `runs/schedule`, `sandbox/generate`, `embeddings`,
  `runs/{id}/images|audio|videos|music|voice/*`, entity chat/visit substrate, and capability-default
  overlay writes. A denied choice returns a machine-readable 403 (`reason_code: model_not_authorised`) and
  never silently substitutes. It applies to admins too, unless the admin explicitly overrides. The discovery
  routes (`/discovery/providers`, `/discovery/providers/{p}/models`, `/models/catalog`, the console
  pickers) filter to the effective list for members, so the UI offers only what will run.
- The same chokepoint clamps a client `tool_policy` to the default grant's ceiling for members (the
  "enforcement wave" `tool_grants.py:18-21` already names), and bounds member workspace self-service to
  narrowing.
- `allowed_models` on an endpoint profile becomes an input to the same resolver instead of display-only
  metadata.

## "Protect the admin account": recommendation

**Do not force a second account at first run.** Offer it, and require an explicit decision, when the network
mode leaves `localhost`.

- **Single-user local install (`localhost`)**: a member account protects nothing there today. The same OS
  user can read the bootstrap token file (`<data>/auth/bootstrap-admin-token`, `config_cli.py:260-264`) and
  mint an admin claim link from the CLI (`first_run.py:279`). The member's runs execute in the same process
  as the same OS user. Until the clamps above land, a member can self-widen tools and paths. Forcing the
  account would add a step to the one-line install (the 0855 wave's whole point) and buy false security.
- **`lan` / `internet`**: the risk changes. Credentials cross plain HTTP (abstractgateway `docs/security.md`,
  "What `lan` does NOT give you"). A captured daily-use session that is an admin session can install
  engines, launch apps, change exposure and restart the host. The docs already advise "prefer non-admin
  accounts for daily use" (`abstractgateway/docs/security.md:258`), but nothing prompts for it.
- **So tie it to `POST /network`** (`routes/network.py`, `network_exposure.apply_network_change`):
  - leaving `localhost` while the registry has no enabled member: the console/TUI/tray flow asks the admin to
    create one (name, then the invite link below). `lan` may be confirmed without one, via a recorded
    acknowledgement (`{at, by}`, the same shape as `acknowledge_internet`). `internet` requires either
    a member to exist or a second explicit acknowledgement;
  - the status payload gains `accounts: {members: n, admin_sessions_from_non_loopback: n}` and a warning row
    while admins sign in from other machines;
  - optional, off by default: `admin_sign_in: loopback_only`, which refuses admin sessions from non-loopback
    peers. This is the one setting that really protects the admin on a network. It is safe only once the
    member role is useful day to day.
- Order: land the member clamps (allow/deny lists, tool-policy clamp, workspace narrowing) first.
  Prompting for a member account before then makes the account mostly cosmetic.

## Migration path for existing installs

- The bootstrap admin (`default/admin`, runtime `default`) stays admin and keeps the default data root
  (`service.py:250-261`). The static operator token and the tray token stay admin.
- Existing records with `roles: ["user"]` become members (`user` is an accepted alias). Records with no
  roles already default to `user` (`users.py:290-298`).
- Allow/deny lists start empty, so nothing changes until an admin sets them. The tool-policy clamp and
  workspace narrowing change behaviour for existing members. Ship them with a one-release warning mode:
  log and audit what would have been clamped, then enforce.
- Token-only installs (user auth off): member accounts cannot be isolated there (see bug 1 below). Creating
  a non-admin user in that mode should be refused with the fix line (`ABSTRACTGATEWAY_USER_AUTH=1`), and
  `/session/login` should refuse registry non-admins while user auth is off.
- **Invitations**: generalise the claim code into an invite. An admin calls
  `POST /api/gateway/admin/users/{id}/invite`, which returns a single-use link with a short TTL and the same
  digest-only storage as `first_run.py`. Differences from the first-run claim: it is minted by an admin over
  the API rather than by the local CLI; it may be redeemed from a non-loopback peer, since members are remote,
  but only when network mode is `lan`/`internet` and only over the configured origins; it can target a
  non-admin only, and never mints an admin session; and redemption rotates the member's token and shows it
  once. The first-run admin claim keeps its loopback-only rule unchanged (`routes/gateway.py:409-443`).
- Add `abstractgateway-config users add|disable|invite` (CLI twin of the console, per the "launch flags"
  rule).

## Acceptance criteria (if promoted)

- [ ] `GatewayRoutePolicy` carries a minimum role (`viewer < member < admin`) instead of
      `admin_required: bool` (`authorization.py:33-74`). `USER_LEVEL_WRITES` becomes the member rows of one
      per-role table.
- [ ] The contract test pins **every route (reads and writes) for every role**: for each `(method, path)` in
      the live route table and each role in {anonymous, viewer, member, admin}, the expected outcome
      (public / allowed / 403 / 401) is recorded. A new route lands RED until it has a row for every role.
      The served-surface proof fires one representative per row per role through the real middleware.
- [ ] A test that deletes one policy row turns RED. A test with an empty allow/deny store proves today's
      behaviour is unchanged.
- [ ] Allow/deny lists: a member picking a denied provider or model gets 403 `model_not_authorised` on
      every door listed above, and discovery lists only allowed models. An admin override is audited.
- [ ] A member's `tool_policy` above the ceiling is clamped, and the run records the clamp. A member cannot
      set `mode: blacklist` or add a root outside the admin's allowed roots.
- [ ] Self-service token rotation for members. The last enabled admin cannot be deleted, disabled or demoted.
- [ ] The network flow prompts for a member account (or a recorded acknowledgement) when leaving
      `localhost`. The status payload reports account posture.
- [ ] Member invite links: single use, TTL, never admin, and redeemable only on a network mode.
- [ ] Console: members see only what they can use, and the workflow Import button is shown for own-registry
      uploads. Terminal console parity.
- [ ] Docs: abstractgateway `docs/security.md` role table; root `docs/faq.md` / `docs/glossary.md` "member".

## What this does NOT cover

- Multi-tenant isolation between organisations (0142) and per-principal secret storage beyond endpoint
  profiles (0147).
- OS-level containment of agent tools (0232). Roles decide who may ask for a tool; only a sandbox decides
  what the tool can reach.
- TLS, reverse proxies and certificates (network exposure docs; mission Z).
- Quotas, rate limits or billing per member. SSO/OIDC/LDAP accounts.
- Entity principals' own rights, shared/org memory, per-app tool grants (reserved in `tool_grants.py:23-25`).
- Anything the console hides but the server allows. Hiding is UX. Enforcement is the policy table.

## Found while writing this (authorization defects, not part of the proposal)

1. **Token-only mode: a registry non-admin signs in and lands in the operator's world.** `/session/login`
   authenticates registry users whatever the auth mode (`routes/gateway.py:362-376`), and session
   authentication does not check the mode (`security/sessions.py:345-397`). With user auth off,
   `get_gateway_service()` returns the one shared service (`service.py:103-111`). The contract test's
   justification for `USER_LEVEL_WRITES` names a `_principal_requires_isolation` function that does not exist
   in the tree or its history (`test_gateway_route_authorization_contract.py:100-107`). Hermetic probe
   (`untracked/missionAA/probe_tokenonly.py`, scratch data dir and HOME, in-process TestClient): the admin
   token creates `bob` (`roles: ["user"]`); bob's bearer is refused (401), but bob's session login succeeds
   with `routing.mode: single-user`. Bob's `PUT /config/capability-defaults/output/text` then rewrote the
   **gateway-wide** AbstractCore text default (the admin read back `openai/gpt-bob`), and bob's user-scope
   endpoint profile appeared in the admin's list. Only the workflow-registry doors are guarded in that mode
   (`routes/gateway.py:6748-6778`). `POST /bundles/{id}/deprecate` and `/undeprecate`
   (`routes/gateway.py:7267`, `:7301`) do not call that guard, although its docstring and
   abstractgateway `docs/security.md:176-178` say they do. In the probe, deprecate reached the handler (404
   for a missing bundle) where reload was refused (403).
2. **`ABSTRACTGATEWAY_PROTECT_READ=0` turns every unauthenticated read into the admin.** When auth is not
   required, the middleware falls back to `local_admin_principal()` (`gateway_security.py:1080-1086`). The
   network-mode check refuses only `SECURITY=0` / `PROTECT_WRITE=0` (`network_exposure.py:223-262`,
   `first_run.py:69-74`), so `lan` is accepted with reads unprotected. Hermetic probe
   (`untracked/missionAA/probe_read.py`, user auth on, `PROTECT_READ=0`, no credential): `GET /me` →
   admin, `GET /admin/users` → 200, `GET /admin/runtime-config` → 200, `GET /files/list` → 200, and
   `auth_check("lan")` → ok.

## Promotion criteria

- The operator rules on: (a) whether a viewer role is wanted (and for what); (b) whether members may
  configure their own entities, and which verbs; (c) prompt-with-acknowledgement vs. hard requirement for a
  member account on `lan` / `internet`.
- 0146's route-family matrix is closed, or explicitly merged into this item.
- Bugs 1 and 2 above are fixed first (they are defects, not RBAC design).

## Receipts

- Hermetic probes and route inventory: `untracked/missionAA/` (`routes.txt` = every served route with its
  admin/user class and handler location, `probe_tokenonly.py`, `probe_read.py`).
- Mission R network-exposure report: `untracked/missionR/REPORT.md`. Mission Q/S claim links:
  `untracked/missionQ/REPORT.md`, `untracked/missionS/REPORT.md`.

## Status update 2026-09-25 (post-release trace)

- Both defects under "Found while writing this" are fixed and released in abstractgateway 0.4.1
  (missions BB and Z): token-only mode admits only admin accounts to the console and browser apps
  (existing non-admin sessions end at next use, create-user 409, last-admin guard), and
  `PROTECT_READ=0` is refused for `lan` / `internet`. Evidence: `untracked/missionBB/REPORT.md`
  (45 tests, 10/10 mutants), `untracked/missionZ/REPORT.md`; gateway CHANGELOG 0.4.1 upgrade notes.
- The three promotion rulings are now a board-visible operator gate: 0870.
