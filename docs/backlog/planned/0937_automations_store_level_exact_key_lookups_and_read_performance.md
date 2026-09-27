# 0937 — Automations: store-level exact-key ledger lookups, and attention/occurrence reads that do not parse the whole controller ledger

- **Status:** planned
- **Created:** 2026-09-27
- **Area:** abstractruntime (storage, `automations/ledger.py`, `automations/attention.py`, `automations/service.py`); abstractgateway (summary rows call these per automation per poll)
- **Parent:** [0928](../completed/0928_automations_v1_runtime_native_scheduled_and_triggered_tasks.md) (Automations v1, completed, unreleased)
- **Source:** review 45 M2 (`untracked/missions-2026-09-25/REVIEW/45-runtime-r2.md`); MISSIONS follow-up "store-level exact-key lookup"

## Summary
A long-lived automation's reads get slower with its age, because several of them parse the automation's whole
controller ledger. The controller writes about 10 ledger records per occurrence. At 10,000 occurrences (35 days at a
5-minute cadence), review 45 measured:
- `list_attention` about 0.31 s and `automation_records` about 0.33 s, on BOTH stores;
- the JSONL `find_by_idempotency_key` about 0.3 s on EVERY controller decision (SQLite answers with an indexed point
  query in 0 ms);
- `pending_waits` walks every child ever created.

The gateway calls these for each automation on each client poll (the Assistant polls every 60 s while visible), so the
cost multiplies with the number of automations and clients. This item gives the stores an exact-key lookup, and gives
the automation reads bounded costs.

## Why
- The decision protocol reconciles by exact idempotency key before every transition (contracts D). On JSONL, that is a
  full ledger scan per decision: O(age) work on the hot path of a 24/7 object.
- Summaries and attention pages are read on every poll. A cost that grows with history makes the product get slower the
  longer the operator uses it, which is the failure mode that runtime 0047 / 0067 / 0068 exist to prevent.

## Scope
### In scope
- An exact-key lookup method on the ledger store protocol, `find_by_idempotency_key(run_id, key)`, implemented natively:
  - SQLite: the existing index;
  - JSONL: a per-run key → offset index, built lazily and maintained on append;
  - in-memory: a dict.

  `automations/ledger.py:66` then calls it instead of scanning, and wrappers (offloading, observable) delegate to it.
- Prefix and range queries for automation records:
  - SQLite: `idempotency_key LIKE 'automation:completed:<id>:%'`, which is indexed;
  - JSONL: the same key index, filtered by prefix.

  `list_attention` and `list_occurrences` read only the page they return.
- `pending_waits` walks only the current `pending_occurrence` tree, not every child.
- A benchmark test at 10k occurrences on both stores with an explicit budget, for example < 20 ms per summary and
  < 5 ms per decision lookup. It goes RED when a full scan comes back.

### Out of scope
- Ledger pruning or archival: runtime 0058 (proposed), and the systemic track's DO-NOT-BUILD list (no ledger
  auto-pruning).
- The gateway's own caching of summaries.

## Current code reality (2026-09-27, runtime `d02578a`)
- `automations/ledger.py:66` `find_by_idempotency_key`:
  - SQLite probes `find_completed_result` first, then still reads `ledger_store.list(run_id)` on a hit;
  - other stores always read `ledger_store.list(run_id)` in full.
- `automations/ledger.py:100` `automation_records` reads the whole ledger every time.
- `automations/attention.py:216` `pending_waits`; `:256` `list_attention`; `automations/service.py:170`
  `list_occurrences`.
- Fixed already: `latest_occurrence` is one index seek (`e8af087`, review 43 F6).
- Related runtime items: `planned/runtime_systemic_reliability/0047_indexed_idempotency_lookup.md` (the general
  O(ledger) scan per effect step), `0067_durable_write_discipline.md`, `0068_hot_path_store_reads.md`. Do this item
  together with 0047 or as its automation slice. Do not build a second index.

## Acceptance criteria
- [ ] A decision lookup and a summary read are O(page), not O(ledger), on JSONL, SQLite and in-memory, proven by the
  budgeted benchmark test at 10k occurrences.
- [ ] Results are identical to today's full scans on both stores, including after a crash-replay: the existing
  `test_automation_controller_recovery.py` and `test_automation_commands.py` stay green.
- [ ] Deleting the new index maintenance on append turns a test RED.

## Related
Runtime 0047, 0067, 0068; review 45 M2; review 44 job 51 note (`resolve_discussion_root` is O(turns) per discussion turn:
fine at chat scale, revisit here if discussions grow long).
