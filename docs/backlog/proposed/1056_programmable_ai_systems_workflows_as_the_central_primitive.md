# 1056 — Programmable AI systems: workflows as the central primitive of an AI-native application layer

> Package: root (vision, cross-package), abstractruntime, abstractflow, abstractgateway, abstractuic, every app
> Type: vision / architecture
> Created: 2026-10-27
> Priority: P2
> Labels: workflows, vision, platform, auditability, gating

## Summary

Workflows are the framework's central native primitive. They define "programmable AI systems": the special agents
people chat with, the automations that run on schedules and triggers, the responses to events, the entities'
reflections. AbstractFlow builds and publishes them to the gateway; the runtime executes them durably with a
replayable ledger; the gateway serves and gates them; the apps are thin clients on those contracts. The framework
is therefore an OS-agnostic layer for AI-native applications, where AI is one part of a larger application logic,
and where every action is auditable (the ledger), traceable (provenance to records, events, artifacts) and gatable
(tool approval, sandboxes, authorization): the "AI going rogue" class of problems is a sandbox-and-gating problem
this layer answers by construction.

## Why

Operator, 2026-10-27: "workflow is a central native primitive of the framework; those define programmable AI
systems and are reused throughout the framework, either to create special agents with which we can discuss in chat,
or to create specific automations, or to define how we respond to triggers/events. We are truly building a
foundational layer to build AI-native applications. I have been thinking of AbstractFramework a bit like Java at the
time: a VM, OS-agnostic, on top of which you build your apps; the same thing here, but with AI-native applications,
fully auditable, traceable, gatable."

## What this changes for ongoing work

- The replayable-ledger view names the workflow, bundle and entrypoint a run executes and keeps the run tree explicit
  (root 0993, runtime 0853).
- Memory capture and reconsideration (AbstractMemory consolidation) are expressible as workflow steps/effects with
  ledger provenance, so AbstractNote and entities drive the graph through workflows where natural.
- Shared UI primitives (abstractuic) are composed on the gateway's contracts and these workflows, so apps are
  assembled rather than rebuilt (see 1057).
- Docs: the root architecture and getting-started pages state this primitive plainly; each package's docs name how
  it serves it (build: AbstractFlow; execute: runtime; serve/gate: gateway; compose: abstractuic; use: apps).

## Acceptance (for promotion to planned)

- [ ] Root `docs/architecture.md` has a section "Workflows: the central primitive" with the four roles above.
- [ ] Each ongoing track (0993, memory consolidation, UI primitives) cites this item where it applies.
