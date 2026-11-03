# 1057 — AbstractApp / AbstractDesigner (name open): visual composition of AI-native apps on the framework

> Package: root (new app), abstractuic, abstractflow, abstractgateway
> Type: vision / feature
> Created: 2026-10-27
> Priority: P3 (exploratory)
> Labels: designer, app-builder, abstractuic, workflows, cross-platform

## Summary

A visual designer where a person composes an application's UI from abstractuic's sharable components (drag and
drop) and ties each component to the foundational layer: the gateway's contracts (runs, replay view, catalogs,
voice, memory) and the workflows built in AbstractFlow for the app's specific usage. The result targets web first,
then macOS, Windows, Linux, iPhone and Apple Watch through the per-framework component shelves abstractuic will hold
(JS/TS, Python/Qt, Rust/TUI, Swift). Many tools let you design a UI visually; the difference here is that every
component is already connected to a framework that executes, audits, traces and gates the AI parts.

## Why

Operator, 2026-10-27: "we may want at some point to create an AbstractApp or AbstractDesigner where we visually help
people create applications for web, macOS, Windows, Linux, Apple Watch etc. by providing (a) the sharable drag & drop
components of abstractuic and (b) their link to the foundational layer that is AbstractFramework and those workflows.
Imagine designing visually your UI, but you tie it up to components already connected to the framework, and you
build the workflow for the specific usage." Not to be started yet: a direction that the ongoing consolidation of
abstractuic (one chat, top-right widgets, drawers, approvals, tool selection, model and voice pickers) and the
workflow primitive (1056) should keep possible.

## Prerequisites (tracked elsewhere)

- abstractuic: components composed on gateway contracts, customizable by props/slots/theme tokens, with a documented
  multi-framework layout (abstractuic ADR and items from the UI primitives track).
- AbstractFlow: workflows published to the gateway with typed inputs/outputs and interfaces an app can bind to.
- Gateway: the replay view (0993) and the capability/catalog contracts every component reads.

## Open questions

- Name (AbstractApp, AbstractDesigner, other); whether the designer is itself a gateway app.
- The binding model between a component and a workflow (inputs, events, approvals) and how it is stored
  (a published "app bundle" next to workflow bundles?).
- Native targets: generate per-framework code, or host a shared runtime view (web view) with native shells?
