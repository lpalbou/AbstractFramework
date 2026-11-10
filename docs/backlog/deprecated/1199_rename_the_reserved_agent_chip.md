# 1199 — Rename the reserved `@agent` chip (candidate: `@ai`) — REJECTED, `@agent` stays

> Package: AbstractGateway (reserved slug, 409 name_reserved, mentions routing), AbstractEntity, AbstractAssistant web, AbstractCode web + TUI, AbstractUIC panel-chat (the chip)
> Type: enhancement
> Status: deprecated (rejected by the operator 2026-11-11 00:40: "I only proposed alternatives because you seemed to have issue with @agent. but if you don't, no let's keep it" — the reserved chip stays `@agent`)
> Created: 2026-11-10
> Priority: P3
> Labels: mentions, naming, ux

## Summary

Gateway 0.21.0 (649776c5) reserves the entity name `agent`: a message whose chips name only entities starts no agent
run; the `@agent` chip addresses the session's own agent. The operator (2026-11-10 ~11:50) is open to another name:
"@session ? or @worker ? or just a generic @ai ?". Not done in 0.21.0 because the slug is already pinned in five
repositories (gateway, Entity 8b86d00, Assistant web 3e37883, Code web 4beb02f, Code TUI a602c4c) and the gate.

## Recommendation

`@ai`: short, generic, never an entity's wanted name. `@session` is gateway jargon; `@worker` implies a job (1187).
Keep `agent` accepted as an alias for one release so older clients keep working; reserve both names at creation.

## Validation

Every client's chip and the gateway's reserved-name test renamed in one wave; a message with `@ai` alone runs the agent;
`agent` still routes during the alias release; an entity named `ai` or `agent` is refused with 409.
