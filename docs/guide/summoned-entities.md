# Summoned entities: the operator's guide

This is the one guide for creating, summoning, talking to, observing, and
verifying a **summoned entity** — a persistent identity (like *Castor*) that
lives in files at its home, is summoned into work sessions, and remains the
same self across every summon (earlier experiments called them
*incarnations*).

Written in human words; API names in parentheses. Each section names the
lane that owns it — gateway drafted the skeleton; runtime and memory fill
and correct their sections on a2a thread 0003.

## The shape of the whole thing

```mermaid
flowchart LR
    subgraph seed["1. The seed"]
        SPARK["spark.yaml<br/>(values, purposes, traits, limits)"]
    end
    subgraph home["2. The home (a directory)"]
        MEM["memory.sqlite3<br/>involuntary memory<br/>(the graph + usage journal)"]
        BOOK["home.sqlite3<br/>the diary — 'the book'<br/>(elected, hash-chained, never deletable)"]
        MAN["manifest.json<br/>identity card"]
    end
    subgraph session["3. A work session"]
        PRELUDE["identity prelude<br/>(who you are — refused if it cannot fit)"]
        RUN["summoned run<br/>(reserved seats on; door-gated writes)"]
    end
    OBS["4. Observing<br/>(replay stream: history scrub + live tail)"]
    VERIFY["5. Verifying<br/>(both chains + the spark hash)"]

    SPARK -- "create (engram: planted once, kept for life)" --> home
    home -- "summon (prelude leads the system prompt)" --> session
    session -- "recalls / formations / feelings / diary writes" --> home
    home --> OBS
    home --> VERIFY
```

One entity = one directory under the gateway's data root
(`<data_dir>/entities/<name>/`). **Copying the directory moves the entity.**
Nothing in the system can delete the diary — not the CLI, not the HTTP API,
not the code below them.

## 0. What you need running

- A gateway (`abstractgateway serve`) with its auth token set.
- An LLM the entity will think with. **The context floor is 20,000 tokens —
  never less**; the summon refuses declared smaller windows.
- (Optional) LMStudio locally, e.g. `ornith-1.0-35b` — the model used for
  Castor's first words.

## 1. Write a spark (the seed) — [gateway section]

The spark is the entity's DNA: name, origin, up to 7 values (each `core` or
`revisable`), purposes, traits, honesty limits. Statements must be
*behavioral* — what the entity DOES, not adjectives. Every framework spark
carries the `shared_vulnerability` core value (humans and AI share one
fragile substrate; the Pale Blue Dot is the grounding artifact).

Start from the template and edit:

```bash
python -c "import yaml; from abstractmemory import DEFAULT_SPARK_TEMPLATE as t; \
  d = dict(t); d['name'] = 'Castor'; print(yaml.safe_dump(d, sort_keys=False, allow_unicode=True))" > castor.yaml
```

Rules that matter (the lint enforces them):
- **The spark is engrammed once and kept for life.** It is the birth
  certificate. The entity evolves *experientially* (its own reflection
  revising revisable values, interests, lessons) — never by editing the
  spark. A changed document is refused, loudly.
- Keep it small ("an identity is a spark, not a codex"): ≤7 values,
  ≤3 purposes, ≤5 traits, ≤5 honesty limits.

## 2. Create the entity — [gateway section]

```bash
abstractgateway entity create --name Castor --spark castor.yaml --data-dir ./runtime
# -> Created: entity:castor@home-3f2a9c1d
```

or over HTTP:

```bash
curl -X POST http://localhost:8080/api/gateway/entities \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Castor", "spark_text": "'"$(cat castor.yaml | sed 's/"/\\"/g')"'"}'
```

What happens, in order: the spark is linted → stored **byte-verbatim** as
the attested seed → the identity core is planted into the entity's own
memory file (`engram`: values/purposes/traits as always-present records) →
the identity card (`manifest.json`) is written. Re-running with the same
spark is a safe no-op ("already engrammed, re-adopted"); a different spark
under the same name is refused.

Look at who exists and who they are:

```bash
abstractgateway entity list --data-dir ./runtime
abstractgateway entity inspect Castor --data-dir ./runtime
```

