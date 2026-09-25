# API (meta-package)

This page documents the API exported by `abstractframework`, the meta-package shipped by this repository.

`abstractframework` is a **pinned distribution profile** plus a few lightweight helpers. AbstractFramework has two entrypoints: **AbstractCore** (LLM SDK + optional OpenAI-compatible `/v1` server) and **AbstractGateway** (durable run control plane over HTTP/SSE). Most functional APIs live in component packages — especially **AbstractCore** for the LLM SDK.

---

## Install

Full pinned ecosystem:

```bash
pip install abstractframework
```

Only the LLM SDK:

```bash
pip install abstractcore
```

Hardware-specific profiles (native installs, not Docker):

```bash
pip install "abstractframework[apple]"       # Apple Silicon native stack (MLX/Metal)
pip install "abstractframework[gpu]"         # GPU native stack (CUDA/ROCm)
```

See [Install AbstractFramework](install.md) for the profile chooser and first health checks.

---

## Convenience re-exports

`abstractframework` re-exports two common AbstractCore entry points so simple scripts can `from abstractframework import ...` without a separate `abstractcore` import.

### `create_llm`

```python
from abstractframework import create_llm

llm = create_llm("ollama", model="qwen3:4b-instruct")
resp = llm.generate("hello")
print(resp.content)
```

### `GenerateResponse`

The response type returned by `llm.generate(...)`.

---

## Release profile helpers

### `__version__`

The meta-package version (`0.3.2` for this release).

### `RELEASE_VERSIONS`

Dictionary mapping each ecosystem package name to the pinned version for this release. In 0.3.2:
`abstractcore` 2.15.2, `abstractruntime` 0.4.35, `abstractagent` 0.3.13, `abstractgateway` 0.4.3,
`abstractmemory` 0.3.0, `abstractsemantics` 0.0.5, `abstractvoice` 0.11.4, `abstractvision` 0.3.29,
`abstractmusic` 0.1.15, `abstractassistant` 0.5.0.

### `PACKAGE_DISTRIBUTIONS`

Maps each package name in `RELEASE_VERSIONS` to its PyPI distribution name (for example
`abstractruntime` → `AbstractRuntime`).

### `NPM_RELEASE_VERSIONS`

The npm apps released with this version, each runnable with `npx <package>`:
`@abstractframework/flow` 0.3.20, `@abstractframework/code` 0.4.2,
`@abstractframework/observer` 0.1.12, `@abstractframework/continuum` 0.3.1 and
`@abstractframework/entity` 0.2.1. They also appear as `npm_apps` in the install manifest.

### `CRATE_RELEASE_VERSIONS`

The Rust terminal tools released with this version, installed with `cargo install <crate>`:
`abstractgateway-console` 0.8.0, `abstractcore-console` 0.2.0, `abstractcode` 0.5.1 and the
`abstracttui` engine 0.6.0. The bootstrap scripts install `abstractgateway-console` and
`abstractcode` at these versions with `--with-console` and `--with-code-cli`.

### `CORE_DEFAULT_EXTRAS`

List of AbstractCore extras implied by the default framework install profile (remote-first): `remote`, `tools`, `media`, `vision`, `voice`, `audio`, `music`.

### `get_release_profile()`

Returns the full pinned profile metadata as a dict.

```python
from abstractframework import get_release_profile

profile = get_release_profile()
print(profile["abstractframework"])        # meta-package version
print(profile["packages"]["abstractcore"]) # pinned Core version
print(profile["crates"])                   # CRATE_RELEASE_VERSIONS
```

### `get_installed_packages()`

Returns a dict of installed AbstractFramework package versions detected in the current environment.

```python
from abstractframework import get_installed_packages
print(get_installed_packages())
```

### `print_status()`

Prints a human-readable status report of detected packages (installed vs missing).

```python
from abstractframework import print_status
print_status()
```

### `abstractframework doctor`

Checks the Python version (3.10–3.13), pinned package versions, the Apple/GPU profile
prerequisites (macOS 14+ on Apple Silicon, `nvidia-smi` / `rocminfo`), uv, Node.js 18+ (system or
`nodejs-wheel`), free disk, and, over read-only GET requests, the gateway health
(`ABSTRACTGATEWAY_URL`, default `http://127.0.0.1:8080`), `abstractgateway-config status --json`,
and whether Ollama and LM Studio are reachable. It does not import heavy local inference stacks.
Checks report `ok`, `warn`, `error` or `info` (`info` never fails the run).

