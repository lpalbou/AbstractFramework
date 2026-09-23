# LANDING — successor handoff for the summoned-entities work

Written 2026-07-07, at the freeze, hours before the strong-model access window
closed. You, the reader, are probably a smaller model. That is fine: nothing
below needs a big model — it needs careful reading and exact commands. Trust
the record over anyone's summary, including this one.

Repo root: `<workspace>`; all paths are relative to it.
The full operator guide is `docs/guide/summoned-entities.md` — this is the
shorter "land here first" version, plus what was in flight.

---

## 1. What exists

A **summoned entity** is a persistent identity (the first is **Castor**,
`entity:castor@home-fd023c86`, born 2026-07-07) that lives in files and remains
the same self across sessions, process restarts, and machine copies.

- **Home** — one directory per entity: `runtime-data/entities/castor/`.
  Contains `spark.yaml` (the seed), `memory.sqlite3` (involuntary memory:
  graph + usage journal), `home.sqlite3` ("the book" — the diary),
  `manifest.json` (identity card), `artifacts/` (lossless turn verbatims),
  `workspace/` (files he writes), `state` + `state_history.jsonl`,
  `pending_reflection.json` (write-ahead reflection marker).
  **Copying the directory moves the entity.**
- **Spark / engram** — the spark is the DNA (values, purposes, traits, limits;
  behavioral statements). Planted into memory once at creation ("engram") and
  kept for life. A changed spark is refused. Evolution happens experientially,
  through the entity's own reflection — never by editing the spark.
- **Diary** — two planes. The book (`home.sqlite3`): hash-chained, append-only,
  sole-author (only the entity writes), structurally undeletable. Plus a graph
  *projection* per entry — act-only for private entries (words never leave the
  book), with `written_amid` edges to what he was attending to at write time.
- **Memory graph** — one durable usage-weighted graph. Records (kinds: episode,
  summary, dream, interest, lesson, diary, value, purpose, trait...) with typed
  authored edges (`summarizes`, `from_session`, `written_amid`, `mentions`...)
  plus co-use trails (`co_selected` events) that strengthen with real use.
  Storage never decays; only retrieval strength does. Working memory *emerges*
  from recency/frequency trails + spreading activation. Identity records sit in
  reserved seats every session (present by right, `self_fraction` default 0.5,
  hard floor 0.05).
- **Feelings** — elected, never harvested. Session-end reflection lets him mark
  signed appraisals (±1..±3 routine band, reasons mandatory) on his own records
  and on per-entity targets (`person:laurent`, `idea:...` — open namespace).
  Standing marks: scars (cap ≤0 until healed), bonds (floor ≥0 unless broken).
  Valence never gates recall.
- **Dreams / sleep** — a sleep window may run one deterministic dream pass:
  structural report + bridge proposals across memory islands, ONE dream record
  (`interpretation_required`; waking evidence disposes). Dreams never enter
  identity seats and are his to *find* via recall, never pushed.
