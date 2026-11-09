# 1145 — Every entity activity is durable in the runtime, and the entity can probe it

> Package: AbstractRuntime (identity/life.py personal time, chat.py, artifacts), AbstractGateway (serving entity runs and
> artifacts), AbstractEntity (reads them; other agent), AbstractMemory (verbatim/rehydration seam)
> Type: architecture + implementation
> Status: completed
> Created: 2026-11-07
> Completed: 2026-11-10
> Priority: HIGH (operator 2026-11-08: "this needs to be prioritized")
> Labels: entities, runtime, ledger, durability, memory

## Operator rationale (2026-11-08)

"Everything that is in the runtime enables some sort of 'rehydrate' to memory. So the entity itself could probe the
runtime to get access to more verbatims and/or to understand why certain things happen. So I want durability here."
Earlier the same day: "Any activity HAS to go through the runtime and the ledger"; "anything the AI retrieves (pages,
images) becomes part of its runtime."

## Current code reality (verified 2026-11-07, memory note `entity-live-ledger-2026-11-07`)

- Visits ARE durable: `entity-visit@1` runs with `tool_calls` effects in the home's `runtime_<slug>.sqlite3` ledger.
- Personal time is NOT: it runs home-direct (`identity/life.py` ~1529 "ChatSession, no run ledger"; stand-in `_Run`,
  `chat.py` ~1075; tools are direct abstractcore calls, `tools.py` ~794/824). Its tool calls survive only inside the
  tick's `memory_verbatim` artifact written at tick end (`GET /entities/{name}/records/{graph_id}/verbatim`).
- Fetched pages and images are not kept anywhere.
- The gateway's `/runs/{id}/view` reads only the gateway run store: 404 for entity runs.

## Scope

### In scope

1. **Personal ticks are real runtime runs**: each tick (day, nap, dream window) is a run in the home's runtime with the
   same ledger as a visit (llm_call, tool_calls, artifacts), resumable and replayable; the loop heartbeat and the
   1800 s patience (runtime 0.18.4) unchanged.
2. **Retrieved material is kept**: every page, image, file or search result a tool returns during entity activity is an
   artifact of that run (content-addressed, size-bounded with the bound recorded, never silently dropped), referenced
   from the ledger effect, so memory can rehydrate the verbatim later.
3. **The gateway serves entity runs**: `/runs/{id}/view`, `/ledger` and artifact reads work for entity runs (read through
   the home's runtime store, principal-scoped), so AbstractEntity, Observer and the entity itself can probe them.
4. **The entity can probe its own runtime**: a read-only tool (or memory verb) "what happened at <time> / around
   <record>" that returns the ledger slice and verbatims for a run, so a memory can be re-understood from evidence
   (feeds 1146).
5. Tests: a personal tick with two tool calls and one fetched page leaves a run whose ledger lists both calls and whose
   artifact holds the page; the gateway returns it; deleting the artifact write makes the test red.

### Out of scope

- The understanding pass itself (1146). The Entity app's screens (other agent; coordinated through 1145's gateway contract).

## Coordination (settled with the AbstractEntity session, 2026-11-08 ~02:00)

The AbstractEntity owner (another Claude session on this machine) holds the full design and 12 draft items:
`untracked/understanding-pass-2026-11-07/DESIGN.md` and `drafts/{abstractmemory,abstractruntime,abstractgateway,
abstractentity,abstractframework}/`. Agreed split: **framework owns abstractruntime + abstractgateway** (this item, plus
drafts runtime 0867–0870 and gateway 1012–1013, which belong to 1146); **the Entity owner owns abstractmemory
(0059 versions, 0060 task queue, 0061 ripple v1), the app (0001–0002) and the one-time backfill (1137)**. Whoever starts
a repo says so first; nothing in a base package starts before the operator's go on DESIGN.md §16 (8 open decisions).
Rules for all: one checkout per repo (main), small commits, adversarial review with screenshots before the operator
tests, no publish without their go.

Facts corrected by the Entity owner: theforge-nvidia (`compat-theforge-nvidia`, 192.168.1.7:1234) runs
`qwen/qwen3.8-27b` at 62,464 tokens of context (not 140k); inputs are capped at 56k (longest verbatim ≈ 24k); the whole
understanding plan is ≈82 h in 15 steps (not 26 h).

## Acceptance criteria

- [ ] Every entity activity since the change has a run id; `GET /runs/{id}/ledger` lists its tool calls.
- [ ] A fetched page is readable as an artifact a week later.
- [ ] AbstractEntity's "Now" line and ledger show personal-time tool calls live (today impossible).
- [ ] No duplicate loops, no change to the 1800 s patience or the heartbeat contract (runtime 0.18.4 tests stay green).

## Operator ruling (2026-11-08 11:45) and the order of work

"Do your best. But there should be no activity, either by human or by entities, that does not go through the
runtime. One of the reasons is to enable retrospective analysis / search, including to rehydrate context/memory."