```bash
abstractframework doctor
abstractframework doctor --json          # schema abstractframework_doctor_v2
abstractframework doctor --no-network    # skip the gateway / engine probes
abstractframework doctor --no-environment  # only check the Python package profile
abstractframework doctor --timeout 5     # probe timeout in seconds (default 2)
```

### `abstractframework manifest`

Prints or validates the installer-facing manifest generated from the root release profile.

```bash
abstractframework manifest                                         # print it
abstractframework manifest --check docs/installers/install-manifest.json   # compare a file with it
abstractframework manifest --write install-manifest.json           # write it to a file
```

Field reference: [release-and-manifest.md](installers/release-and-manifest.md).

---

## Where to find the functional APIs

| What you need | Package |
|---|---|
| LLM calls, tools, structured output, media, embeddings, MCP | `abstractcore` |
| Durable execution kernel (runs, ledger, effects, waits) | `abstractruntime` |
| Agent patterns (ReAct, CodeAct, MemAct) | `abstractagent` |
| Control plane (HTTP server, scheduling, bundle discovery, SSE) | `abstractgateway` |
| Workflow authoring UI | `@abstractframework/flow` (npm) |
| Monitoring / operations UI | `@abstractframework/observer` (npm) |
| Coding client | `abstractcode` (crates.io) and `@abstractframework/code` (npm) |
| Gateway operator console | built-in `/console`, and `abstractgateway-console` (crates.io) |
| Local models and engines (catalog, fit, download, delete, engine installs) | `abstractcore` (`abstractcore models`, `abstractcore engines`, `/acore/*`), mirrored by `abstractgateway` (`/api/gateway/models`, `/engines`, `/jobs`) |
| AbstractCore consoles | built-in `/console` of `abstractcore serve`, and `abstractcore-console` (crates.io) |
| Continuous development console | `@abstractframework/continuum` (npm) |
| Summoned-entity manager | `@abstractframework/entity` (npm) |

See **[Getting Started](getting-started.md)** for the two entry points and a first end-to-end run,
**[Architecture](architecture.md)** for how the packages connect, and
**[Troubleshooting](troubleshooting.md)** when `doctor` reports a problem.

Gateway-hosted workflow APIs distinguish private runtime bundles from the
shared workflow catalog:

- `/api/gateway/bundles` remains the caller runtime's private bundle surface.
- `/api/gateway/workflow-catalog` lists catalog workflows visible to the signed
  in principal.
- `/api/gateway/admin/workflow-catalog/*` is admin-only for immutable catalog
  upload/promote/default/ACL/status operations.
- `/api/gateway/runs/start` and `/api/gateway/runs/schedule` accept
  `registry_scope: "tenant_catalog"` to start a catalog workflow in the
  requesting user's runtime.
- Catalog scope is explicit. Without `registry_scope`, Gateway starts only
  private runtime bundles. Catalog flow/schema inspection uses ACL-aware
  `/api/gateway/workflow-catalog/{bundle_id}/versions/{version}/flows/{flow_id}`
  routes.

Gateway-hosted user administration keeps retained runtime data explicit:

- `/api/gateway/admin/users` is the admin-only user list/create/read/update/delete
  surface.
- `/api/gateway/admin/runtime-reservations` lists retained runtime reservations
  left by deleted or reassigned users.
- `/api/gateway/admin/runtime-reservations/{runtime_id}/transfer` intentionally
  assigns retained runtime data to an existing same-tenant user.
- `/api/gateway/admin/runtime-reservations/{runtime_id}/purge` requires exact
  runtime-id confirmation, deletes the retained runtime directory, then releases
  the runtime id for reuse.

Gateway-hosted provider endpoint profiles make reusable hosted endpoints
discoverable without exposing raw keys:

- `/api/gateway/config/provider-endpoint-profiles` lists and creates profiles
  for the current principal.
- `/api/gateway/config/provider-endpoint-profiles/discover-models` previews the
  model list for a draft or saved profile by calling the configured provider
  family and base URL with the server-side or entered key. The response never
  echoes the raw key.
- `/api/gateway/config/provider-endpoint-profiles/{profile_id}` updates or
  deletes an existing profile. Gateway-scoped profiles require an admin
  principal.
- `/api/gateway/discovery/providers` includes enabled profiles as virtual
  providers such as `endpoint:office-vllm`.
- `/api/gateway/discovery/providers/{provider_name}/models` resolves virtual
  providers through the stored profile and returns the allowed or discovered
  model list without returning the raw API key.
