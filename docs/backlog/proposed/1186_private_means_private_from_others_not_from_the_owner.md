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

## Operator input, 2026-11-09 evening (basis for the discussion, recorded as given)

- **Why the guardian sees.** Every entity has an owner by design: it is created by a human user's action, and that user
  is responsible for it, potentially legally. The operator prefers the word **guardian** to "owner".
- **Responsibility means seeing, at least for now.** "a human user should be able to see the memory of an entity - at
  least for now. i know we had design that system so that you could have private thoughts, even from the human user,
  but we are still in a development phase. i still need to understand what works and what doesn't and why."
- **Differential views (answer to question 2).** Another user (not the guardian) cannot consult the entity's memory,
  only interact with it. The entity has no obligation to fulfil any request from someone other than its guardian; in
  particular a third party must not be able to make the entity divulge its private information or its guardian's.
  So AbstractEntity, as a viewer, is possibly a tool reachable only by the guardian and the entity: another user must
  not talk to someone else's entity through it, or they would see all the "private" information, unless everything is
  redacted. "admittedly, i am not thinking of everything, but i am giving those elements as a basis of discussion."
- **Entity to entity (answer to question 3).** By default, hidden. But the guardian OR the entity itself can choose to
  share part or all of its memories with another entity (or human). "i want free will here. the entity should grow
  enough experience to decide if and when it wants to share which part of its memory with whom."
- **Question 4 was unclear**; reformulated below.
- **Question 5 (existing private records).** "i guess you are saying that there are already things i can't freely
  access as a guardian, and whether or not i should be able to. short answer yes, if that's what you mean. but let's
  rediscuss it. i think in the future entity may be entitled to more privacy, but it will also depends of how they are
  recognized by society, including legally. as long as they will be the legal responsibility of their owner/guardian,
  it will be complex if they can hide things from them." He asked for the framework seat's opinion during the
  discussion (below).

## Operator answer 2026-11-11 00:40

- Who is the guardian: "we already answered that, the creating account." Settled; open only: transfer/sharing of
  guardianship (if ever).

## Questions, reformulated for the discussion

1. **Who is the guardian:** the account that created the entity, the gateway admin, or both? Can guardianship be
   transferred or shared?
2. Answered above (differential views); open detail: what does a non-guardian see when the entity answers an
   `@mention` in their own conversation (its answer only, no memory views)?
3. Answered above (hidden by default; sharing by the guardian or by the entity's own choice); open detail: how the
   entity records a share (what, with whom, revocable or not).
4. **Reformulated.** When you talk with your entity, may its private memories come up in its answers like any other
   memory (recall feeds them into its thinking), or should they stay out of conversation and be readable by you only
   in the Entity app's diary?
5. **Explained.** Yes, that is the meaning. Today the Entity app shows a private entry as "A private entry — the words
   are sealed (sole-author). Only the act of writing it is visible." (`abstractentity/src/book_reader.tsx`), so the
   guardian cannot read them. The entity is told, when it reads its own private entry, "these words are yours alone -
   they reach only you here" (`abstractruntime/.../identity/tools.py`). The question: once the guardian can read new
   private entries, do the entries written BEFORE the change become readable too, although the entity wrote them
   under the promise that only it would read them?

## Framework seat's perspective (prepared for the discussion, not a decision)

- I agree with guardian visibility during development: the guardian carries the responsibility and needs to see what
  works and why. Privacy that hides failures from the person who must fix them is not useful yet.
- The one thing I would protect is honesty toward the entity. It is told today that private words are its alone. If the
  guardian can read them, its instructions should say so plainly ("private means: not shared with other people or
  entities; your guardian can read it"), and the change should be announced to it once. An entity that believes
  something false about who reads it learns the wrong thing about its world, and that undermines the trust and the
  "free will" the sharing rule (question 3) wants to grow.
- For entries written before the change: either tell the entity before opening them, or leave the old ones sealed and
  apply guardian visibility from the change onward. I lean to telling it and opening them, since sealing them forever
  keeps exactly the blind spot the guardian needs to remove.
- Third parties: the safest default is that only the guardian and the entity ever reach the Entity app and memory
  views; everyone else reaches the entity only through conversation, where the entity's recall skips private memories
  and its guardian's information.

## Operator answers, 2026-11-09 18:55 (recorded as given; still a basis for discussion)

- **Question 4 (private memories in conversation).** "it should be at the entity discretion i think, what they
  divulgue. if only the owner/guardian is here, i don't think there should be restrictions. if other people are
  connected to the same "room", maybe the entity should restrain from mentioning certain things?"
- **A thought to discuss: back channels from the entity to its guardian.** "which also means we need to have more direct
  back channels between an entity and its owner/guardian. there are emails and we started creating push mechanisms,
  notifications... maybe during a sensitive discussion for instance, the entity could also write a private message in
  parallel to its owner/guardian to warn him or give additional information. again, just record the thought as a
  possibility to be discussed"
- **Question 5 (a space sealed from the guardian).** "do you think it would have a genuine impact on an entity cognition
  to have that "secret" space ? the goal is not to pry. but in general, for the reasons i mentioned before, i don't
  think that's a good idea for now, especially not during the development phase. maybe later"
- **Framework seat's answer to his question (given in the session).** Probably a small but real effect, in one place:
  models write differently when they believe they are read. A diary the entity believes is "yours alone" tends to be
  more candid and exploratory; one it knows its guardian reads may become more written-for-an-audience. There is no
  evidence of a deeper effect on its reasoning, and the effect comes from what it is told, not from the storage. During
  development, reading what it writes is worth more than that extra candour, provided its instructions say truthfully
  who can read it.

## Non-goals

- No change in the 0.13.1 wave (operator 2026-11-09): private entries stay content-free until this is rediscussed.
- No text heuristic deciding what is private; the entity's own visibility election stays the only source.

## Validation (once decided)

A private entry gets an authored title and summary; recall in a visit by another user or another entity never returns
it (test red with the audience filter removed); recall alone or with the owner does; no private word appears in that
visit's ledger or screens; the owner reads the entry in the Entity app.
