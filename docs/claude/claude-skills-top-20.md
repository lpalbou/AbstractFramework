# Claude Top 20 Skills (As Of Feb 2026)

This list curates the most impactful Claude skills based on Anthropic documentation and
announcements. Each entry includes what the skill is, how it works (high-level), and evidence.

## 1) Text Generation And Rewriting
- **What it is:** High-quality text creation (summaries, reports, support replies, creative writing).
- **How it works:** Standard Messages API prompts; model generates fluent text with instruction
  following and brand-voice control.
- **Evidence:** https://docs.anthropic.com/claude/docs/overview

## 2) Code Generation, Debugging, And Translation
- **What it is:** Write, edit, debug, and translate code across languages and codebases.
- **How it works:** Natural-language prompts + code context; often paired with tools for edits or execution.
- **Evidence:** https://www.anthropic.com/news/claude-3-family,  
  https://www.anthropic.com/news/claude-3-5-sonnet

## 3) Advanced Reasoning And Analysis
- **What it is:** Strong performance on reasoning, math, forecasting, and multi-step analysis.
- **How it works:** Model-level capability expressed through instruction-following and structured prompts.
- **Evidence:** https://docs.anthropic.com/claude/docs/overview,  
  https://www.anthropic.com/news/claude-3-family

## 4) Multilingual Fluency And Translation
- **What it is:** Accurate responses and translations across non-English languages.
- **How it works:** Same generation pipeline with multilingual training; usable for translation features.
- **Evidence:** https://docs.anthropic.com/claude/docs/overview,  
  https://www.anthropic.com/news/claude-3-family

## 5) Vision Understanding (Images, Charts, Diagrams)
- **What it is:** Analyze visual inputs like charts, photos, diagrams, and scanned documents.
- **How it works:** Multimodal inputs (image + text) processed by vision-capable Claude models.
- **Evidence:** https://docs.anthropic.com/claude/docs/overview,  
  https://www.anthropic.com/news/claude-3-family,  
  https://www.anthropic.com/news/claude-3-5-sonnet

## 6) Long-Context Processing (200K To 1M Tokens)
- **What it is:** Read and reason over very large document sets in a single request.
- **How it works:** Large context windows in Claude models; Sonnet 4.6 adds a 1M token context in beta.
- **Evidence:** https://www.anthropic.com/news/claude-3-family,  
  https://www.anthropic.com/news/claude-sonnet-4-6

## 7) Tool Use / Function Calling (Client Tools)
- **What it is:** Structured tool invocation to integrate with external systems.
- **How it works:** Provide tool schemas; Claude emits `tool_use` blocks; app executes and returns
  `tool_result` blocks.
- **Evidence:** https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/overview

## 8) Strict Tool Use / Structured Outputs
- **What it is:** Schema-validated tool inputs for robust production integrations.
- **How it works:** Tool definitions can be marked `strict: true` to guarantee schema conformance.
- **Evidence:** https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/overview

## 9) Parallel Tool Use
- **What it is:** Multiple independent tool calls in a single model response.
- **How it works:** Claude returns multiple `tool_use` blocks; client returns matching results in one turn.
- **Evidence:** https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/overview

## 10) MCP Tool Integration And Connectors
- **What it is:** Use tools from MCP servers and connectors without custom adapters.
- **How it works:** MCP tool schemas are converted to Claude tool schemas; connectors can be used
  in Claude.ai and related products.
- **Evidence:** https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/overview,  
  https://www.anthropic.com/news/claude-sonnet-4-6

## 11) Web Search Tool (Grounded Research + Citations)
- **What it is:** Server-side web search with citations in responses.
- **How it works:** Claude triggers `web_search` server tool; results are injected with citations.
  Newer versions add dynamic filtering with code execution.
- **Evidence:** https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/web-search-tool

## 12) Web Fetch Tool (Full Page/PDF Retrieval)
- **What it is:** Fetch and analyze full web pages or PDFs with optional citations.
- **How it works:** Claude calls `web_fetch`; the server retrieves content, optionally filters
  it, and returns it to the model.
- **Evidence:** https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/web-fetch-tool

## 13) Computer Use (Desktop Automation)
- **What it is:** Operate a desktop environment via screenshots, mouse, and keyboard actions.
- **How it works:** A specialized computer-use tool emits action requests (click, type, screenshot);
  the client executes them in a sandboxed environment and returns results.
- **Evidence:** https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/computer-use-tool

## 14) Multi-Step Agent Looping
- **What it is:** Iterative tool calling until a task is completed.
- **How it works:** Claude alternates between tool requests and tool results in a loop
  (“agent loop”) across multiple turns.
- **Evidence:** https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/computer-use-tool,  
  https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/overview

## 15) Thinking / Extended Thinking (Reasoning Budget)
- **What it is:** A controllable reasoning budget and optional visibility into the model’s
  reasoning process.
- **How it works:** A `thinking` parameter with a token budget is provided; the model returns
  reasoning traces and uses those tokens for deeper deliberation.
- **Evidence:** https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/computer-use-tool,  
  https://www.anthropic.com/news/claude-sonnet-4-6

## 16) Prompt Caching
- **What it is:** Reuse cached context for faster, cheaper follow-ups.
- **How it works:** Clients add `cache_control` breakpoints; cached tool results and context are
  reused in subsequent requests.
- **Evidence:** https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/web-search-tool,  
  https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/web-fetch-tool

## 17) Context Compaction
- **What it is:** Automatic summarization of older context to extend effective context length.
- **How it works:** As conversations approach limits, older context is compacted to preserve
  key information while freeing tokens.
- **Evidence:** https://www.anthropic.com/news/claude-sonnet-4-6

## 18) Artifacts (Interactive Workspace In Claude.ai)
- **What it is:** A dedicated workspace for generated code/documents alongside chat.
- **How it works:** Claude.ai renders outputs in a separate pane for editing and iterative work.
- **Evidence:** https://www.anthropic.com/news/claude-3-5-sonnet

## 19) Memory (Personalization / Long-Term Preferences)
- **What it is:** Persist user preferences and interaction history across sessions.
- **How it works:** Documented as a product feature; later announcements reference a memory tool.
- **Evidence:** https://www.anthropic.com/news/claude-3-5-sonnet,  
  https://www.anthropic.com/news/claude-sonnet-4-6

## 20) Safety And Prompt-Injection Defenses
- **What it is:** Guardrails to resist jailbreaks and prompt injection, especially in tool use.
- **How it works:** Model training plus classifier defenses; computer-use adds extra checks and
  may request user confirmation on risky steps.
- **Evidence:** https://docs.anthropic.com/claude/docs/overview,  
  https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/computer-use-tool

