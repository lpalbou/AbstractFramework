# 0928 — Automations v1: runtime-native scheduled/recurrent/triggered tasks with clear management and a chat representation

- **Status:** planned (design approved by the operator 2026-09-26; ships as the minor wave AFTER the 2026-09-26 patch wave)
- **Created:** 2026-09-26
- **Area:** abstractruntime, abstractgateway, abstractuic, abstractflow, abstractobserver, abstractassistant (v1); abstractcode + console (0930)
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
