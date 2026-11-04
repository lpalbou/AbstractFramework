# 1124 — Read-aloud replay cache: synthesised audio kept per segment for 120 minutes

> Package: abstractcore (TTS layer), abstractgateway (keying by identity, storage location), abstractvoice
> Type: feature
> Created: 2026-11-04
> Priority: normal
> Labels: voice, tts, cache, latency, read-aloud
> Ships: a later release (not the current wave)

## Summary

Operator, 2026-11-04: "cache with TTL certain requests for speed, especially voice (TTS) when the AI speaks; to replay
we currently recompute; a temporary cache between (message of a session read) ↔ (cached audio to replay that
message), TTL ~120 min, enough to stop and go back."

Today a message read aloud a second time (Replay, going back after a stop, resuming on another device) is synthesised
again from its text. This item keeps the synthesised audio for a while, so a replay plays it back without a new
synthesis.

## Design

- **Key: what was spoken and how, not where.** The key is a content hash of the text segment plus the voice identity
  that read it: provider, model, voice, speed, language and quality preset. The same sentence read twice with the same
  voice hits the cache, whichever session or message it came from.
- **Stored per segment.** The read-aloud already splits a message into text segments (piece-wise resumable reading,
  AbstractVoice 0.20.0 names the segment of every audio line). The cache stores one audio piece per segment, so a
  resume after a stop, a replay from the start and a replay of one paragraph all reuse the same pieces.
- **Bounded.** A size cap (bytes), least-recently-used eviction under it, and a time to live of 120 minutes by default.
  Both are plain settings with plain names (for example `voice.replay_cache_minutes`, `voice.replay_cache_mb`); `0`
  turns the cache off.
- **Where.** Per account under the gateway's data dir, never shared across gateways and never sent anywhere. The
  gateway computes the key from the speaker's identity (ADR 0052: an entity's recorded voice, else the account's
  voice), so it is the gateway that decides which voice a key names.
- **Invalidation by construction.** A change of voice (an identity's new voice, a different speed or language)
  changes the key, so the old audio is simply never asked for again and ages out. No explicit invalidation path.
- **Metrics.** Hits, misses, evictions and the bytes held, readable by the operator (gateway metrics or the console's
  status), so the TTL and cap can be tuned from facts.

## Why

Replay and resume are the common case once a reading is interrupted ("enough to stop and go back"). Re-synthesis
costs seconds per segment on local engines and money on hosted ones, and it can give a slightly different reading of
the same sentence.

## Scope

### In scope

- AbstractCore: the cache in front of the TTS call (key, per-segment store, TTL, size cap with LRU, metrics); a
  setter for the policy a host relays.
- AbstractGateway: the key's voice identity from the speaker's recorded voice, the storage location per account under
  the data dir, the two settings, the metrics.
- AbstractVoice: whatever it needs to expose for the key to be exact (the resolved model, voice, speed, language and
  quality of a synthesis).

### Out of scope

- Caching any request other than speech synthesis; sharing audio across accounts or gateways; keeping audio beyond the
  TTL.

## Acceptance criteria

- [ ] Replaying a message that was read within the TTL makes zero synthesis calls (a fake engine counts calls); a
      resume after a stop reuses the pieces already synthesised.
- [ ] After the TTL, or after a change of voice, speed or language, the same message is synthesised again.
- [ ] The same sentence read in two different sessions of one account, with the same voice, is synthesised once.
- [ ] The cache never exceeds its size cap: a test fills it past the cap and checks the bytes held and the LRU order.
- [ ] Two accounts on one gateway never read each other's audio; the store lives under the gateway data dir.
- [ ] `0` turns the cache off; hits and misses are reported.

## Receipts

- Operator idea of 2026-11-04 (quoted above), relayed by the coordinator; design improved per the coordinator's
  brief (content-hash key, per-segment storage, bounded cache, per-account location, invalidation by key).
