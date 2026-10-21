# 1035 — iPhone cycle graph and separate tool call details

> Package: abstractassistant
> Type: bug
> Created: 2026-10-18
> Status: Completed
> Completed: 2026-10-18
> Priority: P1
> Labels: iphone, observability, tools, ux

## Summary

Give the cycle and tool counters different destinations: a recorded agent-cycle graph and
a tool-call collection with inputs, outputs and timing. Keep approval icons amber after
resolution, and tool icons consistently lavender, with failures separately identified.

## Why

Operator IMG_1354 shows approval resolved in mint and both counters opening the same generic
activity list. The operator requests distinctive non-red tool color and useful separate views.

## Current code reality

AnswerActivityButtons uses one showing Bool for cycle/tool actions and one AnswerActivitySheet.
RunActivityItem retains public outputs and timing, but no general tool input or cycle identity.
ActivityEventRow colors every completed kind mint. Existing tool pairing, cursor dedup,
redaction boundaries and stored replay ownership must be preserved.

## Scope

### In scope

- Recorded cycle ownership, graph lanes per agent/run, public model details and auxiliary routing.
- Tool-only collection, bounded redacted inputs/outputs, search, timing and approval context.
- Consistent semantic icon palette, accessible distinctions and native visual validation.
- One existing adversarial reviewer, package/physical checks, normal guarded phone install.

### Out of scope

- Private reasoning, raw provider prompts, fabricated cross-agent graph edges, new endpoints,
  Watch edits, remote agent/tool execution or package publication.

## Acceptance criteria

- [x] Cycle and tool counters open distinct, purpose-built screens.
- [x] Graph shows recorded cycles and their tool/approval context without invented causality.
- [x] Tool calls expose available inputs/outputs safely, including multiple/repeated calls.
- [x] Approval hand stays amber; tool icons lavender; failures remain explicitly identifiable.
- [x] Tests, inspected native screenshots, adversarial review and normal phone install recorded.

## Receipts

- Intake before production edits; baseline iPhone0.6.15(23), related completed1032–1034.
- Existing reviewer tools_astra; UX review skill used for the two distinct user journeys.
- ADR impact: none intended; existing public ledger remains canonical.


## Completion report

Completed 2026-10-18. Cycle and tool counts select different destinations. Cycles shows a
connected graph per recorded agent run, with stable per-run ordinals and expandable public
model details, timings and approval context. Routing/generation sits separately; tools and
approvals without a retained cycle remain visible. Association is explicitly the preceding
reason in the same run, not a fabricated runtime causal link.

Tools opens a searchable collection of individual calls, preserving repeated identities and
call numbers under filtering. Each call expands to recorded input, public output, status,
timing and run/step. Structured arguments hide credential fields recursively and omit private
control fields before formatting; missing/invalid arguments remain unavailable. Inputs and
outputs are bounded with explicit display truncation. Approval icons stay amber even after
resolution; tool icons use lavender across app entry points and activity; failed status is red.

Validation: **228 package tests** passed (152 AssistantKit + 76 client); five new cases cover
parallel runs, repeated IDs, late updates, trimming/ordinals and credential formatting.
**Three native UI tests** passed after fixing a parent accessibility-ID override and a test
race while a disclosure row collapsed. Screenshots inspected directly and by one adversary:
Approved, no material visual/source blocker. Physical saved gateway history: **12 cycles,
four tool calls/inputs, four approvals, zero loading issues**; read-only test passed.
Hosted launch retains an existing AVAudioSession main-thread warning, recorded in evidence.
Normal signed **0.6.16 (24)** installed/launched successfully, without test plugins.

README, architecture, validation index and Assistant llms aggregate updated. No backend/API,
Watch source or Watch product change; no remote tool/media execution. Changes remain
uncommitted. [Logs, screenshots, review and install receipts](../evidence/1035/README.md).

### Insight and follow-up triage

ADR impact: None. This is a client projection over existing public ledger contracts.
History retention and missing legacy fields stay explicit. Credential masking is field-name
based; arbitrary secrets embedded in ordinary command/URL/document text are not detected.
The audio startup diagnostic is pre-existing and outside this activity UI change; evidence
preserves it without claiming a repair. No new urgent backend or release follow-up is needed.
