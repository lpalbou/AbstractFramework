---
name: abstractframework
description: Install the pinned AbstractFramework profile, inspect its component versions and installer manifest, and diagnose package or service health before using the component APIs. Use for choosing light, Apple or GPU installs and checking whether the intended Gateway and engines are reachable.
license: MIT
compatibility: Python 3.10–3.13. Apple local inference needs supported Apple Silicon/macOS; the GPU profile targets supported NVIDIA hosts. Browser apps need Node.js 18 or newer.
metadata:
  package-version: "0.14.4"
---

# AbstractFramework

The meta-package pins a compatible Python stack and lists the matching npm apps and Rust
consoles. It supplies installation inspection; the component packages own inference, durable
runs, memory and application behavior. Choose a profile, inspect the installation, then follow
the owning component's documentation.

## Install and verify

This guide describes AbstractFramework 0.14.4. Follow the installed version's documentation
when it differs from this guide.

Use a virtual environment. Select one of the three supported profiles:

```bash
python -m pip install abstractframework
# Supported Apple Silicon local inference:
python -m pip install 'abstractframework[apple]'
# Supported NVIDIA local inference:
python -m pip install 'abstractframework[gpu]'
```

The base profile supports remote inference without installing every local engine. Extras add
hardware dependencies; they do not create credentials, download all model weights, start the
Gateway or register a login item. Use the [installation guide](https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/docs/install.md)
when you want the complete application installer.

Verify the installed version and inspect the supported commands:

```bash
python -c 'from importlib.metadata import version; print(version("abstractframework"))'
abstractframework --help
abstractframework doctor --no-environment --json
```

Compare the version with `metadata.package-version`. Use that installed version's documentation
when they differ. `--no-environment` checks the Python release profile without host, tool or
network probes. Read both `status` and individual `checks`: the command exits 1 for an error,
and 0 can still include warnings. A source import alone does not prove installed metadata or
all pinned distributions agree.

## Expert workflow

1. Choose the environment and profile for the machine that will run inference. A thin browser
   client does not need the Gateway host's local model stack.
2. Run `abstractframework doctor --no-environment --json` and inspect version mismatches or
   missing distributions. For a release install, restore the chosen pinned profile instead of
   independently upgrading arbitrary components.
3. Run `abstractframework doctor --no-network --json` for host, disk and command availability
   without HTTP probes. For service checks, run `abstractframework doctor --json`; it makes
   read-only requests to the configured Gateway health, Ollama and LM Studio endpoints. Check
   that these are the endpoints you intended. It does not start a missing service or load a model.
4. Route the actual task to the owning component below. The root manifest describes the release
   matrix; it is not a workflow submission API.

The command uses `ABSTRACTGATEWAY_URL` for the Gateway (default `http://127.0.0.1:8080`),
`OLLAMA_BASE_URL` for Ollama and `LMSTUDIO_BASE_URL` for LM Studio. A connection failure needs
service or address diagnosis; repeatedly reinstalling a profile does not start a service.

## Inspect the matrix

```bash
abstractframework manifest
python -c 'from abstractframework import print_status; print_status()'
```

The manifest is JSON generated from the installed package's release pins. To keep a copy and
verify that it still matches this installation:

```bash
abstractframework manifest --write install-manifest.json
abstractframework manifest --check install-manifest.json
```

`--write` writes the named file. `--check` reads it and exits nonzero on a mismatch. Neither
command installs packages or changes Gateway settings. Do not hand-edit a generated manifest
to claim that a different set of versions is the pinned release.

## Component routes for this profile

- [AbstractCore 2.39.0](https://raw.githubusercontent.com/lpalbou/AbstractCore/v2.39.0/skills/abstractcore/SKILL.md): providers, model discovery and inference.
- [AbstractRuntime 0.21.0](https://raw.githubusercontent.com/lpalbou/AbstractRuntime/v0.21.0/skills/abstractruntime/SKILL.md): durable workflows, effects and replay.
- [AbstractGateway 0.24.0](https://raw.githubusercontent.com/lpalbou/AbstractGateway/v0.24.0/skills/abstractgateway/SKILL.md): HTTP control plane, authentication, models and apps.
- [AbstractMemory 0.5.2](https://raw.githubusercontent.com/lpalbou/AbstractMemory/v0.5.2/skills/abstractmemory/SKILL.md): durable memory and the diary graph.
- [AbstractAssistant 0.19.1](https://raw.githubusercontent.com/lpalbou/AbstractAssistant/v0.19.1/skills/abstractassistant/SKILL.md): desktop, browser and Apple clients.
- [AbstractAgent 0.6.1](https://raw.githubusercontent.com/lpalbou/AbstractAgent/v0.6.1/README.md): agent patterns.
- [AbstractSkill 0.3.13](https://raw.githubusercontent.com/lpalbou/AbstractSkill/v0.3.13/skills/abstractskill/SKILL.md): curated skill installation and management.
- [AbstractSemantics 0.0.5](https://raw.githubusercontent.com/lpalbou/AbstractSemantics/v0.0.5/README.md): semantic predicates and validation.
- [AbstractVoice 0.21.1](https://raw.githubusercontent.com/lpalbou/AbstractVoice/v0.21.1/README.md): speech capabilities.
- [AbstractVision 0.3.36](https://raw.githubusercontent.com/lpalbou/AbstractVision/v0.3.36/README.md): image and video capabilities.
- [AbstractMusic 0.1.17](https://raw.githubusercontent.com/lpalbou/AbstractMusic/v0.1.17/README.md): music generation.
- [Abstract3D 0.3.2](https://raw.githubusercontent.com/lpalbou/Abstract3D/v0.3.2/README.md): 3D capabilities.
- [AbstractCamera 0.2.1](https://raw.githubusercontent.com/lpalbou/AbstractCamera/v0.2.1/skills/camera-piloting/SKILL.md): camera capture tools.
- [AbstractAvatar 0.2.0](https://raw.githubusercontent.com/lpalbou/AbstractAvatar/v0.2.0/skills/abstractavatar/SKILL.md): avatar identity and rendering.
- [AbstractNote 0.3.1](https://raw.githubusercontent.com/lpalbou/AbstractNote/v0.3.1/README.md): note capture and durable ingestion.
- [Full release matrix](https://github.com/lpalbou/AbstractFramework/blob/main/README.md#release-matrix-abstractframework-0141): every Python, npm and Rust version in this profile.

Use a component's own versioned guide for its API and operational limits. Keep credentials in
that component's documented configuration; manifests and doctor output are not a secret store.
