# Backlog: Remove root specialized workflow doc

## Summary
Remove the root-level specialized workflow doc and link, keeping SmartNote-specific guidance inside SmartNote docs.

## Why
- The specialized workflow explanation is SmartNote-specific and should live in SmartNote docs only.

## Scope
### In scope
- Delete `docs/specialized-workflow.md`.
- Remove the link from `docs/README.md`.

### Out of scope
- Changes to SmartNote workflow behavior or gateway APIs.

## Dependencies
- SmartNote specialized workflow doc exists under `smartnote/docs/`.

## Expected outcomes
- Root docs no longer contain SmartNote-specific specialized workflow content.

## Full Report
- **Summary**: Removed the root specialized workflow doc and its docs index link.
- **Implementation**:
  - Deleted `docs/specialized-workflow.md`.
  - Removed the link from `docs/README.md`.
- **Tests**: Not run (not requested).
