# Backlog Item 069: Claude Shareable Skills Research

## Summary
- Research Anthropic’s shareable “Skills” (Agent Skills standard).
- Explain what skills are, how they work, and how they are shared.
- Produce a top-20 skills list as of Feb 2026 with sources.
- Assess AbstractFramework fit, with justification and integration paths.

## Why We Are Doing This
- The previous Claude capability analysis did not address shareable skills.
- Skills are model-agnostic and interoperable, so they materially affect architecture choices.
- We need a source-backed view to decide how to integrate skills into the framework.

## Scope
- In scope:
  - Anthropic’s Agent Skills standard and official docs.
  - Claude Code skills behavior (invocation, sharing, directories).
  - Claude API skills integration (container + code execution).
  - Anthropic’s official skills examples repository.
  - Top-20 skill list with “what/how” notes and citations.
  - AbstractFramework fit analysis with rationale and suggested paths.
- Out of scope:
  - Implementing skills support in AbstractFramework.
  - Benchmarking skills or model performance.
  - Community skills marketplaces beyond official Anthropic sources.

## Dependencies
- Public documentation access (agentskills.io, code.claude.com, docs.claude.com).
- Anthropic skills repository on GitHub.

## Expected Outcomes
- New skills-focused research docs in `docs/skills/`.
- A corrected fit analysis focused on shareable skills, not model capabilities.

## Full Report
### Work Completed
- Researched Agent Skills standard, Claude Code skills behavior, and Claude API skills integration.
- Reviewed Anthropic’s official skills repository and compiled a top‑20 list.
- Produced a new AbstractFramework fit analysis focused on shareable skills.

### Deliverables
- `docs/skills/claude-agent-skills-overview.md`
- `docs/skills/claude-agent-skills-top-20.md`
- `docs/skills/claude-agent-skills-sources.md`
- `docs/skills/abstractframework-agent-skills-fit.md`

### Key Findings
- Agent Skills are a portable, model‑agnostic format: folders with `SKILL.md` plus optional
  scripts and resources, loaded via progressive disclosure.
- Claude Code extends the standard with invocation control, allowed tools, subagents,
  and dynamic context injection.
- Claude API supports skills via `container.skills` and code execution tools, with
  versioned skill IDs and beta headers.
- Anthropic’s official skills repo provides 16 example skills; a top‑20 list requires
  adding four canonical examples from Claude Code docs.

### Recommendations
- Add Agent Skills support to AbstractCode/Assistant and a registry in AbstractGateway.
- Enforce skill‑level tool allowlists and ledger logging for provenance.
- Consider an ADR for skills integration (discovery paths, security, packaging).

### Tests
- Not run (research/documentation only).
