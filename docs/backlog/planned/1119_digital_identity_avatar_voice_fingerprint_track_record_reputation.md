# 1119 — Digital identity: avatar, voice, fingerprint, track record and reputation per entity, surfaced by reference

> Package: AbstractRuntime (record, recorded default, biography row, summon cue, track record and reputation computation), AbstractGateway (validation, boot pass, routes, CLI, refs on runs/updates/segments), abstractentity (Identity settings, avatar by reference, Track record view), abstractassistant (Watch look by reference), abstractobserver (entity page identity and trust), abstractavatar (catalog read; no contract change), abstractvoice (no change; its catalog and presence probes are what the gateway checks)
> Type: feature
> Created: 2026-11-04
> Status: Planned
> Priority: high
> Labels: entities, identity, voice, avatar, reputation, fingerprint, portability
> Ships: this wave — Runtime 0.18.0 → Gateway 0.20.0 → Entity 0.11.0, Assistant 0.18.0 (Watch), Observer 0.12.0
> ADR: [0052](../../adr/0052-digital-identity.md) (Proposed); [1083](1083_composable_entity_activity_and_avatar_state_contract.md) / [ADR 0044](../../adr/0044-composable-activity-and-expression-presentation.md) stay separate

## Summary
Every entity holds one digital identity in its home: an avatar design with a colour and a voice, recorded from birth
by a deterministic default and changed only on purpose; a fingerprint that names the individual; a track record
(sessions, runs, successes, failures, tokens) and a reputation (trust per task kind, with its evidence) computed from
the records the runtime already keeps. Runs, spoken segments and public updates name the identity by reference. For a
regular agent the same record rides its session.

