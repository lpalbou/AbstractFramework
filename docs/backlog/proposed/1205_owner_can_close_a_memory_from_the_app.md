# 1205 — The owner can close (retract or supersede) a memory from the Entity app

> Package: AbstractGateway (a close route on a memory, owner-only, with reason and kind), AbstractEntity (Retract / Supersede action in Detail), AbstractMemory (close_record / close_assertions exist: retract, supersede, reinterpreted, merged)
> Type: feature
> Status: proposed
> Created: 2026-11-10
> Priority: P2
> Labels: entities, memory, ownership, privacy

## Summary

Found by the website's user review (2026-11-10): "can I make it forget something?" has no answer in the app. Facts: memory is
append-only, never deleted; a closure (retract / supersede / reinterpreted / merged, with a reason) takes a memory out of
every recall and prompt and keeps it in the book as history; the Entity app shows closed memories as Retracted /
Superseded; but today closing is reachable only as the entity's own act or an operator flow (MEMORY_ADJUST op=close):
the gateway has no close route and the app no button. The owner sees everything (ruling 2026-11-09) and should be able
to close a memory with a reason, as the entity itself can.

## Scope

1. Gateway: `POST /entities/{name}/memories/{id}/close {kind, reason}` (owner-only; kinds retract / supersede with the
   replacing id), recorded in the stream as the owner's act (author = the owner, never the entity), the closure's row
   served with the record as today.
2. Entity app: Retract / Supersede in Detail with a reason field; the entity learns of it (a notice on its next summon:
   "your owner retracted X: reason") so nothing happens behind his back.
3. Docs: entities.md "What the owner can do to a memory"; the website's forgetting paragraph updated.

## Non-goals

No deletion, no purge, no silent closure (the entity is told), no closing of another entity's memories.

## Validation

A retracted memory stops appearing in recall and the prompt; shows Retracted with the reason in Detail and the Book; the
entity's next summon carries the notice; a non-owner is refused.
