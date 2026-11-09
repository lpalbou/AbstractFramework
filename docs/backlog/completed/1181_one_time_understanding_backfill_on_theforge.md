# 1181 — One-time backfill: every mechanical episode, session summary and card rewritten, every dream narrated, in the four live homes, on theforge with Qwen 3.8 27B

> Package: AbstractFramework (operator procedure across AbstractMemory's verbs; homes under `runtime/entities/`)
> Type: task
> Status: completed
> Created: 2026-11-07
> Completed: 2026-11-08
> Priority: P1
> Labels: understanding-pass, backfill, memory, seat-entity

## Id note

Drafted as "1137" in `untracked/understanding-pass-2026-11-07/drafts/abstractframework/1137_one_time_understanding_backfill_on_theforge.md`
("re-check the next free id on landing"). Root 1137 is
[the 0.13.1 follow-ups](../planned/1137_follow_ups_after_the_0_13_1_wave.md), so this record takes the free id 1181 (renumbered from 1180 on 2026-11-08: the framework seat's planned 1180 was filed the same minute).
References to "backfill (1137)" in [1146](1146_understanding_pass_summaries_always_computed.md) and in
DESIGN.md mean this item.

## Summary

Run once, sample first, home by home, on the operator's go: rewrite in place (memory 0059, versions kept) every
mechanical episode, session summary and world-model card, and narrate every dream, in nerin, castor, hypnos and
ephemeral, with `qwen/qwen3.8-27b` (Q4_K_M, loaded at 62,464 tokens of context) on the LAN endpoint
`endpoint:compat-theforge-nvidia` (`http://192.168.1.7:1234/v1`), thinking off, prompt cap 56,000 tokens. Usage, ids
and replay stay unchanged; everything can be rolled back with `revert_digest(record_id, 0, expected_version=1)` or
the backups.

## Why

Operator ruling 2026-11-07, rule 5: "One-time backfill of every mechanical summary/card/dream in the live homes using
the theforge-nvidia endpoint with the Qwen 3.8 27B model … context must stay < 140k tokens." Decision 6 (2026-11-08):
castor's 34 `entity-authored` digests (29 with leaked reasoning, every one starting "Thinking Process:") are
backfilled too.

## Planned procedure (draft, 2026-11-07)

Preflight (read-only) → dry run of 10 records per home for operator review → pilot on a scratch copy of hypnos with
HOME isolated → live, one go per home (hypnos → nerin → castor → ephemeral) → rollback path. The draft expected the
runtime drain's CLI (`trigger="backfill"`) and the queue's `enqueue_debt(cause="backfill")`; estimate ≈2,054 calls,
≈4.9M prompt + 0.6M completion tokens, 4.5–7 h serial.

## Scope

### In scope

Episodes (mechanical-v2 / flow), floor session summaries, mechanical cards and formed dreams in the four homes;
castor's 34 `entity-authored` digests.

### Out of scope

Maintenance candidates and dedup groups (review offers, not understanding), model-written reflections, the 13 other
home directories, any change to a tracked file in any repo.

## Acceptance criteria

- [x] Every target listed with its token estimate; 0 tasks over 56k (largest prompt 19.0k tokens).
- [x] Dry-run pairs reviewed by the operator (template v1 → five rulings → v2), measured s/call, thinking absent.
- [x] Pilot on a hypnos copy: usage unchanged, no new replay rows in the six standard families, versions 0 and 1
      present, FTS and vectors consistent, idempotent second run.
- [x] Each live home written with 0 skips; failures listed (none) — see the completion report.
- [x] Final report with calls, tokens, wall time and sample pairs (`untracked/understanding-backfill/report.md`,
      `SAMPLE-for-operator.md`).

## Completion report (2026-11-08)

**What was done.** The Entity owner did not wait for the runtime drain (still paused, [1171](../planned/understanding-pass/1171_understanding_drain_in_turns_and_idle_windows.md)).
Two untracked tools replaced it: `untracked/understanding-backfill/generate.py` (staging only: homes read with
`sqlite3 -readonly`, outputs under `out/`) and `apply.py` (`dry-run` / `apply` / `verify`, writes only through
abstractmemory's verbs `rewrite_digest`, `author_world_model(in_place=True, expected_fingerprint=…)` and
`narrate_dream`, under the home's writer lease, holder `maintenance`, after an embedder preflight at cosine ≥ 0.999 and
a pre-apply backup). Five re-checks per record before each write (record live and same kind, not already applied,
version and digest equal to what the model read, source re-hashed, card still standing with the same fingerprint);
`apply_selftest.py` proves each re-check fails on broken input (71 cases).

**Generation** (`report.md`, 2026-11-08 00:10–01:18 UTC): 2,176 of 2,176 targets, 0 failed, 0 skipped, 0 deferred;
templates in force episode v2, session summary v2, card v2, dream v1 (the v2 changes are the operator's five rulings
on the dry run: lead with what happened, 2–6 sentences, whose lines are whose on cards, skip ephemeral's observation,
single-exchange summaries). Own-time formula openers fell from 135/340 to 9/1,857.

**Throughput.** Full phase 2,148 calls in 68 min of wall time: 31.6 calls/min, 916 prompt tok/s, 66 completion tok/s,
latency median 6.2 s / p90 12.2 s / max 47.7 s, one rejected attempt accepted on retry. Concurrency sweep: **4 in
flight is the best point** — at 5 completion tok/s fell (77.5 → 69.4 on comparable windows) and median latency rose
47%, so 6 was not tried; no window had an error, timeout or busy reply. Totals including the dry run: 2,569 calls,
5.0M prompt + 0.34M completion tokens, about 1.6 h of LAN GPU time against the 4.5–7 h serial estimate; no API cost.

**Live apply** (`apply-runs.jsonl`, `verify/verify-apply-*.json`; 2026-11-08 UTC):

| Home | Run | Episodes | Summaries | Cards | Dreams | Written | Version rows | Verify |
|---|---|---|---|---|---|---|---|---|
| hypnos | `apply-20261108T025827Z` 02:58 | 47 | 0 | 2 | 4 | 53 | 102 | ok, 4/4 recall probes |
| castor | `apply-20261108T025831Z` 02:58 | 444 (incl. the 34 `entity-authored`) | 0 | 0 | 10 | 454 | 898 | ok, 3/3 |
| ephemeral | `apply-20261108T025855Z` 03:00 | 1,159 | 112 | 72 | 66 | 1,409 | 2,752 | one failure: 3/4 recall probes (below) |
| nerin | `apply-20261108T031105Z` 03:11 (fresh dry run first; nerin keeps living) | 207 | 34 | 9 | 10 | 260 | 510 | ok, 4/4 |
| **total** | | **1,857** | **146** | **83** | **90** | **2,176** | **4,262** | |

In every home: `selected_counts_equal` true (usage unchanged), 0 new envelopes in the six standard replay families
(the opt-in `revision` family carries the version rows), `PRAGMA integrity_check` ok, FTS5 integrity ok, diary chains
intact, recall traces unchanged by the probes.

**Backups.** `untracked/understanding-backfill/backups/`: `hypnos-apply-20261108T025827Z.sqlite3` (11 MB),
`castor-apply-20261108T025831Z.sqlite3` (31 MB), `ephemeral-apply-20261108T025855Z.sqlite3` (431 MB),
`nerin-apply-20261108T031105Z.sqlite3` (102 MB), plus the pilot's hypnos backup; each with its `-shm`. Rollback:
`revert_digest(record_id, 0, expected_version=1)` per record, or restore the backup.

**Choices recorded** (APPLY-REPORT "Choices and schema mismatches"): `sources` name a deposited artifact holding the
accepted generation line (no ledger step existed), so each home gained one artifact per record; author id
`endpoint:compat-theforge-nvidia/qwen/qwen3.8-27b`, author kind `capability-model`, cause `backfill`; digest method
`authored-backfill-v1` for episodes and summaries; cards carry the verb's `authored-card-v1` and the apply time as
`understood_at` (no `understood_at` parameter on `author_world_model`); narrations have no version 0.

**Deviation from the draft.** No queue tasks and no runtime drain were used (the drain is paused); provenance points
at deposited artifacts rather than a ledger step (memory ADR 0003 decision 11 prefers a step). ADR impact: none new;
memory ADR 0003 decision 6a (in-place understanding) was amended with 0059.

**Follow-ups** (not covered elsewhere unless linked):

- Recall probe limitation on ephemeral: `ex:episode-724cd50d0402f5f4aa3269eb8a` was not surfaced for its own new
  title ("Resuming the deep search on self-evolving AI systems"); the keyword channel is the v1 token scan over the
  newest candidate window per scope (`#FALLBACK: keyword channel v1 = token scan (FTS5 lands with 0019)`), so an old
  record in a 1,159-episode home can sit past it. A probe limit, not a write failure; abstractmemory 0019 (FTS5
  recall) is the fix.
- `recall_reads.absence_diagnosis` (abstractmemory `recall_reads.py:253`) reads `getattr(a, "embedding")`, a field
  `TripleAssertion` does not have, so it always reports "NO stored vector" — the pilot proved the vectors exist
  (1,024 dimensions, cosine matches). An abstractmemory bug, to file in its backlog.
- Session summary titles were not generated: only episodes got a new `title`; summaries keep their mechanical titles
  (e.g. "session reflection: owntime-…"). The drain's `{title, digest, keywords, change}` schema (1171) covers new
  ones; existing summaries need one more pass or the drain's turn.
- Scratch left in place (rm denied): `dryrun-snapshots/` 541 MB, `pilot/` 40 MB, `backups/` ≈587 MB, `bench/`,
  `verify/`, logs — the operator decides what to keep.

**Validation evidence.** `untracked/understanding-backfill/report.md` (generation, throughput, samples),
`APPLY-REPORT.md` (dry run, pilot, live commands, choices), `apply-runs.jsonl`, `verify/verify-apply-20261108T0258*Z.json`
and `verify-apply-20261108T031105Z.json`, `SAMPLE-for-operator.md`.

## Receipts

- Original planned path: `untracked/understanding-pass-2026-11-07/drafts/abstractframework/1137_one_time_understanding_backfill_on_theforge.md`
  (never filed in the repo); final path: `docs/backlog/completed/1181_one_time_understanding_backfill_on_theforge.md`.
- Parent: [1146](1146_understanding_pass_summaries_always_computed.md); track: [understanding-pass](../planned/understanding-pass/README.md).
