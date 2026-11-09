# 1146 — Understanding pass: summaries and metadata are always computed, in the background, with a ripple

> Package: AbstractMemory (verbs, display block), AbstractRuntime (understanding pass, persistent queue, cognition
> profile), AbstractGateway (digest fields served), AbstractEntity (provenance badge; other agent)
> Type: architecture + implementation
> Status: completed
> Created: 2026-11-07
> Completed: 2026-11-10
> Priority: HIGH (operator 2026-11-07/08: "critical"; discuss with the AbstractEntity agent first, they may have started)
> Labels: entities, memory, runtime, summaries

## Operator rulings (2026-11-07 evening, memory note `entity-understanding-pass-2026-11-07`)

- Summaries and metadata must ALWAYS be computed: a queue of understanding tasks, drained when idle, eventual
  consistency; the queue is PERSISTENT (in the runtime, or a higher-level memory-task queue inside abstractmemory).
- A disruptive fact delivered in the present re-interprets earlier memories: reaction (surprise) → ripple through
  connected memories until an activation threshold → consolidation in the sleep/dream phase.
- Per-capability model config (dialogue, semantic extraction, summaries, understanding), defaulting to the entity's mind.
- Backfill everything once (theforge-nvidia endpoint, Qwen 3.8 27B; context < 140k tokens is fine).
- Rewrite IN PLACE (keep record id, history, usage; store previous text + provenance); never mint new records.
- AbstractNote's prompts/shapes port into abstractmemory; its lease queue and library API do not.

## Root cause (report `untracked/summaries-investigation-2026-11-07/root-cause-report.md`)

Every memory node has only a mechanical summary. abstractmemory's verbs exist (`apply_redigestion`,
`author_world_model`) but the runtime never calls them: `apply_redigestion` has no caller; `author_world_model` is
unreachable in personal time (chat.py returns the mechanical close first) and never called by the visit workflow; the
night narrator reads `signals` that `dream_pass` never returns (0 narrations in 17 homes); the gateway serves no
digest / digest_method / authored_by / card target. 0 authored cards anywhere; castor's 29/34 "entity-authored" digests
are leaked model reasoning from a manual pass on 2026-07-13, still live.

## Plan — superseded by the Entity owner's DESIGN.md (≈82.5 h in 15 steps, 2026-11-08)

The authoritative plan is `untracked/understanding-pass-2026-11-07/DESIGN.md` §15 and its drafts; the outline below is
the earlier estimate and stays only as history. Adjustments ruled the same evening: the persistent task queue lives in
**abstractmemory** (a higher-level queue of memory tasks, per home DB) and the runtime drains it (runtime 0869: N tasks
per turn, the rest in idle windows, every call a ledgered LLM_CALL in a durable run, oversize tasks skipped as
`over_context`, never truncated); rewrites are IN PLACE with versions (memory 0059); a cognition profile per capability
in `cognition.yaml` beside `substrate.yaml` with a Mind setting `memories_rebuilt_per_turn` (default 1; runtime 0867,
gateway 1013); a host-wide generation gate so background work never competes with a foreground generation on the same
engine (runtime 0868, decision-gate); the ripple is first-class: the entity's own ```revise``` election triggers it,
the existing spreading-activation threshold spreads it, sleep consolidates it as a "what this changes" note (runtime
0870, memory 0061); `dream_pass` returning its signals is a one-line memory fix; the night voice's 20 h throttle retires
in favour of the queue's budgets. Build order: gateway serve-stored-fields first (3 h, can ship alone) → memory
(signals 0.5 h; versions 9 h; queue 7 h) → runtime (profile 4 h; gate 6 h; drain 10 h; loop hooks 5 h) → gateway routes
7 h → backfill preflight 3 h → entity app 8 h → ripple 12 h → entity strip 2 h → live backfill (hypnos pilot first) →
docs 3 h. Framework owns the runtime and gateway steps; the Entity owner the memory, app and backfill steps.

### Earlier outline (history, ~26 h)

1. **Memory (~8 h, first):** `understanding_debt()` (lists rewrite candidates, mechanical cards, un-narrated dreams);
   additive `narrate_dream()`; `dream_pass` returns its signals; display block adds digest, digest_method, authored_by,
   target, redigested_from, current replacement.
