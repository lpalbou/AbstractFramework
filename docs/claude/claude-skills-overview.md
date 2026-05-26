# Claude Skills Research Overview (Feb 2026)

## Definition
A "Claude skill" here means any publicly documented capability of Claude models or the Claude
developer platform (API + tools + claude.ai features) that enables users to perform a class of
tasks. This includes model-level capabilities (reasoning, vision, long-context) and platform
capabilities (tool use, web search/fetch, computer use, artifacts, memory).

## Sources And Scope
This overview is based on Anthropic’s public documentation and product announcements available
as of February 2026. See `untracked/skills/claude-skills-sources.md` for the full list of sources.

Key references include:
- “Building with Claude” (capabilities overview, tool use, vision, long context)  
  https://docs.anthropic.com/claude/docs/overview
- Tool use docs (client tools, server tools, strict tool use, MCP)  
  https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/overview
- Computer use tool (desktop automation, agent loop, thinking param)  
  https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/computer-use-tool
- Web search tool (citations, dynamic filtering with code execution)  
  https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/web-search-tool
- Web fetch tool (page/PDF fetch, citations, dynamic filtering)  
  https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/web-fetch-tool
- Claude model announcements (reasoning, vision, long context, artifacts, memory)  
  https://www.anthropic.com/news/claude-3-family  
  https://www.anthropic.com/news/claude-3-5-sonnet  
  https://www.anthropic.com/news/claude-sonnet-4-6

## How Claude Skills Work (High-Level)
1. **Model capabilities**  
   Claude’s core skills (reasoning, writing, coding, multilingual, vision) are model-level
   capabilities described in the model announcements and overview docs. These are accessed
   through the standard Messages API.  
   References: https://docs.anthropic.com/claude/docs/overview,  
   https://www.anthropic.com/news/claude-3-family

2. **Tool use (function calling)**  
   Claude can emit structured tool calls based on a schema you provide. The API returns
   `tool_use` blocks, your app executes them, then sends `tool_result` blocks back. This
   enables deterministic integration with external systems.  
   Reference: https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/overview

3. **Client tools vs server tools**  
   - **Client tools** run on your infrastructure (custom tools, computer use, bash, text editor).  
   - **Server tools** run on Anthropic’s infrastructure (web search, web fetch), with results
     embedded back into Claude’s response.  
   Reference: https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/overview

4. **Agent loop for multi-step tasks**  
   Claude can repeatedly request tool actions and consume results until a task completes.
   This “agent loop” is central to computer use and multi-step automation.  
   Reference: https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/computer-use-tool

5. **Server-side grounding and citations**  
   Web search and fetch tools provide citations, and can dynamically filter content using
   code execution to reduce token usage and improve relevance.  
   References:  
   https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/web-search-tool  
   https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/web-fetch-tool

6. **Reasoning transparency and long-horizon context**  
   Some models support “thinking” parameters (a dedicated reasoning budget) and context
   compaction to extend effective context for long-running tasks.  
   References:  
   https://docs.anthropic.com/claude/docs/agents-and-tools/tool-use/computer-use-tool  
   https://www.anthropic.com/news/claude-sonnet-4-6

7. **Product-layer skills (claude.ai)**  
   Features like Artifacts and Memory are positioned as collaboration and personalization
   features inside the Claude product experience.  
   References:  
   https://www.anthropic.com/news/claude-3-5-sonnet  
   https://www.anthropic.com/news/claude-sonnet-4-6

## Interpretation Notes
- Some skills are **model capabilities** (intrinsic) while others are **platform features**
  (API tools or claude.ai UX). This report distinguishes them explicitly.
- Several features are in **beta** (e.g., computer use) and carry additional security and
  privacy constraints documented by Anthropic.
- Where a feature is announced but not fully specified (e.g., Memory in early announcements),
  this report documents only what is explicitly stated by Anthropic.

