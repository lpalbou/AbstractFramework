# 1059 — Everything the runtime holds, browsable and searchable: a virtual file/message/artifact/event space

> Package: root (cross-package), abstractgateway, abstractobserver, abstractruntime, abstractmemory, abstractsemantics
> Type: architecture / feature
> Created: 2026-10-27
> Priority: P2
> Labels: search, artifacts, ledger, observer, rbac, entities, performance

## Summary

Humans and digital entities must be able to browse and search everything the runtime creates and holds:
runs, messages, events, artifacts, files, memories, notes, voices, workflows, by name, title, content,
modality, time, owner, run and provenance. Pieces exist: the gateway's `GET /artifacts/search`,
`/artifacts/stats`, `/runs/{id}/artifacts`, the ledger tail and the per-user event stream (1046), the
console pages, AbstractObserver's run and workflow views, AbstractMemory's graph and AbstractSemantics'
indexes. None of it is native: there is no one addressable space with one query model, one permission model
and one index.

Target: a virtual space (think a filesystem with typed nodes) exposed by the gateway, served from the
runtime's stores and indexes, where every node has an id, a kind, a modality, a title, an owner, timestamps,
provenance (run, record seq, artifact id) and content access; one search (name/title/content/modality/
time/provenance, full text and semantic through AbstractSemantics/AbstractMemory), one listing, one RBAC
gate. Thin clients (Observer first, then every app) browse it; entities use the same API as tools.

## Why

Operator, 2026-10-27: "we need to be able to browse everything that will be created and hold by the runtime.
by name, title, content, modality type etc. we started building that in both the gateway and observer, but I
don't feel it's native yet. consider it as a virtual file/message/artifacts/events system that we should be
able to query and search. and this should work for both human users and digital entities. but all of that
should follow strict security and governance/RBAC."

## Design constraints

- The ledger stays the source of truth; the space is a projection with indexes (SQLite FTS and the semantic
  index), never a copy of content. The replay view (0993) is the per-run projection; this is the cross-run one.
- RBAC first: a node is visible only through the caller's grants (own runs, shared voices/library, admin);
  entities act under their own principal (same rules as a person).
- Performance budget (1060): listing and search answer from indexes; content streams from the store; no
  full re-parse of ledgers on query; measured on a realistic corpus before promotion.
- Served through runtime facades (runtime ADR 0008, gateway ADR 0001).

## Links

- Existing: gateway `routes/gateway.py` artifacts search/stats/list/content/export/import; ledger_tail.py;
  Observer; AbstractMemory graph (memory transition track, ADR 0003); AbstractSemantics.
- Related: 0993, 1056, 1058 (push is the outbound side of the same events), 1060.

## Acceptance (for promotion to planned)

- [ ] A node model and query contract (gateway ADR) with the RBAC rule stated.
- [ ] One end-to-end: Observer lists and searches artifacts, messages and events of the caller through
      the new contract, with a measured latency table on a 10k-record corpus.
