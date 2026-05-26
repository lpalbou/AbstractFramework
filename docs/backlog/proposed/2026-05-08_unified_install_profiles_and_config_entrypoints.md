# Proposed: Unified Install Profiles And Configuration Entrypoints

## Metadata
- Created: 2026-05-08
- Status: Proposed
- Completed: N/A

## Context

AbstractFramework has two real user entry points:

- AbstractCore for direct application development against LLMs, tools, media, and capability
  plugins.
- AbstractGateway for deployable 24/7 runtime control: durable runs, bundles, ledgers,
  tools, memories, triggers, Gateway auth/origin policy, and thin-client access.

The package stack behind Gateway is layered:

- AbstractCore owns provider/capability execution.
- AbstractVision, AbstractVoice, and future AbstractMusic own modality-specific capability
  backends.
- AbstractRuntime owns durable graph execution and artifact-safe effect handling.
- AbstractAgent uses Runtime plus Core tools to implement agent behavior.
- AbstractGateway composes Runtime, Core, Agent, capabilities, Memory, and Semantics into a
  deployable control plane.
- AbstractMemory owns memory stores and query contracts.
- AbstractSemantics owns shared vocabulary and schema validation.

Current pending changes show the architecture pressure clearly. Gateway, Vision, and Voice are
moving toward lightweight remote defaults, while the root `abstractframework` package still pins
older broad dependency sets and the Gateway base install is being pulled toward a server profile.

## Current Code Reality

- Root `pyproject.toml` still pins older package versions and broad default dependencies, including
  heavy Core extras and app packages.
- AbstractCore already has a light base, remote/provider extras, `all-apple`, and `all-gpu`.
- AbstractVision has an empty base dependency set and explicit local extras such as `diffusers`,
  `sdcpp`, and `local`.
- AbstractVoice has a light base and explicit local extras such as `local`, `voice`, `audio-io`,
  and heavyweight cloning/model extras.
- AbstractRuntime base depends only on AbstractSemantics; Core integration is optional.
- AbstractMemory base is dependency-light; LanceDB is optional but required by current Gateway KG
  workflows.
- AbstractGateway currently has pending changes that make bare `pip install abstractgateway` pull
  the multimodal Runtime/Core/Vision/Voice control plane.

## Problem

The tempting simple rule is:

```text
pip install package
pip install "package[apple]"
pip install "package[gpu]"
pip install "package[all-apple]"
pip install "package[all-gpu]"
```

That vocabulary is useful, but applying it mechanically to every package would blur the package
boundaries:

- Runtime should not pull Core, Vision, Voice, or local engines in its base install.
- Semantics has no hardware role, but may expose no-op hardware profile aliases so aggregate
  installs can use one vocabulary without special casing.
- Memory should not own provider/model selection; embeddings should use the Core-owned
  `embedding.text` capability route, with Gateway acting only as the control-plane entry point.
- Gateway should compose the deployment profile, but a bare Gateway install may still need to
  remain runner/CLI-light.
- Python extras use bracket syntax, not colon syntax: `package[apple]`, not `package:apple`.
- Extras can only add dependencies. They cannot create a "runner-only" install after the base
  install already pulled server dependencies.

## Proposed Direction

Unify the vocabulary, not the dependency closure.

Use these terms consistently:

- `package`: the smallest useful install for that package's own responsibility, with no local model
  engines and no model downloads.
- `package[remote]`: hosted/API provider support when not already in base.
- `package[server]`: deployable HTTP/server profile for packages that host a server.
- `package[apple]`: native Apple local engines where the package owns such engines, or an
  explicit no-op/pass-through alias for packages with no hardware dependency.
- `package[gpu]`: generic GPU local engines where the package owns such engines, or an explicit
  no-op/pass-through alias for packages with no hardware dependency.
- `package[all-apple]`: aggregate native Apple stack for an entry-point package, or the package's
  Apple-relevant optional dependencies.
- `package[all-gpu]`: aggregate GPU stack for an entry-point package, or the package's
  GPU-relevant optional dependencies.

Keep no-op compatibility extras documented. They are acceptable for dependency-light packages such
as Semantics, and pass-through extras are acceptable for Runtime/Agent so Gateway/root profiles can
cascade without custom resolver logic. Do not use no-op aliases to imply an unavailable runtime
capability.

## Installation Strategy

Preferred deployment profiles:

- AbstractCore:
  - `abstractcore`: light library/core HTTP-compatible base.
  - `abstractcore[remote]`: official hosted providers such as OpenAI and Anthropic.
  - `abstractcore[apple]`: Apple local LLM engine alias.
  - `abstractcore[gpu]`: local GPU LLM engine alias.
  - `abstractcore[all-apple]`: local Apple stack.
  - `abstractcore[all-gpu]`: local GPU stack.
- AbstractGateway:
  - `abstractgateway`: runner/CLI/durable host base, unless leadership explicitly chooses a
    server-by-default package.
  - `abstractgateway[server]`: default Docker/server profile for remote providers plus light
    Vision/Voice plugins.
  - `abstractgateway[memory]`: Gateway KG memory profile with `abstractmemory[lancedb]`.
  - `abstractgateway[apple]`: full native macOS Python deployment profile.
  - `abstractgateway[gpu]`: full native GPU Python deployment profile.
  - `abstractgateway[all-apple]`: same deployment intent as `apple`, kept as an explicit aggregate
    spelling.
  - `abstractgateway[all-gpu]`: same deployment intent as `gpu`, kept as an explicit aggregate
    spelling.
  - `abstractgateway[server-nvidia]`: current experimental CUDA/NVIDIA image profile.
