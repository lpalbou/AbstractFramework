# 1014 — Run window: draw the real execution tree from flow-step records

> Package: abstractflow
> Type: feature
> Created: 2026-10-11
> Priority: normal
> Labels: run-window, observability, visualflow
> Depends on: 1013

## Summary

Build AbstractFlow's run window execution tree from the `abstract.flow_step` records of 1013
(control stack replay) instead of guessing: a Sequence shows each branch it actually ran (a branch
of Set Variable nodes shows them, never "Pending…" once done), a ForEach shows its items as
"Item k/n" groups with their steps inside, If/Else and Set Variable appear as rows, and nesting
follows the real stack. Runs recorded before 1013 keep today's grouping.

## Why

Operator, 2026-10-11 (see 1013): "Pending" on a finished Set Variable branch, the ForEach absent,
loop-body steps at the top level.

## Current code reality (2026-10-11, from the 1013 dry run)

- The tree is built in `src/components/RunFlowModal.tsx` (~3940-4400): `groupSequenceNodes`
  (~4113-4231) anchors on the first Sequence occurrence (~4127) and guesses branch extents
  (~4161-4168); "Pending…" ~6807. With flow-step records this heuristic would cut the last branch to
  one step and never group loop items 2..n, so patching it does not work.
- Ledger records are mapped to events in `src/utils/ledgerEvents.ts` (~242-260), shared by live
  following (`useWebSocket.ts` ~616) and history replay (`Toolbar.tsx` ~661). Loop-progress code
  that expects index/total already exists but receives nothing (`useWebSocket.ts` ~388-397).
- `runHistoryReplay.ts` only filters trace/approval events (unaffected).

## Scope

- `ledgerEvents.ts`: map `abstract.flow_step` to a flow-step event (dedupe on run_id + seq),
  projecting index/total for the existing loop progress.
- A stack-replay tree builder emitting the existing `StepTreeNode { sequenceBranches }` shape
  (loop items as branches "Item k/n"), so the renderer stays mostly as is; Sequence / loop records
  are structure, If/Else and Set Variable records are rows.
- The run spotlight trail (case 2 of 1013, 2026-10-12: ForEach never lit): `useWebSocket.ts` turns
  a flow-step record into the node's `node_start`, so `setExecutingNodeId` / `withTrailStep` see
  ForEach, Set Variables, Add to List Variable and Loop Limit like any other node. The trail code
  itself (`runSpotlight.ts`) needs no change.
- Keep `groupSequenceNodes` for ledgers without flow-step records.
- Tests on recorded ledgers: the 2026-10-11 `assist` shape (Sequence of Set Variables + Planner +
  13-item ForEach + Reviewer + If/Else loop-back), live following and history replay, selection
  and follow-live unchanged, subflow children still nested.

## Required adversarial reviews

Same rule as 1013: an adversarial design review before code (is stack replay the simplest correct
builder? what can go wrong with selection, follow-live, subflow children, very long loops?), an
adversarial implementation review after (on real recorded runs, desktop and phone), and
mutation-checked guard tests, so the abstraction and implementation are as clean, simple, robust
and efficient as possible.

## Acceptance criteria

- [ ] On the `assist` shape the tree reads: On Flow Start → Sequence { Then 0: Set history, Set
      knowledge; Then 1: Planner → ForEach { Item 1/13: Show Message, Task Executor, Sequence {…};
      … } → Reviewer → If/Else (false) → ForEach … }.
- [ ] No "Pending…" for a branch that ran; old runs render exactly as before.
- [ ] Run spotlight: with Task Executor running on item 2, the trail is Show Message → ForEach →
      Add to knowledge (the last three nodes that ran), on the full graph and the execution view.
- [ ] Both adversarial reviews done and findings resolved; suite passes; browser-checked live.

## Receipts

- (to fill)
