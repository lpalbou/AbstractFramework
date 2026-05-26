# AbstractFramework Fit Analysis For Claude Skills (Feb 2026)

## Current AbstractFramework Capabilities (Relevant Snapshot)
Based on `README.md` and `docs/architecture.md`, the framework already provides:
- **Universal tool calling + MCP** via AbstractCore (single tool schema across providers).
- **Structured output** and **streaming/async** across providers.
- **Durable execution and auditability** via AbstractRuntime’s ledger and artifacts.
- **Memory system** via AbstractMemory + AbstractSemantics.
- **Chat compaction** in AbstractCore `BasicSession` for long conversations.
- **Multimodal input** with policy-driven fallbacks.

These align well with Claude’s API-first skills. The main gaps are provider-specific
capabilities that are not yet explicitly integrated (e.g., Anthropic server tools and
computer-use tool).

## Where Claude Skills Would Benefit AbstractFramework (Why + How)

### 1) Web Search Tool (Server Tool + Citations)
- **Why:** AbstractFramework already supports “deep search” use cases, but Claude’s server-side
  web search provides built-in citations and dynamic filtering for more reliable research results.
- **How:** Add an Anthropic-specific tool adapter in AbstractCore that registers `web_search`
  server tools. Store citations as artifacts linked in the ledger. Expose allowlist/denylist and
  `max_uses` in config. If disabled, emit `#FALLBACK` warnings and do not silently simulate search.
- **Evidence:** Claude web search tool docs show citations and dynamic filtering.

### 2) Web Fetch Tool (Pages + PDFs With Optional Citations)
- **Why:** AbstractFramework workflows often require document ingestion; web fetch adds a direct,
  cited path to pull full pages or PDFs with guardrails.
- **How:** Implement a server-tool mapping for `web_fetch` with strict domain controls, and
  enforce `max_content_tokens`. If truncation occurs, label `#TRUNCATION` in the ledger.
- **Evidence:** Claude web fetch docs describe PDF support, citations, and content limits.

### 3) Dynamic Filtering Via Code Execution (Server Tool Optimization)
- **Why:** Long document retrieval can be expensive. Claude’s dynamic filtering reduces token
  costs and improves relevance.
- **How:** When `web_search_20260209` or `web_fetch_20260209` is enabled, require a code-execution
  tool and sandbox it. Log filtering decisions and parameters in the ledger for auditability.
- **Evidence:** Web search/fetch docs note dynamic filtering and dependency on code execution.

### 4) Computer Use Tool (GUI Automation)
- **Why:** AbstractFramework already targets durable automation. Computer use enables tasks
  against legacy GUIs where APIs don’t exist.
- **How:** Add a computer-use tool integration as an optional capability with explicit user
  approval gates. Run in a sandboxed VM/container; store screenshots and action logs as artifacts.
  Enforce allowlisted domains and add prompt-injection warnings (`#FALLBACK` if disabled).
- **Evidence:** Computer use docs specify agent loops, action schemas, and safety constraints.

### 5) Thinking / Extended Thinking Controls
- **Why:** Many AbstractFramework flows (planning, code review, audits) benefit from controllable
  reasoning budgets to increase reliability.
- **How:** Extend AbstractCore provider settings to accept Anthropic `thinking` parameters and
  expose them in Flow node configs. Record the chosen budget in the ledger for reproducibility.
- **Evidence:** Computer use docs and Sonnet 4.6 announcement describe thinking modes.

### 6) Prompt Caching For Long-Running Workflows
- **Why:** Durable workflows often re-use large context; caching can reduce cost and latency.
- **How:** Add a session-level option to emit `cache_control` breakpoints in Anthropic requests.
  Record cache hit/miss metrics in the ledger when exposed by the API.
- **Evidence:** Web search/fetch docs describe cache_control usage for prompt caching.

### 7) Context Compaction Alignment
- **Why:** AbstractCore already has compaction; Claude’s platform compaction can further extend
  effective context. Coordinating the two avoids redundant summarization.
- **How:** Make Claude context compaction optional and mutually exclusive with BasicSession
  auto-compaction for a given run; emit `#FALLBACK` warnings if forced to downgrade.
- **Evidence:** Sonnet 4.6 announcement references context compaction.

### 8) Artifacts-Like Workspace In AbstractObserver / Code Web
- **Why:** Claude Artifacts demonstrate strong UX for code/document iteration. AbstractObserver
  and Code Web could surface ledger artifacts in a side pane to match this workflow.
- **How:** Add an “artifact workspace” UI surface for generated code/docs with inline editing,
  backed by ledger artifacts. Keep edits as new artifacts for full provenance.
- **Evidence:** Claude 3.5 Sonnet announcement describes Artifacts as a dedicated workspace.

### 9) Memory Tool Integration (Optional)
- **Why:** Claude Memory is positioned for preference retention; AbstractFramework already has
  a richer memory system. A thin integration could provide model-side personalization when desired.
- **How:** Map user preferences stored in AbstractMemory into Claude’s memory tool where available.
  Require explicit user consent and provide opt-in controls. Never silently sync.
- **Evidence:** Claude 3.5 Sonnet and Sonnet 4.6 announcements reference memory features.

### 10) Citation-Aware Outputs In Ledger And UIs
- **Why:** Claude server tools produce citations; surfacing them makes AbstractFramework’s
  auditability even stronger.
- **How:** Persist citations alongside tool results and render them in AbstractObserver. Ensure
  citations are preserved when outputs are post-processed.
- **Evidence:** Web search and web fetch docs describe citation structures.

## Skills That Are Already Covered (Low Incremental Value)
- **Text generation, reasoning, multilingual, vision, long context** are model capabilities
  already accessible via AbstractCore by selecting Claude models.
- **Tool calling, structured output, streaming** are already part of AbstractCore’s core
  abstraction; Claude can be plugged in without new architecture.
- **MCP integration** already exists in AbstractCore; Claude’s MCP support is complementary.

## Risks And Guardrails (Align With Framework Principles)
- **Prompt injection & unsafe automation:** Computer use and web tools require allowlists,
  human approval gates, and explicit warnings (`#FALLBACK` when safety constraints disable tools).
- **Truncation risk:** Web fetch and large content limits must tag `#TRUNCATION` and preserve
  provenance in the ledger.
- **Privacy:** Server tools are not always ZDR; the system should surface privacy mode in UI and logs.

## ADR Suggestion (Crucial Architecture Decision)
Create an ADR for “Anthropic Server Tools + Computer Use Integration” covering:
- Security model (allowlists, sandboxing, approvals)
- Logging and provenance requirements
- Fallback and truncation policy (`#FALLBACK`, `#TRUNCATION`)
- UX for citations and artifact outputs

