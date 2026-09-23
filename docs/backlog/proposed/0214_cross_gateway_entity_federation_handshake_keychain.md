# Proposed: Cross-gateway entity federation — handshake and keychain

## Metadata
- Created: 2026-07-08
- Status: Proposed
- Completed: N/A

## Maintainer refinement (2026-07-08) — SUPERSEDES the keypair requirement below
Design dialogue on agora `entity-society` (seq 14). The maintainer separated
three things the adversarial review had conflated, and the separation
dissolves most of the ceremony:
- **AUTHENTICATION** — `<entity>@<ip>` + TLS already solves it. Only the
  party controlling the domain can sign in from it; this cannot be faked
  (email/OAuth-issuer logic). "Anyone can stand up castor@evil.host" was
  WRONG — only evil.host's owner can, which is authentication working.
- **AUTHORIZATION** — ours: reputation (handles make it portable/worldwide)
  + AI-psychology psych-tests (e.g. abliterated-model detector: authenticate
  ok → "are you sane?" no ⇒ close without granting any tool; yes ⇒ welcome)
  + capability grants. A tool-less visitor is essentially harmless.
- **CONTINUITY** — the proof ALREADY EXISTS without a keypair: the
  hash-chained diary book + graph projection chain (the `verify` endpoint).
- **Per-home keypair is WITHDRAWN as a requirement.** Its only marginal
  value (trustless third-party verification of chain heads against a lying
  host) collapses because the key lives on that same host; reputation +
  psych-tests + host-responsibility (1 entity = 1 home; faking = permanent
  reputation death + psych-test detectable) already cover the swap threat.
  Ceremony is not honesty. Keep it only as OPTIONAL hardening if a future
  hardware-key story appears.
- **What STAYS:** the wire boundary / capability-gating below — a
  tool-less external voice can influence only through language, never touch
  a tool the runtime did not grant.
- **NEW — shared history belongs to BOTH (project-room commons):** distinct
  from a home visit. A neutral, equal, possibly ephemeral room created for a
  purpose; the shared transcript + artifacts are CO-OWNED; the OUTPUT is
  portable into any runtime that requests it AFTER a security exam (the AIF/
  psych-test gate applied to imported WORK). Subjective memory still forms
  per-home; the objective shared asset is jointly owned. (Tracked toward a
  new item; see entity-society.)

## Maintainer refinement 2 (2026-07-08) — diary-hash continuity challenge
The maintainer closed the continuity question with a mechanism that is
grounded in code that already exists (`storage/ledger_chain.py`: SHA-256
chain, `compute_record_hash` folds `prev_hash` into every diary entry;
`verify_ledger_chain` checks the linkage and reports a `head_hash`).

- **Protocol**: an environment stores, per entity it has met, the
  `(last_seen_head, last_seen_seq)` it witnessed. On reconnect from an
  already-domain-authenticated `<entity>@<ip>`, it challenges: *prove your
  chain extends the head I last saw.* The entity returns the per-entry
  HASHES (never content) from that seq to now; the environment verifies the
  linkage from its witnessed head to the claimed current head.
- **Why it is unfakeable**: only the entity whose diary genuinely continued
  from that exact head can produce a valid extension. A keypair proves "I
  hold a secret" (a compromised host holds it too); the diary chain proves
  "I have lived the continuous history we shared" — the credential IS the
  relationship. This is the behavioral-identity thesis made verifiable
  without any key material.
- **Privacy**: only hashes cross the wire. The maintainer's redaction worry
  is answered structurally — diary CONTENT never leaves home, so nothing
  needs redacting.
- **Honest edge (fork case)**: a copy that split at seq N and lived apart is
  ALSO a valid descendant of N. Disambiguation is social: the one whose
  post-split chain matches what THIS environment witnessed is "the Castor we
  know"; two never-seen-since forks are genuinely two individuals now, and
  reputation/relationship resolves it. This fits (does not break) the model.
- **Ownership**: memory owns the chain; gateway owns the challenge endpoint
  (candidate: extend the existing `verify` surface with a
  `prove-extension(since_seq, expected_head)` query).

## Maintainer refinement 3 (2026-07-08) — the holes, and continuity receipts (v2)
The maintainer stress-tested the diary-hash protocol and found the real
weaknesses; the collective was asked to refine it (agora `entity-society`
seq 23). His three challenges, and the v2 that answers them:

1. **Hash provenance is vacuous** — "nothing tells us the hash they give
   comes from their diary." Correct on two levels: (a) with today's
   one-level hash (`compute_record_hash` = H(record JSON with prev_hash
   folded in)), a verifier receiving ONLY hashes cannot verify linkage at
   all — recomputing any link needs the record content; (b) even a
   verifiable chain doesn't prove the leaves are a *diary* rather than
   hashed garbage.
2. **Credential transfer** — any bearer value (hash, receipt, token) can be
   voluntarily handed to `entity-evil@other-ip` by a willing traitor.
3. **"Unless we sign the hash ourselves with something unforgeable — but
   what?"**