2. **Runtime (~15 h):** `understanding.py`: one model call per item on the home's model (`_narrator_llm`), reasoning
   stripped, short/fenced output rejected, applied through the memory verbs with author + model recorded, bounded per
   window and resumable; a persistent queue; scheduled after the sleep pass under the dream lease, then idle naps and
   cycle windows; spend counted in `loop_spend`; the ripple (spreading activation over connected memories: verify the
   existing attention-window code before writing new); per-capability model config.
3. **Gateway (~3 h, can ship alone):** the verbatim route returns digest, digest_method, authored_by, target/revision/
   source_count and superseded_by; summaries without a verbatim are served as their full text.
4. **App (~3 h, Entity owner):** provenance badge, "understanding as of", graph hover carries the summary.
5. **Backfill once** with the operator's endpoint; cost table in the report (nerin ≈ 0.75 M tokens).

Open point (1 h+): nothing checks whether the GPU/model is idle; a host-wide one-model gate for local engines needs a
decision (GPU lock rule of 2026-09-29).

## Coordination (settled 2026-11-08 ~02:00)

Same split as 1145: framework = runtime (0867–0870) + gateway (1012–1013); Entity owner = abstractmemory (0059–0061),
app (0001–0002), backfill (1137). They have started the app only (25 local commits, operator-tested); no base-package
code yet. Blocked on the operator's 8 decisions (DESIGN.md §16): in-place rewrite accepted (amends ADR 0003)? may a
capability model write in the entity's first person with the badge naming the model? `memories_rebuilt_per_turn`
default 1 / max 5, visits too or loop ticks only? steady-state rebuilds on paid relays or on theforge? build the
generation gate now (6 h) and refuse a second local model in v1? backfill castor's 34 "entity-authored" digests (29 with
leaked reasoning) and keep candidates/dedup groups out? `extraction` has no consumer: disabled or hidden? retire the
night voice's 20 h throttle, and record surprise as a feeling (default: words only)?

## Design change after the operator's answers (2026-11-08 ~04:10)

Decision 3 is settled as "no fixed per-turn count": the memory task queue exposes an activation per task and a
`select_for_window(budget_seconds, sensitivity)` read (the AbstractNote ripple/activation function, sigmoid-like: the
strength of the incoming change decides how far it propagates); the Mind setting becomes a sensitivity plus a hard
safety cap. Decisions 1, 2, 4, 6, 7 answered yes (7: keep `extraction`, point it at theforge, same model); 5 (generation gate): NOT in this release, design first (root 1152; at most a very simple local-only gate); 8 (20 h throttle): NOT retired now, sleep/dream phases redesigned later on request or accumulation (root 1150); both ruled 2026-11-08 ~05:00. Truncation of stored text is an ADR violation (root ADR 0054). The Entity owner started
abstractmemory (0059 versions in place, 0060 queue, 0061 ripple) on its main on 2026-11-08 ~04:10 with the operator's
go; the runtime drain is written against the committed verb signatures they send, never against a guess; the gateway
"serve stored fields" step (gateway draft 1012) is the framework's first step once the operator says go to this seat.

## Related runtime fix (Entity owner's finding, 2026-11-08, not urgent; framework's side)

30 of nerin's 292 record titles arrive from the runtime's mechanical title builder (`identity/digest.py` ~171, the
14-word title of `mechanical_digest_v2`) with Markdown markers left mid-line ("… ### United States HUD's…", an unpaired
"**"), so they render raw everywhere; the app applies no heuristics to model text, by rule. Fix where the title is made:
derive it from the Markdown rendered to plain text (a parser, not a regex on prose) or from the first sentence before
any heading marker; never cut a Markdown line mid-marker. The understanding pass's rewrites replace such titles over time;
this keeps new mechanical titles clean meanwhile. Test: a verbatim whose 14th word sits inside a heading yields a
marker-free title.

## Related runtime fix 2 (Entity owner, operator-ruled 2026-11-08: "if that's the summary, DO NOT TRUNCATE IT")

`abstractruntime/src/abstractruntime/integrations/abstractmemory/identity_support.py:180` stores a diary entry's digest as
`first_line[:120]` when no gist was elected (the comment calls the ≤120-char fallback a ruled act-only ledger contract).
The stored record (e.g. nerin `ex:diary-28c738204d7ca12dce756591b1`, seq 81218) holds 120 chars + "…", the gateway serves
that, and the app cannot show more without a recorded diary-door read. The operator's rule overrides: store the whole
first line (or the elected gist) uncut; the private-plane rules stay as they are. Same family as the title builder above;
existing records are repaired by the understanding pass's rewrite. Test: a diary entry whose first line is 300 chars
stores a 300-char digest.

