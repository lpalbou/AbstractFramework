# ADR-0029: Permissive Dependency and Licensing Policy

## Status
Proposed (2026-01-31)

## Dates
- Proposed: 2026-01-31
- Accepted: TBD
- Updated: 2026-05-08 (aligned with ADR-0033)

## Context
AbstractFramework is intended to be open source and easy to adopt, fork, and deploy in many environments (personal laptops → servers). A growing dependency set can undermine this goal by:
- introducing restrictive licensing obligations,
- increasing security and supply-chain risk,
- increasing build and runtime complexity,
- increasing maintenance burden and “dependency churn”.

Some upcoming work (e.g., maintenance agents for report triage and backlog stewardship) will naturally invite new dependencies (LLM clients, scheduling, notifications). We need an explicit framework-wide policy to keep the project:
- permissively licensed,
- dependency-light by default,
- and explicit when exceptions are required.

## Decision
### 1) License policy (new dependencies)
For new **code dependencies** introduced into the AbstractFramework repository (Python, JS/TS, etc.):
- Prefer permissive, OSI-approved licenses.
- Preferred allowlist: **MIT**, **Apache-2.0**, **BSD-2-Clause**, **BSD-3-Clause**.
- Other permissive licenses may be acceptable but require an explicit justification (backlog/ADR) (examples: **ISC**, **Python Software Foundation License**, **PostgreSQL License**).
- Default denylist includes copyleft licenses (e.g. **GPL**, **AGPL**) and network-copyleft (AGPL) unless explicitly approved via a dedicated ADR or a backlog item with an explicit rationale.
- If a dependency’s license is unclear or mixed, treat it as disallowed until resolved.

### 2) Dependency minimization
- Prefer standard library implementations when reasonable.
- Prefer reusing existing dependencies already present in the repo.
- Each new dependency must have:
  - a short justification (“why is this required?”),
  - a scope statement (“where is it used?”),
  - and an exit strategy (“how hard to remove/replace?”) when feasible.

### 3) Dependency minimization by install profile
- Base installs should be the smallest useful install for the package's own role.
- Local model engines, audio stacks, GPU runtimes, vector stores, and server dependencies belong in
  explicit extras unless they are truly required for the package's base role.
- Entry-point packages such as AbstractCore and AbstractGateway may define aggregate profiles that
  intentionally pull lower package extras.
- Do not add fake hardware/provider extras to packages that do not own that dependency class.

### 4) Local-capable, provider-agnostic AI integrations
- Direct local experiences remain valid and should be supported through explicit local profiles
  where they need heavy dependencies.
- Server/default installs should be remote-light unless maintainers intentionally choose a heavier
  base persona for that package.
- OpenAI-compatible local servers such as LMStudio remain important provider targets, but provider
  and model selection should stay configurable.
- The framework code remains open source; model weights and provider services are treated as user-selected runtime configuration.

## Consequences
### Positive
- Maintains a permissive open source posture that is easy to adopt and redistribute.
- Reduces long-term maintenance overhead.
- Improves supply-chain posture by minimizing dependency footprint.

### Negative
- Some “convenience” libraries may be rejected, requiring more in-house code.
- Certain integrations (especially notifications and scheduling) may require extra design work to remain dependency-light.

### Neutral
- This policy does not forbid adding dependencies; it requires explicit justification and licensing clarity.

## Packages Affected
- All

## Related
- Backlog: `docs/backlog/planned/644-framework-automated-report-triage-pipeline-v0.md`
- ADR-0001: `docs/adr/0001-layered-architecture.md`
- ADR-0006: `docs/adr/0006-durable-tool-execution.md`
- ADR-0019: `docs/adr/0019-testing-strategy-and-levels.md`
- ADR-0033: `docs/adr/0033-install-profiles-config-entrypoints-and-server-boundaries.md`
