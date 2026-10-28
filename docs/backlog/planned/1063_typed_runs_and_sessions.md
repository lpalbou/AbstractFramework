# 1063 — Typed runs and sessions: one canonical type on every run and session, in the ledger and the replay view

> Package: abstractruntime (the type, stamped at start; its 0858), abstractgateway (listing, filters, migration; its 0951), every client that lists or routes runs (panel-chat, AbstractCode, Assistant desktop/iPhone/watch, Observer, Entity, Continuum, Note, consoles)
> Type: feature
> Created: 2026-10-28
> Priority: high
> Labels: ledger, replay, sessions, runs, search, routing, multi-client
> Links: [0993](0993_one_ledger_replay_many_views.md) (one ledger, many views), [1059](../proposed/1059_runtime_holdings_as_a_queryable_virtual_space.md) (queryable runtime holdings), [1024](../proposed/1024_requester_attribution.md) (requester attribution, decision gate), completed [1038](../completed/events-and-attention/1038_run_origin_recorded_at_start.md) (run origin)

## Summary

Every run and every session carries ONE canonical type (what it is: a conversation, an automation, a
trigger occurrence, an entity visit, a scheduled run, an import, a docs chat...) and the surface that
started it (desktop, iPhone, watch, web, terminal, API). The type is stamped once at start in the run's
`vars._meta`, indexed in the run store, served by `GET /runs` and `GET /runs/{id}/view`, so clients
filter, search and route on one field instead of deriving the kind from three overlapping fields.

## Why

Operator, 2026-10-28: every run/session should carry a type (session, automation, trigger,
iPhone/watch-originated, entity visit, scheduled, import...) in the ledger and in the replay view so
clients can filter, search and route cleanly.

## Current understanding (inventory, origin/main 2026-10-28)

Three partial vocabularies exist and none is complete:

| Field | Where | Values | Stamped by | Gaps |
|---|---|---|---|---|
| `session_kind` + `role` + `automation_id` + `occurrence_index` | runtime `core/run_attribution.py` (`SESSION_KINDS`, `ROLES`, `INDEX_FIELD_NAMES`); run index columns in `storage/sqlite.py` / `json_files.py` | `chat`, `automation`, `occurrence`, `discussion`; roles `controller`, `occurrence`, `descendant`, `discussion`, `legacy_schedule` | DERIVED at index time from `_meta.automation` / `_meta.occurrence` / `_meta.discussion` / `_meta.schedule` (automations v1, contracts C11/E) | Everything not an automation is `chat` (entity visits, imports, bridges, docs chats, Flow runs) |
| session purpose (`kind`) | gateway `session_kinds.py` (`KINDS = ("conversation", "docs")`), `<data_dir>/session_kinds.json` | `conversation`, `docs` | `POST /runs/start` marks docs-qa sessions; one-time migration `docs_qa_bundle_v1` | A side file beside the archive, not in the ledger; a second vocabulary for the same question; `/runs?kind=` vs `session_kind=` |
| `_meta.origin` | runtime `core/run_origin.py` (`ORIGIN_KINDS`), gateway `routes/gateway.py:_stamp_run_origin` | `kind`: `person`, `trigger`, `agent`, `system`; `actor`; `client`; `ref{automation_id, event_id, origin_run_id, bridge, ...}` | the host at `/runs/start` and bridges; the automation controller for occurrences | `client` is the workflow `interface` the request named (`abstractassistant.agent.v1`), so an iPhone, a watch and the desktop are indistinguishable; not indexed; not in the replay view; entity visits (home runtimes) and Note imports do not stamp it |

Readers: `GET /runs` (`session_kind`, `kind`, `root_only`, `archived_only`; `_parse_session_kind_filter`
refuses unknown kinds with 400), `/conversations/search` (`session_kind` defaults to `chat,discussion`),
`events_stream.run_origin`, `memory_access.run_origin_actor`. The replay view (`replay_view_v1`,
runtime `replay/view.py`) carries status, interaction and activities but no type or origin.

## Chosen route

