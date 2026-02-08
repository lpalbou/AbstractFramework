# API

This document covers the Python API exposed by the `abstractframework` meta-package.

## Purpose

`abstractframework` is a unified distribution package for the ecosystem. It provides:

- one-command installation for the pinned full framework profile
- lightweight runtime helpers to inspect installed component versions
- convenience re-exports from `abstractcore`

## Installation

```bash
pip install "abstractframework==0.1.0"
```

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

List of default `abstractcore` extras installed by `abstractframework==0.1.0`:

- `openai`
- `anthropic`
- `huggingface`
- `embeddings`
- `tokens`
- `tools`
- `media`
- `compression`
- `server`

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
