# 0928 — Automations v1: runtime-native scheduled/recurrent/triggered tasks with clear management and a chat representation

- **Status:** completed — UNRELEASED (the operator tests first; ships in the next minor wave). Was: planned (design approved by the operator 2026-09-26; ships as the minor wave AFTER the 2026-09-26 patch wave)
- **Created:** 2026-09-26
- **Completed:** 2026-09-27 (built, reviewed and E2E-tested; local commits only, no version bump, no push; see the Completion report)
- **Moved:** `planned/0928_…` → `completed/0928_…` on 2026-09-27
- **Area:** abstractruntime, abstractgateway, abstractuic, abstractflow, abstractobserver, abstractassistant (v1); abstractcode + console (0930)
- **Contracts:** untracked/design/automations-CONTRACTS.md (final, 2026-09-27; supersedes PLAN §3)
- **Design:** untracked/design/automations-PLAN.md (co-built with Codex "Astra", 5 turns, untracked/design/astra/DIALOGUE.md); the
  superseded first draft untracked/design/automations.md holds the evidence from the four code explorations.

## Summary
Today a "schedule" is a gateway-generated wrapper run (`scheduled:<uuid>`, `POST /runs/schedule`) with no object to list, no origin
marker on occurrences, no time-of-day, no delivery, no unread state, and a Launch form that takes ~12–14 interactions; the Observer is the
only surface; Code's session lists show a schedule as a one-turn conversation and hide the result-bearing children; the Assistant cannot
see gateway-created runs. Automations v1 gives the framework ONE runtime-native concept: an Automation IS a durable runtime root run
(`automation_id == run_id`) driven by one shipped controller VisualFlow bundle (`abstractframework.automation-controller@1.0.0`, package
data of abstractruntime), definition in `vars._meta.automation` with ledger-recorded revisions, occurrences as serial child runs with
deterministic ids, a trigger-source registry declared now (v1 sources `schedule`, `manual`), growing/independent context, Discuss as a
forked durable session, a gateway façade `/automations` over runtime objects and the existing command store, one shared panel in
abstractuic, and management in the Observer and the Assistant.

## Why (operator, 2026-09-26, verbatim)
"(a) i am not against creating a higher-level object Automation to handle those (b) those objects have to run on the runtime, so they can
be fully traceable / replayable (c) we do not want to over engineer this … i think i want the equivalent of a "Triggerable" interface, so
that we can later bind Automation to different triggers (eg file changed; run finished or failed; email received; search completed;
program built; critical decision gated to human; etc). we don't want them all now, but … whenever we create new "triggerable" objects,
they are automatically accessible to the framework. (d) who say schedule, trigger etc say we need to have clear visual and management of
those. (e) we do not want a parallel system, this should run on the runtime and benefit from all the tools and searchability we already
have. … we need also to be able to alter the automation (eg change intervals, pause it, resume it, change the conditions, etc), as well
as to dialogue with the context created by that automation … a chat representation of an automated task is not a bad thing either …
when dialoguing with it however, it's more like a fork on that context at that time and it should not affect the normal process of the
automated task. … there should be a way that the context grows (or not) at each iteration."

## Operator rulings (2026-09-26)
1. Runtime-root model with child occurrences: approved. 2. Independent context as the default. 3. `schedule` + `manual` first; external
triggers are 0929 (planned). 4. Discuss = a new DURABLE runtime session forked/seeded from the automation's conversation through the
chosen occurrence, with the target's normal tools (NOT read-only); isolation only means it never writes back into the automation.
5. Quiet results (`notify:false` / empty answer) stay quiet; failures and human waits always surface — accepted provisionally, see the
open questions. 6. v1 apps = Observer + Assistant; Code and the console are 0930. 7. The patch wave releases first; this is the next wave.

## Scope
### In scope (v1)
- Runtime (mission R): `automations/` + `triggers/` packages, `Runtime.start(run_id=)` create-if-absent + `START_SUBWORKFLOW.payload.run_id`,
  deterministic occurrence ids `uuid5(automation_id, f"{revision}:{index}")` / `"manual:"+command_id`, the controller bundle, definition
  and `_runtime.automation` cursors, ledger record types `automation.*`, `apply_automation_command` under the per-run lock,
  `select_session_turns`, index additions (`automation_id, role, occurrence_index, session_kind, change_cursor`; `list_automations`,
  `latest_occurrence`), trigger registry + entry-point group `abstractruntime.trigger_sources`.
- Gateway (G): façade routes (`POST/GET /automations`, `GET/PATCH /automations/{id}`, `/commands` types `automation.revise|pause|resume|
  run_now|stop_current|archive`, `/occurrences`, `/discuss`, `/seen`, `GET /trigger-sources`), `session_kind chat|automation|occurrence|
  discussion` stamped at index time, per-principal attention cursor, legacy `scheduled:*` projection (`legacy:true`, recreate offered, no
  migration), `manifest.metadata.automation_defaults[flow_id]`, acceptance script `scripts/accept_automations_v1.py`; the `GET /runs`
  list-row `is_scheduled: False` bug fixed on the way.
