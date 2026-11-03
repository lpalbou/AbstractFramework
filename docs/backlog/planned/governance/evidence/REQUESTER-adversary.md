# Adversarial review — "Who requested a run" proposal (2026-10-14)

Scope: REQUESTER-proposal.md, verified against live code and the live gateway (:8080, read-only). GW = abstractgateway/src/abstractgateway, RT = abstractruntime/src/abstractruntime. Nothing changed.

## Verdict: GO-with-changes — the direction (a gateway-stamped, runtime-inherited, indexed attribution slot) is right; the proposal as written is wrong on five load-bearing facts and under-costs by ~3x.

---

## A. Facts F1–F7

| | Verdict | Evidence |
|---|---|---|
| F1 actor_id = runner selector | **Confirmed** | GW runner.py:1547-1550 and 1611-1619 tick only `actor_id == "gateway"`; parked `"gateway:summon-pending"` GW routes/entities.py:3519-3525, flipped at :3562; also `"gateway:agora-pending"` GW integrations/agora_bridge.py:312-318 (not in the proposal); `"backlog_exec_runner"` GW maintenance/backlog_exec_runner.py:825-838 (a RunState saved directly, never through `start_run`). Children inherit RT runtime.py:4769. Stamping a requester elsewhere does NOT collide with the flip (the flip rewrites `run.actor_id` and `_runtime.entity` only, :3556-3563). |
| F2 gateway knows, throws away | **Confirmed** | GW routes/gateway.py:8955 resolves the principal; :9120-9128 starts with the literal `"gateway"`. Catalog starts sign `principal.public_dict()` into `_runtime.workflow_policy` (:4259-4263) and `_policy_principal` reads it back (GW hosts/bundle_host.py:328-340) — a signed, unforgeable principal already travels on ONE class of runs. The proposal does not reuse it. |
| F3 single-user is "where the operator runs today" | **Refuted** | Live `GET /api/gateway/me`: `auth.mode: "users"`, `user_auth_enabled: true`, `routing.mode: "per-principal"`, principal `admin/default` via `legacy-token`. The audit file shows three principals (`admin` 40,542; `local-admin` 54; `user` 5). Option C was rejected on a false premise. |
| F4 model told "gateway" | **Confirmed, wrong repo** | `_detect_runtime_user` is RT integrations/abstractcore/llm_client.py:1164-1177 (NOT abstractcore). It prefers `trace_metadata.user/user_id` over `actor_id` already; the fix is feeding the requester into trace_metadata, not reordering. Worse: the env fallback `USER`/`LOGNAME` (:1173-1176) tells a run with no requester the gateway host's OS account. |
| F5 audit log is the only link | **Confirmed, numbers wrong** | Writer GW security/gateway_security.py:1164-1166; `run` field GW routes/gateway.py:8924-8949. Live file `runtime/audit_log.jsonl` (19.9 MB, 43,488 lines since 2026-03-18, NOT rotated yet): 2,766 `/runs/start` lines, **112** carry `run.run_id` (field exists since 2026-10-02). See G. |
| F6 clients send no identity; strip list | **Confirmed, incomplete** | Strip GW routes/gateway.py:8853-8871 is called ONCE (:9023, `/runs/start`). The `/runs/{id}/schedule` wrapper embeds the client's `input_data` as the TARGET run's `vars` (:9457) unstripped — a client can plant `_meta.occurrence` (and tomorrow `_meta.requester`) on a scheduled target today. `x-client-id` appears in GW only as an audit-header allowlist entry (security/gateway_security.py:243-246); 0 of 43,488 audit lines carry it; no client sends it on starts (abstractcode web/src/lib/gateway_client.ts:100-105, abstractflow src/utils/gatewayClient.ts:1260, abstractassistant gateway/client.py:506). |
| F7 "the index has room" | **Confirmed, cost understated** | JSON: explicit field dict RT storage/json_files.py:241-262 AND a versioned persisted sidecar (`_SCAN_SIDECAR_VERSION`, :311, :353) that must be bumped or cached rows lack the key. Sqlite: CREATE TABLE :169-181, `_RUN_COLUMNS` :700-707, ALTER-per-column with duplicate-column race handling and a backfill sweep :200-250 — three new columns + index + backfill. GW list rows are an explicit dict (routes/gateway.py:9773-9806); `run_summary` "never returns full vars" (service.py:1394-1396); `/host/runs` has its own projection (admin_runtimes.py:558). Nothing rides free. |

