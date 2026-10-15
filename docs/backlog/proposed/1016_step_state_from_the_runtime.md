# 1016 — Step state comes from the runtime, not from each client's grouping of ledger records

> Package: abstractruntime, abstractgateway, abstractflow, abstractobserver, abstractuic (panel-chat), abstractcode, abstractassistant
> Type: proposal
> Created: 2026-10-11
> Priority: normal
> Labels: ledger, replay, architecture, multi-client
> Related: 0993 (one ledger replay, many views), 1013 (flow-step records)

## Summary

What a step is, and its status (running, waiting on approval, approved and executed, failed),
should be stated by the runtime and read as-is by every client. Today each client decides which
ledger records form one step, and they had to learn, one by one, that an approved tool call's
execution is a different record. Make the runtime expose a step identity and a current status (in
the records, or in a replay contract shared by all apps, 0993), and remove the client-side
grouping rules.

## Why

Operator, 2026-10-11, approving a client-side fix: "leave a trace in backlog proposed that we may
want something cleaner than this... the state is provided by the runtime and we should only be
reading what's in the runtime. this is possibly linked to the replayable ledger backlog item too,
that we should be sharing across apps."

## The case that exposed it (2026-10-11, run 15dc6e47)

- A tool call that needs approval (`edit_file`, `execute_command`) is written as STARTED then
  WAITING under step A (`tool_approval:<run>:act:<key>` wait). Once approved, the runtime writes
  the execution as COMPLETED under a NEW step B with the SAME idempotency key, plus a `resume`
  record. Step A never gets a terminal record.
- AbstractFlow's agent trace (`src/components/AgentSubrunTracePanel.tsx`) and Observer's run view
  (`src/ui/run_steps.ts` `build_run_steps`) grouped by `step_id`, so every approved call showed
  "WAITING" forever beside a completed copy. 70 approvals in that run, all executed.
- Fixed client-side the same day in both apps (unreleased): tool-call records are grouped by
  idempotency key (`ledgerStepKey` / `ledger_step_key`). Checked against every ledger on the
  operator's gateway: 1,424 keys follow the approval pattern, 2 are replays of one step; none
  groups two different calls.

## Second case: one node execution, several steps (2026-10-11, run b683459f)

An Agent node execution writes `start_subworkflow` (started → waiting), `resume`, then its
structured-output `llm_call`, each under its own step id, with no execution id. The run window
showed each Agent twice with wrong durations (0 ms + 14.5 s for a 37 s run). Fixed client-side the
same day in AbstractFlow (`executionIdFor`, `src/utils/ledgerEvents.ts`, five rules, scanned over
9,476 ledgers: 1,668 duplicate rows removed, none added). The runtime knows the execution: writing
an `execution_id` on every record of one node execution (it would also cover the approved-tool-call
case above) removes the rules from every client.

## Why the client fix is not the end state

- The rule ("tool calls: group by idempotency key") is knowledge of runtime internals copied into
  each client; AbstractCode (web, TUI), panel-chat and the Assistant may need the same rule or
  already carry their own, and they can drift.
- The runtime knows the truth: the wait it created, the resume that answered it, the execution it
  ran. A client should not have to infer it from record shapes.

## Options to discuss

1. **Runtime keeps one step id per effect occurrence**: the post-approval execution reuses step A
   (COMPLETED under A), so `step_id` alone is the identity everywhere. Smallest client impact;
   needs care with the ledger's append-only/hash chain and crash replay.
2. **Runtime states the link**: the post-approval record carries `resumes_step_id: A` (and the
   resume record too), and clients merge on that explicit field.
3. **Shared replay (0993)**: one replay reducer, published for every app, turns records into steps
   with statuses; clients render its output only. This item becomes one of its rules.

## Promotion criteria

An operator choice among the options (or 0993's contract absorbing it), and the list of clients
still grouping records themselves.

## Required adversarial reviews

A design review before code (ledger invariants, hash chain, crash replay, every client's reader)
and an implementation review after, with mutation-checked tests, so the abstraction and
implementation are as clean, simple, robust and efficient as possible.