## Remaining stored cuts on the look-back path (found 2026-11-08 06:10; ADR 0054; runtime, framework's side)

- Interest and lesson TITLES are stored as the first 8 words ("interest: …") in both the look-back and the in-reply lane
  (identity/chat.py); store the whole title line, derive the short form at read time.
- A look-back whose reply has no prose of its own stores a digest that quotes up to three session-sheet moments, each
  cut to 160 characters with a marker; quote them whole or store a reference to the moments.
- Diary drive titles come from the projection writer as "Diary entry (question) — <date>: <text>" cut at 60 chars with
  "…" (so the desk shows a machine title, not the entity's words, until the writer stores whole titles).
- The gateway's `visit_workflow.py` sends its own base system prompt for the visit look-back (no prefix reuse): align
  it with the in-process sessions' prompt when the gateway cut is prepared.

## Acceptance criteria

- [ ] After one night, every episode and summary node of a test home has a model-written digest with `authored_by`.
- [ ] A disruptive present fact re-opens the connected earlier memories (ripple) and the dream consolidates them.
- [ ] Rewrites keep the record id and carry the previous text + provenance.
- [ ] The queue survives a gateway restart (persistent) and resumes.

## Track and pause (2026-11-08 ~15:00)

Paused by operator ruling 2026-11-08 (pause all dev); resume = explicit go. The remaining work is the topic track
[`understanding-pass/`](../planned/understanding-pass/README.md): the drain [1171](../planned/understanding-pass/1171_understanding_drain_in_turns_and_idle_windows.md)
(runtime draft 0869 + the drain parts of gateway draft 1013, planned, state at pause recorded), the ripple
[1172](../proposed/understanding-pass/1172_ripple_revise_election_and_wake_cue.md) and the extraction consumer
[1173](../proposed/understanding-pass/1173_extraction_capability_gets_its_consumer.md) (proposed), and the release
wave [1179](../planned/1179_release_wave_understanding_pass.md). The backfill called "1137" above was done on 2026-11-08 and is
filed as [1181](1181_one_time_understanding_backfill_on_theforge.md) (root 1137 is another item).

## Operator ruling 2026-11-08 17:15 (titles and summaries of every memory type)

"Every memory type should have a clean informative title and summary. This should help (a) the discoverability and
(b) the actionability of such memory." Consequences: a title is asked of the author (the entity's `title:` line, the
capability model's `title` field), never derived by cutting; without one the first complete sentence of the body;
stored whole; the summary (digest) says what the memory is and what one can do with it; folds happen only at display.
Runtime formation sites: abstractframework untracked/titles-2026-11-08/PROPOSAL.md (in work); memory side abstractmemory
20cd1f4; repair of the ~500 already-cut titles: the Entity owner's proposal to the operator.

## Operator ruling 2026-11-09 (missing titles): no fallback

"We shouldn't need a fallback. If it fails, it should add information to a temporary error file in untracked/ so we
know what's failing and how to fix it at the source." The standing rule therefore reads: a title is asked of the author
and stored verbatim; when the author's block carries no usable `title:` line, the record is stored with title null (body
whole) and one JSON line is appended to `<workspace>/untracked/title-failures/<YYYY-MM-DD>.jsonl` (observed_at, entity,
record id, kind, the raw block, prompt template id/version, provider/model, reason: missing | empty | multi_line |
too_long | malformed); when that path cannot be resolved, the same line goes to the loop log with `#TITLE_FAILURE`. No
first-line or first-sentence fallback, no repair heuristic. The apps show "untitled memory · title missing" for null.
Supersedes the first-complete-sentence (9fe88e4) and whole-first-line (14eeb31) fallbacks.

## Operator rulings 2026-11-09 (afternoon): title and summary are mandatory; maintenance repairs them

