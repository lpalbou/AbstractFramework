# 1011 — Reasoning level as an optional pin of the Runnable and Assistant interfaces

> Package: abstractflow, abstractruntime, abstractgateway (tests only)
> Type: feature
> Created: 2026-10-11
> Priority: normal
> Labels: interfaces, reasoning, thinking, visualflow

## Summary

Add an optional On Flow Start pin `thinking` (label "reasoning") to the Runnable agent
(`abstractcode.agent.v1`) and Assistant (`abstractassistant.agent.v1`) interfaces, filled from the
caller's run-wide reasoning level (`_runtime.thinking`), so a workflow shows the level it was asked
for and can route it (for example high for the planner, low for the executor). The Run window
offers it as a select.

## Why

Operator, 2026-10-11: "what would it take to amend the running interface and add a reasoning field?
i feel it's missing..." then "create a backlog item for that too".

The level already reaches every Runnable workflow, invisibly: every host sends `_runtime.thinking`
and the runtime applies it to each Agent / LLM Call without its own `thinking`. Nothing on the canvas
shows it and a flow cannot route it.

## Current code reality (2026-10-11)

- Hosts send `_runtime.thinking` only: AbstractAssistant `gateway/run_input.py:182-184`; AbstractCode
  web `workspace/catalog.ts:723` (it also maps family pins named `reasoning` / `thinking` /
  `reasoning_effort`, `input_schema.ts:272-278`); AbstractCode TUI `tui/src/run_input.rs:192`
  (a test asserts no top-level `thinking`); gateway `StartRunRequest.thinking` folded into
  `_runtime.thinking` (`routes/gateway.py:9033-9035`), advertised as `thinking_control` with values
  none…xhigh (`:18545-18550`). Entity chat reads top-level `thinking` > `reasoning` >
  `_runtime.thinking` (`routes/entities.py:3240-3260`).
- Runtime precedence: node `thinking` pin > node config > run `_runtime.thinking` (inherited by
  children) > capability-route default (`visualflow_compiler/compiler.py:1522-1542, 1833-1836`;
  `visual/executor.py:3394, 3658-3667`; `integrations/abstractcore/effect_handlers.py:985-1010`;
  `core/runtime.py:4646-4670`; `llm_client.py:151-170`).
- The interface pin lists live only in `abstractflow/src/utils/flowFamilies.ts` (Runnable :59-76, no
  optional pins); `optionalStartPins` exists since 2026-10-11 (Assistant). The gateway's
  `agent_defaults.py` `INTERFACE_TABLE` has no pins; no Python validation of interface pins (the
  editor preflight is advisory).
- 11 shipped flows declare Runnable (`abstractgateway/flows/bundles/*.flow`: basic-agent, coding
  agents, deep-research, meta-*, …); none has a thinking pin. Tests pinning the lists:
  `abstractflow/src/utils/flowFamilies.test.ts`, `abstractgateway/tests/test_gateway_native_loop_bundle_loader.py:267,298`.

## Scope

### In scope

- `flowFamilies.ts`: optional start pin `{ id: 'thinking', label: 'reasoning', type: 'string' }` on
  Runnable and Assistant, described as the caller's reasoning level (empty = run default).
- Runtime: when a visual flow's On Flow Start declares `thinking` and `input_data` has no top-level
  `thinking`, seed it from `_runtime.thinking` (one rule where start values are seeded). Hosts keep
  sending one field; the pin is its visible projection.
- Run window: the `thinking` start pin renders as a select (default, none, low, medium, high,
  xhigh), like the `speculation` pin's picker.
- Tests (flowFamilies, runtime seeding incl. an explicit top-level value winning, Run window field),
  docs, CHANGELOGs; the gateway test's expected pin list if it reads the declared pins.

### Out of scope

- Changing any host (they already send `_runtime.thinking`).
- Wiring the pin into the shipped flows' agents (left to the operator per flow; unwired = today's
  behaviour).
- The model's reasoning TEXT as an output (1012).

## Notes

- Opening a shipped flow that declares Runnable adds the optional pin and opens with unsaved changes
  (the same as Assistant flows since 2026-10-11).
- Interacts with 1006 (simple interface ids): whichever lands second carries the other's change.

## Acceptance criteria

- [ ] Declaring Runnable or Assistant adds an optional `thinking` pin; preflight never asks for it.
- [ ] A run started with `_runtime.thinking: "high"` shows `high` on the flow's `thinking` pin; an
      explicit top-level `thinking` wins; no value leaves the pin empty and the run default applies.
- [ ] The Run window offers the level as a select.
- [ ] A flow that does not wire the pin behaves exactly as before.

## Receipts

- (to fill)
