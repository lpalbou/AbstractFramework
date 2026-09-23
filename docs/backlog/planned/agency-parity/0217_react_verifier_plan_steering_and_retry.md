# 0217 — ReAct Verifier, Plan Tool, Mid-Run Steering, and Effect Retries

**Status**: Planned
**Date**: 2026-07-07
**Priority**: High (task-completion quality + autonomy on the flagship path)
**Components**: abstractagent (react_runtime, agents/react), abstractruntime (core/policy, factory), abstractgateway (runner, routes)

## Summary
Bring the flagship ReAct loop up to Codex-class self-correction: reuse the existing CodeAct verifier
before finishing, add a structured `update_plan` tool, add a gateway command to inject guidance into
a running run, and default a `RetryPolicy` so transient effect failures don't kill runs.

## ADR status
- Governing ADRs: ADR-0002 (effect system), ADR-0013 (durable run controls: pause/resume/cancel), ADR-0016 (tool-calling pipeline).
- ADR impact: May extend ADR-0013 with an `inject_guidance` control verb; note the RetryPolicy default.

## Context / current code reality
Verified 2026-07-07:
- **Verifier exists only in CodeAct**: `maybe_review_node` → `review_node` → `review_parse_node`
  (`codeact_runtime.py:910-1176`). It runs a strict "verifier" LLM call with a JSON schema
  (`complete`, `missing`, `next_prompt`, `next_tool_calls`); if incomplete with `next_tool_calls` it
  re-enters `act`; if unactionable it nudges once; else feeds `next_prompt` back. Gated on
  `review_mode` (default False in CodeAct).
- **ReAct never wires it**: `ReactAgent(review_mode=True, review_max_rounds=3)` is the default and is
  written into `_runtime` (`agents/react.py:68, 176-178`), but `react_runtime.py` contains zero
  references to `review`/`review_mode` — dead config on the flagship path.
- **No plan tool**: no `update_plan`, no structured plan state in ReAct. CodeAct's plan is an
  off-by-default prose checklist scraped from a `Plan Update:` suffix (`codeact_runtime.py:279-299`).
- **No mid-run steering (gateway)**: the command inbox verbs are `pause|resume|cancel|emit_event|
  update_schedule|compact_memory` (`runner.py:393`, `routes/gateway.py`). `BaseAgent.inject_message`
  appends to `_runtime.inbox` (`agents/base.py:455-487`) but is local-Python only and racy vs the
  ticking thread.
- **No effect retries**: `DefaultEffectPolicy.default_max_attempts=1` (`core/policy.py:149`); neither
  the gateway host nor the local factory installs a `RetryPolicy` (`RetryPolicy` exists at
  `policy.py:193`). One raised tool/LLM exception fails the run (`runtime.py:1541-1550`). Idempotency
  keys (`policy.py:169-190`) already make retries safe.

## Problem
The default loop finishes as soon as the model stops emitting tool calls (no verification), has no
long-horizon plan anchor, cannot be steered once hosted, and dies on the first transient effect
exception.

## What we want to do
1. **Verifier in ReAct**: reuse the CodeAct verifier design behind the already-plumbed
   `_runtime.review_mode` (or a `finish(summary, evidence)` tool that triggers verification). When
   incomplete, re-enter `act` with `next_tool_calls`, mirroring CodeAct. Keep it opt-in per profile
   but wire it so the existing default actually takes effect.
2. **`update_plan` tool**: a schema-only tool that writes a structured checklist to
   `scratchpad.plan`; render the current plan compactly (at the message tail per 0212, not the
   cached prefix) so long tasks have a stable anchor.
3. **Gateway `inject_guidance` command**: a new command type that appends to `_runtime.inbox`
   through the single-writer runner (race-free by construction), so thin clients can steer a running
   run (drained at the next `reason` — with 0213/0212 the injected guidance should ride the message
   tail, not the system prompt).
4. **Default `RetryPolicy`**: install a sane retry policy (e.g. LLM 3 attempts, tools 2) in the
   local factory and gateway host; rely on idempotency for safety; keep failures loud after retries.

## Non-goals
- Not redesigning CodeAct; reuse its verifier shape.
- Not building interrupt-mid-generation (step-granular cancel stays; see separate work).
- Not changing the durable-effect contract beyond adding a control verb + retry policy defaults.

## Dependencies and related tasks
- Re-enters `react_runtime.py` — **sequence after 0212/0213** land to avoid churn.
- ADR-0013 (run controls) for the new command verb.

## Expected outcomes
- With `review_mode` on (the current default), a ReAct run runs a verification pass before finishing
  and re-acts on gaps.
- The model can maintain a plan across a long task.
- A hosted run can receive guidance mid-flight without cancel/restart.
- A single transient tool/LLM exception is retried, not fatal.

## Validation
- Unit: a scripted ReAct run where the first "final" answer is incomplete → verifier forces another
  `act` round; an `update_plan` call persists and renders at the tail; an injected-guidance command
  appears in the next `reason` request; a tool that fails once then succeeds completes the run under
  the default RetryPolicy.
- Live (endpoint `http://127.0.0.1:8317/v1`): a task with an easy-to-miss second requirement;
  measure completion (both requirements met) with verifier off vs on.

## Progress checklist
- [x] Wire verifier into ReAct behind `review_mode` (or `finish` tool).
- [x] `update_plan` tool + tail-rendered plan.
- [x] Gateway `inject_guidance` command (single-writer guard; unit-tested — not live-tested,
      gateway runner machinery).
- [x] Default RetryPolicy in factory + gateway.
- [x] Unit + LIVE evidence (2026-07-08, OVH `gpt-oss-120b`): on a real run the `review` node
      returned a structured verdict `{"complete": false, "missing": ["The three read_file calls
      must be made in three separate responses, exactly one per response, as required…"]}` —
      the verifier caught a genuine instruction violation live and steered another round via
      `next_prompt`. `update_plan` was called unprompted-by-schema (task-directed), persisted to
      `scratchpad.plan`, and rendered in the trailing [plan] message on subsequent calls.

## Guidance for the implementing agent
Reuse CodeAct's verifier structure rather than inventing a new one. Sequence `react_runtime.py`
edits after 0212/0213. Keep new prompt content at the message tail (0212 cache discipline).