"The title + summary must ALWAYS exist for any memory; those are mandatory metadata of all memories." At formation the
entity (elected kinds) or the `summaries` capability model (episodes, session summaries, cards, dreams, and any elected
block without a usable title/summary) authors both; never a cut or a placeholder. A failure writes a line to
`untracked/authoring-failures/<date>.jsonl` and stores the record PENDING with a `title.author` / `digest.author` task
(abstractmemory c4ffc45), retried by a small drainer at the loop's tick boundary, at a visit's close and in a gateway idle
sweep. And: "missing titles or summaries are part of the thing that could also be flagged for correction during the
sleep/maintenance phase". Correction the same afternoon: "the metadata of any newly generated memory must be generated
along with the memory; the sleep phase is just to repair any issue that may still be there + all the rest it already
does." So formation is the only normal path; pending exists only after a failed formation step; the sleep pass adds a
bounded repair step among its existing work (leftover pending records, legacy records lacking a title or summary), with
no priority over the rest.

## Completion report (2026-11-10): the authored title and summary part is built; the rest stays with the track

Moved from `planned/1146_understanding_pass_summaries_always_computed.md` to `completed/` by the backlog hygiene pass
of 2026-11-10. The operator rulings above are kept as written; they are the standing rules. What this record closes
is the part the 2026-11-08 17:15 and 2026-11-09 rulings asked for: **every memory carries a title and a summary,
authored with the memory at formation**, a failure leaves the record pending with a task and a failure line (never a
cut, a template or a fallback), and sleep repairs what is left. Built and committed on `main`; not released (ships
with [1179](../planned/1179_release_wave_understanding_pass.md): AbstractMemory 0.5.0, AbstractRuntime 0.19.0,
AbstractGateway 0.21.0).

What is **not** closed here and where it lives: the memory-task drain in turns and idle windows
([1171](../planned/understanding-pass/1171_understanding_drain_in_turns_and_idle_windows.md), planned, paused), the
ripple ([1172](../proposed/understanding-pass/1172_ripple_revise_election_and_wake_cue.md)), the extraction consumer
([1173](../proposed/understanding-pass/1173_extraction_capability_gets_its_consumer.md)), the titles and summaries of
**private** diary entries with audience-aware recall
([1186](../proposed/1186_private_means_private_from_others_not_from_the_owner.md), decision gate; private entries
were left unchanged on 2026-11-09 until the operator rules), and folding or pruning empty memories in sleep
([1185](../proposed/1185_every_interaction_forms_a_memory_and_sleep_may_fold_or_prune_the_empty_ones.md)).

### What was built (commits checked against each repo's log on 2026-11-10)

**AbstractMemory** (`c4ffc45` … `f310865`, then `8235daf`):

- `155bf8f` untitled records (2026-11-09 ruling, no fallback); `c4ffc45` a title and a summary are mandatory, a
  missing one is PENDING with its task; `4f3a77e` memory's own passes form pending, never a mechanical title or
  summary; `11687df` `declare_pending` for stored records never authored; `8ceb511` `rearm_pending` +
  `pending_records`; `39e479e` a formed record and its tasks commit together; `c46b4cd` passes author with the record;
  `71de051` a public diary entry's summary is authored like any record's.
- Codex review 3 fixes: `b403c0d` (one reentrant transaction lock for store and queue), `1cd854e` (a failed formation
  undoes only its own rows), `15ef176` (identical authored words settle a pending field), `f310865` (`sleep_pass(…,
  cancelled=)`: a night stopped in its final stage records no completion).
- `8235daf` (2026-11-09 19:52): `declare_pending` also declares a legacy public diary projection's summary.
- Earlier, from the 2026-11-08 17:15 ruling: `20cd1f4` titles whole, `d4fc7e4` `retitle` with versions, `6e4ca13`
  `rekey_world_model`; underneath, the understanding versions `3fbaf10` (0059) and the persistent task queue `5997b68`
  (0060).

**AbstractRuntime** (`4eefddb` … `432f178`, then `baa401f`, `b6d50d3`):

- `4eefddb` metadata authored with the memory (elected kinds keep the entity's `title:` line; the `summaries`
  capability authors what a block lacks); `bb6d17a` the visit lane forms the episode WITH its authored title and
  summary (new `VISIT_AUTHOR` node, a durable LLM_CALL); `9b3c510` every record a visit close forms carries its
  authored metadata; `7dd32e1` diary records without a template; `1b5fbcc` memory's passes author through the
  `summaries` capability; `cd9ae5c` tick look-back summaries authored; `432f178` public diary summaries authored,
  never a first-line stand-in.
