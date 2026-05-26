# Backlog: SmartNote specialized workflow documentation

## Summary
Explain the SmartNote gateway bundle and specialized workflow, including a clear diagram and step-by-step expectations.

## Why
- Users need a concrete explanation of why the bundle exists and how gateway runs execute SmartNote workflows.
- Clear expectations reduce confusion about attachments, tool execution, and outcomes.

## Scope
### In scope
- Create `docs/specialized-workflow.md` with diagrams and step-by-step flow.
- Link the new doc from the docs index.
- Capture any key insight in `AGENTS.md`.

### Out of scope
- Behavior changes to SmartNote or gateway runtime.
- UI or CLI changes.

## Dependencies
- Existing SmartNote gateway bundle + tool flows.

## Expected outcomes
- Documentation clearly explains the bundle, the workflow path, and expected outputs.
- Readers understand when and why tools are invoked via the gateway.

## Full Report
- **Summary**: Added a dedicated SmartNote specialized workflow doc with diagrams and step-by-step expectations, then linked it from the docs indexes.
- **Implementation**:
  - Wrote `docs/specialized-workflow.md` explaining the bundle, rationale, flow internals, and expected outcomes.
  - Linked the doc from `docs/README.md` and `smartnote/docs/README.md`.
  - Added AGENTS notes capturing the bundle rationale.
- **Tests**: Not run (not requested).