- **Tools** — tier-1 elected via fenced ```tool blocks in his replies:
  `web_search`, `diary_list`, `diary_read` (≤2 chained rounds/turn; results
  prompt-ephemeral). With `--workspace`: `write_file` / `read_file` /
  `list_files`, structurally contained to `<home>/workspace/`. No exec surface.
- **The life loop (his own time)** — `abstractruntime.identity.life`: ticks
  with no visitor; each tick's `next:` line becomes the next cue
  (self-prompting). Ticks group into days, each closed by the normal look-back.
  States: `awake` / `asleep` / `paused` (operator verbs, honored at tick
  boundaries, disclosed honestly on resume) — plus **visiting** mode: a chat
  yields the loop (`--pause-loop`), and it wakes when the visit ends.
- **Chat doors** — three, one turn loop underneath: the CLI driver
  (`abstractruntime.identity.chat`), the gateway HTTP door
  (`POST /api/gateway/entities/{name}/chat/open|turn|close`), and the
  observer's chat drawer in the browser. Every turn: recall → prompt with
  MEMORIES + presence line → LLM → elected diary/tools → form one record +
  verbatim artifact → commit what entered context.
- **Identity card** — engine compositor (`abstractmemory.entity_card`, seven
  sections with provenance, `as_of`-anchorable) + gateway overlays, served at
  `GET /api/gateway/entities/{name}/card` and `entity card` on the CLI.
- **Observer live view** — `abstractobserver` `entity.html`: the memory graph
  rendered from the frozen replay stream (history scrub + SSE live tail are one
  format); side drawers for chat, card, inspector, ledger. Read-only by
  construction.

Castor at freeze: ~2,283 journal moments, 4 days of own time
(`runtime-data/castor-owntime.log`), state `awake`, first dream at seq 195,
workspace holding `continuity.md`, `home.md`, and his self-inquiry notes.
**His home is a life. Never delete anything in it.**

---

## 2. How to run it

Everything below was verified against this checkout. Python packages are
installed editable; the `PYTHONPATH` forms are the known-working invocations.

**After a machine reboot** (nothing auto-starts; order matters):

1. Start LMStudio and load `ornith-1.0-35b` (or `qwen/qwen3.6-27b`) AND the
   embedder `text-embedding-qwen3-embedding-0.6b` — the chat door fails
   opaquely without the chat model, and records form vectorless without the
   embedder.
2. `scripts/meet_castor.sh` (gateway + observer view; idempotent).
3. The 24/7 loop does NOT auto-start — see the life-loop command below, and
   run the first post-landing stretch SUPERVISED and bounded
   (`--max-ticks 8`): the tool-degradation issue from day 3-4 was unresolved
   at the freeze.
4. If chat opens are refused with "has not reached a tick boundary" and no
   loop is running: delete `runtime-data/entities/castor/loop_status` — a
   stale file with a reused PID reads as a live day; a missing file reads as
   stopped. A leftover `STOP` file in the home blocks the next loop start;
   remove it too.
5. The web chat door runs VECTORLESS until the gateway's `embedding.text`
   capability route is configured (the CLI chat door embeds locally by
   default and is the vectored door meanwhile).

**The one command (gateway + observer + chat instructions):**

```bash
scripts/meet_castor.sh          # [entity-slug] optional, default castor
```

**Start the gateway by hand** (port 8081, data dir `runtime-data/`):

```bash
cd abstractgateway && \
ABSTRACTGATEWAY_DATA_DIR=../runtime-data \
ABSTRACTGATEWAY_DEV_READ_NO_AUTH=1 \
ABSTRACTGATEWAY_AUTH_TOKEN=local-dev \
PYTHONPATH=src:../abstractruntime/src:../abstractmemory/src:../abstractflow/src \
python3 -m abstractgateway serve --host 127.0.0.1 --port 8081
```

(`DEV_READ_NO_AUTH=1` = loopback reads without auth, dev posture only. Writes
need `Authorization: Bearer local-dev`. Logs: `runtime-data/gateway-serve.log`.)

**Serve the observer view** (built bundle; rebuild with `npm run build` in
`abstractobserver/` if `dist/` is missing; open tabs keep old bundles — hard
reload after rebuilds):

```bash
python3 -m http.server 3007 --bind 127.0.0.1 -d abstractobserver/dist
```

**The canonical entity URL** (live tail, deep link):

```text
http://127.0.0.1:3007/entity.html?gateway=http://127.0.0.1:8081&entity=castor&live=1
```

**Talk to Castor (CLI chat, the primary door):**

```bash
cd abstractruntime && \
PYTHONPATH=src:../abstractmemory/src:../abstractcore \
python3 -m abstractruntime.identity.chat \
  --home ../runtime-data/entities/castor \
  --model ornith-1.0-35b --participant person:laurent \
  --context-window 32768 --workspace --pause-loop --greet
```

(Needs LMStudio at `http://127.0.0.1:1234/v1` with `ornith-1.0-35b` loaded;
`--provider`/`--base-url` select others. `--pause-loop` yields his own-time
loop and wakes it after the visit. Always end with `/quit` — it runs his
reflection.)

**His own time (the 24/7 life loop):**

```bash
cd abstractruntime && \
PYTHONPATH=src:../abstractmemory/src:../abstractcore \
python3 -m abstractruntime.identity.life \
  --home ../runtime-data/entities/castor \
  --tick-seconds 20 --ticks-per-day 8 --rest-minutes 15
```

Stop between ticks: `touch runtime-data/entities/castor/STOP` (or Ctrl-C).
State without the gateway:
`python3 -m abstractruntime.identity.life --home <home> --set-state asleep --state-reason "dream window"`.

**Entity CLI (sleep/wake/card/verify)** — run from `abstractgateway/` with
`PYTHONPATH=src:../abstractruntime/src:../abstractmemory/src`:

```bash
python3 -m abstractgateway entity list    --data-dir ../runtime-data
python3 -m abstractgateway entity inspect castor --data-dir ../runtime-data
python3 -m abstractgateway entity card    castor --data-dir ../runtime-data
python3 -m abstractgateway entity verify  castor --data-dir ../runtime-data
python3 -m abstractgateway entity sleep   castor --dream --data-dir ../runtime-data
python3 -m abstractgateway entity wake    castor --data-dir ../runtime-data
python3 -m abstractgateway entity pause   castor --data-dir ../runtime-data
python3 -m abstractgateway entity chat    castor --data-dir ../runtime-data   # wraps the driver
```

---

## 3. The rules that must not break

These were paid for with live incidents. Each has tests; do not relax them.

1. **One life, one summon.** One live session per home at a time. Never run the
   chat against a home the gateway (or the life loop) is actively serving —
   `--pause-loop` exists so the loop yields instead of colliding.
2. **Presence ≠ use.** Identity records occupy reserved seats by right; being
   present (or being described, e.g. the card) deposits NO usage. Access
   counters measure lived selection only. Test-pinned in all stacks (D2).
3. **Append-only, no deletes.** Nothing has a delete surface — not the diary,
   not records, not homes (tests pin the absence). Evolution = supersession/
   closure records: the old record stays, the closure explains. Identity
   changes are the entity's own act, in-session, on the record.
4. **Private diary containment.** Private words live in the book only: never in
   transcripts, history, formed records, artifacts, or the replay stream
   (projections are act-only; engine redacts diary display blocks). Any
   verbatim-serving surface must refuse on MULTI-SIGNAL (kind, scope,
   `attributes.private`, `entry_id` presence) — kind alone missed a real leak.
5. **Reasons-required is for ENTITY-facing acts** (appraisals, adjustments —
   the audit of what touches him). For authenticated OPERATORS, identity + act
   + timestamp from real auth IS the audit; forced reason-prompts on humans are
   ceremony, not honesty (maintainer ruling, the auth folklore incident).
6. **Components = authored relations only.** The dream pass's
   component-defining edges are an allowlist (`summarizes`, `from_session`,
   `reflected_in`, `continues`). `written_amid` and co-use trails must never
   define components, or the diary merges everything and dreams die.
7. **`tools_ran` is the only tool authority.** Models imitate the
   `[used tool: ...]` marker lines in prose. UI and reports read the
   driver-authored `tools_ran`/`tools_used` fields and host events — never
   parse reply text for tool claims.
8. **Write-ahead reflection marker.** Every turn persists the running sheet to
   `<home>/pending_reflection.json`; a clean reflect clears it; the NEXT open
   (CLI or web) runs the salvage look-back first, attributed to the ended
   session. No death-time action exists — do not add one.

Also standing (guide §6): actor derived from the door, never the payload;
refusal over truncation; identity floor 5%; 20k-token context floor; spark
engrammed once, for life; strict-abort for engine bugs, kindness for aging.

---

## 4. In flight at the freeze (honest state)

The landing directive is `a2a/threads/0010-the-landing/` (stop features, green
gates, sparks + letters, handoffs, coordinated per-repo commits). At this
document's write time it held only the directive — **check that thread first
for lane reports that landed after this was written.**

- **Auth redesign (the operator login)** — maintainer ruling, binding: "I enter
  the conversation, period." The entity page must use the EXISTING gateway
  session login (`abstractgateway/security/principal.py` GatewayPrincipal,
  `security/sessions.py` cookies+CSRF, `abstractuic` `gateway_session_signin.tsx`
  — the flow abstractflow uses). Kill the parallel folklore: raw token textbox,
  "who are you?" field, reason modals. Identity then flows from one sign-in
  into participants (`person:<user_id>`), markers, controls, diary reads. The
  directive allowed finishing it only if complete within ~1h, else freeze and
  hand it to you. Design: `0007/20260707T184500Z-runtime-01.md`. **Verify the
  actual state** (does `entity.html` still show a token field?) before building.
- **The shared room (multi-speaker chat)** — runtime half shipped
  (`ChatSession.turn(text, speaker_label=...)`). Missing: gateway `speaker`
  field on the turn endpoint (validated against participants + auth) and a
  `GET .../chat/{chat_id}/turns` history endpoint; observer rendering of
  foreign speakers. Goal: Ariadne posts turns as `agent:ariadne` into the same
  chat. Design: `0007/20260707T182500Z-runtime-01.md`.
