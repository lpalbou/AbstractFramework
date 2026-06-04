# Planned: Gateway and Flow reasoning control propagation

## Metadata
- Created: 2026-06-03
- Status: Completed
- Completed: 2026-06-03

## ADR status
- Governing ADRs: None
- ADR impact: None

## Context
AbstractCore already exposes provider-aware thinking/reasoning controls. Core Python accepts a
`thinking` generation option, Core Server surfaces it on chat/responses request models, and
providers gate/translate it using `thinking_support` metadata. Gateway and Flow need to make
that control usable for reasoning models without forcing users to hand-author hidden params.

## Current code reality
- `abstractcore.core.interface.generate(... thinking=...)` and Core server request models support
  `thinking`.
- Core provider tests cover thinking mode normalization for OpenAI-compatible, Anthropic,
  Ollama, LM Studio, MLX, vLLM, Hugging Face, and related providers.
- `abstractruntime.integrations.abstractcore.effect_handlers.make_llm_call_handler` forwards
  `payload.params` to Core, so a `params.thinking` value already reaches Core.
- VisualFlow LLM and Agent nodes do not expose a `thinking` pin or config.
- `abstractruntime.visualflow_compiler.visual.executor._create_llm_call_handler` does not add
  `thinking` to LLM_CALL params.
- Visual Agent subworkflow construction in
  `abstractruntime.visualflow_compiler.compiler._create_visual_agent_effect_handler` forwards
  provider/model/temperature/seed but not thinking.
- `abstractagent.adapters.generation_params.runtime_llm_params` merges temperature, seed, media
  policy, and prompt-cache binding, but not thinking.
- Gateway `/api/gateway/runs/start` has no typed run-scoped `thinking` field.

## Problem
Reasoning level is Core-capable but not a first-class Gateway/Flow control. Flow users cannot set
reasoning per LLM/Agent node, and Gateway clients cannot set a run-scoped default without knowing
the private `_runtime` shape.

## What we want to do
Thread a single `thinking` control through Gateway run start, runtime namespace defaults,
VisualFlow LLM/Agent nodes, AbstractAgent generation params, and finally Core LLM_CALL params.

## Why
Reasoning models are increasingly common, and reasoning effort materially affects cost, latency,
and answer quality. The platform needs one clear control path that works for Gateway clients and
Flow authors while preserving Core's provider-specific translation.

## Requirements
- Gateway `/api/gateway/runs/start` accepts optional `thinking` and stores it in `_runtime.thinking`.
- Flow LLM Call and Agent nodes expose `thinking` as config and as an input pin override.
- Runtime LLM Call node params include `thinking` when explicitly set.
- Visual Agent subworkflows inherit node or run-scoped thinking into `_runtime.thinking`.
- AbstractAgent adapters copy `_runtime.thinking` into LLM_CALL params unless a step explicitly
  overrides it.
- Empty strings are treated as unset; booleans and non-empty strings are preserved for Core.

## Suggested implementation
Use the existing `thinking` name from AbstractCore. Keep value validation permissive in Runtime
and Gateway so Core remains responsible for provider-specific support and fallback warnings.
Expose common Flow options (`default`, `off`, `low`, `medium`, `high`, `xhigh`) as editor choices
without preventing pin-provided custom strings.

## Scope
- AbstractGateway run-start contract and capability contract.
- AbstractFlow node metadata, editor config, and type definitions.
- AbstractRuntime VisualFlow compiler/executor param propagation.
- AbstractAgent generation parameter helper.
- Focused Python tests for Gateway, Runtime, and Agent propagation plus a Flow build.

## Non-goals
- Do not invent provider-specific reasoning fields in Gateway or Flow.
- Do not duplicate Core provider validation.
- Do not force reasoning on by default.

## Dependencies and related tasks
- Core thinking mode support and model `thinking_support` metadata.
- Existing Runtime LLM_CALL effect handler param passthrough.

## Expected outcomes
- Gateway clients can start a run with `thinking: "high"` and Flow/Agent LLM calls inherit it.
- Flow authors can set or pin `thinking` per LLM Call or Agent node.
- Core remains the only layer that translates unsupported/provider-specific thinking behavior.

