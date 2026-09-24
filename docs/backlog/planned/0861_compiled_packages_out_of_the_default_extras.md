# 0861 — Compiled packages out of the default `all-apple` / `all-gpu` extras

> Package: abstractcore, abstractvision, abstractvoice (root pins follow)
> Type: task
> Created: 2026-09-24
> Priority: normal
> Labels: install, packaging, wheels

## Summary

Three packages in the default heavy extras are published on PyPI as source only and need a C/C++
compiler: `llama-cpp-python` (abstractcore `all-apple`, `all-gpu`, `huggingface`),
`stable-diffusion-cpp-python` (abstractvision `apple`, `local`, `all-*`) and `aec-audio-processing`
(abstractvoice `apple`, `gpu`, `all-*`, Python 3.11+; wheels exist only for Windows and macOS 15+).
`vllm` in abstractcore `all-gpu` has no Windows build at all. On 2026-09-24 the first real-user
install on a Mac without Xcode Command Line Tools failed on this class of dependency.

The one-line installers work around it with uv overrides, `--no-build-package` and upstream's
prebuilt llama.cpp wheels (root `main`, 2026-09-24). The plain pip route
(`pip install abstractframework[apple]`, `pip install abstractcore[all-apple]`) cannot, because pip
has no way to skip a transitive dependency. The owner decided on 2026-09-24 to leave the package-side
fix for a later wave rather than release three patches now.

## Acceptance criteria

- [ ] `abstractcore`: `llama-cpp-python` moves out of `all-apple` / `all-gpu` into an opt-in extra
      (for example `gguf`); `vllm` carries `; sys_platform == 'linux'`.
- [ ] `abstractvision`: `stable-diffusion-cpp-python` moves out of `apple` / `all-*` into an opt-in
      extra (`sdcpp` already exists).
- [ ] `abstractvoice`: `aec-audio-processing` gets a platform marker (Windows, macOS 15+) or moves to
      an opt-in extra.
- [ ] `uv pip install --dry-run --no-build-package llama-cpp-python --no-build-package
      stable-diffusion-cpp-python --no-build-package aec-audio-processing 'abstractframework[apple]'`
      resolves on macOS arm64, Linux x86_64 and Windows amd64 with Python 3.12.
- [ ] Root pins bumped in one root patch release; docs/install.md says which extras need a compiler.
- [ ] The installers' overrides for these packages are removed once the pins no longer pull them.

## Notes

- Upstream llama.cpp wheels: Metal 0.3.28 works on Apple Silicon (0.3.32–0.3.35 Metal wheels fail
  zip checks), CPU 0.3.35 works on Linux x86_64 and Windows. No Linux aarch64 or Intel macOS wheels.
- Related: 0855 (install wave), 0856 (Windows validation), ADR-0038.

## Status update 2026-09-25 (post-release trace)

Still open at abstractcore 2.15.1 (`all-apple` / `all-gpu` still carry `llama-cpp-python`); the
0.3.0 and 0.3.1 root dry-run matrices resolve only with the installer's rules. Related: 0881
(`evdev` sdist on Linux via abstractassistant).