1. **One enum, two axes, stamped once.** `_meta.run_type` (what the run is) and the existing
   `_meta.origin` (who/what started it), with `origin.surface` added (where the person was):
   - `run_type`: `conversation`, `docs`, `automation_controller`, `occurrence`, `discussion`,
     `scheduled` (legacy schedule wrapper), `entity_visit`, `entity_life` (24/7 loop / night passes),
     `import`, `correction` (person edits applied as runs, memory decision 8), `bridge`, `flow` (a Flow
     editor run), `subrun` (any descendant; the root's type is the session's type).
   - `origin.surface`: `desktop`, `iphone`, `watch`, `web`, `terminal`, `console`, `api`, `none`
     (sent by the client as a hint, validated against an enum, never trusted for authorization).
   - The session type IS its root run's `run_type`; a session never changes type.
2. **Where it is stamped.** Runtime `core/run_type.py` (enum + `stamp_run_type`, written once like
   `stamp_origin`); the gateway host at `/runs/start`, schedule, bridges, entity visit/life hosts,
   the automation controller (`build_prepared`) and the Note importers' runs. `run_attribution`
   keeps deriving `session_kind`/`role` for one release as a compatibility projection of `run_type`.
3. **Exposure.** Run index column `run_type` (+ `origin_kind`, `origin_surface`); `GET /runs?run_type=a,b`
   and `surface=`; `/conversations/search` uses the same filter; `replay_view_v1` gains `run.type` and
   `run.origin` (additive, no version bump needed if clients ignore unknown keys; the conformance
   fixtures pin it). `session_kinds.json` is retired into the index (its docs mark becomes `run_type=docs`).
4. **Migration.** A one-time, resumable index backfill (no ledger rewrite: the ledger is append-only):
   derive `run_type` from the existing signals (`_meta.automation` -> controller, `_meta.occurrence`,
   `_meta.discussion`, `_meta.schedule`, docs-qa bundle id / `session_kinds.json`, entity home runtimes
   -> `entity_visit`/`entity_life`, else `conversation`); runs with no signal are `conversation` with
   `run_type_source: "backfill"` so a reader can tell a derived type from a stamped one.

## Evidence

- `abstractruntime/src/abstractruntime/core/run_attribution.py` (module docstring: derivation order).
- `abstractruntime/src/abstractruntime/core/run_origin.py` (`ORIGIN_KINDS`, `origin_for`, `stamp_origin`).
- `abstractgateway/src/abstractgateway/session_kinds.py` (`KINDS`, side file, docs-qa migration).
- `abstractgateway/src/abstractgateway/routes/gateway.py` `_stamp_run_origin`, `_parse_session_kind_filter`, `_LIST_RUNS_KNOWN_PARAMS`.
- `abstractgateway/docs/api.md` (`GET /api/gateway/runs` rows carry `session_kind`, `automation_id`, `role`).

## Open decisions (operator)

- D1: the enum's exact names (above is the proposal) and whether `scheduled` stays distinct from `occurrence`.
- D2: does `surface` live in `origin` (proposed) or as its own field; and is it shown to other users of a shared session.
- D3: retire `session_kind`/`role` after one release, or keep them as permanent aliases.
- D4: interaction with 1024 (requester attribution): `origin.actor` vs `requester`; this item does not decide 1024.

## Scope

### In scope

- The enum, stamping at every start path, index column, `/runs` + search filters, replay view fields, backfill, conformance fixtures.
- Client adoption: list filters and routing (iPhone/watch show conversations only; Observer filters by type).

### Out of scope

- The sessions index with exact counts (gateway 0939).
- Requester/delegation semantics (1024).

## Acceptance criteria

- [ ] Runtime 0858: `run_type` stamped once on every start path; a test per path, red when the stamp is removed.
- [ ] Gateway 0951: `GET /runs?run_type=` and `surface=` filter on the index; unknown values 400; backfill is idempotent and resumable.
- [ ] `replay_view_v1` carries `run.type` and `run.origin`; conformance fixture updated.
- [ ] Every client in [1065](1065_replay_view_client_migrations.md) reads the type from the view or the listing, never derives it.