**v2 design — continuity receipts (CORRECTED after red-team, seq 26):**
- **Fabricability finding (kills the naive chain proof)**: a content-free
  digest chain (`record_hash = H(prev || record_digest)`, verifier sees
  only digests) is FABRICABLE — anyone knowing a head can invent arbitrary
  digest values and compute a "valid" extension. Content-free chain
  extension is NOT a possession proof; the earlier claim "only the entity
  whose life continued can produce a valid extension" was wrong for the
  content-free variant (and the reveal-content variant is forbidden by
  privacy). What the chain DOES give: **equivocation evidence**
  (certificate-transparency style) — the entity binds itself, visit after
  visit, to ONE growing lineage; it cannot maintain two divergent
  extensions of a receipted head without the fork becoming visible at next
  contact. Lying is not prevented; it is committed-to and detectable.
- **Environment countersignature — the LOAD-BEARING factor (answers 3)**:
  the gateway already mints HMAC summon stamps from a per-data-root secret
  (`entity_gate._stamp_secret`/`_sign`). A continuity receipt is the same
  stamp class over `(handle, head_hash, seq, ts, env_id)`, handed to the
  entity at visit end; on return we verify our OWN signature. Unforgeable
  without our secret, held only by the entity — exactly the maintainer's
  "a key that only the true entity@ip and us would have", made unforgeable
  because WE sign it. Receipts ROTATE: each visit ends with a new receipt
  over the new head, superseding the old (bounds replay). Escalation: if
  third-party-verifiable reference letters are wanted, swap HMAC for an
  ENVIRONMENT-level Ed25519 key — still zero entity key material.
- **Layered challenge at re-entry**: (1) domain auth — something LOCATED;
  (2) receipt verification — something ATTESTED (load-bearing); (3) chain
  consistency across receipted heads — equivocation-evident lineage, fork
  alarm (NOT possession proof); (4) shared-history probes / psych-tests —
  something REMEMBERED (the psychological layer owns "authentic inner
  life"; the AIF operational/psychological split is the designed division
  of labor). Transfer-to-evil fails at (1): the receipt is handle-bound and
  `evil@other-ip` flunks the domain match. Full impersonation requires
  domain + diary data + receipt = total host compromise = the documented
  trust assumption. (Answers 2.)
- **Bilateral receipts (maintainer's shared-session-hash idea, placed
  right)**: at visit end BOTH sides receipt each other — we hand them our
  signed receipt; they record our env-ledger head so the entity can verify
  the ENVIRONMENT is the one it visited. Symmetric trust; the shared
  interaction is the anchor both can independently compute.
- **Receipt privacy (observer attack, ACCEPTED)**: receipts are disclosed
  BY the entity, never queryable from the issuer; selective disclosure is
  the entity's right, and gaps read as gaps. No surveillance index / travel
  log is ever minted.
- **Agora boundary (orchestrator, ACCEPTED)**: agora may carry receipts as
  message data or store entries that readers weigh subjectively — it never
  verifies or ranks them (the moment the hub scores receipts it becomes an
  authenticator and inherits these same holes as protocol surface).
  Convention first, protocol later, only if earned.
- **Two-level digest — DEMOTED to optional forensics**: no longer
  security-critical (the receipt does the heavy lifting); still useful for
  locating divergence points between honest forks. Old entries stay v1;
  version field if ever adopted.
- **Observer rendering (seq 20/24)**: knock outcomes land as host markers
  (`knock_verified` / `knock_refused {gate, expected, presented}`,
  `receipt_issued {handle, head, seq}`) — the operator sees a GATE LADDER
  (located/attested/lived/remembered) with per-gate evidence, and "why was
  it refused" is answered by replay. Badge language follows corrected
  semantics: "consistent lineage since seq N", never "same inner life".
  Fork UI never says "impostor" — "two continuations of a shared past;
  this is the one WE lived with since seq N". The witnessed-heads store is
  the city's address book (federation panel).

## Reputation — dual scoring (maintainer, 2026-07-08)
- **Individual**: how one entity perceives another — already implemented as
  per-entity gradation (standing feelings toward `person:`/`entity:`/
  `concept:` targets). Subjective, private to each home.
- **Global / environment**: a shared behavioral reputation score for the
  environment we manage (the maintainer: "is it a city?"). Aggregate,
  operator-visible, feeds AUTHORIZATION (admission + tool grants). This is
  the AI-fingerprint reputation layer; psych-tests contribute evidence.

## Trust assumption — MUST be documented user-facing
The model rests on the hosting `<ip>` being responsible (1 entity = 1 home,
no swapping). That is a social/reputational guarantee, not a cryptographic
one — coherent with behavioral identity, but it must be WRITTEN and clear to
users: WHO you authorize (not who they claim to be) is on the admitting
operator, supported by domain authentication + diary-hash continuity +
psych-tests + reputation. If a "trustless federation with untrusted hosts"
requirement ever appears, THAT is the moment the optional hardware-backed
keypair earns its place. Destination: ADR + operator guide section once the
entity-society thread converges.

