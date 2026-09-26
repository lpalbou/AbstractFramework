# 0929 — Automations v2: durable external-event inbox, generic `event` source, `run.finished`/`run.failed` chaining

- **Status:** planned (after 0928; the operator asked for this to be PLANNED, not proposed)
- **Created:** 2026-09-26
- **Area:** abstractruntime (triggers/, admission), abstractgateway (`emit_event` admission, reconciliation hooks), abstractflow, apps
- **Design:** untracked/design/automations-PLAN.md §5 and the turn-2/3 admission design in untracked/design/astra/DIALOGUE.md

## Summary
0928 ships the trigger-source registry with `schedule` and `manual`. v2 adds the first EXTERNAL sources so an Automation can be bound to
things that happen: a generic `event` source bound to `{scope, name}` (so Rust/browser apps such as AbstractCode can fire "program built"
through the authenticated `emit_event` command without a Python plugin), and `run.finished` / `run.failed` (watch a named automation's
top-level occurrences; enables chaining "when the news digest finishes, …"). Both need reliable admission: today plain events miss busy
listeners and the gateway mailbox tolerates save races (`runner.py:~2209`); a failure path saves terminal state before appending the
terminal event (`runtime.py:~2688`), so callbacks alone are insufficient.

## Scope
- Runtime-owned durable inbox OUTSIDE run variables, unique on `(automation_id, binding_revision, event_id)`; stable terminal event ids
  derived from the source occurrence and outcome; admission persisted with the reserved occurrence id/index and captured revision before
  work starts; idempotent child creation on that id; the consumption cursor advanced only after the child relationship is durable;
  terminal callbacks accelerate delivery and a paginated reconciliation of watched terminal runs repairs missed callbacks; dedup receipts
  retained after consumption; overflow/refusal and paused-event disposition recorded. Reject self/cyclic chains.
- Sources: `event@1` config `{scope, name, filter?}` (schema-validated equality filters only), `run.finished@1` / `run.failed@1` config
  `{automation_id}`; `finished` = runtime completion, `failed` = runtime failure (never inferred from output fields).
- Gateway: `emit_event` admission into the inbox with principal scoping; `GET /trigger-sources` lists them as available when configured.
- Out of scope: file/email/build/journal connectors (0931), a filter expression language, a universal broker.

## Validation
Crash-point tests around admission, child creation and cursor advance on both stores; duplicate deliveries after restart admit once;
a chain of two automations runs exactly once per upstream occurrence; a paused downstream records the event's disposition.

## Related
0928, 0931; abstractruntime and abstractgateway planned items for v2 (written 2026-09-26).
