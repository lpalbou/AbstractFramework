# 1184 — A visit never fails on a busy entity: no time limit between the click and the open visit

> Package: AbstractRuntime (`identity/life.py`, `identity/chat.py`), AbstractGateway (`entity_visits.py`, `entity_chat.py`, `routes/entities.py`), AbstractEntity (`stream_source.ts`, `chat_drawer.tsx`)
> Type: bug
> Status: completed
> Created: 2026-11-09
> Completed: 2026-11-09
> Priority: P0
> Labels: entities, visit, life-loop, timeouts, adr-0027, review, adversarial-review-required

## Review flag — OPERATOR REVIEW PENDING

Built, tested and reviewed by one adversarial sub-agent (three passes), committed **locally on main, not pushed, not
released**. The operator has not yet checked it. What to review:

1. The behaviour below, on the real app, after a gateway restart (test list under *How to verify*).
2. The three commits: AbstractRuntime `4978eda`, AbstractGateway `81a92233`, AbstractEntity `e07f930`.
3. The locally deployed Entity app **r39b**: it is the live build (`2dbe105`) plus this fix only, NOT AbstractEntity
   main (main carries the phase bar `9ec60aa`, which needs a gateway contract that is not served yet).
4. The choices listed under *Left as is* (each is the operator's call).
5. Whether the operator rule below deserves its own ADR (see *ADR state*).

Until the review passes, treat this record as "built, not accepted".

Note 2026-11-10: the operator tested the live stack on 2026-11-09 evening (restart #10 at 20:03: gateway `2b6722c4`,
runtime `baa401f`): visits waited for the busy entity and the hand-over worked (a second window joined the same
visit; running log `untracked/release-2026-11-07/RESUME.md`, 20:40). The review flag above stays until he says so.

## Summary

On 2026-11-09 the operator clicked visit on the entity aletheia twice while its personal time was running a tick, and
both times the visit was cancelled after 55 seconds and the entity went back to personal time. The cause was a
55-second wait in the gateway's visit doors (then a roll-back and a 409 `loop_busy`), a loop that only looked for a
visitor between ticks (ticks run about 5 minutes on qwen3.8-27b with web searches), and a 90-second client limit in
the Entity app. The fix removes every time limit between the click and the open visit, makes the loop stop starting
new work as soon as a visitor knocks, and keeps the one timeout the operator allows: an open visit with no message for
60 minutes closes itself properly and the entity goes back to what it was doing.

## Why

Operator, 2026-11-09 (verbatim):

- "visit should ALWAYS be available and i should ALWAYS be able to interrupt any other action to visit the entity.
  however, it is ok to let it finish its turn, but within a minute or 2, i should be able to talk with it."
- "a request for visit may never fail. never impose a limited wait, that's a violation of our ADR. it must be a
  deterministic process. so when clicking visit, the only outcome is that visit mode is triggered"
- "when a visit is requested, the only acceptable outcome is to open that visit. there should be no 90s or timeout of
  any kind. the only acceptable timeout is when a visit has been opened for too long without any message, eg 1h. then,
  the entity can close the visit (properly with end visit process) and go back to its previous state (eg if it was
  working, it continue to work; if it was sleeping, it goes back to sleep; if it was on personal time, it goes back to
  personal time)."
- "i only want SMALL clean targeted fixes for this, not a full rewrite" — other agents are redesigning the entity
  state transitions (`untracked/entity-phases-2026-11-08/`); this item is the stop-gap so the operator can always
  talk with an entity.

Incident (UTC, from `runtime/entities/aletheia/state_history.jsonl`, `own_time.log`, `runtime/audit_log.jsonl`):

| UTC | What happened |
|---|---|
| 09:29:14 | Personal day 10 begins (ticks 53–57, about 5 min each) |
| 09:50:42 → 09:51:37 | Visit 1: the door writes the visiting posture, waits 55 s, rolls back to "awake … (visit open aborted: loop did not yield in time)", answers 409 `loop_busy` (55,229 ms) |
| 09:52:22 → 09:53:17 | Visit 2: same (55,373 ms); tick 57 (web_search + fetch_url) ends seconds later |
| 09:54:24 → 09:57:03 | Personal-time stop, honoured at the boundary; the loop exits: "loop ended (stop_command) - idle is sleep (v8)" |
| 09:59:03, 10:07:01 | Two Wake clicks: state file says awake, the app still shows SLEEP (the gateway's `life_state` serves `sleep` whenever no loop runs) |
| 10:18:05 | Visit through the Chat tab's knock opens in 23 ms (no loop running) |

Root causes, in the code at the time:

- AbstractGateway `entity_visits.py` `_preflight`: `await_loop_quiescent(home_dir, timeout_seconds=55.0)`, then
  `_restore_prior_state` + `VisitRefused(409, …, code="loop_busy")`; same in the hosted chat lane
  (`entity_chat.py` `DEFAULT_YIELD_WAIT_S = 55.0`). Untagged, not configurable: breaks root ADR-0027.
- AbstractRuntime `life.py`: the loop checks the state only at the tick boundary ("turn atomicity: never mid-turn");
  a tick is many model and tool calls, then a look-back call.
- AbstractEntity `stream_source.ts`: `openVisit`/`openChat` abort at 90 s, turns at 600 s, closes at 300 s;
  answer/decide/guide at 120 s; `postMention` 600 s; meet open 120 s.

Full investigation: `untracked/entity-visit-2026-11-09/REPORT.md`.

## Scope

### In scope

- Every path from clicking visit (the Chat tab's knock) to an open visit and an answered message: gateway doors,
  the own-time loop, the app's client calls.
- The idle close as the only timeout (already 60 min on the durable lane; verified, unchanged).

### Out of scope

- The entity phase redesign (phase bar, toggles, Stop/Resume, `idle` floor): `untracked/entity-phases-2026-11-08/`
  (TARGET.md, CONTRACT-phases.md v1) and AbstractEntity `9ec60aa`, owned by the agents revisiting the state
  transitions.
- "Stop personal time lands asleep for 6 h" and "Wake shows SLEEP when no loop runs": [1178](1178_stopping_personal_time_leaves_the_entity_awake_and_visitable.md).
- The top-bar visit pill (still disabled in the deployed build; the phase bar makes it a button).
- Releases: nothing published.

## Acceptance criteria

- [x] Clicking visit while personal time runs ends in an open visit, never a refusal or a roll-back (gateway tests).
- [x] The loop starts no new tool, correction call or nudge once a visitor knocks, skips the tick look-back and the
      between-tick pause, closes the day fast on any tick (runtime tests).
- [x] No client time limit on the visit lane in the app (app tests: 12 calls still pending after 3 h of fake time).
- [x] Every new test fails on the old code; every guard pinned by a mutant.
- [x] Adversarial review: three passes, verdict "the three rules are met".
- [ ] Operator review on the real app after a gateway restart (this record's review flag).
- [ ] Release decision (ships with the next AbstractRuntime / AbstractGateway / AbstractEntity cuts).

## Receipts

- Commits (local main, not pushed): AbstractRuntime `4978eda` (main 50 ahead of origin), AbstractGateway `81a92233`
  (92 ahead), AbstractEntity `e07f930` (53 ahead).
- Changelog fragments: `abstractruntime/changelog.d/visitor-at-the-door.md`,
  `abstractgateway/changelog.d/visit-open-never-fails-on-a-busy-loop.md`; AbstractEntity `CHANGELOG.md` [Unreleased].
- App deploy: `abstractentity/untracked/live-ledger/deploy/r39b/abstractframework-entity-0.11.2.tgz` installed into
  `runtime/apps/entity/0.11.2` (previous slot kept at `abstractentity/untracked/live-ledger/deploy/slot-0.11.2-r38-backup`;
  `runtime/apps/state.json` entity integrity `sha512-scVBE8s/…`, installed 2026-11-09T11:11:08Z); :3100 serves
  `assets/index-BDaR1z5p.js`.
- Investigation + fix notes: `untracked/entity-visit-2026-11-09/REPORT.md`.
- Review transcripts: sub-agent scratch under the session scratchpad (`review/probe*`, `mut_*`); not kept in the repo.

## Completion report (2026-11-09)

### What changed

**AbstractRuntime `4978eda`**

- `identity/life.py`: new `visitor_waiting(state)` (asleep + `mode=visiting` or the door's auto-yield reason, the
  same predicate as the tick boundary). The loop sets `session.yield_check` after `open_session()`. The tick
  look-back is skipped while a visitor waits; there is no `tick_seconds` pause before the next boundary; the day
  close sets `visit_yield` from the state too, so a knock on the day's last tick, or on a rest or work-verdict tick,
  gets the fast close (look-back deferred to the next open, the existing B1 path); a rest chosen as the visitor knocks
  is not slept over the visit (`continue` to the gate, which idles on the visit). `await_loop_quiescent` accepts
  `timeout_seconds=None` (no limit) and treats a `day` status that `read_loop_status` does not count as running
  (dead or recycled pid, stale heartbeat) as quiescent.
- `identity/chat.py`: `ChatSession.yield_check` (None by default; only the loop sets it, so visit sessions are
  unchanged). In `turn()`, with a visitor waiting: the reply's newly elected tools do not run (every
  `[used tool: X]` for them becomes `[tool call not run: X - a visitor arrived]`, plus a `#NOTE`); the marker-imitation
  correction, the format-repair nudge, the speak-now guard and the liveness correction do not run (the nudge and the
  liveness skips are noted). A tool batch already running finishes, and its one follow-up call still runs.

**AbstractGateway `81a92233`**

- `entity_visits.py`: the door waits for the loop with no limit (no roll-back, no `loop_busy`) and, while waiting,
  writes its visiting posture back if something replaced it (`hold_visiting_posture`, an `await_loop_quiescent`
  sleep_fn; never over `paused` or another door's posture). A held home makes open, turn, close and tick wait for
  its writer (logged once, naming it) instead of 409 `home_lease_held`; `lease_without_waiting()` keeps the old 409
  for the reaper's sweep (one thread for every home must never stall) and for the operator's own pause/sleep
  teardown. The stale-yield reaper leaves a visiting posture alone while the loop is still in its day or while a
  visit is opening on that home (`_slug_lock(slug).locked()`).
- `entity_chat.py` (the console/Watch lane, `/chat/open`): same no-limit wait, posture hold and lease wait;
  `DEFAULT_YIELD_WAIT_S` and the `yield_wait_s` parameter removed.
- `routes/entities.py`: `POST /state` paused/asleep tears the open visit down inside `lease_without_waiting()`
  (answers at once; a busy home stays labeled `teardown_failed`, as before).
- `docs/entities.md` + `llms-full.txt`: the visit open paragraph says the open waits with no limit; `loop_busy` and
  `home_lease_held` dropped from the documented refusals.

**AbstractEntity `e07f930`**

- `stream_source.ts`: `postJson(…, timeoutMs: number | null)`; `null` = no timer. No client limit on visit
  open/turn/close/tick, chat open/turn/close, guidance, answer, decision, `@mention` (`postMention` default) and meet
  open.
- `chat_drawer.tsx`: the knock note says "Opening — if he is busy with his own time, he finishes what he is doing,
  then the visit opens…" (was "… tick boundary (up to a minute)…").

### Tests

| Repo | New / changed | Related suites | Red without the fix |
|---|---|---|---|
| AbstractRuntime | `tests/test_visitor_at_the_door.py` (11) | 480 passed (identity, loop, lease, look-back, visit files) | 3/4 first-round tests red on HEAD (the fourth is the no-visitor control); 10 mutants (wiring, look-back, last-tick close, rest, tick pause, imitation, speak-now, nudge note, liveness note, all-markers) each turn exactly their test red |
| AbstractGateway | `tests/test_visit_open_waits_for_a_busy_loop.py` (6); `test_gateway_entities_lease.py::test_visit_open_waits_while_home_has_a_writer` and `test_gateway_entities_visits.py::test_turn_waits_while_home_has_a_writer` re-based from "refuses 409" | 519 passed (entity, visit files) | all 6 new + 2 re-based red on HEAD (with the operator's exact 409 texts); posture-hold and reaper-no-wait mutants red |
| AbstractEntity | `src/visit_no_client_limit.test.ts` (12 calls) | 1231 passed, `tsc --noEmit` clean | 12/12 red on the old client |

All gateway tests ran on a hermetic test gateway (conftest isolates HOME and the data dir); the live gateway on :8080
was never touched (audit log checked). The r39b build ran its own 1202 tests + build in a scratch export of `2dbe105`.

### Adversarial review (one sub-agent, Opus; a Fable attempt hit its usage limit)

- Pass 1 found: last-tick/rest/verdict ticks still reflected while the visitor waited, a rest could sleep over the
  visit, correction calls still ran, the 20 s pause, a 409 during a sleep's consolidation pass, a reaper race, the
  app's remaining 120/600 s limits and the "up to a minute" note — all fixed.
- Pass 2 found: the reaper could stall on one held home (one thread for all), pause/sleep would wait for an in-flight
  turn, the door did not hold its posture — all fixed; no deadlock in any new wait.
- Pass 3: no blockers; two one-line hardenings applied (two doors no longer rewrite each other's posture; a nested
  `lease_without_waiting()` restores the previous value). Verdict: the operator's three rules are met.

### How to verify (operator)

1. Restart the gateway (the server-side half is live only after it; the runtime half applies at the next
   personal-time start — no loop runs now). Reload the Entity page (the app on :3100 already serves r39b).
2. Start aletheia's personal time; while a tick runs (a web search), open the **Chat** tab and knock: "Opening — if
   he is busy with his own time, he finishes what he is doing, then the visit opens…", then the visit opens, no
   error, within about one model call (the tick's own log shows `#NOTE a visitor is at the door`).
3. Send a message (answered however long the turn takes); close the visit: personal time resumes by itself.
4. Optional: leave a visit without messages for an hour: it closes itself (60–65 min) and personal time resumes.

### Behaviour changes worth knowing

- Visits, turns and closes now wait for a busy home instead of refusing; nothing on that path times out.
- A visitor's knock cuts the entity's current tick short: the tools that reply asked for do not run (recorded as
  "not run"), and that tick has no look-back of its own (the day's deferred look-back covers it).
- The operator's pause/sleep answers at once as before; the reaper behaves as before toward busy homes.

### Left as is (operator's call)

- An operator Sleep clicked while a visit is still opening does not stop it: the door writes its posture back and the
  visit opens ("a click on visit always wins"). A Pause is respected: the open waits until unpause.
- A rest the entity chose as the visitor knocked is dropped (he does not rest after the visit).
- The console/Watch lane (`/chat/open`) closes after 15 idle minutes (the app lane after 60).
- The command-line `--pause-loop` visit keeps its 900 s limit; meet relay/close keep client limits (20 min / 5 min).
- After a visit, a restored self-chosen sleep is recorded as operator-written and, without a wake time, restarts its
  1 h bound.
- A request waiting on the loop holds a worker thread; a gateway stop may linger until the loop yields.

### Residual risks and drift

- r39b is a deploy from a scratch export (`2dbe105` + this change), not from a commit; the same change is committed on
  AbstractEntity main (`e07f930`) so the next deploy from main carries it.
- The seat missions in each repo's CLAUDE.md still say "AUDIT ONLY: change no tracked file"; this work changed
  tracked files on the operator's direct request (decision gate
  [1177](../proposed/1177_seat_missions_still_say_audit_only_while_builds_are_directed.md)).
- Overview drift fixed in the same pass: the counts note named the backfill record "1180"; it is 1181.

### ADR state

Root ADR-0027 (timeout policy) is the rule this enforces; no ADR was changed. The operator's rule "a visit request
never fails; the only timeout is the idle close" is durable policy and a candidate for its own ADR or an ADR-0027
amendment — left to the operator's review.

### Follow-ups

- [1178](1178_stopping_personal_time_leaves_the_entity_awake_and_visitable.md): Stop → awake and
  visitable; Wake showing SLEEP when no loop runs (still open; the phase contract covers it).
- The phase contract (`untracked/entity-phases-2026-11-08/CONTRACT-phases.md` line 379) still refuses a visit during
  an operator sleep (`entity_asleep`): it conflicts with this rule and should be amended by the agents building it.
- Release: ships with the next AbstractRuntime → AbstractGateway → AbstractEntity cuts; the gateway needs the runtime
  floor that carries `await_loop_quiescent(timeout_seconds=None)` and `ChatSession.yield_check`.