Order, settled with the operator the same morning: (1) every tool result during entity activity (pages, files,
search output, images) stored whole as an artifact in the entity's home and referenced from the verbatim; (2) the
gateway serves entity runs read-only (`/runs/{id}/view`, `/ledger`, artifacts) so the Entity app, Observer and the
entity itself can open them; (3) the probe tool "what happened around <time>"; (4) personal ticks as real runtime
runs (the principle above makes this mandatory, not optional; it is the largest step and comes last).

## Status 2026-11-08 14:10 (operator: steps 3–4 are a planned item for the NEXT release)

Done and live since 13:30: step 1 (runtime d217d93: every tool result during entity activity rests whole as a home
artifact, visits and personal time) and step 2 (gateway d1d9656f: `GET /entities/{name}/artifacts`, `/{id}/meta`,
`/{id}`; visit tool results wired). Remaining for the next release: step 3 (the "what happened around <time>" probe
tool) and step 4 (personal ticks as real runtime runs). The Entity app's artifact chip is root 1170.

## Completion report (2026-11-10): steps 1–2 built; steps 3–4 continue as 1188

Moved from `planned/1145_entity_activity_is_durable_in_the_runtime.md` to `completed/` by the backlog hygiene pass of
2026-11-10. This record closes **steps 1 and 2** of the order settled on 2026-11-08 (tool results kept whole in the
entity's home; the gateway serves them). **Steps 3 and 4** (the probe tool, personal ticks as real runtime runs) are
the operator's planned item for the next release ("steps 3–4 are a planned item for the NEXT release", 2026-11-08
14:10); they continue, with this item's rulings and the acceptance criteria not met here, as
[1188](../planned/1188_the_entity_probes_its_own_runtime_and_personal_ticks_are_real_runtime_runs.md). Built and
committed on `main`; not released (ships with [1179](../planned/1179_release_wave_understanding_pass.md)).

### What was built (commits checked against each repo's log on 2026-11-10)

| Repo | Commit | What |
|---|---|---|
| AbstractRuntime | `d217d93` (2026-11-08 12:20) | `execute_tool_elections(artifact_store=, artifact_context=)` stores every executed tool result whole through `keep_tool_result_artifact`: content-addressed, no size cut, metadata (tool, arguments, turn or tick id, record id, lane, run id, entity id, bytes); the result text ends with `[artifact: <id>]` so the verbatim and the records name it. `fetch_url` keeps the whole page past its 6,000-character view, `read_file` the whole bytes, `execute_command` the whole output. Wired on the effect lane (real run id) and on the home-direct `ChatSession` lane (visits and personal time) |
| AbstractGateway | `d1d9656f` (2026-11-08 12:33) | the visit tool handler passes the home's artifact store; result rows and `tool_details` carry `artifact_id`; three read routes: `GET /entities/{name}/artifacts` (filters by run, tool, turn; newest first; bounded; cursor), `…/artifacts/{id}/meta`, `…/artifacts/{id}` (bytes with the stored content type); 404 for an unknown id; no host path in any answer |

Live since restart #2 (2026-11-08 13:30, runtime `da03304`, gateway `2a68b105`). Release floor: the gateway needs the
runtime that carries `keep_tool_result_artifact` / `tool_result_media`, i.e. AbstractRuntime 0.19.0 (HARD; 1179).

### Tests

- `d217d93`: effect lane with a search and a 30 KB `read_file` (two artifacts, byte for byte); a personal-time fetch
  of a 20 KB page kept whole and named by the verbatim; a lane without a store unchanged; all red against the source
  before the change.
- `d1d9656f`: route tests for the list, meta and bytes reads and the 404; docs, changelog fragment, llms-full.
- Hermetic suites at every HEAD, 2026-11-09 (`untracked/release-2026-11-07/audit-fable/VERIFY.md`): none of the
  failures is in these files.

### Acceptance (as written above)

- [ ] Every entity activity has a run id and its ledger lists the tool calls: visits yes; personal time still runs
      home-direct with a stand-in `_Run` (`identity/chat.py:630`, `identity/life.py:2394` "no run ledger") → 1188.
- [x] A fetched page is kept whole as an artifact of the home and readable through the gateway route (the "a week
      later" check has not been run; the store is durable and content-addressed).
- [ ] AbstractEntity's "Now" line and ledger show personal-time tool calls live → 1188 (needs step 4); the app's
      artifact chip is [1170](../planned/1170_session_kinds_client_halves.md).
- [x] No duplicate loops, no change to the 1800 s patience or the heartbeat: steps 1–2 do not touch the loop.

### Residual follow-ups

- Steps 3–4 → 1188 (planned, next release).
- The Entity app's artifact chip on tool lines → 1170 (planned, first in the next release).
- The generic `/runs/{id}/view` (`routes/replay_view.py`) and `/runs/{id}/ledger` (`routes/gateway.py:11994`) still
  read the gateway run store only; entity runs are served by the entity routes (`routes/entity_replay.py`: replay,
  verbatim, artifacts). Whether the generic routes must also answer for entity runs is part of 1188.
- ADR state: no new ADR; the rule "no activity, human or entity, outside the runtime" (operator 2026-11-08) is
  recorded here and in 1188. An ADR is due when step 4 changes the loop's contract.
