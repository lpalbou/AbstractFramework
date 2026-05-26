# 135 — AbstractFlow Exec Fan-In + Path-Selected Inputs (JoinExec + PathMux)

**Status**: Planned  
**Date**: 2026-03-29  
**Priority**: High (authoring UX + correctness)  
**Components**: abstractflow/web (frontend), abstractflow (portable VisualFlow schema + executor), abstractruntime (VisualFlow compiler + runtime), abstractgateway (compat for VisualFlow host)

## Summary

Enable a **simple “loop wire back into a node”** authoring pattern in AbstractFlow without requiring:

- recursive `Subflow` self-calls, or
- explicit `While` + `Set/Get Variable` scaffolding

…by adding a *strict but ergonomic* fan-in mechanism:

1) When a user attempts to connect a **second execution wire** into a node’s `exec-in`, the editor **auto-inserts** a hidden helper node `join_exec`.
2) When a user attempts to connect a **second data wire** into an already-connected data pin, the editor **auto-inserts** a hidden helper node `path_mux` (a φ/mux) that selects which value to forward based on the `join_exec` route.

This preserves the current Blueprint-style “one connection per input pin” invariant for normal nodes, while making loopback authoring feel like “just wire it”.

## Why

### Current pain

- The editor enforces **at most one incoming edge per input pin**, including `exec-in`:
  - `abstractflow/web/frontend/src/utils/validation.ts` (“Inputs accept at most one connection”)
- Users cannot create a natural “chat loop”:
  - `On Flow Start → Agent → Ask User → (loop back) Agent`
- Workarounds today:
  - recursion via `Subflow` (self-call) which creates unnecessary run nesting and complexity
  - `While` + variables which is correct but visually/statefully verbose for basic “repeat conversation” flows

### Correctness constraint (non-negotiable)

AbstractRuntime caches **pure node outputs** (`Flow._node_outputs`) for data-edge evaluation. Explicit loop nodes (`Loop/While/For`) already do special cache invalidation so pure nodes recompute per-iteration.

If we allow loopbacks via wiring without introducing an iteration boundary / invalidation, common flows become incorrect:

- `Agent.response -> Concat -> AskUser.prompt`
- next iteration: `Concat` must recompute, but a cached pure node would otherwise stay stale.

Therefore, the loopback feature must include a robust, durable cache invalidation story.

## Goals

- **G1 — Simple loop UX**: users can loop `exec-out → exec-in` in one gesture.
- **G2 — No semantic change when unused**: flows with no `join_exec/path_mux` behave exactly as today.
- **G3 — Deterministic selection**: trajectory-dependent data pins are resolved predictably and can be inspected.
- **G4 — Durable correctness**: works across WAIT/RESUME and gateway-hosted durable runs.
- **G5 — Keep the canvas clean**: helper nodes can be collapsed/hidden by default.

## Non-goals (v0)

- “True” multi-edge inputs on arbitrary nodes (implicit resolution everywhere).
- A wholesale pivot to a Node-RED “single message frame” model.
- Real concurrency semantics (Parallel remains deterministic pin-order scheduling as today).
- Supporting “any cycle anywhere” without guardrails.

## Proposed design (recommended): Strategy 2 helper nodes + auto-insert

### Concepts

**Exec fan-in** is made explicit via `join_exec`:

```text
          (exec)
Start ─┐
       ├─▶ join_exec ─▶ Agent
Ask ───┘
```

**Data ambiguity** is made explicit per-pin via `path_mux`:

```text
Start.prompt ─┐
              ├─▶ path_mux(out) ─▶ Agent.prompt
Ask.response ─┘        ▲
                       │
                 join_exec.which
```

### Visual example: chat loop (desired user gesture)

User draws one additional wire:

```text
OnStart.exec ─▶ Agent.exec ─▶ AskUser.exec ─┐
                                           │
                                           └────────▶ Agent.exec-in   (attempted loopback)
```

Editor rewrites into (internal graph):

