# Backlog: Agent Skills ecosystem scan + framework deep dive

## Summary
Expand research on shareable Agent Skills beyond Anthropic and deepen AbstractFramework architecture understanding before making recommendations.

## Why
- We need broader ecosystem signals to avoid narrow or vendor-specific skill suggestions.
- Architectural constraints (durable runtime, tool approvals, gateway-first clients) must be understood before proposing integrations.

## Strategy
- Use a curated ecosystem list plus targeted repository inspection of `SKILL.md` files for concrete evidence.
- Review architecture documentation across core and application packages to map constraints and capabilities.

## Scope
### In scope
- Collect additional skill sources and concrete examples (security, infra, product, UI).
- Produce architecture deep-dive notes from AbstractCore/Runtime/Agent/Flow/Gateway/Code/Assistant/Observer/Memory/Semantics/SmartNote docs.
- Summarize high-value skill categories with justifications (no implementation changes).

### Out of scope
- Implement skill loaders, registries, or runtime changes.
- Create ADRs or code changes beyond documentation.
- Evaluate new LLM providers or run operational benchmarks.

## Dependencies
- Public repos and docs (GitHub skill libraries, curated lists).
- Existing AbstractFramework architecture documentation.

## Expected outcomes
- New docs in `docs/skills/` covering ecosystem scan, sources, and architecture deep dive.
- Updated `AGENTS.md` with ecosystem insights.

## Full Report
### Overview
Expanded the skills ecosystem scan beyond Anthropic and performed a full architecture deep dive across core and application packages to ensure recommendations are grounded in real constraints.

### Approach (Why this route)
- **Ecosystem scan**: used a curated list and direct `SKILL.md` inspection to capture concrete, verifiable skill definitions rather than speculative summaries.
- **Architecture deep dive**: reviewed the architecture docs for AbstractCore/Runtime/Agent/Flow/Gateway/Code/Assistant/Observer/Memory/Semantics/SmartNote to map invariants like durability, tool boundaries, and replay-first observability.

### Key Findings
- Additional high-value skill packs exist for security scanning, IaC workflows, secrets hygiene, engineering process rigor, product/specification quality, and UI performance/UX review.
- The framework’s durable run model, ledger observability, and explicit tool approvals are strong constraints that any skill integration must respect.

### Deliverables
- `docs/skills/agent-skills-ecosystem-scan.md`
- `docs/skills/agent-skills-ecosystem-sources.md`
- `docs/skills/abstractframework-architecture-deep-dive.md`
- `AGENTS.md` updated with ecosystem notes

### Limitations / Notes
- GitHub code search API requires authentication (401), so the scan relied on curated lists + repo inspection instead of global code search.

### Tests
- Not applicable (documentation-only research task).
