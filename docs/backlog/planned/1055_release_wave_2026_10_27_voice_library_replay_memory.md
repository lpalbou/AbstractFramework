# 1055 — Release wave 2026-10-27: voice library, personal voices, replayable ledger, memory graph, shared UI primitives

> Package: root (release sequence), abstractvoice, abstractruntime, abstractgateway, abstractuic, abstractassistant (desktop, iPhone, watch), abstractcode, abstractobserver, abstractentity, abstractnote, abstractmemory
> Type: release + architecture
> Created: 2026-10-27
> Priority: P0
> Labels: release, voice, replay, memory, ui-kit

## Summary

One wave, in dependency order, that (1) ships the voice library and personal voices per account through every
layer, (2) lands one replayable-ledger abstraction (runtime reducer, gateway projection) every thin client builds on,
(3) starts moving AbstractNote's graph logic into AbstractMemory as the one semantic temporal memory graph with
ledger provenance, and (4) consolidates the shared UI primitives in abstractuic. The gateway 0.16.0 release waits for
(2); the apps release after the gateway.

## Tracks and their backlog items

| Track | Items | Status (2026-10-27) |
| --- | --- | --- |
| Voice library and personal voices | abstractvoice 0063, 0065 (done, 0.19.0/0.19.1); abstractruntime 0851, 0852 (done, 0.13.0/0.13.1); abstractgateway 0942 (done, unreleased); abstractcore 0857 (planned) | released up to the runtime; gateway main carries it |
| Architecture rule: no direct lower-level imports | abstractruntime ADR 0008; abstractgateway ADR 0001 | accepted |
| Shared UI: voice picker, create a voice | abstractuic 0.6.4 / ui-kit 0.8.9 (released); AbstractCode, Observer, Entity merged on main (unreleased); Assistant desktop branch; iPhone/watch branch | in progress |
| Replayable ledger | root 0993 (master); abstractgateway 0082, 0075; abstractruntime 0853 (reducer + `/view`, in progress) | in progress (blocks gateway 0.16.0) |
| Memory graph consolidation | abstractnote 0033-0036; abstractmemory ADR + items (being written) | audit and design in progress |
| Shared UI primitives consolidation | abstractuic items (being written): chat, attachments, questions and approvals, tool selection, provider/model/reasoning/MTP picker, voice controls, top-right widgets, drawers | audit in progress |

## Release order

abstractvoice 0.19.1 (done) → abstractruntime 0.13.1 (done) → abstractuic 0.6.4 (done) → abstractruntime 0.14.0
(replay view) → abstractgateway 0.16.0 → abstractassistant, abstractcode, abstractobserver, abstractentity,
abstractnote, abstractflow → abstractmemory and abstractnote (memory track) → root `abstractframework` pins.

## Acceptance criteria

- [ ] Every track above has its backlog item in its package, linked here, with evidence on completion.
- [ ] Each release merged only on green CI after an adversarial review of the diff.
- [ ] A final per-package table: what was released, new capabilities, remaining work and improvements.