```text
OnStart.exec ─▶ join_exec.exec-in
AskUser.exec ─▶ join_exec.exec-in
join_exec.exec-out ─▶ Agent.exec-in

OnStart.prompt ─▶ path_mux.in0
AskUser.response ─▶ path_mux.in1
join_exec.which ─▶ path_mux.select
path_mux.out ─▶ Agent.prompt

Agent.response ─▶ AskUser.prompt
```

### Helper nodes (schema)

#### `join_exec` (internal-only control node)

- **Type**: `join_exec`
- **Inputs**:
  - `exec-in` (execution) — **special-case**: allows N incoming exec edges
- **Outputs**:
  - `exec-out` (execution)
  - `which` (number) — 0..N-1 index indicating which incoming path triggered the join
  - `from` (string) — predecessor node id (debug-only; optional but strongly recommended)
- **Semantics**:
  - Reads `prev_node_id` from durable run state (runtime-provided).
  - Computes `which` by matching `prev_node_id` against the set of incoming exec edges.
  - Persists `{which, from}` under `_temp.node_outputs[join_node_id]` for data-edge consumers and observability.
  - **Cache invalidation boundary**: clears cached pure node outputs (see “Correctness” below).

#### `path_mux` (internal-only pure node)

- **Type**: `path_mux`
- **Inputs**:
  - `select` (number)
  - `in0` (any), `in1` (any), … (dynamic)
  - optional `fallback` (any) — only if we choose the “explicit fallback” policy (see below)
- **Outputs**:
  - `out` (any)
- **Semantics**:
  - Outputs `in{select}` when defined.
  - Fallback policy is explicit (see “Defaults & fallback”).

### Defaults & fallback policy (decision)

We must pick one stable rule for pins that are “selected” but unwired / missing.

**Option A (strict)** — simplest, safest:
- `path_mux` outputs `null` when `select` points at an unwired input.
- Editor warns “selected arm missing” in preflight.

**Option B (explicit fallback pin)** — recommended:
- `path_mux` has an optional `fallback` input:
  - if selected arm missing/unset, return `fallback`
  - if `fallback` missing, return `null`
- When auto-inserting a `path_mux` for an existing connected pin, the editor can optionally:
  - preserve the original “unconnected pin default” by inserting a Literal node and wiring it into `fallback` (if a default existed).

**Option C (carry/keep-last)** — feels intuitive but is hidden state:
- If selected arm missing, retain previous `out`.
- Not recommended for v0 (debuggability + hidden state coupling).

## Correctness plan (pure-node cache invalidation)

### Problem

Pure nodes feeding a re-entered node must be recomputed after each iteration (or after each causal change), otherwise values become stale.

### v0 policy (recommended)

Treat `join_exec` as the canonical “re-entry boundary” and **clear cached pure node outputs** each time `join_exec` executes:

- Clear `flow._node_outputs[pure_node_id]` for `pure_node_id in flow._pure_node_ids`
- Preserve `flow._static_node_outputs` (literals/schemas) by re-seeding after clear or by clearing only non-static ids.

This is intentionally conservative and trades small recomputation cost for robust semantics.

**Why this is acceptable**:
- The primary target loops include a WAIT (`Ask User` / `Wait Event`), so iteration rate is human-speed.
- Pure node counts are small in typical editor-authored flows.
- It avoids introducing “magic” dependency tracking in v0.

### Guardrails

- The editor should warn (preflight) on **execution cycles that do not pass through a `join_exec`**, because they will not get the cache invalidation boundary.
- The editor should warn on **cycles with no WAIT-like yield** (AskUser/WaitEvent/Delay), because they can create tight infinite loops; recommendation: use `While/ForEach/For` with explicit max-iterations caps for compute loops.

## Collapsing / simplifying the visualization (UX)

### Principle

The persisted graph is explicit (`join_exec`/`path_mux` exist in JSON), but the editor renders them **collapsed by default** so the user experiences:

> “I connected a loop wire back into the node.”

### Proposed UI behaviors

- Add a global toggle: **View → Show internal junction nodes**
  - off (default): helper nodes are hidden; wires render as if connected directly to the target pin with a small “merge/mux” badge
  - on: helper nodes are visible and selectable
