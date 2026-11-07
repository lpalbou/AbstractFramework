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

## Coordination

Split proposed to the AbstractEntity session 2026-11-08: framework owns runtime + gateway; the Entity owner owns the app
side; abstractmemory verbs to whoever is free first. Their answer is appended here when it arrives.

## Acceptance criteria

- [ ] Every entity activity since the change has a run id; `GET /runs/{id}/ledger` lists its tool calls.
- [ ] A fetched page is readable as an artifact a week later.
- [ ] AbstractEntity's "Now" line and ledger show personal-time tool calls live (today impossible).
- [ ] No duplicate loops, no change to the 1800 s patience or the heartbeat contract (runtime 0.18.4 tests stay green).
