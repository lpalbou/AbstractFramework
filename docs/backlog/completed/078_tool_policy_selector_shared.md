# Backlog: Tool policy selector + shared thin-client component

## Summary
Fix the AbstractAssistant tools selector and introduce a shared tool policy selector component in AbstractUIC so thin clients can configure allowlists and approval defaults consistently.

## Why
- The current tools button does not surface gateway tools reliably.
- Users need a clean allowlist with default approve/ask behavior (no deny mode).
- Thin clients should share the same UX and policy defaults.

## Scope
### In scope
- Gateway tool discovery fixes and fallback handling in AbstractAssistant.
- Default approve/ask classification for safe vs mutating tools.
- Shared tool policy selector component in AbstractUIC UI kit + documentation.

### Out of scope
- Gateway API changes for tool discovery payloads.
- New runtime approval modes beyond approve/ask.

## Dependencies
- AbstractRuntime tool approval policy defaults.
- AbstractGateway discovery tools endpoint.

## Expected outcomes
- Tools button opens a working selector with allowlist + approve/ask modes.
- Default modes match safe/read-only vs mutating/write tools.
- UI kit exposes a reusable Tool Policy Selector for thin clients.

## Full Report
- **Summary**: Restored a working tools selector in AbstractAssistant with proper safe/ask defaults and added a shared `ToolPolicyEditor` component to AbstractUIC for thin clients.
- **Implementation**:
  - Gateway tool inventory now pulls approval defaults from `ToolApprovalPolicy` and falls back to local default tool specs with `#FALLBACK` messaging when discovery fails (`abstractassistant/ui/qt_bubble.py`).
  - Tool selector copy now clarifies default approve vs ask behavior and can surface fallback notes.
  - Added `ToolPolicyEditor` to `abstractuic/ui-kit` with allowlist controls and approve/ask modes (no deny), plus theme styles and API documentation.
- **Tests**: Not run (not requested).
