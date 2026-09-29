# 0993 — One ledger replay, many views (cross-machine, cross-application replayability)

> Package: abstractruntime (ledger, run store), abstractgateway (history bundle, runs/ledger/SSE routes), abstractuic (`@abstractframework/panel-chat`, ui-kit), abstractcode (web + terminal), abstractassistant, abstractobserver, gateway consoles (web + TUI crate)
> Type: investigation + refactor
> Created: 2026-09-30
> Priority: high
> Labels: ledger, replay, architecture, multi-client, durability

## Summary

The run ledger is the record of the run, and every client should derive what it shows (status,
waits and approval gates, tool rows, live replies, activity) from **one replay of that ledger plus
the durable run state**, through one shared reducer. Today each client, and sometimes each code
path inside one client, reconstructs state its own way (live SSE vs. history bundle vs. run
snapshots vs. local memory), so two clients looking at the same run can disagree. Investigate the
current replay paths, specify a single replay contract, and move every client onto it; views may
differ, the replay may not.

## Why

Operator (2026-09-30), after the approval-gate bug: "it feels like we have something not clean in
the architecture... there should be only one unified way to replay the ledger, on top of which we
could have different views, but only one way to replay the ledger." Ruling already in force: one
session pool for all clients; "the run waits for your approval, in every client".

## The incident that exposed it (2026-09-29)

- Gateway default agent `basic-agent@0.0.5`: the turn's root run parks on its agent loop with a
  delegation wait `subworkflow:<child>`; the child run asks for approval of `write_file`
  (`tool_approval` wait).
- The client that started the turn received the child's waiting record live over SSE and showed
  "Approval needed" with Allow / Deny.
- A browser on the gateway machine and a phone opening the same conversation showed "Running a
  tool write_file" and a Steer composer. `WorkflowSessionController.load` (panel-chat
  `src/workflow_runtime.ts`) folded the child's waiting record from the history bundle, then
  replaced it with the root run's own durable wait (the delegation), which is not a question.
- The tool row read "Running" because the waiting record's `effect.payload.tool_calls` was the
  ledger's `$slim` dedup pointer to the STARTED record; the fold did not resolve it.
- Fixed tactically in panel-chat 0.1.20 / AbstractCode web 0.6.2 (delegation waits never displace a
  person-facing wait; durable child waits adopted from `GET /runs/{child}`; resolved waits never
  re-opened; `$slim` payloads folded from the wait's own details). Evidence and tests:
  `abstractuic/panel-chat/scripts/check_approval_sync.mjs` (+ redacted live fixture
  `scripts/fixtures/run_approval_subrun.json`), `abstractcode/web/e2e/approval_sync.spec.ts`
  (two browser contexts; red on 0.1.19, green on 0.1.20). The fix is correct but it is a patch on
  top of several replay paths; the class of bug remains possible elsewhere.

## Current code reality (to verify and extend with file:line during the investigation)

- **Sources of truth a client combines:** the append-only ledger (`GET /ledger`, SSE tail, the
  history bundle's windowed records), run snapshots (`GET /runs/{id}` with `waiting`, status,
  child run ids), and client memory (optimistic state, "granted" sets, live reply buffers).
- **Ordering hazard:** the runtime appends a `resume` record before it saves the run without its
  wait, so a snapshot read in between still says "waiting" (panel-chat now tracks
  `resolvedWaits`).
- **Storage encodings clients must understand:** `$slim` pointers (ledger dedup), windowed
  bundles that can drop a waiting record, child runs discovered only through `subworkflow:` wait
  keys.
- **Clients with their own reconstruction:** panel-chat (AbstractCode web and anything using it),
  the AbstractCode terminal client (Rust), the Assistant (Python/Qt), the Observer, the gateway web
  console and its terminal console (Rust crate), AbstractFlow's run views. Each needs to be
  inventoried: which endpoints it reads, in which order, and how it decides status / gate / tool
  rows.

## Scope

### In scope

1. **Inventory** every replay path (per client and per server endpoint) with file:line; list the
   decisions each one makes (status, current interaction, tool rows, live text, activity) and
   where they can diverge. Include the history bundle builder and SSE hub in the gateway.
2. **Specify one replay contract**: a deterministic reducer `state = replay(ledger records of the
   run tree, durable run snapshots)`, defined once:
   - the run tree (root + children via delegation waits) and which run holds the person-facing
     interaction;
   - precedence rules (ledger record vs. snapshot, resume-before-save ordering);
   - resolution of storage encodings (`$slim`, windows) — ideally resolved server-side so clients
     never see them;
   - idempotence and order independence (live SSE and full replay converge to the same state);
   - the output model views consume (status, interaction, tool activities, messages, activity).
3. **Decide where the reducer lives**: options — (a) server-side projection in the gateway
   (a `GET /runs/{id}/view` or state stream every client renders; clients become thin), (b) one
   shared reducer package (TypeScript for web + a Python/Rust port validated by a shared
   conformance fixture set), (c) both (server projection authoritative, client reducer for live
   latency). Recommend with trade-offs (latency, offline replay, Rust/Qt clients, cost).
4. **Conformance suite**: recorded ledger fixtures (redacted real runs: delegated approvals,
   questions, parallel tool batches, cancellations, reconnects, windowed bundles, cross-client
   resume) with the expected reduced state; every client implementation must pass it in CI.
5. **Migrate** panel-chat, the AbstractCode terminal client, the Assistant, the Observer and the
   gateway consoles onto the contract; delete their private reconstruction logic.
6. **Cross-machine checks**: two or more clients on different machines (and after a gateway
   restart) converge on the same state for the same run, including answering a gate from any
   client.

### Out of scope

- Changing the ledger's append-only semantics or storage format beyond what the contract needs.

## Acceptance criteria

- [ ] Inventory document with every replay path and divergence risk (file:line).
- [ ] Written replay contract (docs/architecture) and a decision on where the reducer lives.
- [ ] Conformance fixture suite, run in CI by every client that renders runs.
- [ ] All clients migrated; the 2026-09-29 scenario and its variants pass in every client
      (web, terminal, Assistant, Observer, consoles), including answering from a second machine.
- [ ] No client reads raw storage encodings (`$slim`, windows) directly, or they are resolved by
      the one shared reducer.

## Validation

Conformance suite in each repo's CI; a multi-client end-to-end (two browsers + terminal client +
Assistant against one hermetic gateway); a manual cross-machine check on the operator's gateway
(Tailscale) after upgrade.