## Why
Operator, 2026-11-04 (verbatim in ADR 0052's status line): persistent named entities we recognise when they talk,
dialogues between entities where we know who speaks, and "how much do we trust an agent/entity for a task, based on
past experiences" — the article's "history of successes and failures" for "self-evolving persistent AIs".

## Today
`voice.yaml` and `appearance.json` per entity on the gateway, with different contracts (ADR 0052, Context); no per-entity design; no counts of anything
per entity; `ActorFingerprint` used only by abstractagent; the hub has the only explainable reputation precedent.

## Deliverables

AbstractRuntime 0.18.0
- `identity/digital_identity.py`: `DigitalIdentity`, `AvatarChoice`, `VoiceChoice`, `IdentityRef`, `read_identity`,
  `write_identity` (bounds → `identity_changed` biography row → atomic write, `rev+1`), `default_identity(entity_id,
  gateway_default_voice)` (ADR §2, pure), `identity_at_rev`, `identity_ref` / `parse_identity_ref`,
  `identity_change_cue(home_dir, since)`, `IdentityUnreadable`; the cue's one line in the summon prelude.
- `identity/track_record.py`: `TrackRecord`, `TaskKindRecord`, `TokenCounts`, `Reputation`, `TrustCell`,
  `OutcomeEvidence`, `entity_fingerprint(manifest) -> ActorFingerprint`, `compute_track_record(run_store,
  ledger_store, *, subject, since=None)`, `compute_reputation(record)`; `task_kind_of(run)`; counted-run rule.
- Exports in `identity/__init__.py`; docs (entities page: the home file, the default rule, the counters and the trust
  formula in plain words); `changelog.d/identity.md`; llms regen.

AbstractGateway 0.20.0
- `entity_identity.py`: validation ladder; `set_identity` (runtime writer + host marker `identity_changed`);
  `materialize_default_identity` (birth, boot pass, lazy GET); `identity_view` (+ `age`, `watch_code`, `fingerprint`).
- `entity_record.py`: `track_record(registry, name, since)` / `reputation(...)` over the entity runtime's stores,
  cached per newest run `updated_at`; the session variants over the gateway store.
- Routes (ADR §11); legacy `PUT /voice` / `PUT /appearance` write through the record, `clear` refused; derived
  `GET /voice` / `GET /appearance`; `identity` on the list row, on `POST /entities`, on `POST /runs/start`;
  `identity_ref` on visit open, both TTS lanes (`X-Identity-Ref`), meets, visit public rows, view messages.
- CLI `entity identity get|set`, `entity record`. Dependency `abstractavatar>=0.1.1`. Authorization contract rows.
  Docs, api page, configuration (the dependency, the boot pass line), changelog fragment, llms, README what's new.

abstractentity 0.11.0 — Identity page (picker, colour, voice, one save; "No identity yet" never appears for an
entity the gateway serves — the default is recorded; the refusal sentence verbatim), `AvatarVisitView` with the
entity's design and colour, "Track record" and "Trust by task" with evidence links; 400 px.

abstractassistant 0.18.0 (Watch) — entity responders draw `identity.avatar.watch_code` and colour; the global design
stays for the Assistant itself; complication untouched.

abstractobserver 0.12.0 — entity page: design, colour, voice name, overall trust cell with support.

Not touched: Code web 0.15.0, Flow 0.14.0, Assistant desktop (no entity conversations), abstractagent 0.6.0.

## Acceptance criteria (each goes red without its rule)

Runtime — identity
- [ ] Round trip: write → `rev 1`, second write → `rev 2`; the biography row exists BEFORE the file (injected failing
      rename leaves the row and the old file).
- [ ] Every ADR §1 bound refuses naming the field; `voice: null` is accepted only with `source: default`.
- [ ] `schema_version 2`, a corrupt file, an unknown field → `IdentityUnreadable` on read and write.
- [ ] `default_identity` is pure: same `entity_id` → identical record across 1000 calls; two ids differing only by
      `home_id` → different colours; every pool style exists in the abstractavatar catalog with a `watch_code`
      (test reads the catalog through `abstractavatar.catalog()` — skipped loudly if the package is absent).
- [ ] `identity_at_rev` returns the first record after two writes; an unknown rev raises; `parse_identity_ref`
      round-trips and refuses `castor`, `entity:castor#0`.
- [ ] The cue renders exactly one sentence for a row newer than the last summon and none otherwise; the prelude
      test shows the line in place.
- [ ] `life_sleep_stats` unchanged by identity rows.

Runtime — track record and reputation
- [ ] A fixture store with 3 sessions, 7 turn roots (4 completed, 2 failed, 1 cancelled), 2 sub-runs, 1 owner run,
      1 occurrence completed, 1 occurrence failed gives `sessions 3, runs 9, successes 5, failures 3, cancelled 1`;
      removing the counted-run rule (sub-runs counted) turns it red.
- [ ] Tokens equal the sum of `result.usage` over `llm_call` records of counted runs and their sub-runs, input and
      output separately, matching `metrics_many`.
- [ ] `task_kind_of` gives `visit/<workflow>` for a stamped visit run, `occurrence/<workflow>` for an occurrence,
      `chat/<workflow>` otherwise; it never reads prompt text (the test passes runs whose text would mislead a
      classifier).
- [ ] Trust: 4 successes, 1 failure → 5/7 (0.714…), `support 5`; no outcomes → 0.5 with `support 0`; cancelled
      changes nothing; `overall` is the support-weighted mean; `evidence` is the last 20 in time order with the
      signal named; a work-order `done:` and an entity task `done` each count once.
- [ ] `entity_fingerprint` is deterministic from `(entity_id, home_id, spark_hash)` and changes when any of them does.
- [ ] `assessed` is 0 and the follow-up (1120) is named in the docs — the field exists, typed.

Gateway (fakes; scratch data dir; never :8080)
- [ ] The refusal ladder in order for admin AND creator: hold → 409; unknown style / `iphone-weave` → 400; voice not
      offered → 400; model not downloaded → 409 with `error.download`; nothing written, no marker on refusal.
- [ ] A valid PUT writes through the runtime (`set_by` = principal, `source: chosen`), records the host marker with
      `rev/from/to`; `GET /identity` carries `age.born`, `fingerprint.actor_id`, `avatar.watch_code`; `?rev=1` works.
- [ ] Birth without `identity` records the default (`rev 1`, `set_by default`); birth with a bad `identity` creates
      no home; the boot pass writes exactly one record per legacy home, skips held homes with a log line, is
      idempotent on a second boot; `GET /identity` on a skipped, unheld home records it once.
- [ ] A changed gateway default voice leaves recorded identities untouched (test asserts the file and `rev`).
- [ ] Legacy writers over a record: partial write `rev+1`, `clear` → 409; `GET /voice` `source: identity`;
      `GET /appearance` colour + derived shape; legacy-home tests (`test_gateway_entity_voice.py`,
      `test_r16w6_entity_settings_authz.py`) unchanged and green before the boot pass runs.
- [ ] Visit open stamps `_runtime.identity_ref` beside the stamp; the signature verifies unchanged.
- [ ] Entity TTS lane: `identity_ref` and `X-Identity-Ref`; applies `identity.voice`; with `voice: null` → "<name> has no
      voice yet: choose one in its Identity settings or set the Gateway default voice" (ADR 0052 §8); with a removed model → the engine's error, never another voice (fake engine that would succeed on
      the default).