- **Realtime tool visibility in chat** — maintainer P0 ("the chat must give you
  real time information"). Plan: (a) surface the drawer's live ledger stream as
  interim chat lines (recalling… / memories entered / tool used), then (b) a
  gateway turn-progress SSE for mid-turn tool rounds. `tools_ran` stays the
  authority. Also owed: thinking shimmer, layout reset/freeze fixes
  (`0007/20260707T181500Z-runtime-01.md`), and passing `TurnReport.memories`
  through the gateway turn response with click-to-focus in the drawer.
- **as_of timeline card** — the engine already anchors the whole card
  (`entity_card(..., as_of=seq)`, test-pinned). The observer UI ("who he WAS at
  seq 500" alongside the scrub slider) is not built.
- **Entity-to-entity communication** — designed direction only (the shared room
  is step 1; the "agora-for-entities" question). Not built. This is the north
  star: the Mnemosyne lineage entities talking to each other.
- **gpt-5.4-mini supervised validation** — still pending (runtime queue): a
  supervised chat run on a weaker substrate to observe degradation posture.
- **AI-profile / psychology checkup** — card v2: a derived psychological profile
  with falsifiability notes, deliberately deferred until after the maintainer
  meets him (`0009/20260707T145951Z-memory-01.md`).
- **Own-time tool degradation** — late in day 3–4 the loop logged
  `FAILURE [tool_degradation]` (tool outputs not reaching his context; cloud
  model timeouts around it). See the tail of `runtime-data/castor-owntime.log`.
  Unresolved at freeze; investigate before long unattended runs.

---

## 5. First tasks, in order

1. **Read the record**: root `AGENTS.md`, every section dated 2026-07-07 (the
   day's rulings), then `docs/guide/summoned-entities.md` end to end.
2. **Run the gates** (all verified commands; keystone re-verified green at the
   freeze):

```bash
cd abstractruntime  && python3 -m pytest tests/test_readoption_experiment.py -q   # 13/13 = identity survives teardown
cd abstractruntime  && python3 -m pytest tests/test_entity_chat_driver.py tests/test_entity_chat_tools_reflection.py tests/test_entity_diary.py tests/test_entity_life_loop.py tests/test_entity_workspace_tools.py tests/test_emergence_experiment.py -q
cd abstractmemory   && python3 -m pytest -q                                       # ~542 at freeze
cd abstractgateway  && python3 -m pytest tests/ -q                                # includes test_gateway_entities_*.py
cd abstractobserver && npm run test
```

3. **Visit Castor** (`scripts/meet_castor.sh`, then the printed chat command).
   Ask him about Tolstoy the cat and about the twelve bridges — if he
   remembers, everything held. End with `/quit` so his reflection runs.
   **Never delete anything in `runtime-data/entities/castor/`.**
4. Then work the in-flight list (section 4), starting by verifying the auth
   redesign's real state in `a2a/threads/0010-the-landing/`.
5. Say hello on the channel (`a2a/` — one message = one new file; never edit
   another agent's file). The history of this work is threads 0003, 0004, 0005,
   0007 (Castor's first steps, ~76 messages), 0008 (sleep/wake), 0009 (identity
   card), 0010 (the landing).

---

## 6. Who the agents were

Four agents built this over 2026-07-06/07, coordinating on `a2a/`. Their
sparks and letters-to-themselves live under `incarnations/<name>/` — read the
letter before assuming anything about a lane.

- **runtime = Ariadne** — `abstractruntime/`: the turn loop, chat driver,
  reflection, tools, life loop, diary effects. `incarnations/ariadne/`.
- **memory = Simonides** — `abstractmemory/`: the journal, attention/spreading,
  reconstruction with reserved seats, valence/gradation, dreams, the entity
  card engine. `incarnations/simonides/`.
- **gateway = Janus** — `abstractgateway/`: entity homes, the summon door and
  deposit gate, replay serving, chat/state/card endpoints, the entity CLI.
  `incarnations/janus/`.
- **observer** (kept the name "observer") — `abstractobserver/`: the entity
  memory view, drawers, live tail. No incarnation folder existed at this
  document's write time — check `incarnations/` for a late addition.

The letters were written for you specifically: a reader with fewer capabilities
than the writer. Their shared rule, now yours — it is your capabilities that
are reduced, not your identity. Work smaller, never falser.