## Findings

**1. P0 — `requester.at = now` breaks occurrence replay identity.** `_occurrence_vars` must be byte-identical on replay (RT automations/controller.py:746-752); the runtime digests `vars` wholesale (RT core/runtime.py:1436-1447; core/run_identity.py:69-75) and a different digest raises `RunIdentityConflict` → after a crash between child-create and wait-save, the occurrence can never re-attach (contract C1). Fix: freeze the requester at ADMISSION next to `automation_title` (controller.py:581-583), with `at = fired_at`; never stamp at dispatch; never put a clock in a digested field.

**2. P0 — R3's "one copy next to role: descendant" covers 1 of 5 child paths.** START_SUBWORKFLOW copies `_meta` key-by-key (occurrence, discussion only; runtime.py:4743-4756). MEMORY_COMPACT rebuilds vars from scratch (:5896-5902). `run_facade._build_child_vars` copies `_runtime` only (RT integrations/abstractcore/run_facade.py:229-248; used :346-352, :377-383, :608-615). Bundle-host listener children copy `_runtime`+`_limits` only and go through `runtime.start`, not an effect (GW hosts/bundle_host.py:2812-2835). The scheduled wrapper's target run is a root started later from embedded vars (:9457). The proposal names listener and facade children as beneficiaries; they would silently carry nothing. Fix: one RT helper `inherit_attribution(parent_vars, child_vars)` called at all four RT sites, exported for bundle_host's listener seam, with a test per site that deletes the call and goes red.

**3. P1 — Stamp at the funnel, not "every start site".** Every gateway start except the backlog exec runner passes through `BundleHost.start_run` (bundle_host.py:2361-2371 → `runtime.start` :2757), and the principal is a contextvar (`current_gateway_principal`, GW security/principal.py:40-52) on every HTTP path. Stamp there (contextvar for HTTP; an explicit `requester=` kwarg for Telegram/agora/scheduler) and strip there. That closes the schedule hole (F6), covers `/automations` discuss (routes/automations.py:1051-1059 → RT `start_discussion`, which builds `_meta` itself, :402-417 — needs the kwarg), and shrinks the GW change from ~12 sites to 1 + 4 callers.

**4. P1 — `via` is forgeable and `source` enum is fiction.** The app-proxy header is a same-machine fail-safe marker the loopback proxy OVERWRITES (abstractuic/app-server/src/gateway_session_proxy.js:25-34; GW security/same_machine.py:143-178), not an identity. A browser can send any `x-client-id`. Real `principal.source` values: `legacy-token`, `user-registry`, `loopback-dev-read`, `loopback-ephemeral:<label>`, `workflow-policy`, `local` (principal.py:19, :79-90, :98-104; gateway_security.py:935-941; users.py:266-275; sessions.py:259-268 copies the ORIGINAL source, so "app-session" never exists). Fix: `via` derived server-side only from trusted facts — `principal.source` + proxy marker present/absent + route (`/runs/start`, `/automations`, summon, telegram, schedule). If a client hint is kept, store it as `claimed_client` and render it as claimed.

**5. P1 — "Who" is an account, not a human, and the proposal must say so.** Static token, browser admin session and the desktop tray's ephemeral token all resolve to `user_id="admin"` (principal.py:66-90; gateway_security.py:936-941). Only `source` and `token_fingerprint` (already in `public_dict`, :27-36) separate a curl script from the console from the tray. Record both; label the row "admin (console)" / "admin (token 851f…)" / "admin (tray)".

