# Backlog Item 068: Claude Skills Research And Fit

## Summary
- Conduct an evidence-based survey of Claude skills as of Feb 2026.
- Explain what each skill is and how it works at a high level.
- Assess AbstractFramework fit: where these skills add value, why, and how.

## Why We Are Doing This
- Provide a reliable, source-backed view of Claude’s capabilities for planning.
- Identify high-leverage integrations that align with AbstractFramework’s durable, observable architecture.
- Inform product and architecture decisions with explicit justification.

## Scope
- In scope:
  - Online research across Anthropic docs and announcements.
  - A curated “top 20” Claude skills list with technical summaries.
  - Fit analysis against current AbstractFramework capabilities.
  - Findings delivered as versioned Markdown reports in `docs/claude/`.
- Out of scope:
  - Implementing integrations or changing AbstractFramework code.
  - Benchmarking or empirical testing of Claude models.
  - Vendor comparisons beyond Anthropic sources.

## Dependencies
- Web access to Anthropic documentation and announcements.
- Current AbstractFramework docs for architecture and capabilities.

## Expected Outcomes
- Clear, cited explanation of Claude skills and how they work.
- A top-20 skills list as of Feb 2026 with rationale.
- Actionable assessment of which skills to adopt and how.

## Full Report
### Work Completed
- Researched Claude capabilities across Anthropic documentation and announcements.
- Documented what each skill is and how it works at a high level, with citations.
- Assessed AbstractFramework fit and identified high-value integration opportunities.

### Deliverables
- `docs/claude/claude-skills-overview.md`
- `docs/claude/claude-skills-top-20.md`
- `docs/claude/claude-skills-sources.md`
- `docs/claude/abstractframework-fit.md`

### Findings Summary
- Claude’s top skills span model-level capabilities (reasoning, code, vision, long context)
  and platform capabilities (tool use, web search/fetch, computer use, artifacts, memory).
- Server-side tools (web search/fetch) provide citations and dynamic filtering, which
  align well with AbstractFramework’s auditability and ledger design.
- Computer use is promising for legacy GUI automation but requires strong sandboxing
  and human-in-the-loop guardrails to avoid prompt-injection risk.
- AbstractFramework already covers tool calling, structured output, MCP, and compaction;
  most incremental value comes from provider-specific features and UX.

### Recommendations
- Prioritize integration of Claude server tools (web search/fetch) and citation handling.
- Add optional support for computer use with explicit approval boundaries and sandboxing.
- Expose Anthropic thinking parameters and prompt caching in provider configs.
- Consider an ADR for Anthropic server tools and computer use integration.

### Tests
- Not run (research and documentation task only).
