# 039 — Tool Argument Type Coercion (Centralized)

**Status**: Planned  
**Date**: 2026-02-20  
**Priority**: High (safety + correctness)  
**Components**: abstractcore/tools, providers, docs

## Summary

Centralize tool-argument type coercion and validation so string-typed arguments
from tool-call parsing cannot silently bypass security gates (e.g., `"false"`
evaluating as truthy). Provide explicit warnings and errors, and align behavior
across all tool dispatch paths.

## Reason

Tool calls arrive via multiple formats (JSON, XML-ish, code blocks). Several
parsing paths preserve raw string values. Without a centralized coercion layer,
each tool must defensively handle types, which is inconsistent and can produce
security regressions. A single, schema-aware coercion step improves safety,
predictability, and observability.

## Scope

### In scope

- Central coercion and validation of tool arguments based on schema types.
- Consistent warnings for coercions using `#FALLBACK` tags.
- Clear error responses when coercion is impossible or ambiguous.
- Defense-in-depth: keep local checks in high-risk tools (e.g. `execute_command`).
- Tests covering coercion and error paths for security-sensitive flags.
- Documentation updates describing coercion rules and warnings.
- Propose a minimal ADR documenting the decision and rationale.

### Out of scope

- Rewriting provider-specific tool-call formats or transport layers.
- Full JSON Schema validation for deeply nested complex structures.
- Changing tool parameter semantics beyond type normalization.

## Dependencies

- Access to tool parameter schemas in the registry (source of truth).
- Decision on where to record warnings (ToolResult, event stream, logs).
- ADR approval to codify the coercion policy and warning conventions.

## Expected outcomes

- String arguments like `"false"` or `"0"` no longer bypass safety checks.
- Consistent behavior across CLI, server, and registry-based tool execution.
- Explicit `#FALLBACK` warnings when coercion is applied.
- Improved test coverage for tool-call robustness and security.

## Plan (high level)

1) **Inventory inputs**: map all tool-call parse paths and confirm where string
   values enter the system (JSON, XML-ish tags, code blocks, provider payloads).
2) **Define coercion rules**: per-schema-type rules (bool/int/float/string/list/object)
   with explicit accepted string tokens. Anything else should error, not silently
   default.
3) **Implement a central coercer**: a single module (e.g. `tools/arg_coercion.py`)
   that returns `(arguments, warnings)` and never mutates in place.
4) **Wire into tool execution**: apply coercion in `ToolRegistry.execute_tool`
   (and ensure CLI path uses the same registry) before invoking tools.
5) **Add warnings**: emit `#FALLBACK` warnings for any coercion; include
   tool name and argument key for diagnosis.
6) **Tests**: add unit tests for coercion success/failure and explicit security
   tests for `allow_dangerous`, `require_confirmation`, and common numeric fields.
7) **Docs + ADR**: update tool-calling docs and add an ADR describing the
   coercion policy and warning requirements.

## Acceptance criteria

- A tool call with `"allow_dangerous": "false"` is treated as `False` and does
  not bypass the security block.
- Invalid or ambiguous values produce a tool error with a clear explanation.
- Coercions produce explicit `#FALLBACK` warnings (no silent fallback).
- All tool dispatch paths share the same coercion behavior.

