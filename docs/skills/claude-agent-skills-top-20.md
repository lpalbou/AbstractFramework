# Top 20 Shareable Claude Skills (Feb 2026)

Selection method:
- **16 skills** from Anthropic’s official `anthropics/skills` repository
- **4 canonical example skills** from Claude Code documentation (shareable, SKILL.md‑based)
This yields 20 widely cited, shareable skills as of Feb 2026.

## 1) `docx` — Word Documents
- **What:** Create/read/edit Word documents with formatting, tables, images, and tracked changes.
- **How:** Uses docx-js and XML edit workflows; provides detailed rules and scripts.
- **Source:** https://raw.githubusercontent.com/anthropics/skills/main/skills/docx/SKILL.md

## 2) `pdf` — PDF Processing
- **What:** Extract, merge, split, OCR, watermark, and create PDF files.
- **How:** Uses pypdf/pdfplumber/reportlab plus CLI tools and optional forms guide.
- **Source:** https://raw.githubusercontent.com/anthropics/skills/main/skills/pdf/SKILL.md

## 3) `pptx` — Presentation Creation/Editing
- **What:** Create or edit slide decks with strong layout and QA guidance.
- **How:** Uses markitdown for extraction; pptxgenjs or template editing; QA loop.
- **Source:** https://raw.githubusercontent.com/anthropics/skills/main/skills/pptx/SKILL.md

## 4) `xlsx` — Spreadsheet Modeling
- **What:** Create and edit spreadsheets with formulas, formatting, and recalculation.
- **How:** Uses pandas/openpyxl with a strict formula recalculation workflow.
- **Source:** https://raw.githubusercontent.com/anthropics/skills/main/skills/xlsx/SKILL.md

## 5) `webapp-testing` — Playwright UI Testing
- **What:** Test local web apps, take screenshots, and validate UI behavior.
- **How:** Playwright scripts plus helper server lifecycle scripts.
- **Source:** https://raw.githubusercontent.com/anthropics/skills/main/skills/webapp-testing/SKILL.md

## 6) `web-artifacts-builder` — Advanced HTML Artifacts
- **What:** Build complex Claude.ai artifacts with React/Tailwind/shadcn.
- **How:** Init project, build, then bundle into a single HTML artifact.
- **Source:** https://raw.githubusercontent.com/anthropics/skills/main/skills/web-artifacts-builder/SKILL.md

## 7) `frontend-design` — UI Design + Code
- **What:** Produce distinctive, production‑grade frontend UI.
- **How:** Strong aesthetic rules + real HTML/CSS/JS or framework code.
- **Source:** https://raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/SKILL.md

## 8) `algorithmic-art` — Generative p5.js Art
- **What:** Create algorithmic art and interactive HTML artifacts.
- **How:** Define a generative “philosophy” then implement in p5.js.
- **Source:** https://raw.githubusercontent.com/anthropics/skills/main/skills/algorithmic-art/SKILL.md

## 9) `canvas-design` — Visual Design Artifacts
- **What:** Create visual design output (PDF/PNG) from a design philosophy.
- **How:** Design manifest → render high‑craft visual work.
- **Source:** https://raw.githubusercontent.com/anthropics/skills/main/skills/canvas-design/SKILL.md

## 10) `theme-factory` — Theme Application
- **What:** Apply curated design themes (colors/fonts) to artifacts.
- **How:** Choose from pre‑set themes or generate a new one.
- **Source:** https://raw.githubusercontent.com/anthropics/skills/main/skills/theme-factory/SKILL.md

## 11) `brand-guidelines` — Anthropic Brand Styling
- **What:** Apply official Anthropic brand colors and typography.
- **How:** Prescriptive palette and font rules.
- **Source:** https://raw.githubusercontent.com/anthropics/skills/main/skills/brand-guidelines/SKILL.md

## 12) `internal-comms` — Internal Communications
- **What:** Produce 3P updates, newsletters, FAQs, and status reports.
- **How:** Select format from examples and follow structured guidelines.
- **Source:** https://raw.githubusercontent.com/anthropics/skills/main/skills/internal-comms/SKILL.md

## 13) `doc-coauthoring` — Doc Co‑Authoring Workflow
- **What:** Guided multi‑stage workflow for technical docs and specs.
- **How:** Context gathering → structured drafting → reader testing.
- **Source:** https://raw.githubusercontent.com/anthropics/skills/main/skills/doc-coauthoring/SKILL.md

## 14) `mcp-builder` — MCP Server Builder
- **What:** Build MCP servers with best‑practice tool design.
- **How:** Phased workflow with references for MCP SDKs and evaluation.
- **Source:** https://raw.githubusercontent.com/anthropics/skills/main/skills/mcp-builder/SKILL.md

## 15) `skill-creator` — Skill Authoring Guide
- **What:** Build new skills with proper structure and packaging.
- **How:** Progressive disclosure guidance, packaging scripts, and best practices.
- **Source:** https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md

## 16) `slack-gif-creator` — Slack GIFs
- **What:** Create Slack‑optimized GIFs and animations.
- **How:** Python/PIL workflow with helper utilities and validation.
- **Source:** https://raw.githubusercontent.com/anthropics/skills/main/skills/slack-gif-creator/SKILL.md

## 17) `deploy` — Manual Deployment Workflow (Example)
- **What:** A manually‑invoked deployment checklist.
- **How:** `disable-model-invocation: true` ensures only user can run it.
- **Source:** https://code.claude.com/docs/en/skills

## 18) `safe-reader` — Read‑Only Mode (Example)
- **What:** Restrict Claude to safe, read‑only tools.
- **How:** Use `allowed-tools` to limit tool access within the skill.
- **Source:** https://code.claude.com/docs/en/skills

## 19) `pr-summary` — Dynamic PR Summaries (Example)
- **What:** Summarize pull requests using live CLI data.
- **How:** `!` command injection runs shell commands before the prompt.
- **Source:** https://code.claude.com/docs/en/skills

## 20) `deep-research` — Subagent Research (Example)
- **What:** Launch a forked research subagent with isolated context.
- **How:** `context: fork` and `agent: Explore` run the skill in a subagent.
- **Source:** https://code.claude.com/docs/en/skills

