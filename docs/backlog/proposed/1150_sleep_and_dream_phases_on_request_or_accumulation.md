# 1150 — Sleep and dream phases happen on request or after enough accumulated information, not on a clock

> Package: AbstractRuntime (identity/life.py sleep windows, night narration), AbstractMemory (dream pass), AbstractGateway (sleep action), AbstractEntity (surface)
> Type: design, deferred
> Created: 2026-11-08
> Priority: low (operator: "we can redesign this, but this is not a priority")
> Labels: entities, sleep, dreams, life-loop

## Operator ruling (2026-11-08 ~05:00)

Asked whether to retire the night voice's 20-hour guard: "makes no sense to me. The entity dreams/sleeps when requested
or indeed after a certain accumulation of information. We can redesign this, but this is not a priority: write or update
a backlog item on recurrent / automated sleep phases." So the guard is NOT retired in the current wave and the
understanding-pass queue (root 1146) must not depend on its removal.

## Current code reality (2026-11-08)

- The life loop opens sleep windows on its own schedule (`identity/life.py` `_sleep_window`, cycle windows, idle naps);
  the dream pass (abstractmemory `consolidation.py`) runs inside them and makes no model call by design.
- The night voice (dream narration) runs at most once per 20 h per entity, a hard-coded guard in `life.py`; and it reads
  `signals` that `dream_pass` never returned (one-line memory fix, part of 1146), so 0 narrations exist in 17 homes.
- The gateway's sleep action (`entities.py` ~2204-2235) runs no narrator.
- Nothing measures "accumulated information" today: no counter of unconsolidated episodes, no activation backlog.

## Proposed design (to discuss, not scheduled)

1. **Two triggers, no clock.** Sleep starts (a) on request: the operator's or a visitor's explicit "rest"/"sleep", the
   gateway sleep action; or (b) on accumulation: when the home's understanding debt (root 1146's `understanding_debt()`:
   unconsolidated episodes, pending ripples, un-narrated dreams) crosses a threshold the Mind setting defines (same
   sensitivity as the ripple), with a floor of wakeful time so a chatty hour does not force a nap.
2. **One sleep = one durable run** (root 1145): the dream pass, the narration and the understanding drain are ledgered
   steps of that run, resumable; the 20 h guard disappears because the trigger is the debt, not the time.
3. **The entity knows why it slept**: the wake cue (runtime draft 0870) says "slept after N new memories" or "slept
   because you asked", and the diary records it.
4. Gateway and app: the sleep action enqueues the same run; AbstractEntity shows debt and the next expected sleep.

## Acceptance (when scheduled)

- [ ] No clock-based sleep remains; a quiet entity never sleeps, a busy one sleeps when its debt crosses the threshold.
- [ ] A requested sleep starts within one tick and is a run with a ledger.
- [ ] The narration exists after each sleep (signals returned, narrator run).