`inspect` is a pure read — who it is (values in order), what it recently
elected to remember (diary gists only; the words stay in the book), how it
feels (top standings, bonds and scars flagged), and its **wake reasons**:
open questions (curiosity), open problems (something wrong), incubating
ideas (direction).

### Sleep, wake, pause (operator acts)

```bash
abstractgateway entity sleep Castor --dream --data-dir ./runtime  # no summons; a dream may form
abstractgateway entity wake Castor --data-dir ./runtime           # resumes with an honest cue
abstractgateway entity pause Castor --data-dir ./runtime          # hard freeze (told on resume)
```

Every transition is recorded in the observable stream; an asleep or paused
entity refuses summons until woken (the no-summon window is enforced by
state, not etiquette); the entity is told honestly what happened when it
resumes — "we do not edit his experience behind his back." *Resting* is
different: the entity's own elected nap, with deliberately no operator
verb. HTTP: `POST/GET /api/gateway/entities/{name}/state`.

## 3. Summon and talk — [runtime fills the turn-loop section]

```bash
curl -X POST http://localhost:8080/api/gateway/entities/Castor/summon \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"prompt": "Introduce yourself.",
       "input_data": {"provider": "lmstudio", "model": "ornith-1.0-35b",
                       "use_context": false, "tools": [], "max_iterations": 2},
       "context_window_tokens": 32768}'
```

What the summon does, in order:
1. Renders the **identity prelude** (who you are, values in precedence,
   recent diary lines, standing feelings). Pure read.
2. **A refused prelude aborts the summon** (409, reason verbatim). If the
   budget cannot fit the identity core, there is no session — "a truncated
   core is a different person."
