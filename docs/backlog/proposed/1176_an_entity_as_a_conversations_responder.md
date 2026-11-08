# 1176 — An entity as a conversation's responder (`default_workflow = entity:<name>`)

> Package: AbstractGateway (`/runs/start` resolver, `agents.default_workflow`), the apps' responder pickers (Code, Assistant desktop/web/iPhone/Watch, TUI)
> Type: feature
> Status: proposed
> Created: 2026-11-08
> Priority: P2
> Labels: entities, mentions, sessions, paused

Paused by operator ruling 2026-11-08 (pause all dev); resume = explicit go.

## Summary

Option A2 of `untracked/entity-mentions-2026-11-08/ANALYSIS.md` §2: the account preference `default_workflow`
accepts `entity:<name>`, and `/runs/start` becomes a summon under the same session. A whole conversation then talks to
one entity through the ordinary conversation list, so the watch, iPhone, TUI and scripts need no new code; only the
pickers gain the entity choice. Next release (it changes a base package).

## Why

A visit is a separate object today: each client must open, find and reload it (`GET /visit`), and visits stay out of
the shared conversation list. One conversation list for every client is the stated product direction
([1138](1138_talk_to_entities_from_code_assistant_and_notes.md); one session pool for all clients, ruling 2026-09-27).

## Current code reality (2026-11-08)

- `agents.default_workflow.<interface>` and the server-side `@default` resolution exist
  ([0909](../completed/0909_default_agent_workflow_gateway_setting_and_clients.md)); they accept agent workflows only.
- `POST /entities/{name}/summon` already honours `session_id` and runs in the caller's workspace with the entity's
  identity and model (see [1174](../planned/1174_at_entity_in_the_desktop_assistant_via_summon_into_session.md)).
- Seat refusals (409 while a visit holds the seat) are not mapped for `/runs/start` callers.

## Proposed direction

Gateway resolver (≈1.5 d): `entity:<name>` → summon with the conversation's `session_id`, seat refusals mapped to
clear errors; pickers (≈0.5 d each surface) list entities the person may visit
([1175](1175_may_visit_permission_for_entities.md)).

## Promotion criteria

1174's probe proves the session/home durability; the operator's go for the next release.

## Validation ideas

- A conversation started on the watch with `entity:castor` shows castor's answers in Code web's conversation list.
- A held seat returns a sentence, not a stack trace; the conversation keeps working when the seat frees.

## Non-goals

Several entities answering in one conversation (1174's mention rules cover that); entity-to-entity messaging.

## Guidance for future agents

Read 0909's resolver and the summon route together; the entity's home must keep the episode (1145) before this ships.
