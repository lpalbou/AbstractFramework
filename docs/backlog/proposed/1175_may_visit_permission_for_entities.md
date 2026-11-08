# 1175 — A "may visit" permission: someone other than the creator or an admin may talk to an entity

> Package: AbstractGateway (`entity_access.py`, entity routes, console), AbstractEntity (who may visit), operator ruling
> Type: feature
> Status: proposed
> Created: 2026-11-08
> Priority: P2
> Labels: entities, mentions, access, federation, paused

Paused by operator ruling 2026-11-08 (pause all dev); resume = explicit go.

## Summary

Today an entity can be visited, chatted with or summoned only by an admin or by the account that created it. Talking
to entities from every app ([1138](1138_talk_to_entities_from_code_assistant_and_notes.md)) and from another gateway
([1112](1112_cross_gateway_entity_federation_handshake_keychain.md)) needs a third answer: a permission "may visit"
(talk to the entity), distinct from "may configure" (mind, tools, state, personal time). Next release, after a ruling
on who grants it and what it exposes.

## Why

Analysis `untracked/entity-mentions-2026-11-08/ANALYSIS.md` §3: "The operator's own case (his account on both
gateways) works with his token; anyone else needs a new 'may visit' permission." The framework seat's auth view in
1112 (2026-11-08) makes it the prerequisite for any cross-gateway summon by anyone but the operator.

## Current code reality (2026-11-08)

- `abstractgateway/entity_access.py` `entity_visible_to`: admins see every entity; an entity principal sees itself;
  otherwise only the creator's account (`created_by`); a legacy home with no creator is admins only; hidden → 404.
- Live: all 16 homes have `created_by: null` (governance track, finding 20), so today only admins can visit any of them.
- No visitor list, no grant record, no console page for it. Entity accounts exist but their credential is discarded
  (`entity_accounts.py`).

## Proposed direction

- A per-entity grant list `{principal, may: visit, granted_by, granted_at, expires_at?}` recorded marker-first in the
  home (like the personal grant), revocable, listed in the console and the Entity app.
- "Visit" covers visit, chat, summon and mention for that principal, under the entity's own seat, tool policy and
  limits; configuration stays creator/admin only.
- A remote gateway's paired credential (1112) maps to one such principal.

## Promotion criteria

The operator's ruling on who grants (creator, admin, the entity itself?) and on what a visitor's turn may reach;
governance item [1022](../planned/governance/1022_entities_are_digital_users.md) direction settled.

## Validation ideas

- A member with a grant can summon the entity; without it 404; after revoke 404 again; the home records each change.
- A visitor cannot change the mind, tools or state (403 with a sentence).

## Non-goals

Public or anonymous visits; reputation-based access (1120).

## Guidance for future agents

Re-read `entity_access.py` and the governance README findings 19–24 first; the visit-turn speaker check (finding 23)
must hold for granted visitors too.