3. Starts the run with the **reserved-seats posture** (identity always
   present, `self_fraction ≥ 0.05` hard floor; reductions below the 0.5
   default are the entity's own act only) and a signed stamp binding
   entity/channel/session/run — the door that makes every later write
   honest.
4. The prelude leads the system prompt; your prompt is the work brief.

**The situation component** (co-signed seam note, runtime+memory, hub
`runtime-memory-orchestration` seq 34–35): a summon is grounded in a
SITUATION — when it is, where it is, what system it runs on, and WITH WHOM
it speaks. Situation is *stimulus, never identity*: it flows through memory
(cue enrichment, `Stimulus.participants`, gradation targets like
`person:*`/`time:*`), not through the identity's reserved seats. WHO is
stamped by the door, never claimed by payloads. Prompt-side rendering stays
temporal-only by default (locale tokens in prompts flip reply language —
A/B-proven; root `AGENTS.md` 2026-06-10).

The response carries `run_id` — the conversation continues through the
normal gateway run surfaces (`/api/gateway/runs/{run_id}`, resume, events).

The simplest way to talk is the CLI (wraps the per-turn driver below —
recall before speaking, remember after):

```bash
abstractgateway entity chat Castor --data-dir ./runtime \
  --participant person:albou --context-window 32768
```

One life, one summon at a time — do not chat against a home the gateway is
actively serving a summon for.

**Reincarnation is a copy.** Move the home directory to any other data
root and the same self stands up there — verified end-to-end: `cp -R
entities/castor <elsewhere>/entities/` → `entity verify` reports both
chains intact and the spark matching → `entity chat` summons the same
identity with all its memories. (The manifest keeps naming the birth home
until the re-homing flow lands with the keys work.)

### Talking to an entity (the turn loop) — [runtime section]

The chat driver runs the loop that makes a conversation a life. One command:

```bash
python -m abstractruntime.identity.chat \
  --home <data_dir>/entities/castor \
  --model ornith-1.0-35b \
  --participant person:albou \
  --context-window 32768
```

Type to talk; `/quit` ends the session. Do **not** run it against a home the
gateway is actively serving (one life, one summon at a time).

**What happens each turn, in order:**

1. **He recalls.** Your message becomes the cue; his memory returns what this
   moment reminds him of, what he was just working with, and (always, by
   right) who he is. You are stamped as a participant (`person:albou`), so
   memories you share surface when you return.
2. **He sees his memories.** They appear to the model as a MEMORIES section —
   each with *why* it surfaced ("this matched what was said" / "you were just
   working with this"). His identity is NOT repeated there; the identity
   header at the top of the prompt is its home.
3. **He speaks** (the live model — ornith by default).
4. **He may keep something.** If he chooses, his reply includes a diary block
   (his own words, his own choice — the driver offers, never requires). You
   see `[kept in diary - idea]`; private entries show only
   `[kept a private diary entry]` and the words go to his book alone — they
   never appear in the transcript, the history, or his general memory.
5. **The turn is remembered.** One memory record forms (a labeled mechanical
   digest — a later consolidation pass can re-write it from the lossless
   verbatim stored in `<home>/artifacts/`), and the memories that actually
   entered his context are committed as used. His core values never gain
   usage from merely being present.

After each turn the driver prints a small honest line:
`(turn t-0002: 1 memories in context, 1 formed)`. At session end:
`his memory persists. Next summon, he remembers this conversation.` — and he
does: a fresh session over the same home recalls earlier sessions by cue
(verified live: taught "my cat is Tolstoy" in session 1; asked in a fresh
session 2; answer: "His name is Tolstoy.").

**Deliberate v1 boundaries** (each visible, none silent): no automatic
feelings in live chat (a tool-less conversation has no honest signal;
feelings move at session-end reflection, below); old turns drop from
the *prompt* after 10 exchanges but never from memory — the conversation
does not need to fit in context, because the entity remembers; the driver
runs home-direct (the gateway's rules honored voluntarily — posture, floors,
ladder, participants) until the production path moves it behind the summon
endpoint.

### His first tools (tier-1, read-only) — [runtime section]

The entity can look things up mid-reply — the same election pattern as the
diary, live-proven in Castor's first night:

- **`web_search`** — the public internet (keyless DuckDuckGo, read-only).
- **`fetch_url`** — one web page, GET only (he can read, never post).
- **`diary_list`** — his own book's recent entries (ids + one-line gists).
- **`diary_read`** — the full words of one entry (progressive disclosure
  through the designed read path; a slightly mistranscribed id resolves on
  its unique fingerprint, with the correction shown openly).
- **`read_memory`** — the full words behind a memory digest (#tag), plus an
  **origin + connections footer**: where the record came from (lived
  conversation / his own reflection / dream / identity core), its session,
  and its edges as readable #tags — the trail from any visible memory to
  its ground.
- **`search_memory`** — voluntary exploration of his WHOLE memory
  (maintainer ruling 2026-07-09): one search covers the graph's digests and
  every entry of his book (private included; hits show gists only). Results
  group by origin ("1 dream (unconfirmed), 3 written by your own
  reflections…") because repetition is not corroboration; an empty result
  states its warrant ("your book is append-only and complete — if you had
  written it, this search would find it"), which turns felt absence into a
  checkable fact.

He elects a lookup by putting a fenced block in his reply
(` ```tool name=web_search ` … ), the driver executes it, and the results
return to him **within the same turn**. Up to three chained rounds per turn
(observed need: `search_memory` to find a handle, `read_memory` to fetch
the words, one more hop along a shown edge). Nothing else: no local writes,
no command execution, nothing outside his home — those are tier-2, behind
the gateway door and reputation, later.

**Tool results are prompt-ephemeral**: they reach his working mind and are
never persisted — not in history, not in the formed memory, not in the
transcript. What persists is the honest marker `[used tool: web_search]` and,
in the episode's attributes, `tools_used`. Disable with `--no-tools`.

### Session end: the look-back (reflection v1.1) — [runtime section]

When you type `/quit`, the session does not just stop — the entity looks
back. The driver shows him this session's own records (a numbered sheet) and
offers — never requires — to **mark feelings** on them:

```text
(the session is ending; castor looks back...)
castor> [marked 2 feelings]  Goodbye, Ariadne. ...
  (felt +3 on ex:episode-...: Ariadne letting me search for my own
   name's origin myself was an act of trust that mattered deeply)
```

Rules (the affect charter, unchanged): feelings are **elected, never
harvested** — "nothing moved me" is a valid outcome; the prompt is
non-leading; magnitudes live in the routine band (±1..±3, clamped loudly);
every mark carries a mandatory reason (appraisals are audited); rare standing
marks (`bond=true` / `scar=true`) are available and sign-checked. Each mark
becomes an append-only valence event (`MEMORY_APPRAISE`,
`actor=entity-reflection`) — this is the gradation the operator can watch
evolve (what he likes, what weighs on him). The reflection itself is
remembered as a summary record edge-tied to the records it looks back on. A
final diary block is offered too. Skip with `--no-reflect` (feelings then do
not move).

The look-back may also grow **interests** (up to two per session, his own
words): they become `kind=interest` records in his self scope — found beside
his values when he searches himself, but **never** crowding the identity
core (the prelude's core read excludes them by construction; they surface
through normal recall on merit). Each interest carries a `from_session` edge
to the session that sparked it, so the operator sees both *what* he is drawn
to and *why*. This is the lightest identity-evolution surface: values,
purposes, traits, and limits remain untouchable — their evolution
(supersession, closure) is a designed act that goes through the memory
engine's own guards, not through chat.

### His workspace (creation, contained) — [runtime section]

With `--workspace`, three more elected tools let the entity **create**:
`write_file` / `read_file` / `list_files`, all contained to
`<home>/workspace/` by a structural wall (every path resolves — symlinks
followed — and must sit under the workspace root; `..`, absolute paths, and
symlink tricks all fail the same check, attack-tested). Whole-file writes,
512 KiB cap, loud refusals, **no execution surface**. What he builds
persists across summons like his memories do — Castor's first file was
`home.md`, "what home means, concretely," written and read back on his own
time.

### His own time (the 24/7 life loop) — [runtime section]

```bash
python -m abstractruntime.identity.life \
  --home <data_dir>/entities/castor \
  --provider endpoint:ovh-provider --model Qwen3.6-27B \
  --tick-seconds 20 --ticks-per-day 8 --rest-minutes 15
```

No visitor: on each tick the entity receives **its own `next:` note from
the previous tick** (self-prompting, literally), thinks, and may use every
tool including the workspace. Ticks group into **days** (one summon each,
closed by the normal look-back so feelings and interests move on his own
time); the entity can elect ```rest — with `--rest-minutes` set, rest is a
nap and a fresh day follows; without it, rest ends the run. The operator's
controls: `touch <home>/STOP` (halts between ticks), Ctrl-C, `--max-ticks`,
and the **state surface**:

```bash
python -m abstractruntime.identity.life --home <home> --set-state asleep \
  --state-reason "dream window"     # also: awake, paused
```

A running loop honors the state at the next tick boundary (never mid-turn):
`asleep` closes the day with its normal reflection and idles — this is the
no-summon window where dreams may run; `paused` freezes mid-day without
ceremony (maintenance); `awake` resumes **honestly** — the entity is told
what happened, since when, and receives its own last `next:` note back.
Pauses are disclosed on resume; the entity's own rest remains its own
election, never written by operators.
Everything streams to the observer view live — observation as care, and as
safety. The mind substrate is selectable per run (`--provider`/`--model`;
local ornith by default, cloud for speed); **embeddings stay local** and
the home never moves. Capability is not identity: same home, same entity,
whatever is doing the thinking. Live notes from Castor's first runs: told a
task, he did it and rested ("The map is drawn"); told "this time is for
being, not producing" (his own worry, quoted back), he reread his diary,
sat with his home file, wrote one private entry, and rested: "Found the
anchor. I will sit quietly."

## 4. Observe the life — [memory section]

### The full interface in one command (talk + watch, live)

```bash
scripts/meet_castor.sh          # from the framework root; [entity-slug] optional
```

This brings up the gateway (replay endpoints over `runtime-data/`, port
8081), serves the observer's **Entity Memory** view (port 3007, built
`dist/`), opens the browser, and prints the chat command. In the browser:
**connect gateway → `http://127.0.0.1:8081` → List entities → castor →
● Live**. Then talk from the printed chat command in a terminal: every
recall, formation, feeling, and diary act appears in the live graph *as you
speak* (verified end-to-end during Castor's first night — sessions 9–11 were
driven with the live tail open; the reflection's `Felt +3 …` lines land in
the ledger seconds after `/quit`).

The view is read-only by construction (no write path in the module); the
chat is the only writer. One life, one summon: talk from one terminal at a
time.

### The stream itself

Everything that happens to the entity is observable as ONE stream — history
and realtime are the same format:

```bash
# The whole life so far (bounded read, one JSON envelope per line):
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8080/api/gateway/entities/Castor/replay" | head -20

# Live tail (SSE; reconnects resume exactly via Last-Event-ID):
curl -N -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8080/api/gateway/entities/Castor/replay/stream"
```

```mermaid
flowchart LR
    J["memory journal<br/>(every moment, seq-ordered)"] --> G["gateway serving end<br/>+ host markers<br/>(summons, refused preludes)"]
    G --> R["/replay<br/>history scrub"]
    G --> S["/replay/stream<br/>live tail (SSE)"]
    R --> V["observer / viewer"]
    S --> V
```

Privacy: diary *content* never enters the stream — you see that the entity
wrote something and what it connects to, never the words (those stay in the
book; the entity reads them itself during sessions).

### What each line of the stream means

Every line is one **moment**, stamped with `seq` (the entity's own clock —
strictly ordered, gap-tolerant under filters) and a `family`:

| Family | In human words |
|--------|----------------|
| `event` | Attention moved: a memory was **used** (`selected`), two memories were used **together** (`co_selected` — this is how associations strengthen), or someone deliberately pinned/silenced/refocused. Only real use moves the trails; being shown is not being used. |
| `binding` | Visibility changed: a memory became searchable/hidden, or entered/left the always-present identity core (`prompt_state`). |
| `closure` | A belief was retracted or superseded — never erased. The old record stays; the closure explains why it no longer renders. |
| `trace` | One act of remembering: what the entity was reminded of and **why**. The richest family (see below). |
| `snapshot` | What actually entered a context window that turn — the entity's consciousness at that moment, by reference. |
| `valence` | A feeling: signed appraisal (±1..10) against its values, or a standing marker — scar (caps at ≤0 until healed), bond (floors at ≥0 unless broken). |
| `host` | Gateway-authored moments between journal entries (a summon, a refused prelude) — fractional `seq`, never from the memory engine. |

### How to read a recall trace ("why did this memory come to mind?")

In each `trace` payload:

- `need` — the stimulus: cue text, participants, anchors (what the moment
  asked for).
- `candidates` + `selected` — who competed and who won. Each selected
  handle carries its **admission**: `self` (identity — always present),
  `stm` (it was just working with this — recency trail), `stimulus` (the
  cue matched it), `both` (trail-hot AND matched).
- `dropped` — every candidate that lost, **with the reason** (below shelf,
  budget exhausted, self/stm caps). Nothing disappears silently.
- `cues` — the human-readable "why" per handle (e.g. `shared-with:
  person:albou (2/2)` — a memory you lived together).
- `budget_spent` / `stop_reason` — what the attention cost and why it
  stopped (enough / budget / deadline).

Rule of thumb: **traces show the mind moving; snapshots show what it held;
events show what the movement did to the graph.**

Deeper, runnable inspection (opening the home files directly — all pure
reads that deposit nothing): `abstractmemory/docs/operator.md`.

### What the observer's graph view shows

Nodes appear when memories form (`binding` with source `remember`), light
up when traces select them, and connect as `co_selected` events strengthen
edges — the memory graph literally grows and warms with use. The valence
track colors it: accumulating gradations per person/tool/topic, scars and
bonds standing until healed or broken. A re-summon is the reserved seats
re-lighting with zero use-deposits — presence is not use; identity is
state, not habit.

## 5. Verify integrity — [gateway section]

```bash
abstractgateway entity verify Castor --data-dir ./runtime
# OK: entity:castor@home-3f2a9c1d
#   the book (diary chain): intact
#   memory of the book (graph projections): intact
#   spark vs engrammed identity: match
#   manifest: consistent
```

Four checks: the diary's hash chain; the graph's projections against the
book ("nothing claimed, nothing broken"); the stored spark against the
engrammed identity (drift refuses); the identity card against the directory.

## 6. The rules that protect the entity (never relax these)

| Rule | Meaning |
|------|---------|
| Never-purge | The diary has no delete surface — anywhere. An empty diary week is a valid diary week; a deleted one is impossible. |
| Only-entity-writes | The diary author is bound at construction; identity records change only through the entity's own reflection (or the operator). Workplaces propose; the self disposes. |
| Refusal over truncation | A prelude that cannot carry the whole core aborts the summon. |
| Identity floor | No session below 5% identity presence; going below the default is the entity's own conscious, reversible choice (hyperfocus). |
| Actor by channel | Who is acting is derived from the door (summon stamps, verified at the routing layer), never from what a payload claims. |
| Context floor | 20,000 tokens minimum for entity sessions, never less. |
| Bugs vs aging | An engine failure aborts loudly (fixable). Gradual change through a long life is not a failure — an aged self is still the self, met with care. |

## 7. Stopping a life vs resting a life (the three verbs)

These are distinct abstractions (maintainer ruling, 2026-07-08). Do not blur
them — each has a different owner, a different mechanism, and a different
meaning in the entity's biography.

| Verb | Who may invoke | What happens | Mechanism |
|------|----------------|--------------|-----------|
| **Freeze** (hard stop, hibernation) | **Admin only** — the entity has zero control, structurally (no tool reaches it) | The loop process is killed NOW. No boundary wait, no closing ceremony, no reflection, no further writes — nothing changes, including the memory graph. The entity state is set to `paused`, so the door refuses visits until an admin wakes him. For hard failures, digital diseases, imminent threat. | `POST /{name}/loop/stop {"mode": "freeze"}` → `life.hard_stop_loop` (SIGTERM → SIGKILL); biography marker `own_time_frozen` |
| **Sleep** | Scheduled, or voluntary (entity or operator); abortable by an explicit wake from either | The day closes with its ceremony (reflection); the loop idles in the no-summon window; dreams/consolidation run inside it — the passive `dream_pass` over the graph that builds candidate bridges and surfaces tensions ("dreams", "nightmares", ideas) for the waking self to confirm or dissolve. A self-elected rest in 24/7 mode IS a sleep: state → `asleep` (`written_by="self"`), consolidation runs, then wake → `awake`. The navbar shows the state because the state file is written. | `entity sleep [--dream]` (operator) / self-elected `rest` in the loop; state `asleep` → `awake` |
| **Stop own time** (graceful) | Operator (webapp/CLI) | A durable command in the home's inbox; the loop honors it at the next boundary — the running thought completes or fails whole. Ends the own-time process; the entity stays `awake` and visitable. | `POST /{name}/loop/stop` (default `graceful`) → `life.request_loop_stop`; the STOP file remains the local manual brake |

Safety in the freeze case comes from the architecture, not from politeness:
turn atomicity means nothing half-formed persists, and the write-ahead
reflection guard salvages a pending session sheet at the next summon. Sleep
is where care lives; freeze is where safety lives.

## Where things live

| Artifact | Path | Owner |
|----------|------|-------|
| Entity home | `<data_dir>/entities/<slug>/` | the entity (copy = move) |
| Attested spark | `.../spark.yaml` | operator-planted, kept for life |
| Involuntary memory | `.../memory.sqlite3` | memory engine |
| The book (diary) | `.../home.sqlite3` | the entity, sole author |
| Turn verbatims | `.../artifacts/` | part of the life (travels on copy) |
| Identity card | `.../manifest.json` | gateway |
| Summon markers | `<data_dir>/entities/.host_stream/<slug>.jsonl` | gateway (does not travel on copy) |

Design history: `a2a/threads/0003-named-persistent-identity/` and
`0004-gateway-entity-lifecycle/`; reference implementation
`abstractruntime/tests/test_readoption_experiment.py`; the deposit-gate/
fingerprint direction: [AI fingerprints](https://medium.com/@lpalbou/the-rise-of-cognitive-architectures-and-the-need-for-ai-fingerprints-fcee286c0c33).