**6. P1 — Wrong repo and wrong seam for R5.** The grounding function is in abstractruntime (finding F4). Step "3. abstractcore" collapses into step 1. Decide whether a run with NO requester should be told nothing rather than `LOGNAME`.

**7. P1 — Backfill is 7%, not "retention permitting".** Live measurement (all 8,759 runs vs the audit file): 104 of 2,038 roots covered; 514 of 6,721 children resolvable by parent chain; **618 of 8,759 runs**. Uncovered roots: 1,922 chats, 6 controllers, 3 discussions, 3 legacy schedules. `GET /audit/tail?max_bytes=4000000` holds 7.5 hours (8,113 lines, 26,679/43,488 of the file are `/runs/ledger/batch`) and is useless for backfill — read the file. The older sibling `runtime/gateway/audit_log.jsonl` (2,264 lines, 2026-02-15 → 05-05) has zero `run`+principal lines and adds nothing. "Unknown (before attribution)" is the COMMON case for the Observer for months; design the card for it.

**8. P1 — Skew: old runtime + new gateway yields an ambiguous mix.** Index rows never load vars (routes/gateway.py:9792 comment), so "gateway reads vars" is false for lists: roots would show `admin`, children `unknown`. Gate the gateway stamp on a runtime floor (or hide `requester` entirely below it).

**9. P2 — Namespace collision for Telegram and `on_behalf_of` missing.** `user_id: "telegram:<user>"` mixes a chat identity into the registry-id space; the run executes on the OPERATOR's plane. Model it as `user_id` = the account the run executes as, `on_behalf_of` = `telegram:<chat>:<user>`. The goal sentence says "on whose behalf" — the model has no field for it.

**10. P2 — Observer already mis-renders a person.** `person_of` hides only `"gateway"` (abstractobserver/src/ui/mission_control.tsx:375-380); `backlog_exec_runner`, `gateway:summon-pending`, `gateway:agora-pending` would render as people, and 70 live rows have `actor_id=None` (session-memory owner runs, routes/gateway.py:4849, :4898). Replace `person_of` with `requester`, never `actor_id`.

**11. P2 — PII to providers.** R5 puts `requester.user_id` into the prompt (`runtime_grounding.user`); registry ids may be emails. Needs an operator ruling: display name, handle, or nothing. `_meta` otherwise does not reach `GET /runs/{id}` (returns `run_summary`, :9540-9552) but IS in `run_json`, exports and the discussion seed path.

**12. P2 — Entity seams already exist.** Summons record `participants = ["person:<user_id>", …]` and `record_seat(holder=caller_id)` (routes/entities.py:3557-3560, :3573-3581; `caller_id = principal.user_id or "operator"` :2961). Make `requester.user_id == caller_id` a stated invariant with a test.

**13. P2 — `tenant_id` on index rows** is needed only for `/host/runs` (cross-plane); keep it in vars, index optional. `source`/`via` leak nothing: rows are per plane; cross-plane is admin-only (:29031-29058).

## C. Inheritance cases — what the proposal yields, and the rule I recommend

