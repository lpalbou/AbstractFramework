# 1203 — An entity has pronouns, set at creation, and every surface uses them

> Package: AbstractRuntime (identity: the entity's identity record), AbstractGateway (create-entity + identity routes serve `pronouns`), AbstractEntity, AbstractAssistant, AbstractCode, AbstractObserver, AbstractUIC (EntityCard, panel-chat author header), AbstractTUI (copy that names the entity)
> Type: feature
> Status: proposed (operator 2026-11-11 00:40: "delay that, it's fine" — next wave; default for new entities still to decide then)
> Created: 2026-11-10
> Priority: P2
> Labels: entities, copy, cross-seat, decision-gate

## Summary

Operator, 2026-11-10 21:30, on the Entity app's closing line "Closing — his reflection runs now (he looks back over
the visit…)": "be careful of he/she/it?". Fact: no pronoun field exists anywhere today — not in the app, not in the
runtime's `identity.json` (keys: schema_version, rev, avatar, voice, set_at, set_by), not in the gateway's entity
payload. Every entity is "he/his" by hard-coded copy across the Entity app (hundreds of strings: "his own time",
"he looks back", "what he knows", …), the kit's EntityCard and the other apps' entity mentions.

## Scope

1. Runtime: `identity.pronouns` ∈ {he, she, they, it} (subject/object/possessive derived), default `they` for new
   entities, set by the creator at creation (creator-configures-entity, root 1199 family) and editable in Settings;
   existing homes keep `he` until edited (no silent change of a living entity's voice).
2. Gateway: served on the entity payload and the roster; accepted by the create and identity-update routes.
3. Apps/kit: one pronoun helper per surface (`pron.subject/object/possessive/reflexive`, capitalised variants) and a
   sweep of every hard-coded "he/him/his" string; the kit's EntityCard and panel-chat author header take the entity's
   pronouns as a prop. No regex rewriting of model text: the entity's own words stay as it wrote them.
4. Until 1–3 land, new copy written for an entity avoids pronouns where it reads naturally (the Entity app's closing
   notice is already pronoun-free, 2026-11-10).

## Validation

A `she` entity and a `they` entity created through the gateway show correct copy on the roster, the entity page
(toolbar sentences, closing notice, Topics, Card), the Assistant/Code mention bubbles and the TUI; a test per surface
renders the three pronoun sets; `grep -n " he \| his \| him "` over user-facing strings finds only the helper.

## Owner

Framework seat (runtime + gateway contract first), then the Entity/kit seat for the sweep. Decision gate: the operator
confirms the default (`they`) and whether `it` is offered.
