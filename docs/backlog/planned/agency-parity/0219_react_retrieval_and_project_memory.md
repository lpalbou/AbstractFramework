# 0219 — ReAct Retrieval + Project Memory (backlog only)

**Status**: Planned (backlog record only — implementation owned elsewhere / in progress)
**Date**: 2026-07-07
**Priority**: High (retrieval quality per token)
**Components**: abstractagent (react_runtime), abstractruntime (memory seam / MEMORY_RECALL, integrations/abstractmemory), abstractcode/gateway (AGENTS.md loading)

## Summary
Give the coding ReAct loop (a) retrieval-first context backed by the real `abstractmemory` engine
instead of grep-grade span matching, and (b) repo-level `AGENTS.md` project memory. **This item is a
backlog record only** — per maintainer direction, do not implement it in the current agency-parity
wave; the retrieval work is owned/underway elsewhere.

## ADR status
- Governing ADRs: ADR-0005 (memory architecture), ADR-0007/0009 (active context/provenance), ADR-0026.
- ADR impact: To be determined by the owning track.

## Context / current code reality
Verified 2026-07-07:
- The `abstractmemory` engine (vector/keyword/exact/participants channels, spreading activation,
  usage-weighted ranking, budgeted shelf) is wired **only** into entity homes: its seam handlers are
  consumed by `abstractruntime/identity/chat.py`, `abstractgateway/entity_gate.py`, and tests/demos.
  The default runtime factory registers no `MEMORY_RECALL` handlers.
- ReAct's `recall_memory` maps to `MEMORY_QUERY`: metadata-first substring/tag/time filtering over
  compaction spans, "intentionally metadata-first and embedding-free (semantic retrieval belongs in
  AbstractMemory)" (`core/runtime.py:2871-2896`).
- The entity chat driver is the existing retrieval-first loop (recall → render-under-budget → LLM →
  commit → form episode; transcript capped at 10 turns), `identity/chat.py`.
- The MemAct composer is the one existing bridge from a memory store into an agent loop
  (`memory/memact_composer.py`, `memact_runtime.py:239-398`), opt-in.
- **No project memory**: no `AGENTS.md`/`CLAUDE.md`/rules loading anywhere in abstractcode/
  abstractagent/gateway (the only `AGENTS.md` hits are code comments). The mechanism to inject exists
  (`_runtime.system_prompt_extra`, `react_runtime.py:391-404`).

## Problem
Coding sessions get weak retrieval while a strong engine sits unused next door, and the loop has no
repo-specific behavioral memory that Codex-class harnesses get for free from `AGENTS.md`.

## Proposed direction (for the owning track)
- A `MEMORY_RECALL`-backed composer for ReAct (mirroring the MemAct composer / entity driver) plus
  per-task episode formation, so coding context is retrieval-first and usage-weighted.
- Load workspace-root `AGENTS.md` (and nested/team variants) into `_runtime.system_prompt_extra`,
  respecting the cache-prefix discipline from 0212 (stable placement) and language-safety rules.

## Maintainer review 2026-07-08 (scope caution + cache placement ruling)

The maintainer is UNSURE this is a good idea ("i am unsure of it"); the plausible case he named is
session persistence (reconnecting to a session where the project context should still hold).
Record the honest analysis:

- **Verified today**: nothing injects AGENTS.md anywhere; the only injection surface is
  `_runtime.system_prompt_extra`, which `_compose_system_prompt` appends at the END of the SYSTEM
  prompt (`react_runtime.py:394-407`) — i.e. the head of the request, inside the cached prefix.
- **Cache math (the maintainer's concern)**: content in the system prompt invalidates the whole
  prefix cache when it CHANGES. The right policy is therefore snapshot-at-session-start: read the
  file ONCE when the session/run starts, freeze it in `_runtime.system_prompt_extra` (durable
  vars), and never re-read mid-session. Within a session the prefix stays byte-stable and CACHED
  (that is where rarely-changing, always-relevant content belongs — it gets cache HITS, unlike
  the per-call volatile tail); an edited AGENTS.md takes effect on the next session, costing one
  cold prefix — the same cost every harness pays. Live-verified context: the 0212 evidence shows
  the system prompt is currently byte-stable and OpenAI serves ~61% of input from cache.
- **Risks that justify the maintainer's hesitation** (must be addressed by any implementing
  track): (a) prompt-injection surface — a repo file becomes system-prompt content; anyone who
  can commit to the repo steers the agent (Codex/Claude Code accept this; a gateway-hosted
  multi-tenant deployment maybe should not — needs a policy/size cap + provenance marker);
  (b) size discipline — an unbounded file bloats every call in the session (needs a documented
  cap with an explicit ADR-0026-marked notice, or artifact-backed overflow);
  (c) opt-in vs default — given (a), load-if-present should likely be a per-run/gateway policy
  flag, not silently-on.
- **Skills relationship** (maintainer asked): skills are NOT implemented; per the 074 design
  (docs/guide/agent-skills.md), only name/description METADATA would enter the prompt
  (progressive disclosure) and full SKILL.md bodies load on explicit activation as tool results
  (message stream, not system prompt) — so skills already follow the cache-friendly pattern:
  stable tiny metadata in the prefix, on-demand bodies in the transcript. AGENTS.md is the
  simpler cousin (always-on project memory), and if both land, AGENTS.md content and skill
  metadata should share ONE stable "project context" block at the system-prompt tail.

## Non-goals
- No implementation under this item now (maintainer direction).
- Do not duplicate the entity-memory engine; reuse the seam.

## Dependencies and related tasks
- Coordinate with the owning retrieval/memory track before promoting to active implementation.
- 0212 (cache discipline for any injected project-memory block).

## Expected outcomes (when the owning track executes)
- ReAct retrieval uses the abstractmemory engine (vectors/activation), not substring matching.
- Repo `AGENTS.md` shapes coding-agent behavior with stable, cache-friendly placement.

## Validation ideas
- Retrieval quality A/B (relevant-context hit rate) vs the current `MEMORY_QUERY` path.
- Behavioral test that repo `AGENTS.md` guidance changes agent behavior.

## Guidance for future agents
Backlog record only. Do not implement in the agency-parity wave; hand off to the retrieval/memory
owner.
