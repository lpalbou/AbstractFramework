# Backlog: Ledger JSONL Recovery + Write Locking

## Summary
- Make JSONL ledger reads resilient to concatenated records.
- Prevent future JSONL corruption with a write lock around ledger appends.

## Why
- Gateway logs show JSONDecodeError "Extra data" while reading ledger files.
- Corrupted ledger lines crash SSE streams and runner ticks, blocking runs.

## Strategy (options + choice)
- Option A: Fail fast on malformed JSON (current behavior).
  - Reject: breaks streaming and runner on a single bad line.
- Option B: Best-effort parse concatenated JSON with warnings + skip unrecoverable fragments.
  - Accept: keeps gateway online while still surfacing data integrity warnings.
- Option C: Migrate entirely to SQLite.
  - Defer: larger operational change than needed for this incident.

## Scope
- In scope:
  - Robust JSONL parsing that can split concatenated records.
  - File-level append locking to avoid interleaved writes.
  - Explicit warnings tagged with #FALLBACK / #TRUNCATION.
- Out of scope:
  - Storage backend migration.
  - Automatic repair tooling for existing files.

## Dependencies
- None (uses standard library only).

## Expected outcomes
- Ledger streams no longer crash on malformed lines.
- Runner tick no longer fails due to JSONDecodeError on ledger reads.
- Warning logs clearly indicate recovery/truncation events.

## Implementation Report
- Added JSONL line recovery using incremental JSON decoding to handle concatenated records.
- Added file write locking + fsync on ledger append to prevent interleaved writes.
- Emitted explicit #FALLBACK / #TRUNCATION warnings when recovery is required.

## Tests
- `pytest abstractruntime/tests/test_jsonl_ledger_recovery.py -q`

