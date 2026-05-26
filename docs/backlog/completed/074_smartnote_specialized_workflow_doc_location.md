# Backlog: SmartNote specialized workflow doc placement

## Summary
Move the specialized workflow explanation into `smartnote/docs/specialized-workflow.md` and link it from SmartNote docs.

## Why
- The SmartNote workflow explanation is SmartNote-specific and belongs in its documentation set.
- Keeps SmartNote users from needing to search the root docs for app-specific guidance.

## Scope
### In scope
- Add `smartnote/docs/specialized-workflow.md` with diagrams and step-by-step outcomes.
- Update `smartnote/docs/README.md` to link the new doc.
- Capture the change in `AGENTS.md`.

### Out of scope
- Workflow behavior changes.
- Gateway API changes.

## Dependencies
- Existing SmartNote gateway bundle + tools.

## Expected outcomes
- SmartNote docs contain the specialized workflow explanation.
- Readers can find the doc from the SmartNote docs index.

## Full Report
- **Summary**: Added the SmartNote-specific specialized workflow doc under `smartnote/docs` and linked it from the SmartNote docs index.
- **Implementation**:
  - Wrote `smartnote/docs/specialized-workflow.md` with bundle rationale, diagrams, and step-by-step expectations.
  - Updated `smartnote/docs/README.md` to link to the new doc.
  - Recorded the doc location in `AGENTS.md`.
- **Tests**: Not run (not requested).
