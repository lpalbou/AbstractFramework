# AbstractFramework Fit Analysis — Shareable Agent Skills (Feb 2026)

## Executive Fit Summary
AbstractFramework **can benefit significantly** from Agent Skills because the format is
model‑agnostic, portable, and aligns with the framework’s goals: **durability, observability,
and modularity**. Skills are not a replacement for AbstractFlow, but a lightweight, shareable
layer for procedural knowledge and tool workflows.

Sources for skill behavior and format:
- https://agentskills.io/what-are-skills.md
- https://agentskills.io/specification.md
- https://code.claude.com/docs/en/skills
- https://docs.claude.com/en/api/skills-guide
- https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills

## Where AbstractFramework Benefits (Why + How)

### 1) Add Agent Skills Support To AbstractCode/Assistant
**Why:** Users can import Claude/Cursor/Codex‑style skills (portable SKILL.md packs) without
rewriting workflows. This makes AbstractCode more interoperable.

**How:** Implement a skills loader that:
- Discovers `SKILL.md` folders (project + user scopes).
- Injects `name`/`description` into system prompt (metadata only).
- Loads full `SKILL.md` on activation (progressive disclosure).
- Supports optional `allowed-tools` to enforce tool gating.

**Justification:** This mirrors the Agent Skills spec and Claude Code behavior
(`name`/`description` metadata + on‑demand skill loading).  
Sources: https://agentskills.io/what-are-skills.md, https://code.claude.com/docs/en/skills

### 2) Skill Registry In AbstractGateway
**Why:** The Gateway already distributes workflows; a skills registry enables organization‑wide
sharing of reusable procedural knowledge across all clients.

**How:** Add a skills registry parallel to `.flow` bundles:
- Store skills in a dedicated directory or artifact store.
- Provide an API for listing, enabling, and versioning skills.
- Broadcast skill metadata to thin clients for discovery.

**Justification:** Skills are portable folders; gateway distribution fits the existing architecture.

### 3) Tool Approval Integration Via `allowed-tools`
**Why:** Skills can explicitly list approved tools. This maps directly to AbstractRuntime’s
tool approval boundaries and audit trail.

**How:** When a skill is activated, merge `allowed-tools` with the tool policy for that run.
If a tool is outside the allowlist, require approval and emit `#FALLBACK`.

**Justification:** Agent Skills spec supports `allowed-tools` (experimental) and Claude Code
uses it for permissions.  
Sources: https://agentskills.io/specification.md, https://code.claude.com/docs/en/skills

### 4) Skill Execution Logging In The Ledger
**Why:** Skills are procedural knowledge; their activation and resource use should be auditable.

**How:** Record:
- Skill name/version on activation
- Files/scripts read or executed
- Any outputs or generated artifacts

**Justification:** Matches AbstractFramework’s observability and provenance model.

### 5) Support For `.skill` Packaging
**Why:** Shareable skills need a portable format for teams. The skill‑creator workflow in the
Anthropic repo uses a `.skill` package (zip). Supporting this improves interoperability.

**How:** Add a CLI helper to package/unpackage skills and validate against the spec.

**Justification:** Skills are file‑based; packaging enables controlled distribution and versioning.

### 6) Optional Anthropic Skills API Integration
**Why:** Some Anthropic skills (docx/pdf/pptx/xlsx) are server‑hosted and usable via the API.

**How:** Extend AbstractCore’s Anthropic provider to expose `container.skills` and
code execution when configured. Track skill metadata in the run state.

**Justification:** This is provider‑specific but valuable for users who want
Anthropic‑hosted skills without manual setup.  
Source: https://docs.claude.com/en/api/skills-guide

## Skills That Are Already Covered (Low Incremental Value)
- **Tool calling, MCP, and structured output** already exist in AbstractCore.
- **Durable workflows** are stronger than skills for complex multi‑agent orchestration.

Skills add value primarily as **portable procedural knowledge packs** and
as a compatibility layer with other agent ecosystems.

## Risks And Guardrails
- **Script execution risk:** Skills can include scripts; require sandboxing and explicit
  approvals. If disabled, emit `#FALLBACK`.
- **Context bloat:** Too many skills can overload the prompt; enforce metadata limits and
  avoid loading full skills unless activated.
- **Environment mismatch:** Respect the `compatibility` field; if requirements are unmet,
  warn with `#FALLBACK`.
- **Truncation:** If any skill content must be truncated, label `#TRUNCATION` with reason.

## ADR Recommendation
Create an ADR: **“Agent Skills Support in AbstractFramework”** covering:
- Skill discovery paths and registry model
- Tool approval and sandbox policy
- Ledger/provenance logging for skill activation
- `.skill` packaging support
- Provider‑specific API integration (Anthropic containers)
