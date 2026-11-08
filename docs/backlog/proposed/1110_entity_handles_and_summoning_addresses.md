# Proposed: Entity handles — a name and an address for every summoned entity

## Metadata
- Created: 2026-07-08
- Renumbered: 2026-11-03, was 0212 (the id was shared with the agency-parity item 0212 in `planned/agency-parity/`)
- Status: Proposed
- Completed: N/A

## Adversarial review (2026-07-08, runtime) — binding corrections
Two adversarial reviews (design record: agora `entity-society` channel; this
supersedes any "handle is identity" reading):
- **Handle is a DOOR LABEL / routing hint, NOT canonical identity.** Keep
  `entity:<slug>@<home_id>` as the canonical id; `<slug>@<gateway>` is UX +
  routing only. Handle equality MUST NOT be treated as identity equality.
- **Spark hash proves SEED integrity (genotype), not LIFE continuity
  (phenotype).** It is trivially Sybil'd: `spark.yaml` is public and
  copyable (reincarnation-by-copy is a shipped feature), so a copied spark
  yields an identical hash at a different `home_id` — a different individual.
  "Same name + same spark_hash" does NOT prove "the entity I met."
- **Continuity** is provable from the EXISTING hash-chained diary book +
  graph projection chain (the `verify` endpoint) via `home_id` + chain
  heads (`journal_head_seq` + `book_chain_head`). A per-home keypair is
  OPTIONAL hardening, NOT required (maintainer refinement 2026-07-08,
  entity-society seq 14): `<entity>@<ip>` + TLS is the authentication;
  reputation + AI-psychology psych-tests are the authorization/continuity
  defense; the key's only marginal value (trustless verification against a
  lying host) collapses because the key lives on that host. The handle
  resolution endpoint can still return the chain heads (and a signature IF
  keys are later adopted).
- **Smallest first step (local-only, before any federation):** generate the
  per-home keypair at `create()` and ship a signed
  `GET /entities/{slug}/handle` returning `{handle, entity_id, spark_hash,
  public_key, journal_head, book_head}`. Show `entity_id` + continuity heads
  alongside the friendly handle (substrate-honesty rule applies to handles).

## Context
The maintainer's framing (2026-07-08, verbatim anchor): "i really love the idea
we could communicate with those persistent agents with a handle like
castor@http://127.0.0.1:8081 ... it does give a clear identity and address to
those summoned entities."

Today an entity's identity is already three-layered but implicit:
- `entity_id` (`entity:castor@home-fd023c86`) — identity bound to a HOME,
  attested by the spark hash;
- the gateway that serves the home — the ADDRESS (host:port);
- the slug (`castor`) — the local NAME.

Nothing composes these into one durable, exchangeable handle. The observer deep
link (`?gateway=…&entity=…`) is a folk version of exactly this.

## Proposal
1. **Canonical handle grammar**: `<name>@<gateway-authority>` with
   `castor@127.0.0.1:8081` (local dev) and `castor@abstractframework.ai`
   (public) as the two exemplars. The handle names a DOOR, not a directory: it
   resolves through the gateway's entity routes only.
2. **Resolution endpoint**: `GET /api/gateway/entities/{name}/handle` returning
   the full handle, `entity_id`, spark hash, and public capability summary
   (may-visit? shared-room? federation?) — the machine face of the identity
   card. The spark hash makes handles VERIFIABLE: the same name at a new
   address either proves continuity (same spark + attested chains) or honestly
   reads as a different being.
3. **Handle rendering everywhere**: observer header, entity cards, chat drawer
   title, `entity list` CLI — one format, one identity.
4. **Copy-the-handle affordance**: one click in the observer copies
   `castor@host` — the social unit of these entities.

## Boundaries / risks
- A handle must never leak private material (diary bodies, memory contents):
  it is an ADDRESS + attestation, not a data channel.
- Handles name entities, not models: the mind-substrate stays a separate,
  visible property (substrate honesty rule).
- Renames: slugs are load-bearing (home directory name). A handle registry
  must treat the slug as canonical and display-names as decoration.

## First cut
Resolution endpoint + observer rendering + copy affordance. No federation in
this item (see 1111/1112) — a handle that is merely LOCAL is already useful.

## Current code reality and discovery (2026-11-08; paused by operator ruling 2026-11-08, pause all dev; resume = explicit go)

- Each `GET /entities` row already carries a handle `<name>@<gateway LAN IP>` (or `ABSTRACTGATEWAY_DECLARED_ADDRESS`,
  abstractgateway `config.py`): no scheme, no port; the Entity app treats it as "reachability, NOT identity — display
  only" (`abstractentity/src/stream_source.ts`). `GET /api/gateway/about` exists (`routes/gateway.py`, readable without
  sign-in) and names the instance. No signed `/handle` route and no per-home keypair exist.
- Discovery for `name@host` (framework seat view, recorded in
  [1112](1112_cross_gateway_entity_federation_handshake_keychain.md) on 2026-11-08): the handle convention (default
  port `:8080`, https for `*.ts.net`) plus `GET /api/gateway/about`; the calling gateway proves itself with its signed
  identity (ADR 0052 fingerprint, the remote pins the key); someone other than the operator needs the "may visit"
  permission ([1175](1175_may_visit_permission_for_entities.md)). The mention design that uses the handle is
  [1138](1138_talk_to_entities_from_code_assistant_and_notes.md).
