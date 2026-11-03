# 1076 — Model scheduling and memory management

> Package: abstractframework (AbstractCore residency, AbstractGateway model host, AbstractRuntime pools)
> Type: design
> Created: 2026-10-29
> Priority: normal
> Labels: residency, scheduling, memory, design

## Summary

Today each gateway process decides alone which models stay in memory: a load checks weights + KV against the free
memory and evicts unlocked models least recently used first, else it refuses with a sentence (AbstractCore ADR 0010).
That is a failsafe, not scheduling. This item collects the longer-term design, with the options and their trade-offs,
so the operator can choose. No implementation now.

## Why

Operator ruling (2026-10-29): longer-term model scheduling (one model host per machine, idle unload after a configurable
time, priorities interactive > automations > embeddings when memory is tight, eviction policy knobs) becomes ONE proposed
root backlog item, written plainly with the options and trade-offs. What it answers, measured on the OVH test server
(one 16 GB GPU): two gateways (8080, 8443) each loaded a 9B text model and could not both run; the embedder held ~5 GB of
the card without a row on the Models page (gateway backlog 0966); a 14B load evicted the only text model and was refused
anyway (fixed in AbstractCore #24).

## The questions and the options

1. **Who owns the GPU: one model host per machine, or one per gateway?**
   - One per gateway (today): simple, isolated, but instances on one card fight blind (each sees "free" memory the other
     will take next).
   - One per machine, shared by every gateway on it: one place sees every model and every request, so it can schedule
     across instances; costs a machine-wide service, an IPC contract, and a security boundary between accounts and
     instances (whose prompts reach which process).
   - In between: per-gateway hosts that publish their residency to a machine-wide ledger and read each other's before a
     load (no shared process, a shared view; races remain).
2. **Idle unload after a configurable time.**
   - Off (today): the first answer after a pause is fast; memory stays taken.
   - Per model idle timeout (e.g. 30 min), "Keep loaded" exempt: frees memory for automations and other users; the next
     interactive answer pays the load (seconds for small GGUFs, tens of seconds for large ones).
   - Per class (text, embeddings, speech) defaults with per-model overrides.
3. **Priorities when memory is tight: interactive > automations > embeddings.**
   - Strict priority: an interactive load may evict an automation's model mid-pause; an automation waits (queued) rather
     than evicting an interactive model. Needs a queue and a visible "waiting for memory" state.
   - Priority as a tie-breaker only inside LRU (cheap; weaker guarantees).
   - Embeddings: CPU by default when the GPU is tight versus GPU always (the person's Device choice wins either way).
4. **Eviction policy knobs.**
   - LRU among unlocked models (today), with "Keep loaded" and in-flight use as the only locks.
   - Cost-aware: prefer evicting what reloads fastest, or what frees the most memory per second of reload.
   - Per-account quotas on a shared host (an account cannot keep more than N GB resident).
5. **Context reservation (already ruled, kept here for completeness).** The KV is reserved at load: the fit rule and the
   allocation ladder choose how much, shown on the Models row with the advertised context and an editable per-model
   setting; a request longer than the loaded context fails with the readable sentence; never a silent cut and never a
   per-route cap.

## Acceptance criteria

- The operator picks an option (or a combination) for each of 1-4; the choice becomes an ADR and planned items.
