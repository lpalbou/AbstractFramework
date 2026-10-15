# 1009 — Typed list variables ("array of object", "array of number")

> Package: abstractflow, abstractruntime
> Type: proposal
> Created: 2026-10-11
> Priority: low
> Labels: visualflow, variables, types

## Summary

Let a variable declaration say what a list holds (`array of object`, `array of string`, ...), so the
editor can show it and the runtime can refuse an element of the wrong type when a list is written or
grown (1008).

## Why

Raised 2026-10-11 while designing 1008: today nothing stops a string from going into a list of
numbers, because a variable declared `array` carries no element type. The only check possible now
would guess the type from the elements already in the list, a heuristic the operator rules out
(no text/shape heuristics without explicit consent).

## Current code reality (2026-10-11)

- Pin types are flat (`PinType` in `abstractflow/src/types/flow.ts`); a pin may carry a JSON
  `schema`, and the editor already renders `items` from it ("of object {id, title, done}" on Break
  Object outputs, `abstractflow/src/utils/operatorNodes.ts` `schemaDetail`).
- Variable declarations (`var_decl`, On Flow Start pins) record a flat type only
  (`abstractflow/src/components/nodes/BaseNode.tsx` variable meta ~852–918).
- The runtime stores untyped JSON (`variable_adapter.py`).

## Open questions

- Declared where: `var_decl` only, or also On Flow Start pins and interface contracts?
- Enforced where: editor preflight only (wire types), runtime writes, or both?
- What an `any` element type means for existing flows (default: unchanged behaviour).

## Promotion criteria

An operator decision on the questions above, and a flow where a wrong-typed element caused a real
failure.

## Progress (2026-10-11, uncommitted in abstractflow)

Operator: "for an array, you should be able to define the types of the elements in the array".
Set Variables rows now carry an element type: an array row has an **of string / number / boolean /
json / any** choice, stored as the pin's `schema` (`{type: 'array', items: {type}}`, the same
"array of X" shape On Flow Start/End pins already use, `flowIoPinPatchForArrayItem` in
`abstractflow/src/utils/pinTypeOptions.ts`). The editor refuses a typed-in value whose items do not
fit (`setVariableValueProblem`, `abstractflow/src/utils/setVariables.ts`). Still open: runtime
enforcement of wired values, element types on `var_decl`, and Get Variable carrying the element type
on its output.
