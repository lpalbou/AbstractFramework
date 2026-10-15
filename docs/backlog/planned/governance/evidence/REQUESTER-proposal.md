# Who requested a run — findings and proposal (2026-10-14, for operator decision; nothing changed)

## Findings (code trace, file:line in the investigation report; GW = abstractgateway/src/abstractgateway, RT = abstractruntime/src/abstractruntime)

F1. `actor_id` is NOT the requester. In the runtime it is "optional provenance" (RT core/models.py:213-214) and in the gateway it is the RUNNER SELECTOR: every gateway start passes the literal `"gateway"` (routes/gateway.py:9120-9128, hosts/bundle_host.py:2370, routes/automations.py:633, entity_visits.py:1020, telegram_bridge.py:2453) and the runner ticks only runs whose actor is `"gateway"` (runner.py:1547-1550, 1611-1619). Summon/agora runs park under `"gateway:summon-pending"` to stay invisible until flipped (routes/entities.py:3515-3562). Children inherit it (runtime.py:4766-4773). Repurposing it would break the runner, the flips and every child.

F2. The gateway KNOWS who asks and throws it away. `POST /runs/start` resolves the principal (`GatewayPrincipal{user_id, tenant_id, roles, scopes, source}`, security/principal.py:12-37; routes/gateway.py:8955) and uses it for policy, catalog and the workspace folder digest, then starts the run without it (:9120-9128). Only catalog starts keep a signed copy in `_runtime.workflow_policy.principal` (:4259-4263). `POST /automations` has the principal (routes/automations.py:653) and uses `(tenant, user)` only to derive the automation id and the creation digest (RT automations/models.py:139-145) — no readable creator field (:435-453), although RT's own docstring says "hosts pass the owning principal" (RT automations/service.py:87-88).

F3. Ownership today is only IMPLIED by the data plane. Multi-user mode gives each principal its own run store under `<data_dir>/users/<tenant>/<runtime_id>/runtime`; the admin uses the default plane (GW service.py:259-301); "a session another account owns is absent from the caller's run store" (routes/session_archive.py:8-11). Single-user mode (the default) shares one plane: everyone sees everything and nothing says who asked. The run listing never reads the principal (routes/gateway.py:9616-9720). The only per-run human record is the entity summon's `_runtime.entity.participants = ["person:<user_id>", entity_id]` (routes/entities.py:3557-3560).

F4. The model is told the wrong user. `_detect_runtime_user` falls back to `actor_id`, so `runtime_grounding.user` reads `"gateway"` (abstractcore llm_client.py:1164-1177; live fixture orch13_ledger.json). Core also receives `X-AbstractCore-Actor-Id: gateway` (:16101-16110).

F5. The audit log is the only link principal → run_id: one JSONL line per mutating request with `principal_user_id`, `principal_tenant_id` and, for run starts, `run: {run_id, workflow, …}` (gateway_security.py:1143-1206; routes/gateway.py:8924-8949). It misses children, occurrences, Telegram, visits, backlog runs; it rotates at 50 MB × 10; older lines (Feb–May 2026) carry no principal and no run field. `account_activity.py` already mines it to attribute "Run started" to an account.

F6. Clients send no identity in the start body (AbstractCode web/TUI, Assistant, Flow: `flow_id`/bundle, `session_id`, `input_data`). `client_id` rides only `/commands` bodies. Clients CAN write arbitrary `input_data._meta` keys; the gateway strips only `automation`, `occurrence`, `discussion`, `creation_digest` (routes/gateway.py:8853-8871).

F7. The index has room. Both stores index `actor_id`, `session_id`, `parent_run_id` and the four `_meta` attribution fields (`automation_id`, `role`, `occurrence_index`, `session_kind`; RT core/run_attribution.py:35-94; storage/json_files.py:241-262; sqlite.py:176, 701-707). A proposed gateway backlog item already asks for a `principal_id` distinct from `actor_id` (abstractgateway/docs/backlog/proposed/2026-05-13_shared_identity_context.md:15,48).

## Goal

Every run — root, child, occurrence, discussion, entity visit, Telegram, backlog — carries ONE unambiguous, indexed, cheap-to-read answer to "who asked for this work, through what, on whose behalf", visible on list rows and detail, inherited down the tree, honoured by the model grounding, identical in single-user and multi-user modes, and impossible for a client to forge.

## Proposal (recommended): a `requester` attribution slot, runtime-owned, gateway-stamped