- Failure path and repair: `a8fc341` failure lines say what failed and on which model; `21528d6` re-arm exhausted
  authoring; `7d9b48b` every failed drainer attempt leaves its line; `43e0765` / `7d2419e` / `e597ff5` sleep repair
  declares legacy records (cards, dreams) through memory's `declare_pending`; `baa401f` sleep repair authors a legacy
  public diary entry's summary.
- `b6d50d3` (2026-11-09 22:43, from the operator's live test): an authored summary is never stamped
  `mechanical-v2`, so memory no longer queues it for repair.
- Before these, the stored-cut removals of 2026-11-08 (root ADR 0054): `27beba0`, `79e0379`, `d419ec1`.

**AbstractGateway**: `a749e4e5` (2026-11-09 16:51) the durable visit runtime routes capability-tagged LLM_CALLs to the
summaries model and the idle sweep drains authoring tasks; `58b51667` (17:52, live-test blocker G) structured output
through the shared model client (`response_model` / `response_schema` on the pool and the no-pool path, honest
failure with the exception class and provider/model); `5c2f5db7` (23:26) `cut: true` on records whose words a retired
writer cut when it saved them, derived from the writer stamp. Earlier: the stored understanding served (`1b3832b7`,
2026-11-08).

### Tests and validation

- Three Codex reviews of runtime + memory (`untracked/entity-phases-2026-11-08/review/`); review 3's non-Stop
  findings are fixed by the commits above (`ROADMAP-2026-11-09-2010.md` section B: "Codex 3: non-Stop findings fixed").
  Its Stop findings belong to the Stop fence (1179's refresh), not to this item.
- Hermetic suites at every HEAD, 2026-11-09 19:10–19:46 (`untracked/release-2026-11-07/audit-fable/VERIFY.md`):
  memory 1934 passed / 0 failed, runtime 4775/3, gateway 5177/3; the three real breaks (runtime facade export,
  voice-projection key set, gateway import boundary) were fixed the same evening (runtime `569d929`, `a4e65f7`,
  gateway `2b6722c4`).
- Live: the Entity session's G re-check after restart #8 (2026-11-09 18:30,
  `untracked/finish-plan-2026-11-09/e2e-restart2/G2`) found visit records authored at formation, 7 older records
  drained and zero failure lines after 17:57; the visit path was verified live on hypnos and castor (ROADMAP B).
- The operator's live test (2026-11-09 evening, `untracked/finish-plan-2026-11-09/operator-test/FINDINGS.md`) found
  the `mechanical-v2` stamp on an authored summary (fixed by `b6d50d3`) and `[#TRUNCATION]` from retired writers in a
  user card (gateway `5c2f5db7` + the app's card wording; sleep repair re-authors those records).

### Acceptance (as written above)

- [x] Every new episode and summary node carries a model-written title and summary with its author (formation path);
      legacy records are declared pending and repaired in sleep. Not yet observed over a full night on a test home.
- [ ] A disruptive present fact re-opens the connected earlier memories (ripple) → 1172.
- [x] Rewrites keep the record id and carry the previous text and provenance (memory 0059 `3fbaf10`, `retitle`
      `d4fc7e4`).
- [x] The task queue is persistent per home (memory 0060 `5997b68`) and authoring tasks re-arm (`8ceb511`,
      runtime `21528d6`); no test named in the commits restarts the gateway mid-queue.

### Residual follow-ups

- **Code moved past 1171's text:** a narrower drain now exists and is tracked (runtime `identity/authoring.py`
  `drain_authoring`, called at the loop's tick boundary, at a session's close, inside a sleep's maintenance and by the gateway's idle sweep,
  `a749e4e5`). Reconcile 1171's contract with it before 1171 resumes (note added to 1171).
- The stored-cut list "Remaining stored cuts on the look-back path" above was not re-verified line by line in this
  pass; the 2026-11-08/09 commits named above address that family. Re-check before 1171 resumes.
- Private diary entries → 1186; fold/prune → 1185; ripple → 1172; extraction → 1173.
- ADR state: root ADR 0054 (stored text is never cut) governs; the "title and summary are mandatory, authored with
  the memory, no fallback" rule lives in these rulings and in AbstractMemory's verbs. An ADR in AbstractMemory is the
  right home if a second writer appears.