- Add per-node badges on pins:
  - `exec-in` shows “merge ×N” when fed via `join_exec`
  - muxed data pins show a “path-selected” icon
- Add an inspector panel section for muxed pins:
  - show “Path 0: source = OnStart.prompt”, “Path 1: source = AskUser.response”
  - show current selected path for the latest executed step (from traces)

## Repository impact (what must change)

### Must change: `abstractflow/web` (frontend)

Primary work: authoring-time rewrite + UX.

Key files/components:

- Connection rules and error classification:
  - `abstractflow/web/frontend/src/utils/validation.ts`
- Connection handling + auto-insert rewrite:
  - `abstractflow/web/frontend/src/components/Canvas.tsx` (`handleConnect`)
  - `abstractflow/web/frontend/src/hooks/useFlow.ts` (`onConnect` + new “rewrite connect” action)
  - New utility module (recommended):
    - `abstractflow/web/frontend/src/utils/graphRewrite.ts` (pure functions; unit-testable)
- New hidden node templates:
  - `abstractflow/web/frontend/src/types/nodes.ts` (add `join_exec` + `path_mux` templates; `hiddenInPalette: true`)
- Type unions:
  - `abstractflow/web/frontend/src/types/flow.ts` (`NodeType` union must include `join_exec` / `path_mux`)
- Collapsed rendering:
  - `abstractflow/web/frontend/src/components/nodes/BaseNode.tsx` (render internal nodes compactly; or hide entirely when toggle is off)
  - `abstractflow/web/frontend/src/components/PropertiesPanel.tsx` (read-only inspector for internal nodes; avoid exposing too much config)

### Must change: `abstractflow` (portable VisualFlow schema + helper reachability)

The web backend and some hosts validate VisualFlow JSON via Pydantic enums.

- Add new node types to the portable schema:
  - `abstractflow/abstractflow/visual/models.py` (`NodeType` enum)
- Ensure reachability/subflow discovery doesn’t ignore `join_exec`:
  - `abstractflow/abstractflow/visual/executor.py` (`EXEC_TYPES` set in `_reachable_exec_node_ids`)

### Must change: `abstractruntime` (compiler + runtime durability)

We need new control-node semantics and a durable predecessor signal.

- Add durable predecessor metadata:
  - `abstractruntime/src/abstractruntime/core/runtime.py`
    - when transitioning to `next_node`, set `run.vars["_temp"]["prev_node_id"] = plan.node_id`
    - on resume (`_apply_resume_payload`), set `prev_node_id` to the waiting node before jumping to resume target
- Add compiler support for `join_exec`:
  - `abstractruntime/src/abstractruntime/visualflow_compiler/compiler.py`
    - detect `effect_type == "join_exec"` and build a handler
    - compute stable incoming-route ordering for the node (from flow edges)
    - persist `{which, from}` into `_temp.node_outputs[join_id]`
    - apply cache invalidation (clear `flow._node_outputs` for pure nodes)
- Add control adapter implementation:
  - `abstractruntime/src/abstractruntime/visualflow_compiler/adapters/control_adapter.py`
    - `create_join_exec_node_handler(...)`
- Add pure node implementation for `path_mux`:
  - `abstractruntime/src/abstractruntime/visualflow_compiler/visual/executor.py`
    - `_create_path_mux_handler(...)`
    - consider marking `path_mux` as volatile (safe default) even if we also invalidate at `join_exec`

### Optional: `abstractgateway`

No direct changes required for **bundle mode** (it compiles VisualFlow via `abstractruntime.visualflow_compiler`).

However, gateway’s **VisualFlow host** imports `abstractflow.visual.models.VisualFlow` and will only accept new node types once `abstractflow` is updated (covered above). Additional gateway changes are not expected beyond test coverage.

## Implementation plan (phased)

### Phase 0 — Decisions (must resolve before coding)

1) Node names: `join_exec` and `path_mux` (or alternative naming) — keep snake_case, internal-only.
2) Fallback policy for `path_mux`: choose Option B (explicit fallback pin) vs Option A (strict null).
3) Guardrail policy:
   - do we allow cycles without WAIT nodes?
   - do we allow cycles that do not include `join_exec`?