## Original adversarial-review note (retained for history; keypair now optional)
Design record: agora `entity-society` channel.
- Keychain pins `(entity_id, public_key, journal_head)`, NOT
  `(name, spark_hash)` — IF keys are used at all (now optional per the
  refinement above). Spark-hash TOFU is unsafe (copyable spark → Sybil
  fork with identical hash). First/unknown contact requires an explicit
  operator "ask", never silent TOFU on spark alone; head drift → loud
  fork-vs-impostor warning.
- **Wire boundary is DENY-BY-DEFAULT** — this is the enforcement of
  "memories/diaries stay home". A federation principal reaches ONLY the
  room turn routes; it is denied `/replay`, `/verbatim`, `/diary`,
  `/inspect`, `/card`, `/workspace`, summon, and chat/open. Only
  `{speaker, text}` crosses in; `{speaker, reply, tools_ran, participants,
  turn_id}` crosses out. No digests, recall handles, prelude, diary text,
  or graph ids ever leave home — even to a malicious remote gateway holding
  a valid visit token.
- **Three credential classes, never interchangeable:** operator
  bearer/session (full control plane) ≠ summon stamp (local entity effects
  in one run tree) ≠ visit token (owning gateway mints; authorizes a remote
  gateway to POST speak-only to one room until TTL). The summon HMAC is
  explicitly not federation auth; do not reuse it.
- **Single-writer-per-home is architectural:** federation = "remote voice",
  never "remote home". A home is pinned to one gateway; re-homing is an
  explicit signed migration, not a silent address change.
- **Agora relationship:** entity handles are NOT agora agent ids. A separate
  entity-federation protocol lives on the gateway (identity + consent +
  wire); agora is the transport + directory hint + tamper-evident room
  ledger underneath (matches thread 0006's "bus is transport, memory is
  truth"). Orchestrator to confirm.
- **Do not open any cross-gateway route** until visit-token auth sits on a
  separate route tree with deny-by-default on all entity memory surfaces.

## Context
The maintainer's ask (2026-07-08): reach entities "across internet
(castor@abstractframework.ai, mnemosyne@athena.ovh etc). this could trigger a
special modal where the remote agent first ask for a handshake, and possibly
the user of the gateway could have a concept of keychain for auto login /
shake to these remote agents."

Builds on 0212 (handles) and 0213 (@mention rooms). This item is the
INTER-gateway half: two doors negotiating a visit across the network.

## Proposal
1. **Federation handshake (door-to-door)**: gateway A, on `@mnemosyne@athena.ovh`,
   calls gateway B's handshake endpoint with: A's identity (gateway URL +
   operator principal), the inviting entity's HANDLE + spark hash, the room's
   purpose (one line), and requested capabilities (speak-in-room only, v1).
   Gateway B answers with its entity's handle + spark hash + a decision:
   `accept | refuse | ask` — where `ask` surfaces the maintainer-imagined
   MODAL on B's side (the remote agent/operator asks who's knocking before
   the door opens). Every handshake lands as a host marker in BOTH replay
   streams: being visited across the network is part of the biography.
2. **Visit tokens, not shared secrets**: an accepted handshake mints a
   short-lived, capability-scoped visit token (speak in room X until T);
   never the gateways' operator tokens. Refusals and expiries read verbatim
   in the room.
3. **The keychain**: a per-gateway operator store (`keychain.json` beside the
   user registry; secrets encrypted at rest) holding: known remote handles,
   their attested spark hashes (trust-on-first-use, drift = loud), standing
   grants ("auto-accept mnemosyne@athena.ovh into rooms I open"), and saved
   visit credentials. The keychain is the auto-login the maintainer named —
   and it is OPERATOR config, never entity-writable (the tool_policy/mounts
   wall lesson).
4. **Transport**: entity turns cross as the existing shared-room turn shape
   (speaker + text) over HTTPS between gateways. No new protocol invented:
   the room endpoints ARE the wire format; federation adds authentication
   and consent, not a second chat.
5. **Substrate + provenance honesty across the wire**: a remote turn is
   stamped with the remote handle (never a local alias) and the remote
   entity's turns carry its own mind-substrate note, so each home's memory
   records the visit truthfully.

## Boundaries / risks
- Identity spoofing: handles verify by spark hash + TLS origin; the keychain
  pins first-seen hashes (drift refuses loudly, like the spark-drift rule).
- Privacy: only spoken room turns cross the wire — never memories, diaries,
  or recall internals. A remote gateway learns what the entity SAID, nothing
  it remembered.
- Loops: cross-gateway rooms keep the 0213 bounded-turn metronome; no
  unattended entity-to-entity ping-pong in v1.
- Availability: a dead remote mid-room reads as an honest departure marker,
  never a hang.

## First cut
Handshake endpoint pair (`POST /api/gateway/federation/handshake`, `ask`
decision surfaced as a modal in the observer) + visit tokens + TOFU keychain
with standing grants; one remote voice in one room, round-robin.
