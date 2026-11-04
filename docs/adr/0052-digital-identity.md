# ADR 0052: Digital Identity — One Record per Entity, a Recorded Default, a Derived Track Record and Reputation, Everything Reached by Reference

Status: Proposed (2026-11-04; the operator accepts it). Architect draft v2, after the operator's rulings of
2026-11-04 ~03:00. Operator design of 2026-11-04:
"a digital identity = a selected avatar + a selected voice … preserved at the runtime level … any app would know which
avatar/voice to surface for each entity … a dialogue between entities, recognizing who is speaking"; "the number of
sessions, number of successes, number of failures and number of tokens … nb of successes and failures is important,
so is the concept of REPUTATION score: how much do we trust an agent/entity for a task, based on past experiences";
"we don't need to wire it to everything yet, but the model must be right". Grounded in the operator's article
("The Rise of Cognitive Architectures and the Need for AI Fingerprints"): an Operational Identity (the badge and the
audit trail) that lets us log who did what, "a quality assessment of the work", and "over time … reputation scoring —
identifying which Cognitive Architectures and Psychological Identities are consistently more trustworthy or thorough,
and why"; "self-evolving persistent AIs — entities developing skills, goals and identity, with a history of successes
and failures". Identity (who) stays separate from activity (what it is doing now; backlog 1083, ADR 0044).

## Context

The tree keeps two per-entity presentation files with different contracts (`voice.yaml`: full triple, degrades to the
gateway default, marker outside the home; `appearance.json`: colour and Watch shape, no marker) and no per-entity
avatar design. Meets stamp `speaker` on each exchange. abstractavatar 0.1.1 has 44 string-keyed designs and a frozen
descriptor v1. The runtime records, for every run, a status (`running|waiting|completed|failed|cancelled`), a
`workflow_id`, a `session_id`, an origin (`_meta.origin.kind` person|trigger|agent|system), an attribution role, and,
on the ledger, every `llm_call`'s `result.usage` tokens; automations record per-occurrence `completed|failed|cancelled`;
entity tasks are `pending|taken|done|parked`; a work order ends with a `done:` or `blocked:` verdict. `ActorFingerprint`
(v0.1) is a deterministic hash id used only by abstractagent. The agora hub's reputation is per-message ±1 ratings
collapsed per colleague with an attributed "why" surface — the one precedent in the framework for a score that is
explainable from its votes.

## Decision

### 1. One record, in the home, owned by AbstractRuntime
`<home>/identity.json`, module `abstractruntime.identity.digital_identity` (typed; no flags; no environment
variables). The gateway validates and calls the runtime writer; apps read through the gateway. When the file exists it
is the only truth for voice and look; `voice.yaml` and `appearance.json` are read only on homes without it (none will
remain after the gateway's boot pass, §2).

| Field | Type | Bounds |
|---|---|---|
| `schema_version` | int | exactly 1; a newer version refuses reads and writes loudly |
| `rev` | int | ≥ 1, +1 per write, never reused |
| `avatar.style` | str | abstractavatar id, `^[a-z][a-z0-9-]{0,63}$`, in the catalog loaded on this gateway, non-empty `watch_code` |
| `avatar.color` | str | `^#[0-9a-f]{6}$` |
| `avatar.source` | str | `default` or `chosen` |
| `voice` | object or null | null only while the record is default-origin and the gateway had no default voice |
| `voice.provider`, `voice.model`, `voice.voice` | str | each non-empty, ≤ 128 printable chars; always all three |
| `voice.speed` | float, optional | 0 < speed ≤ 4 |
| `voice.quality_preset` | str, optional | ≤ 32 |
| `voice.source` | str | `default` or `chosen` |
| `set_at` | str | aware UTC ISO-8601, clocked by the writer |
| `set_by` | str | `namespace:name`, `operator`, or `default` (the birth/boot pass) |

Whole file ≤ 4096 bytes, atomic write; corrupt, partial or unknown fields → `IdentityUnreadable`, never "unset".

### 2. The recorded default (every entity renders and speaks consistently from day one)
`default_identity(entity_id, gateway_default_voice) -> (avatar, voice)`, pure, no clock:
- seed = SHA-256 of the canonical `entity_id` (either generation);
- `avatar.style` = `DEFAULT_STYLE_POOL[seed[0] % 8]` with the pool engraved in this order:
  `watch-halo, watch-vortex, watch-nebula, watch-rings, watch-galaxy, watch-lotus, watch-crystal, watch-aurora`;
- `avatar.color` = HSL(hue = (seed[1] << 8 | seed[2]) % 360, 62 %, 52 %) rendered as `#rrggbb`;
- `voice` = the gateway's configured default voice triple (`output.voice` capability route) AS A VALUE, or null when
  none is configured; `source: default` on both parts; `set_by: default`.
It is written as `rev 1` (a) at birth, right after the manifest; (b) once per existing home when the gateway boots
(idempotent; a held home is skipped and logged; the pass never overwrites a record); (c) by `GET /identity` only when
(b) skipped that home and it is not held. A later change of the gateway default voice never touches a recorded
identity. Two entities born from the same spark on different homes get different colours and may get different
designs: a different `home_id` is a different individual (backlog 1110).

### 3. The reference and where it rides
`identity_ref = {"of": <subject>, "rev": <int>}`, string form `<subject>#<rev>` (`entity:castor#3`,
`session:sess_9f2a#1`). Rides `vars._runtime.identity_ref` beside — not inside — the signed summon stamp; `identity_ref`
and `X-Identity-Ref` on both TTS lanes; `identity_ref` stamped by the gateway at serve time on visit public rows and
`view` `public_update` messages (abstractagent untouched); on meet relay and status rows. An old rev resolves from the
biography (`GET /identity?rev=N`). A ref is never fabricated.

### 4. The fingerprint ties the record to the individual
`fingerprint = ActorFingerprint.from_metadata(kind="entity", display_name=<slug>, metadata={"entity_id", "home_id", "spark_hash"})`
→ `actor_id = ar_<24 hex>`, deterministic from the manifest; served with the continuity receipts the home already has:
`spark_hash` (the seed), `home_id` (the individual), `book_head` (the diary chain head). A regular agent's fingerprint
is abstractagent's existing one (`kind="agent"`, nonce metadata), session-scoped. No keys, no signatures (1110/1112:
authentication is the door, continuity is the chain).