### Phase 1 — Schema + templates (no behavior change yet)

Frontend:
- Add NodeType union entries:
  - `abstractflow/web/frontend/src/types/flow.ts`
- Add hidden templates:
  - `abstractflow/web/frontend/src/types/nodes.ts`

Backend/portable:
- Add node enums:
  - `abstractflow/abstractflow/visual/models.py`

### Phase 2 — Editor auto-insert (authoring-time rewrite)

Implement deterministic graph rewrite utilities:
- New `graphRewrite.ts` that can:
  - insert nodes
  - rewire existing edge(s)
  - preserve edge animation/labels
  - maintain stable ids (or at least stable enough for undo/redo)

Hook into connect flow:
- `abstractflow/web/frontend/src/components/Canvas.tsx`: intercept “input already connected” errors and route to rewrite.
- `abstractflow/web/frontend/src/hooks/useFlow.ts`: add an action `connectWithAutoInsert(connection)` to perform the rewrite as one state update.

Auto-insert rules:
- Second `exec -> exec-in` connection → insert `join_exec`
- Second `data -> data-pin` connection → insert `path_mux`
  - wire `select` from nearest `join_exec.which` that feeds the same target node
  - if none found, warn and leave `select` unconnected (v0 limitation)

### Phase 3 — Runtime/compiler semantics

AbstractRuntime:
- Add `prev_node_id` durability:
  - `abstractruntime/src/abstractruntime/core/runtime.py`
- Implement `join_exec` handler:
  - `abstractruntime/src/abstractruntime/visualflow_compiler/adapters/control_adapter.py`
  - `abstractruntime/src/abstractruntime/visualflow_compiler/compiler.py`
- Implement `path_mux` builtin handler:
  - `abstractruntime/src/abstractruntime/visualflow_compiler/visual/executor.py`

AbstractFlow:
- Include `join_exec` as execution-reachable for subflow discovery:
  - `abstractflow/abstractflow/visual/executor.py`

### Phase 4 — Collapsed visualization + inspector

- Add “Show internal junction nodes” toggle to the UI.
- When hidden:
  - do not show `join_exec/path_mux` nodes
  - render synthetic “direct” edges (non-persisted) for readability
  - show pin badges indicating merged/muxed pins
- Inspector:
  - show a mapping table for muxed pins
  - show the last-selected path (from node outputs / traces)

### Phase 5 — Tests + acceptance harness

AbstractRuntime tests (required):
- Compile + execute a chat loop that re-enters nodes and validates:
  - `path_mux` selects the correct prompt source per entry path
  - pure nodes in the loop body recompute per-iteration (no stale cache)
- Add a “cycle without join_exec” test that demonstrates the warning / unsupported behavior.

AbstractFlow tests (recommended):
- Pydantic validation accepts new node types.

Gateway tests (optional but valuable):
- Run a workflow containing `join_exec/path_mux` through:
  - bundle compilation mode
  - (if maintained) VisualFlow host mode

## Acceptance criteria

- Users can build the chat loop without `Subflow` recursion and without `While/variables`.
- When helper nodes are not used, compilation/execution behavior is unchanged.
- For a loop that uses `join_exec`, pure node outputs do not get stuck across turns.
- Flows containing helper nodes validate in:
  - AbstractFlow web backend
  - AbstractGateway VisualFlow host (via abstractflow models)
- Internal nodes can be hidden by default with a clear reveal path for debugging.

## Risks / mitigations

- **Hidden semantics confusion**: mitigate with pin badges + inspector mapping and a global “show internals” toggle.
- **Infinite loops**: mitigate with preflight warnings and guidance to use `While/For` for compute loops.
- **Cache invalidation too broad**: start conservative (clear all pure nodes) then optimize to dependency-based invalidation later.

## Alternatives considered (not chosen for v0)

1) Global multi-input pins with implicit selection (more “magic”, harder to debug, larger runtime surface).
2) Message/frame-first model (Node-RED style): simpler loops but a product-level pivot and more hidden state coupling.

