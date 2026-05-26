# API

This document covers the Python API exposed by the `abstractframework` meta-package.

## Purpose

`abstractframework` is a unified distribution package for the ecosystem. It provides:

- one-command installation for the pinned full framework profile
- lightweight runtime helpers to inspect installed component versions
- convenience re-exports from `abstractcore`

## Installation

```bash
pip install "abstractframework[all]"
```

Native local-engine deployment profiles are also available:

```bash
pip install "abstractframework[apple]"
pip install "abstractframework[gpu]"
pip install "abstractframework[all-apple]"
pip install "abstractframework[all-gpu]"
```

The `apple` and `gpu` root profiles delegate to the matching full Gateway native Python deployment
profile. Docker remains a Gateway deployment concern: lightweight server image by default, explicit
NVIDIA image for CUDA hosts.

## Installer prototype (GUI)

A GUI installer prototype for AbstractCore lives at `abstractinstallers/abstractcore`.
It installs via **PyPI/pip** into an isolated `.venv` and then runs a multi‑step
configuration wizard. It does **not** clone GitHub repositories. For bundling a
clickable app, see `abstractinstallers/abstractcore/BUILDING.md`.

## Exports

### `create_llm`

Re-export from `abstractcore`.

```python
from abstractframework import create_llm

llm = create_llm("ollama", model="qwen3:4b-instruct")
resp = llm.generate("hello")
print(resp.content)
```

### `GenerateResponse`

Re-exported response type from `abstractcore`.

### `RELEASE_VERSIONS`

Dictionary mapping each ecosystem package to the pinned version used in the global release profile.

### `CORE_DEFAULT_EXTRAS`

List of default `abstractcore` extras installed by the `abstractframework[all]` profile:

- `remote`
- `embeddings`
- `tokens`
- `tools`
- `media`
- `compression`
- `server`
- `vision`
- `voice`
- `audio`

### `get_release_profile()`

Returns the pinned global profile metadata.

```python
from abstractframework import get_release_profile

profile = get_release_profile()
print(profile["abstractframework"])
print(profile["packages"]["abstractcore"])
```

### `get_installed_packages()`

Returns a dictionary of installed AbstractFramework package versions detected in the current environment.

```python
from abstractframework import get_installed_packages

print(get_installed_packages())
```

### `print_status()`

Prints a human-readable status report of detected packages.

```python
from abstractframework import print_status

print_status()
```

## Notes

- Most behavior and feature APIs live in the individual package repos.
- Use this package for unified install/version pinning and ecosystem-level bootstrapping.
- SmartNote is a systray app that runs through AbstractGateway and auto-classifies fragments into cards; install with `pip install -e ./smartnote`.
- Gateway-first clients (AbstractAssistant) use bundle discovery + per-session workflow selection; see `docs/architecture.md`.
- Installer design guidance lives in `docs/installers/README.md`.
