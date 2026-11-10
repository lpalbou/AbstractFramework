# 1185 — Every interaction forms a memory; sleep may fold or prune the empty ones

> Package: AbstractRuntime (`identity/visit_workflow.py` FORM / REFLECT, `identity/chat.py` episode formation, maintenance pass), AbstractMemory (consolidation passes), AbstractGateway (none expected)
> Type: design
> Status: proposed
> Created: 2026-11-09
> Priority: P2
> Labels: entities, memory, formation, sleep, maintenance, decision-gate

## Summary

Operator ruling, 2026-11-09: "a visit, as any work or personal time can generate 1+ memories. the memory can be extremely
short if the interaction was informationless, but i believe every interaction should create a memory. sleep/maintenance
phase could however aggregate irrelevant memories (eg i had 10 "useless" interactions) or prune them entirely - to be
discussed."

The first half is a rule, already met by the code (below). The second half is the open design question this item keeps:
whether, and how, the sleep pass folds or prunes memories that carry no information.

## Current code reality (2026-11-09, runtime 23a79d6)

- A visit forms one `episode` per turn (`visit_workflow.py` FORM, every turn, no content gate), with an authored title
  and summary since gateway 58b51667 (verified live 2026-11-09 18:10 on hypnos and castor).
- A visit with at least one turn forms its close summary in REFLECT. A visit closed with zero turns forms nothing
  (`reflect_node`: empty sheet -> DONE), since no exchange happened. A paused close defers its look-back to the next
  open.
- Own time and work turns form one `episode` per exchange in `chat.py` (also no content gate). Today that path forms the
  episode pending and authors it right after; Codex review 2 finding 10 moves it to authoring before formation.
- A mention answer runs through the visit door, so it forms like a visit turn.
- No maintenance pass folds or prunes low-information episodes today.

## Open questions (operator decision gate; never assignable)

1. Does a zero-turn visit (opened and closed without a word) count as an interaction that should leave a memory?
2. Fold or prune: should the sleep pass fold N low-information episodes into one aggregate record (keeping their ids
   as evidence), delete them, or only lower their recall weight?
3. Who judges "informationless": the entity during its own sleep (authored judgment, no text heuristics per the
   no-regex rule), never a length or keyword threshold.
4. Does folding keep the originals' ledger provenance (the ledger stays the record; memory is reconstruction)?

## Operator answers 2026-11-11 00:40

- Q1 (zero-turn visit): "no and it should not even be remembered, fix it" — a visit opened and closed without a word
  forms NO memory; fixed at the runtime level (visit close) as a 0.19.4 fix, not deferred. A one-line exchange shares
  words and keeps forming a memory (the 2026-11-10 ruling).
- Q2-Q4 (fold / prune / who judges / provenance): "let's leave that for a next release, create a backlog item to
  discuss it" — this item IS that discussion; it stays proposed, decision gate, next release.

## Non-goals

- No content gate at formation: every exchange forms its memory, however short.
- No regex, length or keyword heuristic to classify a memory as useless.

## Validation (once decided)

A day with ten one-line exchanges forms ten authored episodes; the next sleep produces the decided outcome (fold, prune
or reweight) with a receipt naming every record it touched; recall afterwards reflects it.
