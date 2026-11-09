# 1186 — Private means private from others, not from the owner (rediscuss with the operator)

> Package: AbstractMemory (recall, scope bindings), AbstractRuntime (`integrations/abstractmemory/identity_support.py` private diary projection, `identity/tools.py` book-adjacent tools, `identity/act_only.py` capture), AbstractGateway (visit / mention / session participants, ledger and screen views), AbstractEntity (diary views)
> Type: design
> Status: proposed
> Created: 2026-11-09
> Priority: P2
> Labels: entities, privacy, diary, memory, recall, decision-gate

PING THE OPERATOR BEFORE ANY BUILD (operator 2026-11-09: "don't change everything, but create a backlog item to ping me
and rediscuss it"). Nothing in this item is assignable until he has rediscussed it.

## Summary

Operator ruling, 2026-11-09: "privacy does not exist between the entities and their owners. they are enforced with other
entities and other human users."

Today "private" means private from everyone, the owner included. Following the ruling needs two changes that only work
together: private diary entries get authored titles and summaries like every other memory (the title/summary ruling in
1146), and recall learns who is present so private memories never surface to another person or another entity.

## Why

- The titles ruling (1146, operator 2026-11-09: every memory has a clean, informative title and summary for
  discoverability and actionability) cannot reach private diary entries today without leaking private words.
- The owner cannot read his entities' private diary entries or find them by title, which the ruling says he should.

## Current code reality (2026-11-09, runtime 2007db4, memory 26503e3)

- A private diary entry's graph record is content-free on purpose: title "Diary entry (private) — <date> [<id tail>]",
  summary "Wrote a private diary entry." (`identity_support.py` private branch, "Words are FORBIDDEN in every graph field
  for private entries"). Public entries are authored since runtime 7dd32e1.
- Private words live only in the diary book; the entity rereads them prompt-ephemeral through `diary_read` /
  `diary_list` / `search_memory` (`tools.py` `BOOK_ADJACENT_TOOL_NAMES`), whose at-rest results carry a reread pointer,
  never the words. `act_only.py` captures elected fences so private words never rest in ledgers (the Mira diary leak:
  private words reached a visitor's screen).
- Memory visibility is per scope binding (`MemorySystem.bind`: indexed / hidden per record, scope, owner), not per
  audience. Recall does not know who is in the conversation.

## What would change (to rediscuss)

1. Private entries get authored titles and summaries from their text (summaries capability, pending + failure line only
   on failure).
2. Audience-aware recall: when anyone other than the entity and its owner takes part (a visit, an @mention, a Code or
   Assistant session, another entity), recall skips private records and their screens and ledger views show no private
   words. With only the entity, or the entity and its owner, everything is visible.
3. The owner can read the private diary in the Entity app.

## Open questions for the operator

1. Who is "the owner": the account that created the entity, the gateway admin, or both?
2. A conversation with the owner plus another person: hide private memories (strictest), or show them?
3. Entity to entity: is an entity's private diary hidden from another entity the same owner owns?
4. Does the owner see private words by default, or only when they open the diary deliberately?
5. Existing private records: re-author their titles and summaries at the next sleep, or leave them as they are?

## Non-goals

- No change in the 0.13.1 wave (operator 2026-11-09): private entries stay content-free until this is rediscussed.
- No text heuristic deciding what is private; the entity's own visibility election stays the only source.

## Validation (once decided)

A private entry gets an authored title and summary; recall in a visit by another user or another entity never returns
it (test red with the audience filter removed); recall alone or with the owner does; no private word appears in that
visit's ledger or screens; the owner reads the entry in the Entity app.