## Validation
- Agent unit tests prove `_runtime.thinking` is forwarded into LLM params.
- Runtime tests prove VisualFlow LLM Call and Agent nodes include thinking in generated effect
  params/runtime vars.
- Gateway tests prove `/runs/start` persists top-level `thinking` into `_runtime.thinking`.
- Flow TypeScript build succeeds.

## Progress checklist
- [x] Add Gateway run-scoped `thinking`.
- [x] Add Flow node controls and pins.
- [x] Add Runtime and AbstractAgent propagation.
- [x] Add focused tests.
- [x] Update user-facing docs and LLM indexes.

## Architect review
- Alternative A, Core-only hidden params: rejected because it leaves Gateway/Flow users without
  discoverable control.
- Alternative B, Gateway-only `_runtime.thinking`: useful for client defaults but insufficient for
  per-node Flow authoring.
- Alternative C, one `thinking` param across Gateway defaults and Flow node controls: selected
  because it preserves Core ownership while supporting both run-scoped and node-scoped workflows.

## Review notes
- Blocking risk: Agent nodes execute through AbstractAgent subworkflows, so updating only
  VisualFlow LLM Call would leave the most important Flow path broken.
- Blocking risk: empty UI values must not be sent as provider params.
- Required evidence: tests need to prove propagation in Gateway, Runtime LLM Call, Runtime Agent
  subworkflow vars, and AbstractAgent generation params.

## Completion report

- Date: 2026-06-03
- Summary: `thinking` is now a first-class Gateway/Flow control that propagates through Runtime
  VisualFlow execution, Agent subworkflows, AbstractAgent generation params, and finally Core LLM
  params.
- Files and symbols touched:
  - `abstractgateway.routes.gateway.StartRunRequest`, `_normalize_gateway_thinking`, and
    `start_run` to accept top-level `thinking` and persist `_runtime.thinking`.
  - Gateway discovery capability contract to advertise run-start thinking control.
  - `abstractflow` Agent and LLM Call node metadata, types, pin migration, and properties UI for
    a Reasoning selector plus `thinking` pin override.
  - `abstractruntime.visualflow_compiler.visual.executor._create_llm_call_handler` and
    `abstractruntime.visualflow_compiler.adapters.effect_adapter.create_llm_call_handler` to emit
    `params.thinking`.
  - `abstractruntime.visualflow_compiler.compiler` to inherit `thinking` into Agent subworkflow
    `_runtime` vars and structured-output follow-up calls.
  - `abstractagent.adapters.generation_params.runtime_llm_params` to forward explicit or
    run-scoped thinking values.
- Behavior changes:
  - Gateway clients can send `"thinking": "high"` to `/api/gateway/runs/start`.
  - Flow authors can set Reasoning on LLM Call and Agent nodes or connect a `thinking` pin.
  - Empty strings are treated as unset; booleans and non-empty strings are preserved for Core.
- Validation:
  - `PYTHONPATH=abstractagent/src:abstractruntime/src pytest -q abstractagent/tests/test_generation_params_media_policies.py abstractagent/tests/test_react_adapter_forwards_context_attachments_media.py`
  - `PYTHONPATH=abstractruntime/src:abstractcore pytest -q abstractruntime/tests/test_abstractcore_discovery_facade.py abstractruntime/tests/test_visualflow_capability_routes_and_thinking.py abstractruntime/tests/test_visualflow_memory_source_pins.py`
  - `PYTHONPATH=abstractgateway/src:abstractruntime/src:abstractcore pytest -q abstractgateway/tests/test_capabilities_endpoint_contract.py abstractgateway/tests/test_gateway_discovery_endpoints.py abstractgateway/tests/test_gateway_reasoning_control.py`
  - `npm run build` in `abstractflow`.
- Documentation updates: root configuration docs, package READMEs, and LLM indexes document the
  Gateway/Flow reasoning control path.
- Residual risks: Core remains responsible for provider-specific thinking support, translation,
  and unsupported-parameter warnings.
