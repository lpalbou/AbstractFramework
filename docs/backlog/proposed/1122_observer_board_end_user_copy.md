# 1122 — Observer board: end-user copy in plain words (seven findings)

> Package: abstractobserver
> Type: task
> Created: 2026-11-04
> Priority: normal
> Labels: observer, end-user-copy, ux

## Summary

The uxreview personas on Observer #19 found seven places where the Observer shows jargon, abbreviations or raw ids to
the person reading it. They are older than #19 and outside its scope, so they are taken together here. The end-user
copy rule applies: never run ids, never "ledger", never gateway or runtime jargon in an end-user app.

| # | Where | What a reader sees | Why it misleads |
|---|---|---|---|
| 1 | Board → Entities tile | "0 tk" | an abbreviation of tokens; "0" reads as "nothing happened" |
| 2 | Board → Entities tile | "sleep" chip beside "idle · 6m ago" | two state words that look contradictory (phase vs. busy-ness) |
| 3 | Board → Entities tile | "identity changed", "capability map changed" as the moment line | raw event names (de-snaked) presented as sentences |
| 4 | Board → Done card | "completed" pill over "The agent failed before producing a final answer (run 0cefbff3-…)" | success and failure on one card; a sub-run's failure shown without saying it is a sub-run |
| 5 | Board → Done card, Observe run list | raw run ids ("run 0cefbff3-8449-…", "8ea5e8af-6af…") | ids in end-user copy |
| 6 | Observe run list | "(workflow unknown)" with an "unknown" pill for a child run | says nothing the reader can act on |
| 7 | Observe tabs / filters / agent profile | "Ledger", "Terminal", "Runtime allowlist", "no ledger records for this run in what is loaded" | internal vocabulary |

## Why

The three personas (naive, intermediate, expert) each misread these on the review captures. The operator's
end-user-copy rule: no "ledger", run ids or gateway jargon in end-user apps; clean screens; plain words.

## Scope

### In scope

- Rewrite the seven places in plain words built from recorded fields (no text heuristics). For example: the token
  count spelled out, or hidden when there is nothing to count; one state word for an entity; a sentence for each
  moment kind; a Done card that says when a step inside the run failed while the run finished; a readable label in
  place of a run id (ids stay available behind a details or copy action); a child run named by its parent's task.
- The Observe tabs, filters and agent profile labels.

### Out of scope

- New features on the board; the gateway's own messages served verbatim.

## Acceptance criteria

- [ ] None of the seven strings above appears on screen. No run id, "ledger" or runtime/gateway term is visible in
      end-user copy; ids are reachable only through an explicit details or copy action.
- [ ] Each rewritten label is built from recorded fields; a test per row fails if the old string comes back.
- [ ] Screenshots of the board, a Done card with a failed sub-run, the Observe run list and the agent profile, on
      desktop and at 400 px, in a dark and a light theme.
- [ ] A first-time-user (naive persona) review of those screens can say what each tile, card and label means.

## Receipts

- `untracked/release-2026-11-03/q7-observer/copy-followups.md` and `untracked/council-2026-11-02/review-observer-19.md`
  ("Terminology And Meaning Risks"); captures under Q7's `shots/` (root, untracked).
