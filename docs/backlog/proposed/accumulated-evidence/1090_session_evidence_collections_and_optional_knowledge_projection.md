# 1090 — Session evidence collections and optional knowledge projection

> Package: abstractmemory, abstractsemantics, abstractruntime, abstractgateway, abstractnote, abstractflow
> Type: task
> Created: 2026-10-31
> Status: proposed
> Priority: P2
> Labels: decision-gate, awaiting-user-confirmation, collections, knowledge-graph, evidence
> Work-item id: abstractframework-1090
> Owner: framework

## Summary

OPERATOR DECISION GATE (never assignable): design an optional structured view of accumulated
findings, including session collections/subgraphs and integration with the larger knowledge graph.
**Await the operator's explicit confirmation before undertaking this work.** Display 1088 does not
depend on graph storage, and 1089 need not persist every interpretation as long-term knowledge.

## Why

The operator relates this to AbstractNote's text-to-subject/predicate/object processing, while
questioning whether that application's much larger memory workflow is necessary for avatar UX.
A session can define a collection of evidence/findings without becoming a separate graph engine.

## Current code reality

- Note `process/schemas.py:Extraction` has mentions, SPO, certainty/stance, verbatim evidence and
  validity; `process/validate.py` explicitly validates structure, not meaning.
- Note `flows/build.py` runs filing/context, section extraction, resolution, linking and revision
  through several model steps. It is not a lightweight per-tool observation formatter.
- Note `store/kg.py` still owns a private notebook KG projection. Accepted Memory ADR 0003 names
  it as migration debt; importing it as canonical chat storage would perpetuate that divergence.
- No first-class public session-collection API was found in the inspected Note/Memory sources.
  Memory already supplies `TripleAssertion`, `MemoryGraph.apply_revision`, history and source
  indexing; Runtime's `MemoryFacade` stamps and reconstructs typed provenance.
- Memory ADR 0003 defines one graph implementation, minds with strict ownership, and scope distinct
  from owner. Runtime ADR 0011 requires host access through the facade.
- Semantics already declares predicate/role vocabularies. Koine review is separately proposed as
  AbstractSemantics 0004; no ontology change is implicitly approved by this item.

## Proposed direction and boundaries

- Begin with collection membership/query scope over stable existing finding/source identities:
  session, run and owning person/entity are explicit. One session = one collection is a candidate
  default, not permission to merge owners/minds or create another SQLite database per chat.
- Keep direct observations, inferred findings and decisions distinct. Retain the proposition
  itself as well as evidence support, source derivation and extraction activity provenance.
- Use the existing graph/revision surface for selected controlled assertions; resolve vocabulary
  through Semantics. Preserve re-observation, contradiction, retraction and supersession history.
- Preserve source observations and the exact model-visible material. The memory-writing STARTED
  step is process provenance; explicitly reference output artifacts supporting the proposition.
  Current SourceRef has no offset/selector fields; do not smuggle new keys into it.
- Define collection retention/deletion, alias/identity reuse and access filtering. A retained
  hash alone cannot replace evidence after source deletion; source_gone/partial stays visible.
- Share reviewed text-to-claims behavior through the established lower-level boundary if needed;
  Note consumes the same Memory operations. Do not mandate a new package, invoke full note-process
  for every tool, or add a Note dependency to Runtime.
- Selective promotion from a session into durable knowledge requires an explicit policy and
  provenance. Displaying/persisting a draft finding does not establish truth or authorize promotion.

## Acceptance criteria

- [ ] Operator confirms the collection/persistence goal independently of presentation and extraction.
- [ ] Session collection, ownership, membership and optional long-term promotion semantics are reviewed.
- [ ] Public operations route through Runtime facade and existing Memory graph, with no parallel store.
- [ ] Assertions preserve proposition, support references, derivation, producer and temporal scope.
- [ ] Replayed/retried extraction is idempotent; later re-observation remains a distinct event.
- [ ] Multiple sessions, person/entity minds, source deletion, contradictions and reconnection are tested.
- [ ] If a Note adapter is included in the confirmed scope, it reuses shared operations without
      requiring notebook filing/linking for chat UX; generic session collections do not wait for it.

## Testing

After confirmation: `python -m pytest abstractruntime/tests/test_memory_facade.py abstractruntime/tests/test_memory_step_provenance.py`
and `python -m pytest abstractmemory/tests/test_graph_conformance.py`.
Add focused collection/query and promotion tests through public facade/Gateway surfaces, including
cross-owner refusal, late results, source loss and revisions. No hidden direct connector writes.

## Dependencies, promotion and ADR state

Read accepted Memory ADRs 0002/0003, Runtime ADR 0011 and their convergence items before choosing
a storage shape. 1089 supplies optional interpreted deltas; 1088 remains independent. Koine review
in `../../../../abstractsemantics/docs/backlog/proposed/0004_review_koine_general_vocabulary_and_modeling_contract.md`
may inform vocabulary, but cannot silently rename engraved relation strings. A collection/promotion
public contract needs ADR review. No new permanent predicate or wire spelling is chosen here.

## Receipts

Two-round three-agent council: `../../evidence/1088/README.md`. Implementation unapproved.

## Roadmap refinement (2026-10-31)

Deferred behind the avatar/subtitle conversation, live participation, questions and cues in
1088/1089/1092–1095. Those deliveries need no graph. A selected first-host/local-model pilot
should establish useful public communication before choosing collection semantics or a Note
adapter. Promotion remains an independent operator decision; this item is still proposed.
