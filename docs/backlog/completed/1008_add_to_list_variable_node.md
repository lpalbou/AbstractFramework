# 1008 — "Add to List Variable" node: append one item or a list's items to a list variable in one step

> Package: abstractruntime, abstractflow
> Type: feature
> Created: 2026-10-11
> Completed: 2026-10-11 (uncommitted in abstractruntime and abstractflow)
> Original path: planned/1008_add_to_list_variable_node.md
> Priority: normal
> Labels: visualflow, variables, nodes

## Summary

Add one exec node, **Add to List Variable**, that reads a list variable, adds to it and writes it back
in a single runtime step. Two optional inputs say how: `item` adds one element, `items` adds each
element of a list. It replaces the three-node chain Get Variable → Array Append (or Array Concat) →
Set Variable that flows use today to grow a history or a knowledge list.

## Why

Operator, 2026-10-11, on a `history` chain (Get history → Array Append ← Task Executor · response →
Set history): "can we simplify that sequence and how?" Then, on a `knowledge` chain wired into
Array Append's `item`: "will it add each item of the new array as a separate item in the old array,
or will it add an item of type array? i want essentially to concat the array list here and save them
as new knowledge". Both cases (one item onto a list, a list onto a list) occur in real flows.

Besides the canvas, the chain has a correctness gap: the Get reads the variable in one step and the
Set writes it in another, so a write to the same variable between them (a parallel branch, a
subflow) is lost. One node reads and writes in the same step.

## Current code reality (2026-10-11)

- Variable writers: `set_var`, `set_var_property`, `set_vars` (`abstractflow/src/types/nodes.ts`
  ~1774–1823; handlers in `abstractruntime/src/abstractruntime/visualflow_compiler/adapters/variable_adapter.py`
  `create_set_var_node_handler` :74, `create_set_var_property_node_handler` :138,
  `create_set_vars_node_handler` :228; dispatch in `visualflow_compiler/compiler.py` ~4795–4852).
  `_set_by_path` / `_get_by_path` (:15, :30) already handle dotted names; Set Variable refuses an
  empty name and names starting with `_`.
- Array Append (`visual/builtins.py` `data_array_append` :961) adds `item` as ONE element whatever
  its type, so a list item nests (`[1, 2]` + `[3, 4]` → `[1, 2, [3, 4]]`), and it silently wraps a
  non-list `array` (`"text"` → `["text", item]`).
- Array Concat (`visual/executor.py` `_create_array_concat_handler` :1388) flattens list inputs,
  skips `None`, appends non-list values, and takes extra inputs through the node's `+` pin button.
- Lists are untyped JSON lists: a variable declared `array` carries no element type (typed lists:
  proposed 1009).

## Scope

### In scope

- Runtime handler `create_add_to_list_var_node_handler` beside Set Variable, reusing its name checks
  and `_set_by_path` / `_get_by_path`; one `compiler.py` dispatch branch.
- Semantics:
  - `name` (required, dotted paths allowed), `item` (optional, any type: added as one element),
    `items` (optional list: each element added, in order). Both may be wired: `item` first, then
    `items`.
  - Missing or `null` variable → starts as `[]`.
  - Existing value that is not a list → the step FAILS with an error naming the variable and its
    type (Array Append's silent wrap is not copied).
  - `items` that is not a list → the step fails naming the pin.
  - Neither input wired nor set → the step fails ("nothing to add").
  - Outputs: exec-out and `list` (the new list). The pipeline output is not clobbered (Set Variable's
    pass-through rule).
- AbstractFlow template in the Variables category, regenerated `docs/workflow-node-catalog.md`,
  docs (`docs/visualflow.md` authoring ladder rung 3), CHANGELOGs.
- Tests: runtime handler (each rule above, dotted path, pause/resume persistence of the output) and
  editor template/catalog.

### Out of scope

- No type check of elements (lists are untyped; 1009 owns typed lists). No heuristic guessing from
  the elements already in the list.
- No "mode" dropdown on Set Variable (one node, one behaviour, readable on the canvas).
- No migration: existing Get → Append/Concat → Set chains stay valid.
- Removing or changing Array Append / Array Concat.

## Acceptance criteria

- [ ] `history` + item `{role, content}` → one more element; `knowledge` + items `[k3, k4]` →
      `[k1, k2, k3, k4]`; unset variable → `[]` then the additions.
- [ ] A string-valued variable, a non-list `items`, and no input each fail the step with a message
      naming the node and the cause.
- [ ] The node reads and writes in one step (test: a value written by the same step's inputs is not
      lost).
- [ ] Node catalog, visualflow docs and both CHANGELOGs describe it; flow and runtime suites pass.

## Completion report (2026-10-11)

Built because the operator ruled out code in workflows ("i want a visual understanding for non
expert... so no code"); the `assist` flow's `vars.history + [value]` style expressions became
Add to List Variable nodes.

- Runtime: `create_add_to_list_node_handler` (`abstractruntime/src/abstractruntime/visualflow_compiler/adapters/variable_adapter.py`),
  `compiler.py` dispatch, `add_to_list` in `COMPILER_LAYER_NODE_TYPES` (`visual/executor.py`).
- Deviation from the scope above: a null `item` or `items` adds nothing instead of failing the step
  ("nothing to add"). A failed agent step leaves a null report, and failing the run there would be
  worse than adding nothing. An unwired node is an authoring mistake the canvas shows.
- Found on the way and fixed: Set Variables (and this node) took keys of the previous step's output
  as values (`_last_output` is the exec lane's ambient payload), so `set_vars` wrote them as
  variables. Both now keep only their own pins (`_own_input_pin_ids` in `visual/executor.py`).
- Editor: template in Variables, variable picker and "Add to <name>" auto-label like Set Variable
  (`abstractflow/src/components/nodes/BaseNode.tsx`), declares the variable as an array.
- Tests: `abstractruntime/tests/test_visual_loop_limit_and_list_nodes.py` (item vs items, missing and
  null, non-list variable and items fail naming the cause, `list` output read in the same step,
  ambient keys ignored, set_vars ambient keys ignored); `abstractflow/src/components/nodes/loopLimit.test.tsx`.
  Runtime suite 3370 passed; flow suite 1041 passed. Each new runtime test was seen failing with
  its rule removed.
- Docs: node catalog regenerated, `abstractflow/docs/visualflow.md` ladder rung 3, both CHANGELOGs.
