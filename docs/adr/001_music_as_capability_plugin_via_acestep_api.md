# ADR 001 — Music generation as an AbstractCore capability plugin (ACE-Step API backend)

## Status

Accepted — 2026-02-12

## Context

AbstractCore supports optional deterministic “capabilities” (voice/audio/vision) via a plugin layer discovered through Python entry points (`abstractcore.capabilities_plugins`). This design keeps `abstractcore` lightweight while allowing richer modalities when installed.

We want to add **music generation** (text-to-music) to the ecosystem in a way that:

- does not force GPU-heavy dependencies into default installs
- works in “framework mode” (gateway/runtime) with durable artifact outputs
- avoids security surprises (no implicit remote-code execution)
- is consistent with existing plugin ergonomics (`llm.voice`, `llm.vision`, etc.)

ACE-Step 1.5 is a strong candidate backend. Its official distribution emphasizes running a **local server/UI** (`acestep-api` / Gradio) with auto-download and hardware-tiered configuration.

## Decision

- Add a new deterministic capability, **`music`**, to AbstractCore, exposed as:
  - `llm.music.t2m(prompt, ...) -> bytes | {"$artifact": ...}`
- Implement **`abstractmusic`** as a **standalone package** that registers itself as an AbstractCore capability plugin via the existing entry point group:
  - `[project.entry-points."abstractcore.capabilities_plugins"]`
- For v0, provide a backend that talks to an **ACE-Step 1.5 REST API server** (HTTP client), rather than embedding ACE-Step as an in-process dependency.

## Rationale

- **Operational simplicity**: backend hosts (gateway/runtime machines) can run ACE-Step with the correct GPU stack; clients remain thin.
- **Dependency isolation**: ACE-Step has heavy deps and strict environment constraints; keeping it out-of-process avoids conflicts across the ecosystem.
- **Security posture**: avoids implicitly requiring `trust_remote_code=True` patterns.
- **Consistency**: mirrors existing capability plugins (AbstractVoice/AbstractVision) and reuses the same discovery + artifact-output semantics.

## Consequences

- Users must run or provision a reachable ACE-Step API server to use the `abstractmusic` backend.
- AbstractCore gains a small, stable surface area for `music` (protocol + facade + registry plumbing).

## Alternatives considered

- **In-process ACE-Step** (direct import and model execution):
  - rejected for v0 due to heavyweight dependencies, environment pinning, and operational coupling.
- **Treat music as “voice/audio”**:
  - rejected because speech/audio IO semantics don’t match music generation and would muddy the capability surface.

