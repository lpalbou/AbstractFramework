# 0938 — `Runtime.start` on duck-typed run stores: refuse, loudly and early, a store that cannot attribute sessions, and say so to hosts

- **Status:** planned
- **Created:** 2026-09-27
- **Area:** abstractruntime (`core/run_attribution.py`, `core/runtime.py`, `storage/base.py`, docs, CHANGELOG)
- **Parent:** [0928](../completed/0928_automations_v1_runtime_native_scheduled_and_triggered_tasks.md)
- **Source:** MISSIONS follow-up "`Runtime.start` refuses session-bearing starts on stores without a run index — document for duck-typed stores"

## Summary
Since Automations v1, `Runtime.start` resolves `session_attribution` for every root start that names a session, so that
a discussion session is always restamped read-only. The built-in stores answer this from their index. A third-party
("duck-typed") run store has two ways to go wrong:
- **It has no run index at all** (no `session_kinds`, no `list_run_index`). The start is refused with
  `SessionAttributionError`. This is correct, but it is a behaviour change for hosts that used to start ordinary chat
  sessions on such a store: they now fail at their first chat turn, not at startup.
- **It has `list_run_index` but its rows do not carry `session_kind` / `role`** (a store written before v1).
  `store_session_kinds` then derives an empty set. `session_attribution` returns None and the start goes through as a
  plain chat, even for a `discussion-session:` id. That fails OPEN: the read-only anchor is skipped. (This is from
  reading `core/run_attribution.py:183-202, 208-231`; confirm it with a test before fixing.)

## Scope
### In scope
- A capability probe, for example `store_supports_session_attribution(store)` next to `store_supports_create_if_absent`
  in `storage/base.py`: true only when the store's index carries the v1 attribution columns.
- A store that cannot attribute is refused when the host starts, or on the first session-bearing start, with one clear
  error naming what is missing. Never a silent plain-chat start.
- A test with a minimal duck-typed store in each shape: no index; an index without `session_kind`; a full index.
- Docs: `docs/automations.md` "Storage guarantees" already describes the no-index refusal (runtime `a7a1fae`). Add the
  second case, and add an "upgrading a custom store" note to the CHANGELOG and the release notes of the release that
  ships v1 ([0941](../completed/0941_automations_v1_release_wave_floors_bumps_and_root_pins.md)).

### Out of scope
- Making third-party stores work without an index: the refusal is the contract (fail closed).

## Current code reality (2026-09-27, runtime `d02578a`)
- `core/runtime.py:1381-1382`: `if session_id and not parent_run_id: vars = self._anchor_discussion_session(...)`.
- `core/run_attribution.py:183` `store_session_kinds`: `session_kinds()` when present; else it derives from
  `list_run_index(session_id=..., limit=1_000_000)` rows; else it raises.
- `storage/base.py:51-63` has the pattern to copy (`store_supports_create_if_absent`, `require_create_if_absent`).
- The runtime CHANGELOG `## Unreleased` mentions the refusal (line ~70). The gateway's stores are built-in, so the
  gateway is unaffected.

## Acceptance criteria
- [ ] A `discussion-session:` start on an index without attribution columns is refused (test RED today if the reading
  above is right).
- [ ] A store without an index fails with a message that names the missing method, at the first start or at the host's
  startup preflight.
- [ ] Docs and CHANGELOG describe both cases and the upgrade path.
