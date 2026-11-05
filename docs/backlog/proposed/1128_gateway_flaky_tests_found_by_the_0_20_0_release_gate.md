# 1128 — AbstractGateway: four tests that pass or fail by timing or coincidence (found by the 0.20.0 release gate)

> Package: abstractgateway
> Type: bug
> Created: 2026-11-05
> Priority: normal
> Labels: tests, flaky, ci, adr-0050

## Summary

The local release gate of AbstractGateway 0.20.0 (`16f2a1aa` and its re-run on `a86ddab9`, 2026-11-04) failed four
times on tests whose verdict depends on timing, on other threads, on the network, or on a coincidence in a timestamp,
not on the code under test. Each needs a test-only fix that makes it deterministic.

1. **`tests/test_automations_list_order.py::test_the_listing_is_active_by_last_activity_then_paused_and_pausing_moves_a_row`**
   (ci 3.10, shard 2/4; l.163):
   `assert paused_row["status"] == "paused" and paused_row["last_activity_at"] > before_pause[c]` failed with both
   times equal to the microsecond. The listing showed the row paused while its activity time
   (`controller.updated_at`) had not moved yet: the save that flips the status does not stamp the time, a later save
   does. A test fix (wait until the row is paused AND its activity moved, then check the order) is on
   `release/0.20.0` as `a86ddab9`, not on `main` yet. Product question to decide with it: should the save that applies
   `automation.pause` stamp `updated_at` itself, so a paused row never shows its pre-pause activity?
2. **`tests/test_runner_change_token_gate.py::test_benchmark_11500_quiet_runs_probe_under_1ms_and_reads_no_file`**
   (release 3.11; l.92): `assert calls["stat"] <= passes` failed with `202 <= 200`. The test replaces `os.stat` for
   the whole process during 200 probes, so two `stat` calls from another thread of the test process counted against
   the probe. Fix: count only the probing thread's calls (`threading.get_ident()` in the counter).
3. **The perf job** (`.github/workflows/perf.yml`, `timeout-minutes: 15`): the step Install timed out while
   downloading `lancedb` (65.8 MiB). Network, not code. Fix: cache the install (as the other jobs' caches do) or give
   the install its own bound, so a slow download fails as a download, not as the test.
4. **`tests/test_gateway_entities_handle.py::test_address_is_never_identity`** (ci 3.13, shard 1; l.103):
   `assert "8080" not in json.dumps(created.manifest)` failed because the manifest's `created_at` was
   `…3:55:38.248080+00:00`: the microseconds contain "8080". The check greps the whole manifest, which also holds a
   timestamp and a SHA-256. Fix: check the fields that could carry an address (no handle, URL or address field
   equals or embeds the declared `host:port`), not a substring of the whole document.

## Why

ADR 0050: CI fails only by exception, and a test that flaked once is fixed before the next merge. All four turned a
release gate red at random; re-running until green is not a fix.

## Scope

### In scope

- The four test fixes above (test code and the perf workflow's install step), plus the product decision in item 1.

### Out of scope

- Other gateway tests.

## Acceptance criteria

- [ ] Each test is deterministic: a frozen or waited-for clock (1), a counter scoped to the probing thread (2), a
      cached or separately bounded install (3), field-level address checks (4).
- [ ] Each of the four goes red with its rule removed: a paused row whose activity did not move (1), a stat by the
      probe beyond one per pass (2), an address written into the manifest (4).
- [ ] Each passes 5 times in a row on a loaded Mac (beside another test job), recorded in the PR.
- [ ] `a86ddab9` reaches `main`; the `automation.pause` question is answered on the record.

## Receipts

- `untracked/release-2026-11-03/w5-identity/flaky-order-test.md` (root, untracked): the four failures with their
  assertions and the gate runs.