### 5. The track record — derived, typed, nothing new stored
`TrackRecord` is computed by the runtime from the subject's run store and ledger; no field is written anywhere.

| Field | Source (today's records) | Stored? |
|---|---|---|
| `subject`, `fingerprint`, `computed_at`, `as_of` (newest run `updated_at`) | manifest, run index | no |
| `sessions` | distinct `session_id` over counted runs | no (derived) |
| `runs` | counted runs | no |
| `successes` | run `status == completed`; automation occurrence `completed`; entity task `done`; work-order verdict `done:` | no |
| `failures` | run `failed`; occurrence `failed`; work-order `blocked:` | no |
| `cancelled`, `in_progress` | `cancelled`; `running|waiting` | no |
| `assessed` | `_meta.assessment` verdicts (0 until the follow-up lands) | no |
| `tokens` = `{input, output, total}` | ledger `llm_call` `result.usage` (the `metrics_many` fold) | no |
| `by_task_kind[kind]` = `{runs, successes, failures, cancelled, tokens_total, first_at, last_at}` | the same, grouped | no |

Counted runs: turn-root runs (parent-less, not controllers) whose `_meta.origin.kind` is `person` or `trigger`, plus
automation occurrences; never sub-runs, `session_memory_*` owner runs, reflection or dream runs.
`task_kind = <phase or role>/<workflow_id>`: the phase from the entity stamp (`visit|work|personal`), else the
attribution role (`chat|occurrence|discussion`), and the run's `workflow_id`. For a regular agent the subject is its
session and the computation is the same over that session's runs.

### 6. Reputation — trust per task kind from past outcomes, explainable, no learning
`Reputation = {subject, computed_at, overall: TrustCell, by_task_kind: {kind: TrustCell}, evidence: [OutcomeEvidence…]}`,
`TrustCell = {trust: float 0..1, support: int, successes, failures, last_outcome_at}`,
`trust = (successes + 1) / (successes + failures + 2)` (rule of succession; `support = successes + failures`;
cancelled never counts). `overall` is the support-weighted mean of the kinds. `evidence` = the last 20 outcomes
`{run_id, task_kind, outcome: success|failure, at, signal: run_status|occurrence|task|work_order|assessment}`. A kind
with no outcomes reads `trust 0.5, support 0` and is rendered "no experience yet", never as trusted. Numbers are
rendered with their support ("trust 0.83 over 12 outcomes"). No weighting by recency this wave (deterministic, stated
as a follow-up with the assessment signal).

### 7. Remembered in the home, told at the next summon
Each identity write appends BEFORE the file moves: `{"marker": "identity_changed", "rev", "from", "to", "cause",
"written_by", "at", "provenance"}` to `<home>/state_history.jsonl`, with the same field names as `phase_changed`
(`abstractruntime.identity.life.append_phase_changed`: `written_by` is who wrote it, `cause` why), plus `rev`; the gateway also records a host
marker `identity_changed`. The diary stays the entity's elected record: the host never writes a diary entry. The
summon prelude carries ONE sentence from the newest `identity_changed` row newer than the previous summon
("Your voice changed on 4 November (by Laurent): now fr-male-rene." / "You were given your look and voice today.").

### 8. Validation at set time, no fallback after it
`PUT /entities/{name}/identity` (admin or creator; whole record; no `clear`) refuses in order: maintenance hold (409);
unknown or undrawable style (400, naming the catalog); a voice this gateway does not offer (400, the offered list); a
voice whose model is not downloaded (409 with the download action). For every role. After the set the entity lane
never substitutes a voice; a recorded `voice: null` refuses with "Castor has no voice yet: choose one in its Identity settings or set the
Gateway default voice" (the entity's name in place of Castor) — recorded absence, loud, never a borrowed voice.

### 9. Legacy writers; birth; regular agents
On a home with a record: `PUT /voice` and `PUT /appearance` write through it (`rev+1`, `source: chosen`), `clear` is
refused; `GET /voice` serves `source: identity`; `GET /appearance` serves the colour and the shape derived from the
style (`watch-shape-*` → that shape, else `planet`). `POST /entities` accepts `identity` (validated before creation);
without it the default is recorded. `POST /runs/start` accepts `identity` (same body, same validation) → inline
`_runtime.identity` with `_runtime.identity_ref = session:<sid>#n`; a later turn inherits; occurrences inherit their
controller's. Permanence is `POST /entities`.

### 10. Aging
No age in the record. Reads serve `age = {born, days}` and `rev`; appearance over time is a deterministic function of
`(days, rev)` and later of the memory card's key moments — never jitter, never randomness. Rendering it is 1083/0044.

### 11. Gateway surface (read-only unless stated)
- `GET /entities/{name}/identity[?rev=N]` → `{entity_id, identity: {rev, avatar: {style, color, source, watch_code}, voice, set_at, set_by}, fingerprint, age}`; `PUT` as §8.
- `GET /entities/{name}/track-record[?since=ISO]` → `TrackRecord`; `GET /entities/{name}/reputation` → `Reputation`.
- `GET /sessions/{session_id}/track-record` and `/reputation` for a regular agent's session (owner or admin).
- `identity` on the `GET /entities` row; `identity_ref` on visit open, TTS, meets, public rows; CLI
  `abstractgateway entity identity get|set` and `entity record <name>`.

### 12. What the Entity app shows (one view)
On the entity's Identity page: the design picker, colour, the voice picker (one save); below, "Track record": sessions,
runs, successes, failures, tokens, then "Trust by task" rows with `trust`, `support` and the last outcomes, each
linking to its run; "No experience yet" when empty. The Watch draws the entity's design (`watch_code`) and colour;
the Observer's entity page shows design, colour, voice and the overall trust cell.

## Consequences
Positive: one record and one history per entity, inside the home; every entity has a look and a voice from birth, by
a rule anyone can recompute; apps name who spoke by reference; successes, failures, tokens and trust are answers from
records that already exist, with their evidence; the fingerprint gives the operator's "who did what" a stable id.
Negative: the gateway depends on `abstractavatar>=0.1.1`; a boot pass writes one file per existing home (logged);
"success" means "the run completed" until the assessment signal lands; reputation reads cost a run-index scan per
entity (cached per newest `updated_at`); a deleted voice model stops an entity from speaking until re-downloaded.

## Out of scope (this wave)
Activity/poses/expression (1083/0044); descriptor v1 changes; the assessment route and recency weighting (follow-up
1120); colleague notes on entities; an entity changing its own identity; cross-gateway reputation (1112); the
Code web, Flow and TUI apps (no entity conversations there — nothing to render).

## Enforcement and Validation
Runtime: bounds, newer-schema refusal, rev monotonicity, marker-before-file, default determinism (same id → same
record; different home_id → different colour), the cue, counted-run rules, the token fold, trust arithmetic and
evidence order — each red under deletion. Gateway: the refusal ladder for every role; the boot pass idempotent and
hold-safe; refs on runs/TTS/meets/public rows; routes in the authorization contract. Apps: screenshots at 400 px.

## Related
ADR [0043](0043-readable-labels-never-computer-ids.md), [0044](0044-composable-activity-and-expression-presentation.md),
[0046](0046-optional-public-conversation-view.md), [0047](0047-voice-transport-is-never-an-attachment.md); backlog
[1083](../backlog/planned/1083_composable_entity_activity_and_avatar_state_contract.md),
[1110](../backlog/proposed/1110_entity_handles_and_summoning_addresses.md), [1112](../backlog/proposed/1112_cross_gateway_entity_federation_handshake_keychain.md),
[1119](../backlog/planned/1119_digital_identity_avatar_voice_fingerprint_track_record_reputation.md) (this),
[1120](../backlog/proposed/1120_identity_assessment_signal_recency_and_cross_gateway_reputation.md) (assessment
follow-up); the operator's article; agora hub reputation (`abstractcontinuum/vendor/hub/openapi.json`, `/reputation`,
`/colleagues`).