R1. **Model.** `vars._meta.requester = { user_id, tenant_id, source, via, at }`:
- `user_id`/`tenant_id`: the gateway principal (`admin`/`default` under the legacy token; the registry user in multi-user mode).
- `source`: how the principal authenticated (`user-registry` | `legacy-token` | `app-session` | `loopback` | `telegram` | `system`).
- `via`: the surface that asked: `abstractcode-web` | `abstractcode-tui` | `assistant` | `flow` | `observer` | `telegram:<chat>` | `automation:<id>` | `entity:<name>` | `backlog-runner` — from the request's `x-client-id` header when present (clients already send it on commands; they would send it on starts too), else the app-proxy's `X-AbstractFramework-App-Proxy` id, else `api`.
- `at`: ISO time of the request.
`actor_id` keeps its meaning (the executor) and is left alone.

R2. **Stamping (gateway, every start site).** `POST /runs/start`, scheduled starts, `POST /automations` (stored on the definition as `created_by = requester` AND stamped into each occurrence by the controller's dispatch as `{…creator, via: "automation:<id>"}`), discuss, entity visits/summons (`{user_id: caller, via: "entity:<name>"}`), Telegram (`{user_id: "telegram:<user>", source: "telegram"}`), backlog runner (`{user_id: "system", via: "backlog-runner"}`). The gateway STRIPS any client-supplied `_meta.requester` before stamping (same list as automation/occurrence/discussion).

R3. **Inheritance (runtime).** `START_SUBWORKFLOW` copies `_meta.requester` from parent to child verbatim (next to the existing `role: "descendant"` copy, runtime.py:4743-4773), so delegated agents, memory-compaction runs, listener children and run-facade children carry the same requester.

R4. **Index + wire.** `run_attribution.py` gains `requester_user_id`, `requester_tenant_id`, `requester_via` (and keeps the object in vars); both stores index them; list rows carry `requester: {user_id, tenant_id, via, source}`; the detail carries the full object with `at`. The Observer renders `admin · via AbstractCode` on cards and `requested by admin (AbstractCode web) at Oct 1, 09:14` in the (i); automations show `created by`.

R5. **Model grounding (abstractcore).** `_detect_runtime_user` prefers `_meta.requester.user_id` (then the existing fallbacks); `X-AbstractCore-Actor-Id` stays the executor. The agent stops believing its user is "gateway".

R6. **Backfill (optional, one-off).** For existing runs: root runs from the audit log (`principal_user_id` + `run.run_id`, retention permitting) and children by walking `parent_run_id` to a backfilled root; everything else stays `requester: null` and the Observer says "unknown (before attribution)". Never guess.

R7. **Visibility rules unchanged.** Planes keep separating users in multi-user mode; `requester` is an attribution, not an authorization. The admin's cross-plane views (`/host/runs`) gain the owner for free.

## Alternatives considered

A. **Gateway-only sidecar** (run_id → requester JSON in the plane, joined at listing). No runtime change, ships fast. But the gateway never sees child starts (the runtime spawns them) so children need a parent-chain walk at every listing; the record does not travel with the run (export, ledger, artifacts); the model grounding stays wrong. Rejected unless the runtime change is refused.

B. **Repurpose `actor_id` as the requester and add `executor_id`.** Semantically cleanest, largest blast radius (runner selector, bundle host, summon/agora flips, Telegram, inheritance, Core header). Rejected for now; a later rename wave could do it once `requester` exists.

C. **Derive from the data plane.** Works only in multi-user mode, says nothing about `via`, and the default (single-user) mode is exactly where the operator runs today. Rejected.

## Ordering and ownership (if accepted)

1. abstractruntime: `_meta.requester` inheritance + index fields + attribution tests (small; the occurrence/descendant path is the template).
2. abstractgateway: strip + stamp at every start site; `created_by` on automation definitions; rows/detail projection; the `x-client-id` header honoured on starts; audit line gains `requester` (already has the principal).
3. abstractcore: grounding preference (one function).
4. Clients: send `x-client-id` on `/runs/start` (AbstractCode web/TUI, Assistant, Flow, Observer) — optional, improves `via`.
5. AbstractObserver: render; "unknown (before attribution)" for old rows.
Skew: Observer tolerates rows without `requester`; gateway tolerates a runtime without the index fields (reads vars).

## Open questions for the operator — see the message