- abstractuic (U): client module, `AutomationPanel`, panel-chat "Schedule this…" action + badge, canonical fixtures
  `fixtures/automations/{list,occurrences,trigger-sources,commands,errors}.json` (checksum-shared with the Qt Assistant).
- Flow (F): trigger-source discovery, binding editor, `automation_defaults` export, optional `trigger` pin.
- Observer (O): Automate mode (3 fields + Advanced), Automations page, occurrence transcript as chat pairs with ledger steps and
  answerable waits, Discuss; board/navigator tagging by `session_kind`.
- Assistant (A): gateway-fed Automations section, tray entry, "Schedule this conversation…", polling + tray notifications, Discuss,
  answering waits; regular lists show `chat` + `discussion` kinds.
- Docs (D, coredoc per repo) and versions/floors/release order (V): minor bumps for runtime, gateway, ui-kit, flow, observer, assistant;
  gateway floor on the new runtime; apps check the Automation API capability; root last.
### Out of scope (explicit non-goals)
A second execution registry; a template database; per-automation generated flows; automatic legacy migration; a universal event broker;
an arbitrary filter language; concurrent occurrences; a delivery router; agent-memory transfer; automatic summary turns (schema field
reserved, rejected as `unsupported_feature` in v1); Code/console surfaces (0930); external trigger sources (0929); connectors (0931).

## Contracts
Sections 3-A…I of untracked/design/automations-PLAN.md are the contracts (definition/state/ledger; attribution and discussion;
triggers; controller; queries; gateway routes/shapes/errors; panel props/fixtures; acceptance; versions), with the rulings above applied
(Discuss allowlist dropped). Each package's planned item copies the parts it implements.

## Current code reality (2026-09-26)
- Gateway: `routes/gateway.py` `ScheduleRunRequest` ~:2383, wrapper builder ~:2780, `POST /runs/schedule` ~:8145, list-row
  `is_scheduled: False` ~:8657; `runner.py` `update_schedule` ~:2664, resume-fires-now ~:2084; `session_history_bloc.py:54` excludes children;
  `hosts/bundle_host.py` `_seed_session_history` ~:2024/2479 (history seeding happens in the gateway host; subworkflow children bypass it).
- Runtime: `core/runtime.py:1292` `start()` has no run_id; subworkflow dispatch creates a random child ~:4452 before the parent wait
  record ~:3651 (a crash in between can duplicate a child on replay); `_PerRunLocks` ~:481–514 held only by `resume()`;
  `session_history.py:75` bounded history; `history_bundle.py:816` root-only; `event_adapter.py:98-205` on_schedule (intervals `[smhd]`
  or ISO, no cron/tz); `storage/commands.py:277` command store dedups ids; `workflow_bundle/reader.py:75` bundles load without the gateway.
- Observer: `src/ui/app.tsx:5097-5540` single Launch form; no automations list; 3–4 clicks to a result; not on ui-kit.
- Assistant: `core/session_index.py:191` local-only sessions; `app.py:10039` `_notify` reusable; `:11065` tray menu.
- Code: `tui/src/gateway/mod.rs:865` and `web/src/workspace/use_workspace_catalog.ts:87` list `/runs?root_only=true`.
- Flow: `src/utils/flowFamilies.ts:52` local interface vocabulary; `nodes.ts:111` on_schedule; no schedulable marker.

