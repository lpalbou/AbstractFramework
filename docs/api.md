# API (meta-package)

This page documents the API exported by `abstractframework`, the meta-package shipped by this repository.

`abstractframework` is a **pinned distribution profile** plus a few lightweight helpers. The framework can be used in two ways: **via code** (Python SDK, see below) or **via API routes** (HTTP/SSE through AbstractGateway, language-agnostic). Most functional APIs live in component packages — especially **AbstractCore** for the LLM SDK.

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

### `RELEASE_VERSIONS`

Dictionary mapping each ecosystem package name to the pinned version for this release.

### `CORE_DEFAULT_EXTRAS`

List of AbstractCore extras implied by the default framework install profile (remote-first): `remote`, `tools`, `media`, `vision`, `voice`, `audio`, `music`.

### `get_release_profile()`

Returns the full pinned profile metadata as a dict.

```python
from abstractframework import get_release_profile

profile = get_release_profile()
print(profile["abstractframework"])        # meta-package version
print(profile["packages"]["abstractcore"]) # pinned Core version
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

---

## Where to find the functional APIs

| What you need | Package |
|---|---|
| LLM calls, tools, structured output, media, embeddings, MCP | `abstractcore` |
| Durable execution kernel (runs, ledger, effects, waits) | `abstractruntime` |
| Agent patterns (ReAct, CodeAct, MemAct) | `abstractagent` |
| Control plane (HTTP server, scheduling, bundle discovery, SSE) | `abstractgateway` |
| Workflow authoring and `.flow` bundles | `abstractflow` |
| Monitoring / operations UI | `@abstractframework/observer` (npm) |

See **[Getting Started](getting-started.md)** for the two entry points and a first end-to-end run.
