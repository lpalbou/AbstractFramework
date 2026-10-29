# ADR-0044: The Ledger and Its Replay Are the One Signal Every Client Consumes

- Status: Proposed (for the operator's review)
- Date: 2026-10-29
- Scope: every package that shows or drives work — the gateway's replay view, AbstractRuntime, and every client
  (panel-chat and the web apps, the desktop Assistant, the iPhone and watch apps, the AbstractCode terminal client,
  both gateway consoles)

## Context

A run leaves a ledger: the record of what happened, what is waiting, what was answered, what was produced. Several
clients show the same run. Before AbstractRuntime ADR 0010 (2026-10-27, "One replay of the ledger, many views"), each
client rebuilt the run's facts for itself from raw records, snapshots and its own memory, and they disagreed on the
same run (a delegated child's approval shown as "Running a tool" on one client and "Approval needed" on another; 182
runs shown as "Waiting for you" after they had completed; one execution shown as two steps). ADR 0010 fixed the
runtime side: one replay of the ledger, exposed as a view, many clients reading it; the conformance cases
(`abstractruntime/docs/backlog/planned/0854_replay_view.md`) pin what the view must say.

What ADR 0010 does not say is the framework-wide rule the operator stated on 2026-10-29, after seeing clients still
reach for side channels (a run snapshot here, an automation's own status endpoint there, a client-side timer that
decides a wait is over): the replay is not one source among several; it is the only one. The gateway's replay view is
the contract that the things a person or an entity must see — sessions, automations, waits and gating, events,
results — are surfaced, to every client, the same way. A client that computes its own truth from anything else will
disagree with the others again, exactly as in the incidents above.

AbstractGateway ADR 0001 (AbstractCore access goes through AbstractRuntime facades) is about the gateway's access to
AbstractCore; it does not cover what clients consume. AbstractRuntime ADR 0010 is the runtime-level decision this ADR
builds on; it stays as it is. This ADR is the cross-package rule.

## Decision

1. **One signal.** The shared ledger and its replay are the single signal every client consumes. Sessions,
   automations, waits and gating (approvals, questions, timers), events and results reach a client only through the
   gateway's replay view of the ledger.
2. **The gateway guarantees surfacing.** The gateway's replay view is responsible for surfacing everything that must
   be surfaced, to every client. If a client cannot show something a person needs to act on, the replay view is
   missing it; the fix is in the view, never a client-side reconstruction.
3. **Same signal, each app's own flavour.** Each client decides how to show the signal (a chat card, a Mission Control
   lane, a watch face, a terminal line) and what to show of it. It does not change what the signal says.
4. **A thin client replays and forwards.** A client replays the ledger and forwards the requests of the humans or
   digital entities it serves to the gateway, to start or continue work. It computes no truth of its own from side
   channels: no private status endpoint, no snapshot read beside the replay, no local timer that decides a wait's
   state, no memory of its own that outlives the replay.
5. **Side channels are defects.** A client path that derives run, wait, event or result state from anything other
   than the replay view is a defect against this ADR, filed and fixed as such, even when its output happens to match.

## Consequences

- New client features start by asking "is this in the replay view?"; if not, the view grows first (runtime, then
  gateway), then the client shows it.
- A client's tests assert what it shows for a given replay, not what it computes from records.
- Packages that today expose run or wait state through their own routes (the pattern 1075 removes for notes) bring
  that state into the ledger and the replay view instead.

## Enforcement

- The replay conformance cases (AbstractRuntime backlog 0854; the gateway's replay-view tests): every fact a client
  may show has a conformance case, and a client migration cites the case it relies on.
- A review rule for every client PR: a read of run/wait/event/result state outside the replay view is a blocking
  finding.

## Validation

- The per-client replay migration items (root backlog 1065): each client is done when it reads the replay view only
  and its side channels are deleted, verified on the operator's instance at a stated sha.
- The three incidents in the Context cannot recur: the conformance cases for a delegated child's approval, a timer
  wait without a resume record, and one execution shown once are green on every client.

## Related

- AbstractRuntime ADR 0010 — One replay of the ledger, many views (the runtime-level decision this ADR builds on).
- AbstractGateway ADR 0001 — AbstractCore access goes through AbstractRuntime facades (access, not consumption).
- Root backlog 0993 (one ledger replay, many views), 1065 (per-client replay migrations), 1075 (note routes in the
  gateway).