## Missions and order
R first (release gate = restart correctness, not screens) → G integrates against R; U builds from frozen fixtures in parallel; F after G
contracts stabilise; O and A after U + G; D alongside, finalised after; V last. Per-package planned items (each repo's own numbering, written and committed 2026-09-26):
abstractruntime 0847 (v1) + 0848 (v2 inbox); abstractgateway 0928 (façade + acceptance script) + 0929 (v2 event admission) + 0930
(console); abstractuic 0029; abstractflow 0158 (supersedes its proposed 0119 direction); abstractobserver 0002 (adopts the ui-kit panel
through the existing source aliases); abstractassistant 0852; abstractcode 0001 (phase after v1).
Conflicts the package items recorded against the plan (to settle in the contracts pass before implementation): the run stores have no
create-if-absent primitive (SQLite `save` overwrites, JSON replaces — a new primitive on all four stores, not just a `start` parameter);
`on_schedule` computes "now + interval" and accepts ms/decimals, so `schedule@1`'s anchored whole-unit math is new; chat history drops
child runs AND runs tagged as scheduled (`history_bundle.py:708-727/816`, `session_history.py:155-158`) — the new selector replaces both
filters; a discussion must NOT be linked into the automation's run tree (tool ceilings intersect every ancestor, `core/tool_scope.py:20`);
no entry-point group or shipped bundle exists in the runtime package yet; the gateway builds `manifest.metadata` itself
(`routes/gateway.py:6933-6946`) so Flow cannot export `automation_defaults` until that changes; the gateway has no per-user preference
store for the attention cursor; command types are hard-coded in three places (`routes/gateway.py:28465`, `runner.py:1756`, capabilities
:17021); the error envelope `{error:{code,…}}` differs from the router's `HTTPException(detail=str)` style; `/automations` routes mount
under `/api/gateway/` for the apps; no route lists sessions with `session_kind` (the Assistant needs one); Flow interfaces cannot declare
an optional pin yet (`flowFamilies.ts:37-46`); ui-kit tests are `scripts/check_*.mjs` against built output and its fixtures live in
`ui-kit/scripts/fixtures/` (the root identity-sync script already reads that folder).

## Operator rulings, second set (2026-09-26; supersede the plan's notification convention)
1. Discussion workspace = the automation's workspace mounted READ-ONLY; the discussion session is durable on the runtime. The workspace
   guard needs a real read-only access mode (today's modes govern path reach, not permissions): writes/deletes/shell inside that root are
   refused; reads and the target's other tools stay normal.
2. Quiet occurrences stay listed without a badge (expected to be rare).
3. Notification default is QUIET: the task is silent unless the workflow itself creates a notification at that tick (an explicit `notify`
   output/payload or a notify node/tool; in-flow delivery through comms tools counts). Clients are thin and may be disconnected: attention
   items are recorded gateway-side and shown when a client connects. Failures and human waits are attention regardless of this flag.
4. Failures notify only when true: `policy.retry = {max_attempts, backoff}`; attempts are ledger-recorded; attention only when all retries
   have failed; a temporary failure that self-corrects never notifies.

## Validation
- Runtime: `tests/test_automation_{occurrence_recovery,commands,session_turns,discussion_isolation,index,replay_read_only}.py`.
- Gateway: `tests/test_automations_{api,attention,plane_isolation}.py` + `scripts/accept_automations_v1.py` (empty data dir, managed
  gateway subprocess, deterministic fixture target, pause / run-now while paused / resume-without-firing / interval edit / restart
  mid-occurrence → exactly two distinct children / independent vs growing prompts / two discussion turns / replay with zero provider or
  tool calls).
- abstractuic `ui-kit/tests/automation_panel.test.tsx`; Observer `src/ui/automations.test.tsx`; Assistant `tests/test_automation_sessions.py`.
- The three operator scenarios walkable in the Observer and the Assistant: three news monitors at different intervals (independent);
  email triage every 30 min (growing, urgent-only notification, a human-gated "reply to X?" answered from the Assistant); weekly journal
  monitor (growing, target-owned rolling summary).

## Risks
Duplicate children (deterministic create-or-load; crash tests); command races/replay (shared root lock, idempotent outcomes); lost or
duplicated context (shared turn selector, persisted discussion seed); hidden/misleading activity (separate change and attention cursors).

## Effort
33–52 engineer-days (±50 %): runtime 8–12, gateway 5–8, abstractuic 3–5, observer 4–6, assistant 4–6, flow 1–2, integration/docs/release
3–5 (Code/console 4–8 in 0930). Critical path runtime → gateway → apps → docs/floors/release.

## Related
0929 (external triggers, v2), 0930 (Code + console), 0931 (connectors, v3), 0923 (double resume — the same crash window family),
0925 (reasoning retention on long runs — matters for growing mode), 0918, 0922.

## Contracts pass (2026-09-27)

Final contracts: untracked/design/automations-CONTRACTS.md (root repo; rev 2 with Astra turn-6 amendments 1–11). They supersede the contract text copied above; earlier text is kept as history. Concrete changes for this item:

The contracts pass settled every plan-versus-code conflict (C1–C16) and applied Astra's 11 review amendments. What changed vs the plan: explicit-id runs use a mandatory `create_if_absent` on every store, with identity including session and a creation-request digest. Controller transitions follow a recorded-decision/reconcile protocol with exactly checked ledger keys, one controller-writer process per store. `schedule@1` gets full typed adapter signatures, one-shot exhaustion and a new `binding_id` per trigger revision, and is labelled as fixed UTC intervals. Notifications are quiet by default: only a workflow `notify` output or a final failure after `policy.retry` (3 attempts, 30s×2 capped 10m) creates one attention record per occurrence, and interactive USER/EVENT waits always count. Discussions are root runs on the occurrence's workspace mounted read-only; this covers tools, VisualFlow writers and `execute_python`, and is anchored in the runtime. History for automations and discussions is strict, never unseeded. Errors use `{"detail":{"reason_code",…}}` via scoped handlers. `changed_since` is unsupported in v1, so clients poll full pages and page attention. `/runs` gains `session_kind`. The optional trigger pin is dropped. v1 decisions adopted from the review, which the operator may override: the notification boundary is the workflow output (agent targets are wrapped in a `{response, notify}` flow), and schedules are fixed UTC intervals, with calendar/tz in v3. Per-package items carry their own "Contracts pass (2026-09-27)" sections.

## Completion report (2026-09-27)

**Status: completed — UNRELEASED.** The operator tests it first; it ships in the next minor wave (release checklist:
[0941](../completed/0941_automations_v1_release_wave_floors_bumps_and_root_pins.md)). Every package change is a local commit on
`main`: no version bump, no tag, no push. Built in one day by six missions (R runtime, G gateway, U abstractuic, F flow,
O observer, A assistant), reviewed adversarially (REVIEW 41–54 plus jobs 48, 50, 51, 53), then tested end to end with the
operator's own MLX model.

Evidence (all under the root repo's `untracked/`, not published):
- Mission log with every seam, decision and commit: `design/automations-MISSIONS.md`.
- Contracts: `design/automations-CONTRACTS.md` (rev 2). Design: `design/automations-PLAN.md`.
- Reviews: `missions-2026-09-25/REVIEW/41-…54-*.md`. Jobs 48, 50, 51, 53 are sections inside 42, 45, 44 and 44.
- E2E: `missions-2026-09-27/E2E/REPORT.md` with its `evidence/` (44 MB), `observer-captures/` and `reverify-5161785/`.
- Live deployment kit for the two examples (needs the operator's GO; not run by this record): `missions-2026-09-27/LIVE/`.

### What shipped, per package

| Package | Mission | Commits (local `main`) | Tests at the tip | Reviews |
|---|---|---|---|---|
| abstractruntime | R1 + R2 | `79d9bf6` … `d02578a` (26 commits) | full suite **2957 passed / 26 skipped** | 43 GO; 44 GO (history, read-only) / NO-GO (discussion: F1, F2); 45 GO (controller core) / NO-GO (discussion: H2) + **H1 release blocker**; 45 addendum (D1) GO; job 50 GO (`e690b55`); job 51 GO (`af2de4a`: H1, F1, F2 fixed); job 53 GO (`b000036`, J51-1 fixed). J53-1/J53-2 fixed in `d02578a` (not re-reviewed). |
| abstractgateway | G | `57f26b9` … `4ece2f5` (14 commits; docs `9766e29`, `8a8c8d3`; kit re-vendors `6718d3c`, `ea71638`) | full suite **2514 passed**; `scripts/accept_automations_v1.py` **16/16** | 46 GO (G1, G2 → fixed `5161785`); 47 GO for E2E, conditional for apps (P2-1, P2-2, P2-3 → fixed `5161785` / runtime `e690b55`); 52 GO after **R52-1** (the `_runtime` allowlist → `4ece2f5`); 52 addendum (`9975276`) GO with W1, W2 (W2 → `4ece2f5`); **review 55 (the final delta `ea71638` + `4ece2f5`) pending** at completion |
| abstractuic | U | `9da01a0` … `1eb6d82` (8 commits, docs `704f18d`) | `check_automation_fixtures` 151, `_client` 114, `_panel` 216 (at `2081d6a`, job 48) | 42 GO (F1–F7 → fixed `b70db16`); job 48 GO (D1, `2081d6a`). Fixtures regenerated from real gateway output in `a9b73ab`. |
| abstractflow | F | `c5961d1` … `0d4bf76` (4 commits) | `npm test` 1392 passed at review (the 2 failures were an untracked audit copy; excluded in `9f174c9`) | 41 GO (A1, B1 → fixed `9f174c9`) |
| abstractobserver | O | `56af9b4` … `9685fe0` (9 commits, docs `8f41b63`) | vitest **159/159**; headless-Chromium walk **17/17** against gateway `5161785` | 54 GO (O-1 → fixed `9685fe0`) |
| abstractassistant | A | `e3a0445` … `d142d00` + docs `7248daf`, `05161da`, `52d75df` (12 commits) | suite 967; 27/27-step walk against a hermetic gateway (0 provider calls) | 49 GO on the operator's machine (A49-1 → gateway `2146145`/`f9269d9`; A49-2 → `cce2d67` + gateway `5161785`) |
| abstractframework (root) | docs, sync | `cf71688` (identity sync checks the automations fixtures), `606afa6` (docs: automations) | `scripts/check_identity_sync.py` | — |

Per-package records: runtime 0847, gateway 0928, abstractuic 0029, flow 0158, observer 0002 and assistant 0852 are completed
in their own backlogs. Unchanged: runtime 0848, gateway 0929 and 0930 (next phases), abstractagent 0034 (still planned; see
residuals) and abstractcode 0001 (still planned). Root [0929](../planned/0929_automations_v2_external_triggers_durable_inbox.md),
[0930](../completed/0930_automations_code_and_console_surfaces.md) and
[0931](../proposed/0931_automations_v3_connectors_and_calendar_scheduling.md) are unchanged: they are the next phases and
build on what this record describes.

What each package holds now:
- **Runtime:** the `automations/` and `triggers/` packages; the controller bundle
  `abstractframework.automation-controller@1.0.0:controller` shipped as package data. `create_if_absent` on every store,
  plus `Runtime.start(run_id=)` and `START_SUBWORKFLOW.payload.run_id`. `run_mutation_lock` held for the whole tick.
  Deterministic occurrence ids, and a decision-protocol ledger (`automation.*` records, exact idempotency-key reconcile).
  `schedule@1` / `manual@1` through the entry-point group `abstractruntime.trigger_sources`. `select_session_turns`, strict
  `session_chat_messages` and `discussion_seed_messages`. `session_attribution` with the discussion anchor in
  `Runtime.start`. Read-only workspaces (`workspace_read_only`, `TOOL_EFFECT_CLASSES`). Typed `pending_waits` and
  `policy.tool_approval`. The JSON store's session index with a creation journal, and `warm_session_index()`.
- **Gateway:** the `/api/gateway/automations…` façade (create, list, get, revise, commands, occurrences, attention, discuss,
  seen) and `/trigger-sources`. `session_kind` and `role` on `/runs` rows; `root_only` returns turn roots. The per-principal
  seen store and the `{"detail":{"reason_code",…}}` envelope, including on 401/403. The legacy `scheduled:*` projection.
  `automation_defaults` on VisualFlows and in the publish manifest; `contracts.common.automations` in the capabilities.
  Strict seeding for automation and discussion sessions, and read-only restamping on `/runs/start`. Docs
  `docs/automations.md`.
- **abstractuic:** `createAutomationsClient`, `AutomationPanel`, `AfScheduleDialog`, the pure rules, the canonical fixtures
  (`ui-kit/scripts/fixtures/automations/*` + `CHECKSUMS.sha256`), and panel-chat `ScheduleThisAction` / `FromAutomationBadge`.
- **Flow:** trigger-source discovery, the Automation defaults editor, and the `VisualFlow.automation_defaults` field.
- **Observer:** Launch "Run once | Automate", the Automations page (kit panel), legacy rows with Recreate, and tags from
  `role`/`session_kind`. Controllers are hidden from the Board; occurrences are grouped in the navigator.
- **Assistant:** the gateway client, the switcher's Automations section, the automation view (chat pairs, controls,
  discuss, wait answers by kind), "Schedule this conversation", tray notifications from a 60 s / 5 min poll, and the regular
  list filtered to `chat` + `discussion`.

### Plan versus what shipped

- **Polling instead of `changed_since`.** The plan had `changed_since` polling. v1 clients poll full pages; `changed_since`
  answers 422 `unsupported_feature` (contracts).
- **No trigger pin.** The optional `trigger` pin on On Flow Start and `triggerable.v1` were dropped (contracts).
- **Discuss uses a read-only workspace.** The target's normal tools still run, but the automation's workspace is mounted
  read-only (ruling 8). A refused write returns the tool error to the model; the run still COMPLETES (accepted).
  Superseded on 2026-09-27 by the operator's live-test ruling, see "Addendum (2026-09-27, live test)" below: the
  discussion now has its own writable workspace and the automation's folder is mounted read-only inside it.
- **The gateway runner drives controllers.** The ordinary gateway runner drives the controllers;
  `abstractruntime.automations.service.drive_automation` exists but the gateway does not use it.
- **The ADR is not written.** The runtime item expected one ADR ("an automation is its controller root run; occurrences
  are deterministic child runs"), and none was written. See residuals.
- **abstractagent 0034 was not done.** The runtime classifies every tool centrally instead
  (`abstractruntime.integrations.abstractcore.tool_effects.TOOL_EFFECT_CLASSES`, spelling `exec`). Unclassified tools are
  refused under read-only, so `execute_python` is refused (acceptance step). The agent-side declaration is still open.

### Decisions taken during implementation (binding; recorded in MISSIONS)

- **D1, unattended tool approval.** An E2E defect prompted it: every `@default` agent tick parked on a tool approval.
  - The definition carries `policy.tool_approval: "auto" | "ask"`, default `"auto"`: creating the automation is the
    consent.
  - At admission the runtime freezes `_runtime.tool_policy = {auto_approve_tools: [...], source: "automation-policy"}`
    into the occurrence's inputs. The tools are the target's `_runtime.allowed_tools`, or else every classified tool
    (65). The agent's own `allowed_tools` ceiling still applies.
  - Tools outside `TOOL_EFFECT_CLASSES` (third-party MCP tools) **still ask**.
  - Discussions strip the grant. A `policy` revise merges fields (D1-M1, `e690b55`). The gateway strips any client
    `tool_policy` (P2-1).
- **Typed waits.** `pending_waits` → `{run_id, wait_key, kind: ask_user|tool_approval|event, reason, prompt?, choices?,
  details?}`. `details` for `tool_approval` is `[{name, arguments, call_id?}]`. Each kind takes one answer shape, enforced
  at the gateway's resume door (422 otherwise):
  - `ask_user` → `{response}`;
  - `tool_approval` → `{approved}`;
  - `event` → `{payload: <object>}` (A49-2; an object only, which settles J48-1).
- **Session ids.**
  - Controller and growing turns: `automation:<automation_id>`.
  - An independent occurrence: its first attempt's run id.
  - A discussion: `discussion-session:<discussion run id>`, where the run id is
    `uuid5(automation_id, "discuss:"+request_id)`. This is review 45 H2's fix; it amends contract B's bare `request_id`
    form. Reusing a `request_id` with a different prompt gives `identity_conflict`.
- **Turn roots.** A session's turns are its parent-less runs plus its `role:"occurrence"` runs, never descendants or
  controllers. A retried occurrence counts once, as its last attempt (D3, gateway `c1e3460`). `GET /runs?root_only=true`
  returns turn roots with `session_kind` (`chat|automation|occurrence|discussion`), `role`, `automation_id` and
  `occurrence_index`, so existing session folds show automations as chats.
- **Notify convention.** Quiet by default. An occurrence is notable only when its OUTPUT carries
  `notify: true | {title, body}`, which comes from structured output, never from the prose. Agent targets are wrapped in a
  `{response, notify}` flow. Failures notify only after `policy.retry` is exhausted (default 3 attempts, 30 s ×2 capped at
  10 min). Human waits are always counted live and are not cleared by `/seen`.
- **Schedule envelope.** `{tick, scheduled_at, coalesced?: {first_tick, last_tick, missed_count}}`; `fired_at` sits on the
  envelope (review 42 F1). `trigger.summary` uses the cadence in force at that occurrence's revision (D4).
- **Failure row.** `OccurrenceRow.failure = {reason_code: "occurrence_failed", message, attempts}`.
- **Summary capabilities.** Each summary lists the command suffixes it accepts plus `discuss`. Legacy rows carry
  `["legacy"]` and come on the last page. Archived, completed and failed rows carry `["discuss"]`.
- **Command integrity.**
  - The command digest means that a reused `command_id` with a different type or payload is refused as
    `identity_conflict` (M1).
  - The door refuses busy and invalid-state commands at once with 409 (D5).
  - Legacy run commands on an automation root → 409 `invalid_state` (G1).
  - A host-lookup failure is recorded, and the cursor holds if it cannot be recorded (G2).
- **Bounds.** `every` ≤ 366 d, `count` ≤ 1,000,000, backoff bounded (M3 / G4 / P2-5).
- **Creation.** `actor_id` is stamped at creation (P2-3; the gateway's claim step is gone). The gateway strips client
  `_meta.*` and the read-only keys from `target.input_data` and keeps only an allowlist of `_runtime` keys (P2-1; R52-1,
  gateway `4ece2f5`). The review-52 stall is fixed: a planted `_runtime.control = {paused: true}` stopped every other
  automation because the runner re-queued a RUNNING-but-paused run for immediate ticks in a tight loop, starving the
  others (`4ece2f5`).
- **JSON store.** A per-process session index kept current across processes by a creation journal, warmed at gateway boot
  (H1, J51-1, J53, W2).

### E2E (real model), summary of `missions-2026-09-27/E2E/REPORT.md`

Setup: a hermetic gateway (`:18910`, then `:18920` for the re-verification) with user auth and a scrubbed environment. The
operator's text route only: MLX `Jundot/Qwen3.8-27B-oQ4e-mtp`, reasoning low, native MTP. The HF cache was read-only and
offline. Nothing touched `:8080`.

| # | Item | Result |
|---|---|---|
| 1 | Objects: controller root, occurrence children, descendants, deterministic ids (incl. after a target revise), ledger records, `next_fire_at`, counts | PASS |
| 2 | Chats in AbstractCode (fold of `/runs?root_only=true`), the Assistant (history bundle, growing context) and the Observer (rows, ledger) | PASS |
| 3 | Pause, run-now while paused, resume without firing, revise (409 `revision_conflict` on a stale revision), archive mid-occurrence | PASS |
| 4 | Discuss: seed exactly through occurrence 2, turn 2 restamped read-only, `write_file` / `execute_command` refused, `read_file` works, no write-back | PASS |
| 5 | Attention: quiet by default, forced notify = one item per occurrence, `/seen` cursor rules, retry → one failure item | PASS |
| 6 | `kill -9` twice (while waiting; mid-LLM call) → exactly one child per tick, the same agent sub-run resumed | PASS |
| 7 | Replay of everything: 112 reads, 0 provider/tool calls, 201 store files byte-identical | PASS |
| 8 | Acceptance script | PASS (14/14, then 16/16 after D1) |
| 9 | Legacy wrapper projected `legacy: true`, absent from `session_kind=chat,discussion` | PASS |

Defects found and fixed during the run:
- **D1 (major):** the tool approval described above.
- **D2:** a running agent occurrence read "waiting".
- **D3:** a retried occurrence was listed as one turn per attempt.
- **D4:** past occurrences were described with the current cadence.
- **D5 / D6 (from the Observer walk):** commands were refused late; legacy rows lacked `binding_id` and
  `last_occurrence`.

All six were re-verified on gateway `5161785` against a fresh hermetic gateway (`reverify-5161785/`).

**The operator's two examples, with the real model:**
- **Market value, growing (AAPL, `cc3b3b59`, every 2 min in the E2E):** 11 occurrences, all completed, through
  `web_search`/`fetch_url`. Occurrence 3 saw 4 prior messages and occurrence 7 saw 12. The model said "unchanged from
  occurrence N-1" from #2 on. The market was closed (Sunday), so detecting a real price CHANGE was not verified.
- **Memory every 2 minutes:**
  - `4ab8ead7`, the `@default` agent with `execute_command`: 8 occurrences, independent sessions.
  - `2a697b11`, a wrapped flow whose notify is decided by structured output: 6 quiet ticks.
  - `3190bbd1`, a forced notify: one attention item per occurrence.
  - `ecf0d89c`, prompt only under `tool_approval: auto`: 2 unattended ticks.
  - `a493710b`, under `ask`: a typed `tool_approval` wait, approved, completed.

With one automation active, a tick took 24–48 s. With 3–4 automations sharing the one in-process MLX model, ticks reached
2–4 minutes and coalescing absorbed the missed ticks. The live kit in `missions-2026-09-27/LIVE/` creates the same two
monitors on `:8080`: AAPL every 5 min, growing; memory every 2 min, independent, notifying under 10 % free.

Not verified by the E2E:
- the three GUIs' rendering (each app mission ran its own headless walk);
- a live price change;
- `ask_user` / EVENT waits with the real model (the acceptance script covers them deterministically);
- `stop_current` and `count` / `until` exhaustion with the real model (runtime tests cover them);
- the 40-message / 24,000-character truncation.

### Residuals

**Follow-ups collected during implementation (MISSIONS):**

| Follow-up | State |
|---|---|
| `actor_id=` on `create_automation` / `start_discussion` | Done (runtime `e690b55`, gateway `5161785`) |
| Structured failure reason codes on occurrence attempts (every failure is `occurrence_failed`) | Open, not ticketed yet (runtime + gateway) |
| Occurrence `trigger.summary` from the current interval | Done (D4, `f9269d9`) |
| Store-level exact-key lookup for ledger idempotency keys and attention (JSONL scans) | Open → [0937](../planned/0937_automations_store_level_exact_key_lookups_and_read_performance.md) |
| `Runtime.start` refuses session-bearing starts on stores without a run index; duck-typed stores | Open → [0938](../planned/0938_runtime_start_session_starts_on_duck_typed_stores_documented_and_refused.md) |
| R1 F5: the JSON store orders runs by file mtime (a restored backup reorders) | Open → [0939](../planned/0939_json_run_store_recency_order_follows_updated_at_not_mtime.md) |
| R2 replay-conflict semantics documented | Partly: runtime `docs/automations.md` says to replay a command result with the same payload and `expected_revision`; the identity-conflict rules for dispatch replays are not spelled out |
| ui-kit: a prop to open the panel's Revise form from a row (Observer asked); `ledger_url` / `workspace_url` are gateway-relative | Open, not ticketed (abstractuic) |
| Acceptance script: contract H steps it omits (one-shot exhaustion, decision/state crash window, retry matrix, EVENT wait, `execute_python` refusal) | Open, optional (runtime tests cover them) |
| 409 reason codes `history_unavailable`, `session_attribution_failed` in the contract's list | Open: in the gateway docs, not in `automations-CONTRACTS.md` |

**Review items not fixed at the tips read for this record:**
- **W1 (52 addendum, release).** The gateway still floors `AbstractRuntime>=0.5.1` (`pyproject.toml:20`,
  `live_deltas.ABSTRACTRUNTIME_FLOOR`). Boot calls `warm_session_index()`, and creates send `policy.tool_approval`: both
  need the runtime release that carries this work. Part of 0941.
- **J50-1 (low).** Command results recorded before `e690b55` have no digest, so a replay would be refused. No released
  gateway has automations, so this is a release-notes line only.
- **R52-1 / W2.** Fixed in gateway `4ece2f5` (`tests/test_automations_review52.py`). Review 55, of that final delta, was
  still pending at completion.
- **R52-2 (low).** ui-kit `parseEventPayload` (`panel_core.ts:389`) still accepts non-object JSON that the gateway refuses
  with 422. R52-3 (note): the reuse of a queued `command_id` reads "duplicate", not "conflict", until it is decided.
- **Review 45 lows.**
  - L1: the notify / failure bodies are cut at 280 / 2,000 characters with no marker (`controller.py:449`).
  - L2: re-sending a trigger config without `start_at` re-anchors it.
  - L3: a possible second `automation.coalesced` record (ledger noise).
  - L5: a failed occurrence N is absent from its discussion seed.
- **Consent wording (45 addendum).** The kit's `TOOL_APPROVAL_CONSENT` says "Tools run without asking"; the review asked it
  to say that the tools can run commands and send messages.
- **Review 46.** G5 (a 500 exposes the seen-file path; a corrupt seen file blocks `/seen` until repaired by hand) is not
  verified as fixed. G6: the envelope codes `not_found`, `invalid_request`, `rate_limited`, `internal_error` and
  `unavailable` are not in the contract list.
- **Review 49.** A49-3: the Assistant's notification ledger swallows write errors and caps at 2,000 keys. A49-4: the
  fallback client-side filter can hide chats on old gateways.
- **Observer.** O-2: the Automate form's Advanced JSON passes `_`-prefixed keys. The gateway allowlist removes the harm; the
  form should still refuse them visibly → [0940](../planned/0940_observer_automate_form_refuses_server_owned_input_keys.md).
  O-3 (cosmetic): 3600 s is shown as "60 minutes".
- **Review 44.** F5 (a failing run index now raises out of non-strict reads) and F6 (an empty seed passes strict) are
  notes. F3 (a legacy scheduled session's history is empty) is intended.
- **Code lists (G3).** AbstractCode's lists get one session per independent tick until they send
  `session_kind=chat,discussion` or grow the kind filter: root 0930 and abstractcode 0001 (the TUI's pinned query is
  `tui/src/gateway/mod.rs:886`; see also abstractcode 0002). The Assistant already sends the filter.
- **MCP tools still ask** under `tool_approval: auto`: a third-party MCP tool in an unattended automation parks the tick on
  an approval wait.
- **Performance notes.**
  - `list_attention` / `automation_records` take about 0.3 s at 10k occurrences on both stores, and the JSONL key lookup
    about 0.3 s per decision (0937).
  - `resolve_discussion_root` is O(turns) per discussion turn.
  - JSON `warm_session_index()` costs about 0.8 s at 20k runs on boot.
  - A single in-process MLX model shared by several automations serialises their calls.
- **E2E observations.** A failing VisualFlow code node completes its run with `success:false`: the occurrence is `failed`,
  but a legacy projection's `last_occurrence.status` reads "completed". Model readings of `vm_stat` vary from tick to tick
  (model quality).
- **ADR not written.** No ADR records "an automation is its controller root run; occurrences are deterministic child runs;
  the turn-root rule" yet (the runtime item anticipated one).
- **abstractagent 0034.** Still planned: the runtime classifies the tools centrally, and the agent-side effect declaration
  (and its enumerating test) is still open.

**New items from this record:**
- [0937](../planned/0937_automations_store_level_exact_key_lookups_and_read_performance.md): store-level exact-key lookups
  and attention/occurrence read performance.
- [0938](../planned/0938_runtime_start_session_starts_on_duck_typed_stores_documented_and_refused.md): `Runtime.start` and
  duck-typed stores.
- [0939](../planned/0939_json_run_store_recency_order_follows_updated_at_not_mtime.md): JSON store recency order.
- [0940](../planned/0940_observer_automate_form_refuses_server_owned_input_keys.md): the Observer's Advanced `_` keys.
- [0941](../completed/0941_automations_v1_release_wave_floors_bumps_and_root_pins.md): the release wave.

### Addendum (2026-09-27, live test)

The operator tested the local deployment and ruled three changes; all are committed locally, unreleased, and covered by
review job 56 (`untracked/missions-2026-09-25/REVIEW/56-rendering-discussion-fork.md`).

1. **Rendering.** The Assistant's automation view renders occurrence text through the same `MessageCard` as the chat
   (assistant `f487a06`, `1380c28`, `8463b9c`: task turns render markdown inside the user bubble through an explicit
   `markdown_user_body` switch, typed chat prompts stay literal). The web apps render through panel-chat's shared
   renderer (ui-kit `878fae0`, Observer `e2b5783`/`f7d9c1c`). The shared renderer had a CommonMark defect: a heading, a
   code fence or a block quote directly after a text line stayed literal (ui-kit `d6a07f5` fixes it for chats too).
2. **A discussion is a fork at a point in time.** Its seed is the automation's whole timeline through occurrence N
   (`automation_timeline_messages`; occurrences found across sessions through the run index, last attempt each), so an
   independent-mode automation no longer forks with a single data point, and N=1 and N=3 give different pasts
   (runtime `997e72e`, `f830b48`).
3. **Own writable workspace + read-only mount.** The gateway allocates the discussion's folder like a chat session's
   (`/discuss` returns `workspace_root` and `mounted_workspace`; a client cannot name the folder) and the automation's
   folder is mounted read-only through `_runtime.workspace_read_only_paths` (runtime `f830b48`: file write tools and
   VisualFlow writers refuse paths under a mount, reads work, children can only add mounts; `8648930`: builtin allow =
   own root + mount, deny prefixes unchanged; `Runtime.start` restamps later turns with the root's workspace policy).
   The gateway keeps its own restamp because the host guard takes mounts only as an explicit argument, never from client
   vars (gateway `d3cf337`, suite 2522, acceptance 16/16). Known limit, stated in every package's docs: shell commands
   are not sandboxed by the mount; only file tools and workflow writers are refused.

Live examples on the local gateway: the AAPL monitor is archived (history kept); "TotalEnergies (TTE.PA) share value
monitor" `787b7fb6-d7bf-5e16-868e-ba8cf961da3d` runs every 5 minutes; the memory monitor is unchanged. Tips after the
addendum: runtime `27522cd`, gateway `d3cf337`, ui-kit `12f736a`, Observer `a592397`, Assistant `2d40c97`. The local
gateway and Assistant were restarted on these tips.

Review 56/56b: GO for all five repos. Its findings were fixed the same day: F1 (a later discussion turn started directly on
the runtime lost read access to the mount under host deny prefixes; `Runtime.start` now restamps the root's exact
`workspace_builtin_allow`, runtime `56ee3a9`), F5 (the seed's summary line now counts against the budget, runtime
`a59957a`), F2 (the Discuss help text and every docs set state that the mount binds the file tools only and shell
commands are not sandboxed: ui-kit `6aaaa5a`, Observer `c3350a1`, Assistant `dcb8023`). Noted, no change: F3 (a JSON-only
answer is an interactive viewer on the web and a code block in the Assistant), G-56-2 (an operator's stored default tool
grant applies to discussions as to any chat; documented in gateway `2a5bccc`, which also closes an isolation hole in the gateway test suite: the default workspace root was machine state, so a tmp folder under the monorepo made one test pass or fail by environment).

**Priority impact.** Automations v1 is built, tested and waiting for the operator's validation. The release wave (0941) is
next once the operator gives an explicit per-release go. 0929 (v2 external triggers) and 0930 (Code and console) follow
v1's release.