- AbstractFramework root:
  - `abstractframework`: remote-light aggregate, no local model engines.
  - `abstractframework[gateway]` or `abstractframework[server]`: Gateway deployment aggregate.
  - `abstractframework[apple]` and `abstractframework[gpu]`: delegate to the matching full Gateway
    native deployment profile.
  - `abstractframework[all-apple]` and `abstractframework[all-gpu]`: full native stacks.

Do not treat `all` as the recommended install for real users. In cross-platform packages, `all`
too easily combines MLX, CUDA/ROCm, Torch, and local media engines that cannot all install or run
on the same host.

## Configuration Strategy

Add `abstractgateway-config`; keep `abstractcore-config`.

`abstractcore-config` should own:

- provider API keys;
- provider base URL defaults where the provider supports them, or explicit env/runtime setup when
  those URLs are not yet persisted as first-class config;
- standalone AbstractCore server settings;
- Core default provider/model;
- Core media fallback settings;
- local engine profile setup when the user explicitly chooses local/Apple/GPU.

`abstractgateway-config` should own:

- Gateway auth tokens and allowed origins;
- data directory, store backend, and runner mode;
- bundles/workflow source;
- workspace policy and filesystem mounts;
- tool approval mode;
- Gateway default provider/model for runs;
- Gateway embedding provider/model and memory KG preflight;
- capability readiness status across Core, Vision, Voice, Music, Memory, and Semantics.

Gateway config may call Core config during an interactive wizard, but Gateway should not mutate
Core provider/capability environment variables at request time. Capability packages own their
provider defaults; Gateway composes, validates, and reports readiness.

Recommended precedence:

1. explicit request/run values, when Gateway policy permits them;
2. Gateway deployment config/env;
3. AbstractCore persisted config/env;
4. capability package config/env;
5. package defaults, with explicit `#FALLBACK` warnings when behavior changes.

## Security And Cascade Boundary

Do not model auth/CORS as one global cascade through the whole framework. Model them as inbound
server-boundary settings:

- Gateway owns the auth token(s), allowed origins, request limits, and exposure policy for Gateway
  HTTP/SSE routes and thin clients.
- AbstractCore owns the auth token, allowed origins, base URL allowlists, media/fetch/local-file
  policy, and exposure policy for the standalone AbstractCore server.
- Vision, Voice, and Music normally run as capability plugins or outbound clients. They consume
  provider credentials, base URLs, model ids, cache paths, device choices, and backend-specific
  settings. They should not inherit Gateway/Core bearer tokens or browser origin allowlists unless
  they intentionally expose their own production server.
- Optional dev servers, such as a Vision playground or Voice example UI, need their own local/dev
  security notes. They are not the production serving boundary for Gateway or Core.

When Gateway embeds Core in-process, only the Gateway server boundary is exposed to clients. Core
provider/capability config is still used, but Core server auth/CORS settings are not part of the
client-facing surface.

When Gateway calls or launches a standalone Core server, the handoff should be explicit:

- Gateway uses its own client-facing token for thin clients.
- Core uses its own server token, such as `ABSTRACTCORE_SERVER_API_KEY`.
- Gateway-to-Core calls send the Core server token in `Authorization` when Core auth is enabled.
- Per-request upstream provider key overrides use Core's provider override mechanism, such as
  `X-AbstractCore-Provider-API-Key`, not the Gateway auth token.
- Allowed origins are configured independently for Gateway and Core because they protect different
  browser-facing surfaces.

`abstractgateway-config` may generate, store, or pass Core server settings when it manages a
deployment, but it should not silently reinterpret `ABSTRACTGATEWAY_*` values as Core or
capability-package configuration.

## Pending Changes Guidance

Keep with revisions:

- Vision and Voice plugin changes that move OpenAI defaults into the capability packages.
- Gateway remote-light `server` Docker direction.
- Gateway separate NVIDIA profile as an experimental heavy profile.
- Root architecture docs that clarify package boundaries.

Revise before merge:

- Root `pyproject.toml` and `abstractframework/__init__.py` pins; they are stale relative to the
  package versions being used by Gateway/Core/Vision/Voice.
- Root default dependencies; they should not pull heavy local engines by default.
- Gateway base install change; decide explicitly whether bare `abstractgateway` is minimal or a
  remote-light server control plane. Extras cannot undo base dependencies.
- Gateway docs that present port `8000` as default while the CLI still defaults to `8080`.
- NVIDIA image docs/release language; mark it experimental until build and smoke tests exist.

Discard or split from this strategic work:

- virtualenvs, caches, backup clones, gh-pages checkouts, and scratch notes;
- app/front-end changes such as AI-space work, unless handled in separate backlog items.

## Promotion Criteria

Promote this proposal when the maintainers choose:

- whether bare `abstractgateway` stays runner-light or becomes remote-light server-capable;
- whether `abstractcore` base should include official OpenAI/Anthropic SDKs or keep them in
  `abstractcore[remote]`;
- whether Gateway `server` includes `abstractmemory[lancedb]` by default or exposes a separate
  `memory` profile;
- naming for generic `gpu` versus explicit `nvidia`/future `rocm`.

## Validation Ideas

- Packaging tests for root, Core, Gateway, Runtime, Vision, Voice, Memory, Semantics, Agent, and
  Music extras.
- Fresh venv install matrix:
  - no-extra;
  - `remote`;
  - `server`;
  - `memory`;
  - `all-apple` on macOS;
  - `server-nvidia` / `all-gpu` on a CUDA host.
- Import-light tests proving no Torch/Diffusers/vLLM/MLX/faster-whisper/Piper model stack is
  imported by remote-light installs.
- Gateway readiness tests that distinguish installed, registered, configured, and ready.
