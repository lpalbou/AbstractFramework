# 074 — Agent Skills (`SKILL.md`) Integration

**Status**: Planned  
**Date**: 2026-02-21  
**Priority**: Medium–High (interoperability + distribution)  
**Components**: abstractagent, abstractruntime, abstractgateway, docs

## Summary

Add first-class support for the **Agent Skills** ecosystem format (a folder with a required `SKILL.md`) so
AbstractFramework can import/share procedural “skill packs” across hosts and gateway-first deployments.

Key design: **flows run; skills are activated/loaded**. Skill scripts (when enabled) execute only via explicit tools
with approvals and evidence capture.

## Reason

- Skills are an emerging interoperability layer across agent ecosystems (Claude Code/API and third-party packs).
- AbstractFramework already has the right execution substrate (durable runs, tool boundaries, replay-first ledger).
- Skills complement (do not replace) `.flow` bundles: skills are lightweight procedure packs; flows are durable programs.

## Scope

### In scope

- Skill discovery (metadata-only), progressive disclosure, and activation.
- Durable/observable activation:
  - activation and resource reads produce ledger records
  - large skill bodies/resources stored as artifacts (keep run state JSON-safe)
- Optional enforcement of skill `allowed-tools` as a restriction (intersection with run tool allowlists).
- Optional gateway skills registry (list/fetch/install/deprecate) parallel to `.flow` bundle distribution.

### Out of scope (v0)

- “Claude Code extensions” (slash commands, hooks, subagent forks) unless they map cleanly to runtime primitives.
- Provider-specific “container skills” support unless explicitly configured (keep `abstractcore` lean).
- Implicit script execution. Skill scripts only run as explicit tools.

## Proposed interaction model

1) **Run-attached skills (primary)**: hosts attach available-skill metadata to a run; users activate skills explicitly.
2) **Bundle-declared dependencies (secondary)**: `.flow` bundles may declare `skills.required` / `skills.defaults` via
   `manifest.metadata` without changing the bundle format.
3) **Bundle-embedded skills (optional later)**: embed skills under bundle `assets/*` for hermetic distribution.

## Dependencies / decisions

- Skill identity/version semantics:
  - spec-level identity is the skill `name` (leaf directory name; constrained format)
  - additional namespacing (publisher/source) is optional but may be needed to avoid collisions across multiple roots/registries
  - version can live in `metadata` (spec) and/or be derived from content hash (host policy)
- Default search paths (user + project) and precedence rules.
- Runtime data model for active skills (likely under `_runtime` namespace).
- Security policy for `allowed-tools` and for script execution (approvals + sandboxing).
- `allowed-tools` parsing policy:
  - field is experimental and often uses environment-specific tokens (e.g., Claude Code tool names)
  - enforce only when tokens can be mapped to AbstractFramework tool names; otherwise emit `#FALLBACK` and do not relax tool policy
- Authoring UX for bundle-declared skill dependencies:
  - VisualFlow JSON currently has no `metadata` field, and the gateway publish path auto-generates manifest metadata.
  - If we want `manifest.metadata.skills.*` to be author-editable, we need an authoring surface (CLI metadata args,
    Flow Editor fields, or extend the VisualFlow schema).

## Plan (high level)

1) Add a small shared parser/loader library (recommended: new `abstractskills` package).
2) Add local host UX in AbstractCode/Assistant: discovery + explicit activation.
3) Add runtime-owned activation handler + ledger + artifacts + allowlist intersection.
4) Add gateway skills registry (optional): distribution and thin-client discovery.
5) Add script-to-tool mapping with evidence/approvals (safe-by-default).

## Acceptance criteria

- Metadata discovery does not bloat prompts (caps + progressive disclosure).
- Activation is durable and replayable:
  - skill bodies/resources are artifact-backed when large
  - activation records a content hash (and/or the artifact id) so resumed runs don’t silently pick up modified skill files
- `allowed-tools` restricts execution; out-of-policy calls are denied with actionable `#FALLBACK`.
- No silent fallbacks; truncation is labeled `#TRUNCATION`.

## References

- Proposal guide: `docs/guide/agent-skills.md`
- Detailed phased plan: `docs/backlog/planned/074_agent_skills_integration_plan.md`
- Research notes (spec + ecosystem scan): `docs/skills/`
