# Acknowledgements

AbstractFramework builds on a great deal of open-source work — thank you to everyone behind it.

## Components

Each component repository (AbstractCore, AbstractRuntime, AbstractGateway, the apps, …) lists the
libraries it depends on in its own acknowledgements. The [README](README.md#package-map) links to
every component.

## What this repository relies on

- [uv](https://docs.astral.sh/uv/) by Astral — the installers use it to provision Python 3.12 and
  install the gateway as an isolated tool.
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) and its prebuilt wheel index —
  in-process GGUF support without a compiler.
- [webrtcvad-wheels](https://pypi.org/project/webrtcvad-wheels/) — prebuilt voice-activity
  detection wheels.
- [nodejs-wheel](https://pypi.org/project/nodejs-wheel/) — Node.js for the browser apps without an
  administrator install.
- [Ollama](https://ollama.com/) and [LM Studio](https://lmstudio.ai/) — local model servers the
  installer can set up with their official installers.
- [setuptools](https://setuptools.pypa.io/) and [pytest](https://pytest.org/) — packaging and
  tests for the meta-package.
- [Mermaid](https://mermaid.js.org/) — the diagrams in the documentation.
- [Contributor Covenant](https://www.contributor-covenant.org/) — the basis of the
  [Code of Conduct](CODE_OF_CONDUCT.md).