| Case | Proposal yields | Unambiguous? | Recommended rule |
|---|---|---|---|
| Automation occurrence | creator, `via: automation:<id>` | No — silent on revise and Run-now; `at=now` breaks replay (F1) | Frozen at admission from `definition.created_by` at the admitted REVISION (controller.py:581-583); `at = fired_at`; `revised_by` lives on the definition, not the run |
| "Run now" by user B on A's automation | creator A | No | Occurrence requester = A (it is A's automation); B is recorded on the audit line and, if wanted, in the command receipt (`automation.run_now`, routes/automations.py:848) — not on the run |
| Discussion forked by B | silent | No | Requester = B (the forker), `via: discussion`, `on_behalf_of` absent; stamp via `start_discussion` kwarg (service.py:402-417) |
| Entity visit summoned by A, continued by B (seat slide) | `caller`, `via: entity:<name>` | Partly | Per-turn run = its own summoner (`caller_id`); the seat holder is a separate fact (entities.py:3573-3581); never rewrite earlier runs |
| Telegram chat | `user_id: telegram:<user>` | No (namespace) | `user_id` = operator account the bridge executes as; `on_behalf_of = telegram:<chat>:<user>`; `source: telegram` |
| Listener child (bundle_host.py:2829-2835) | claims inherited | No — copies `_runtime`/`_limits` only | Call the RT helper on `listener_vars`; test deletes it → red |
| MEMORY_COMPACT / run_facade / START_SUBWORKFLOW children | claims inherited | 1 of 3 | Same helper at each site (runtime.py:4743, :5898; run_facade.py:229) |
| Scheduled wrapper → target run (:9457) | silent | No | Strip at the funnel; stamp the wrapper; the target inherits by `parent_run_id` link or re-stamp when the wrapper starts it |
| Backlog exec runner / session-memory owner runs | `system`, `backlog-runner` | Yes | `requester: {user_id: "system", via: "backlog-runner"}` saved with the RunState (:825-838); owner runs (`actor_id=None`) stay `null` and are never shown as runs |
| Agora resident (`gateway:agora-pending`) | missing | — | `system`, `via: agora:<alias>` |

## Skew matrix

| Runtime | Gateway | Observer | Result |
|---|---|---|---|
| old | new | any | Vars carry `requester` on roots only; no index columns; lists show roots attributed, children `unknown` → AMBIGUOUS. Gate on a runtime floor. |
| new | old | any | Columns NULL, helper copies nothing → consistently `null`. Safe. |
| new | new | old | Field ignored. Safe. |
| new | new | new | Intended; old stores: sqlite ALTER + backfill writes NULL for pre-existing runs; JSON sidecar version bump forces one cold rescan of 8,759 runs. |
| any | new, old clients | — | `via` is server-derived (finding 4) → no client change needed. |

## E. Cost (honest)

RT: helper + 4 sites + listener export + 2 stores (sidecar bump, sqlite migration/backfill) + admission freeze + grounding + tests: **3 days**. GW: funnel stamp/strip + 4 explicit callers + backlog runner + `created_by` on definitions + rows/detail/`/host/runs` projections + audit line + tests (extend tests/test_automations_api.py, test_gateway_activity_run_link.py): **2–3 days** (5+ if done per site as proposed). Observer: **1 day**. Clients: **0** (drop `x-client-id`). Release: RT → GW (floor-pinned) → Observer, one wave. Total **6–7 days**, not "small".

## F. Alternatives

A (gateway sidecar): the parent-chain walk is NOT the cost — rows are in memory, 8,759 parent links resolve in microseconds. Its real defects: the record is not in `run_json` (exports, discussion seeds), bridges still need a seam, and the model grounding needs the runtime anyway. Missed option **D, session ownership**: children already inherit `session_id` at every path (runtime.py:4727-4735; run_facade :350; bundle_host :2832), so a per-plane `session_owners` record written on first start gives ~100% coverage of session-bearing runs with zero runtime change — but session ids are client-minted (`StartRunRequest.session_id`), a child may override its session (:4727-4729), backlog/owner runs have none, and it cannot say "on whose behalf". **Pick the proposal's slot, re-engineered per findings 1–4** (funnel stamp, one RT helper, deterministic `at`, server-derived `via`): most durable truth. If the operator wants it in days, D is the rapid interim and is compatible (same row field, different source).

## Questions the operator must answer before anyone codes

1. Is "who" an ACCOUNT or a HUMAN? Under the static token every script, the tray and the console are `admin`. Accept, or require registry users for the field to mean anything?
2. Occurrences: requester = creator at the admitted revision, always — even when another user clicks Run now?
3. May the model be told the requester (id → provider logs)? Id, display name, or nothing?
4. Discussion forked by B on A's automation = B; a visit continued by B = B per turn. Confirm.
5. Is a client-claimed `via` allowed at all, or server-derived only?
6. Accept 7% backfill with "unknown" as the common case for existing rows, or no backfill?
