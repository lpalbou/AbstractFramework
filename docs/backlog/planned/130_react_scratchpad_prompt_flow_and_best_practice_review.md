# 130 — ReAct Scratchpad Prompt Flow And Best Practice Review

**Status**: Planned  
**Date**: 2026-03-23  
**Priority**: High  
**Components**: abstractagent, abstractruntime, abstractcode, docs

## Summary

Document, with code-level precision, how the current ReAct loop constructs its working context:

- what is stored in `scratchpad`
- what is appended to `context["messages"]`
- what is appended to `system_prompt`
- which roles are used
- what the model actually sees on each cycle
- where prompt-cache reuse currently helps and where it is defeated

This item is research and architecture documentation only. It must not change runtime behavior.

## Why

- The current flow is easy to misread because “history”, “scratchpad”, and “tool transcript” are not the same data structure.
- Prompt-cache behavior depends on exactly where each piece of state is rendered.
- Before we redesign ReAct prompt assembly, we need one shared document with:
  - current architecture
  - diagrams
  - risks
  - best-practice comparison
  - recommendations

## Current architecture

### High-level loop

```text
init
  -> reason
  -> parse
  -> act
  -> observe
  -> reason
  -> ...
  -> done
```

### Current data lanes

```text
User/task input
  -> context["task"]
  -> context["messages"]

LLM reasoning cycle output
  -> scratchpad["cycles"][i].thought
  -> scratchpad["cycles"][i].tool_calls
  -> scratchpad["cycles"][i].observations

Tool transcript for model-visible chat history
  -> context["messages"].append(assistant tool-call stub)
  -> context["messages"].append(tool observation message)

Scratchpad summary for model-visible planning context
  -> render scratchpad summary
  -> append summary block to payload["system_prompt"]
```

### Current model-visible prompt assembly

```text
payload = {
  "messages": sanitized(context["messages"]),
  "system_prompt": compose(base_system_prompt + rendered_scratchpad_summary),
  "tools": runtime tool specs,
}
```

### Current flow by cycle

```text
cycle N:
  1. Read durable scratchpad state
  2. Render scratchpad summary block
  3. Append summary block to system prompt
  4. Send sanitized message history + system prompt to LLM
  5. Parse thought/tool calls/final answer
  6. Store thought in scratchpad
  7. Store tool transcript in message history
  8. Store observations in both:
     - scratchpad cycle entry
     - tool-role chat history
```

## Current code map

- Scratchpad rendering:
  - `abstractagent/src/abstractagent/adapters/react_runtime.py`
  - `_render_cycles_for_system_prompt(...)`
- Scratchpad appended to system prompt:
  - `reason_node(...)`
- Tool-call transcript appended to `context["messages"]`
- Tool observations appended to `context["messages"]`
- Runtime prompt-cache module partition:
  - `abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py`

## Observed design tensions

### 1. Scratchpad is not only scratchpad

The durable ReAct cycle record is both:

- an internal state structure
- a model-visible summary block

That dual use makes the prompt-cache partition harder to reason about.

### 2. Transcript and scratchpad are split across two prompt lanes

The model sees:

- tool transcript in `messages`
- scratchpad summary in `system_prompt`

That means append-only cycle growth does not map cleanly onto one append-only cached lane.

### 3. The scratchpad summary is bounded

The current rendered scratchpad view is intentionally bounded/truncated before insertion into the system prompt.

Implication:

- “full scratchpad” and “model-visible scratchpad” are already different things today.

## External comparison: current best-practice signals

### ReAct paper

Source:
- ReAct: https://arxiv.org/abs/2210.03629

Relevant takeaway:
- ReAct is defined around interleaved reasoning traces and actions in a trajectory.
- The trajectory is conceptually part of the running interaction state, not a repeated rewrite of static instructions.

### OpenAI conversation-state guidance

Source:
- https://developers.openai.com/api/docs/guides/conversation-state

Relevant takeaway:
- Prior response output is appended to future inputs to preserve state across turns.
- Conversations store messages, tool calls, tool outputs, and related items as conversation state.

### OpenAI prompt-caching guidance

Source:
- https://developers.openai.com/api/docs/guides/prompt-caching

Relevant takeaway:
- Cacheable prefixes should keep stable/repeated content at the beginning and dynamic content at the end.
- Messages, tools, and structured-output schemas are treated as cacheable prefix content.

### Anthropic tool-use guidance

Source:
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use

Relevant takeaway:
- Tool use/result state belongs in the conversation message structure.
- Tool results must be adjacent to the tool-use turn in history.

### Anthropic prompt-caching guidance

Source:
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching

Relevant takeaway:
- Prompt caching is defined over the full prefix of `tools`, `system`, and `messages`.
- Automatic caching advances the cache breakpoint as multi-turn conversations grow.

## Working comparison against current implementation

### What aligns

- Tool transcript is kept in model-visible message history.
- The runtime already thinks in prompt modules and per-session history.

### What does not align well

- Scratchpad growth is rendered into `system_prompt`, which is supposed to be the stable prefix lane.
- The cache partition therefore mixes:
  - stable instructions
  - changing cycle summary
- This defeats the “stable prefix / dynamic suffix” principle from prompt-caching guidance.

## Recommendations

These are recommendations only. Do not implement them under this item.

1. Separate stable system instructions from ReAct working memory.
2. Treat tool transcript and scratchpad as explicit, independently understood prompt lanes.
3. Prefer append-only cacheable lanes for cycle growth.
4. Keep model-visible tool transcript in the conversation history lane.
5. Decide explicitly whether the scratchpad should be:
   - full and durable
   - summarized and durable
   - summarized for the model, full for host-side recall

## Open questions

- Should the model see the full scratchpad, a rolling summary, or only tool transcript plus host guidance?
- Should scratchpad be encoded as assistant/user/tool turns, a separate message role abstraction, or its own provider-agnostic prompt module?
- If scratchpad is summarized, who owns the summarization policy: runtime, adapter, or provider integration?
- How should branching / derived ReAct paths interact with scratchpad caches?

## Deliverable

This planned item should later become the source-of-truth document for ReAct prompt/data flow before any redesign of scratchpad handling or cache strategy.