- [ ] Meet relay carries the speaker's ref; the two legs differ. Visit public rows and view `public_update` messages
      carry the ref when the run has one and no field otherwise.
- [ ] `POST /runs/start` with `identity`: validated, `session:<sid>#1`, inherited next turn, `#2` on change;
      `GET /sessions/{sid}/track-record` and `/reputation` answer for the owner, 404 for others.
- [ ] `GET /track-record` and `/reputation` for an entity match the runtime fixture numbers through the door; a
      second read with no new run hits the cache (test counts store calls).
- [ ] Authorization contract: identity read = member, write = admin-or-creator; record/reputation = member (entity
      visibility rules apply).
- [ ] A gateway without `abstractavatar` importable refuses `PUT /identity` and the boot pass logs one line per home
      and writes nothing (no default without a verifiable design).
- [ ] CLI: `entity identity set/get`, `entity record castor` print the record and the ref against a scratch dir.

Apps
- [ ] Entity app: one save; refusal verbatim; the visit avatar uses the design and colour; Track record numbers equal
      the gateway's; a trust row with `support 0` says "No experience yet"; 400 px screenshots of both.
- [ ] Watch: an entity draws its `watch_code` design and colour; the Assistant keeps the global design; complication
      PNGs byte-identical; simulator screenshot.
- [ ] Observer: the entity page shows design, colour, voice, overall trust with support.

Real check (operator's machine, `untracked/gpu.lock`, scratch data dir and port, admin token unset)
- [ ] Boot the scratch gateway over a copy of two legacy homes: both get a default record; set Castor's identity to
      a downloaded Qwen3-TTS voice and `watch-vortex`; read-aloud from the Entity app and the Watch uses it and answers
      `X-Identity-Ref: entity:castor#2`; a meet relay shows two refs; `entity record castor` shows the counts.

## Follow-ups (named, not built)
- [1120](../proposed/1120_digital_identity_feeding_and_evolution_external_feedback.md): how the digital identity is fed and evolves over
  time (operator, 2026-11-04: "reputation requires external feedback, provided by users or other agents"): external
  feedback from users and other agents, colleague notes, the assessment signal (`POST /runs/{id}/assessment`,
  `_meta.assessment`), recency weighting, the task-kind taxonomy; cross-gateway reputation with 1112. Until then the
  computed numbers are completion rates only, and every surface says so.

## Receipts

- Architect drafts (root `untracked/release-2026-11-03/identity/`): `ADR-draft.md` (now ADR 0052), `BACKLOG-draft.md`
  (this item), `ATTACK.md` (failure scenarios and fixes), `PLAN.md`.
