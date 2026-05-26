# Agent Skills Ecosystem Scan — Additional High-Value Skills (Feb 2026)

## Purpose
Continue the online search for **shareable Agent Skills** beyond Anthropic’s public repo and identify additional skill packs that could be high value for AbstractFramework.

## Methodology + Limits
- **Primary sources**: curated ecosystem lists and public GitHub repositories that publish `SKILL.md`.
- **Repository inspection**: read `SKILL.md` files directly for concrete scope and behavior.
- **Limitations**: GitHub code search API requires authentication (401). I used repository search + curated lists instead of code search.

## Additional Skill Libraries (Beyond Anthropic)

### 1) Vercel — Frontend performance + UI quality
Vercel publishes a curated skill pack with concrete UI/React guidance:
- **React Best Practices**: 57 performance rules for React/Next.js.  
  Source: https://raw.githubusercontent.com/vercel-labs/agent-skills/main/skills/react-best-practices/SKILL.md
- **React Composition Patterns**: guidance for scalable component APIs.  
  Source: https://raw.githubusercontent.com/vercel-labs/agent-skills/main/skills/composition-patterns/SKILL.md
- **React Native Skills**: performance and UI patterns for mobile apps.  
  Source: https://raw.githubusercontent.com/vercel-labs/agent-skills/main/skills/react-native-skills/SKILL.md
- **Web Design Guidelines**: UI review with external rule fetch.  
  Source: https://raw.githubusercontent.com/vercel-labs/agent-skills/main/skills/web-design-guidelines/SKILL.md

### 2) HashiCorp — Terraform/IaC workflows
HashiCorp’s pack focuses on Terraform generation and module design:
- **Terraform Style Guide**: code organization + security rules.  
  Source: https://raw.githubusercontent.com/hashicorp/agent-skills/main/terraform/code-generation/skills/terraform-style-guide/SKILL.md
- **Refactor Module**: monolith → reusable module workflow.  
  Source: https://raw.githubusercontent.com/hashicorp/agent-skills/main/terraform/module-generation/skills/refactor-module/SKILL.md
- **Run Acceptance Tests**: structured provider acceptance testing flow.  
  Source: https://raw.githubusercontent.com/hashicorp/agent-skills/main/terraform/provider-development/skills/run-acceptance-tests/SKILL.md

### 3) Trail of Bits — Security scanning + triage
Trail of Bits publishes a security-centric skill library with tooling guidance:
- **CodeQL**: structured database build + analysis workflow.  
  Source: https://raw.githubusercontent.com/trailofbits/skills/main/plugins/static-analysis/skills/codeql/SKILL.md
- **Semgrep**: multi-agent scan + triage workflow with hard approval gates.  
  Source: https://raw.githubusercontent.com/trailofbits/skills/main/plugins/static-analysis/skills/semgrep/SKILL.md
- **SARIF Parsing**: process and aggregate scan results.  
  Source: https://raw.githubusercontent.com/trailofbits/skills/main/plugins/static-analysis/skills/sarif-parsing/SKILL.md

### 4) OWASP Security Skill — Code review checklist
OWASP/ASVS-based security review guidance:
- **OWASP Security**: Top 10:2025 + ASVS 5.0 + agentic AI security checklist.  
  Source: https://raw.githubusercontent.com/agamm/claude-code-owasp/main/.claude/skills/owasp-security/SKILL.md

### 5) Varlock — Secrets hygiene
Skill focused on preventing secrets from leaking to logs or context:
- **Varlock**: safe environment variable handling rules.  
  Source: https://raw.githubusercontent.com/wrsmith108/varlock-claude-skill/main/skills/varlock/SKILL.md

### 6) Superpowers — Engineering process discipline
Reusable procedural skills for safer engineering workflows:
- **Test-Driven Development**  
  Source: https://raw.githubusercontent.com/obra/superpowers/main/skills/test-driven-development/SKILL.md
- **Systematic Debugging**  
  Source: https://raw.githubusercontent.com/obra/superpowers/main/skills/systematic-debugging/SKILL.md

### 7) Product/PM Skills — Problem framing and delivery
PM-oriented skills for better specification and experimentation:
- **Problem Statement**  
  Source: https://raw.githubusercontent.com/product-on-purpose/pm-skills/main/skills/define-problem-statement/SKILL.md
- **PRD**  
  Source: https://raw.githubusercontent.com/product-on-purpose/pm-skills/main/skills/deliver-prd/SKILL.md
- **Experiment Design**  
  Source: https://raw.githubusercontent.com/product-on-purpose/pm-skills/main/skills/measure-experiment-design/SKILL.md

### 8) Ecosystem discovery infrastructure
Curated lists and skill discovery tooling:
- **Awesome Claude Skills** (curated directory of skill packs).  
  Source: https://raw.githubusercontent.com/BehiSecc/awesome-claude-skills/main/README.md
- **Claude Skills MCP server** (vector search of skills).  
  Source: https://github.com/K-Dense-AI/claude-skills-mcp

## High-Value Skill Categories For AbstractFramework
These categories are likely high value based on the framework’s durable runtime, tool approval boundaries, gateway-first distribution, and observability model (see architecture deep dive notes).

1) **Security review + static analysis**
   - CodeQL, Semgrep, SARIF parsing, OWASP security checklists.
   - These align with durable runs, ledger evidence, and tool gating.

2) **Infrastructure / IaC workflows**
   - Terraform style guide + module refactoring skills.
   - Good fit for deterministic workflows and repeatable automation.

3) **Secrets and environment hygiene**
   - Varlock skill prevents sensitive data leakage.
   - Maps to AbstractFramework’s explicit tool approval boundaries.

4) **Engineering process rigor**
   - TDD + systematic debugging skills.
   - Fits agentic workflows and helps ensure safe, repeatable changes.

5) **Product/specification quality**
   - Problem statements, PRDs, experiment design.
   - Useful for SmartNote ingestion and workflow-driven documentation.

6) **Frontend performance + UX review**
   - Vercel React and UI guideline skills.
   - Helpful for AbstractCode usage and code review flows.

## Suggested Next Research Steps
- Deep-scan curated lists for additional domain skills (DevOps, data engineering, compliance).
- Evaluate skill packaging formats in each repo (compatibility + allowed-tools usage).
- Track skills that already embed MCP usage (for compatibility with AbstractRuntime tool gating).

## Sources Index
See `docs/skills/agent-skills-ecosystem-sources.md` for the complete list of sources.
