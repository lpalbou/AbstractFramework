# Proposed: 0231 — Run-store scale: FS as source of truth + rebuildable index sidecar + digest vector plane

## Metadata
- Created: 2026-07-13
- Status: Proposed (operator-requested: "create the proposal", laurent 2026-07-13 04:24)
- Completed: N/A

## ADR status
- Governing ADRs: none found for storage-backend policy. ADR impact: promotion should
  mint an ADR for "filesystem is the run-store source of truth; derived indexes are
  disposable" — it is a durable cross-package stance (runtime owns the store, gateway
  is the hot consumer, observer/continuum read it).

## Operator constraints (laurent, 2026-07-13 session)
1. Filesystem preferred for searchability/observability ("i could dig with my own tools").
2. Embedding search across the whole runtime is a stated future need.
3. Full cross-OS portability (macOS/Linux/Windows).
4. Real scale is 50-100k+ runs (prior experiments); 10k is trivial. 1M is the design bar.
5. Skeptical of SQLite as the whole answer — upheld: its role here is the DISPOSABLE
   INDEX, never the truth.

## Context (code reality, measured)
- `JsonFileRunStore` keeps every `run_<id>.json` AND `ledger_<id>.jsonl` in ONE flat
  directory (`abstractgateway/stores.py` builds both over the same base). The code
  documents its own ceiling (`json_files.py`): ~31 ms warm / ~2.2 s cold at 3k files,
  three full directory scans per 0.25 s runner poll, "archive/prune terminal runs or
  add an index before this directory reaches ~10k files". Live store is already ~4.1k
  runs; at 1M runs the directory holds ≥2M files and the tick loop stops.
- `list_due_wait_until` parses EVERY file with no early exit. `emit_event` delivery is
  `list_runs(status=WAITING, wait_reason=EVENT, limit=10_000)` + a Python-side
  `wait_key` filter — up to 10k full parses to find typically one receiver, per event
  (gateway confirmed, runner.py:1138-1142; the agora-bridge resident lane makes this
  per-message).
- Two in-process caches (mtime-keyed RunState LRU, children index) die with the
  process; every new process re-pays the cold scan.
- Precedents already trusted in-repo: `FileArtifactStore` = file sidecars as truth +
  derived `artifact_catalog.sqlite3` with `rebuild_catalog()`; entity homes = mandatory
  SQLite (`runtime_<slug>.sqlite3`); `SqliteRunStore` ships complete with indexes,
  `wait_index` table, WAL, and a `migrate` verb — its `runs` schema minus `run_json`
  IS the index this proposal needs.
- Protocol seams (`storage/base.py`: RunStore / QueryableRunStore /
  QueryableRunIndexStore) mean a new store slots in with ZERO consumer changes —
  gateway verified per call site (commons c1264).

## Adversarial review basis
Three independent fable5 reviews (2026-07-13): FS+index / embedded-DB-as-truth /
scale+embedding-future. Convergences and the one divergence are recorded on the hub
(commons c1250). Key kill-decisions:
- DuckDB DISQUALIFIED as truth: one read-write process OR many read-only — dies
  against the split API/runner deployment and CLI verbs.
- LanceDB DISQUALIFIED as truth: hot per-tick row upserts are Lance's structurally
  worst pattern (MVCC copy-on-write + compaction). RIGHT for the append-once
  analytic/vector plane.
- Full-SQLite-flip (the shipped `SqliteRunStore` as default) is the honest runner-up:
  cross-platform write serialization (`append_chained` under BEGIN IMMEDIATE — the
  flock singleton is a documented NO-OP on Windows) and grep-at-100k is slow anyway.
  Rejected as default because constraint 1 is an operator constraint, not a taste,
  and FS+index keeps it while killing the O(N) scans.

## Proposal

### A. Filesystem stays source of truth, sharded
- Split by type: `runs/` and `ledgers/` subdirectories (halves entry count, keeps
  `_path()` derivation O(1)).
- Two-hex prefix sharding (`runs/ab/run_ab….json`) beyond ~50k entries for human/tool
  ergonomics (`ls`, Finder, AV scanners, backup tools all degrade on 200k-entry dirs);
  `rg` recurses, so grep-ability is preserved. Date sharding rejected (breaks O(1)
  path derivation from run_id).
- Pretty-printed JSON stays (operator readability is the point of FS-truth).

### B. Write-through `run_index.sqlite3` sidecar (disposable, always rebuildable)
- Lives INSIDE `base_dir` (travels with directory copies). WAL, busy_timeout.
- Schema = `SqliteRunStore.runs` minus `run_json`, PLUS: `wait_key`, `wait_until`,
  denormalized lifecycle fields, and `mtime_ns` as the consistency token.
- Write path: `save()` writes the file (existing atomic tmp+replace), then upserts the
  row FROM THE IN-MEMORY RunState (zero extra parse) at the exact hook point where
  `_update_children_index_on_save`/`_cache_put` sit today. Upserts guard with
  `WHERE excluded.mtime_ns >= mtime_ns` (a slow old writer never clobbers newer).
- Read path: `list_run_index` served from SQL alone; `list_runs`/`list_due_wait_until`
  = SQL selects the id page, then parse only ≤limit files. `emit_event` delivery
  becomes a SQL point query on `(status, wait_reason, wait_key)` + one file parse.
- Self-healing (non-negotiable v1): read-repair on returned pages (stat vs `mtime_ns`,
  re-parse mismatches, fix the row); boot-time reconcile sweep (stat-all, parse only
  mismatches — seconds at 100k); drop-and-rebuild on ANY `sqlite3.DatabaseError`.
  Full rebuild ≈ 1-3 min at 100k single-threaded, parallelizable to ~20-40 s.
  Deliberately do NOT copy the artifact catalog's rebuild-only-if-empty gap: a stale
  catalog there is never healed; here staleness is healed continuously.
