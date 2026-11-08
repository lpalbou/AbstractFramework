# 1145 — Every entity activity is durable in the runtime, and the entity can probe it

> Package: AbstractRuntime (identity/life.py personal time, chat.py, artifacts), AbstractGateway (serving entity runs and
> artifacts), AbstractEntity (reads them; other agent), AbstractMemory (verbatim/rehydration seam)
> Type: architecture + implementation
> Created: 2026-11-07
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