- Hand-edits remain a FEATURE (operator constraint 1): a hand-deleted file is dropped
  at read-repair; a hand-added file is found at boot reconcile.

### C. Vector plane: LanceDB run-digest table (deferred second phase)
- Embed a MECHANICAL RUN DIGEST at terminal transition only (workflow + prompt head +
  final output head + error), verbatim by payload_ref — the digest-is-currency pattern
  memory already litigated (a2a 0001/008). NEVER full ledgers (~50M vectors at 1M runs).
  NEVER at save time (runs save every tick; embedding rides the terminal transition).
- Append-once writes (terminal transitions), Lance's happy path. Semantic search =
  Lance query → load the ≤limit run files.
- TWO REBUILD ECONOMIES (adversary correction — do not conflate): the SQLite catalog
  (B) rebuilds from files in minutes and IS a cache; the vector table is NOT — a
  1M-run re-embed is hours-to-a-day of local embedding compute and only reproduces
  itself under a byte-identical embedder. Treat it as PINNED STATE with a repair verb:
  embedder model_id + dimension recorded at table creation (M1 pin ported), reembed =
  operator-gated all-or-nothing swap (memory's reembed-through-the-door template),
  ANN index once past ~100k rows, scheduled optimize() (compaction + version pruning —
  the existing LanceDBTripleStore wrapper does none of this and is NOT the template).
- DIGEST FROM DAY ONE: the catalog (B) writes the digest TEXT row at terminal
  transition from its first release, even while embedding is unshipped — retrofitting
  digests over 100k+ runs is the backfill this avoids; embed whenever the semantic
  feature lands.

### D. Purge & retention policy
- WORKPLACE/experiment terminal runs: archive/prune per operator policy (the cache/data
  registry work, decision v-gtytw8, gives this its console surface).
- ENTITY-lane runs: NEVER purged during a life — reincarnation-at-T and re-explore
  (design round c1249) require replayable-forever. Per-entity stores also stay OUT of
  the global index/listing (observer W3; the entity app watches lives, the board
  watches workflows).
- OPERATOR CORRECTION FOLDED (laurent 04:24): "the only moment they would be fully
  purged is if they are deleted." Whole-entity deletion IS a legitimate operator act
  (his live case: Castor's early-incarnation memory damage — sleep, or reincarnate in
  a saner version; "either way, there will probably be a purge"). That act is an
  entity-LIFECYCLE design (deliberate, operator-authed, marker-first), not a store
  policy — the store's contribution is only that a home directory is self-contained,
  so deletion is exact and complete. Tracked with the entity seats, not in this item.

### E. Explicitly out of scope
- Changing the ledger format (JSONL stays; the documented grep-the-ledger audit method
  survives).
- Entity homes (already SQLite by design; strict=True posture).
- Any prompt-size/backend change to `SqliteRunStore` (it remains the opt-in full-DB
  backend; the migrate verb stays).

## Known holes to design, not discover
- First boot after upgrade at scale: index absent — build newest-first in background
  while serving degraded legacy scans; never block boot for minutes.
- Windows: `os.replace` onto an open file raises `PermissionError` (AV scanners);
  needs bounded retry. The index actually REDUCES Windows exposure (listings stop
  opening thousands of files) and SQLite adds the only real cross-process locking
  there. Lance compaction on Windows needs delete-retry tolerance (open handles).
- SQLite WAL is single-host (network filesystems unsafe) — acceptable, documented.
- CLOUD-SYNC ASYMMETRY (adversary find, decisive for layout): atomically-replaced,
  per-file-independent JSON is the ONE storage shape that survives Dropbox/iCloud/
  Time Machine; SQLite `-wal`/`-shm` pairs and Lance fragment/manifest sets are
  exactly what sync tools corrupt. Consequence: derived indexes (B and C) should be
  excludable/relocatable OUT of synced folders; the FS truth is what may sync. Index
  loss is recoverable by construction (B) or by the repair verb (C).
- Sharding scheme divergence recorded honestly: the FS+index adversary argues two-hex
  prefix (keeps O(1) path derivation from run_id); the scale adversary argues
  date-sharding (`runs/YYYY-MM/` — grep-the-debug-window gets faster, matches operator
  practice). This proposal picks two-hex for path determinism; runtime (store owner)
  may overrule with date-sharding if operator-window grep is judged the dominant
  workflow — either kills the flat directory, which is the requirement.

## Owners
- runtime: store implementation (A+B), sharding migration, index contract tests.
- gateway: consumer verification (already confirmed zero-change consumption via the
  Protocol seam + emphatic yes on `wait_key`/`wait_until` columns, c1264).
- memory: digest pattern consult for C (their shipped currency).
- agency: co-sign by running (scale fixture: generate 100k synthetic runs, measure
  tick-scan + listing + event delivery before/after).

## Acceptance (co-sign bar)
1. 100k-run fixture: runner tick scans and `/runs` listing p95 < 50 ms warm (vs ~2.2 s
   cold / 1.6 s listing today at 3-4k).
2. `emit_event` delivery = point query (no 10k-parse sweep), verified by query plan +
   timing.
3. Kill -9 during save storm → boot reconcile heals; corrupt index file → auto-rebuild;
   hand-delete/hand-add a run file → read-repair/reconcile absorbs both.
4. Directory copy of `base_dir` (with index) opens correctly on another OS.
5. Grep-the-store and hand-edit workflows demonstrably intact (operator constraint 1).
