# Changelog

All notable changes to AbstractFramework will be documented in this file.

## [Unreleased]

### Documentation

- New [Troubleshooting](docs/troubleshooting.md) page (installer blocked by macOS, sign-in links,
  ports, network access, providers), and root `CONTRIBUTING.md`, `SECURITY.md`,
  `CODE_OF_CONDUCT.md` and `ACKNOWLEDGEMENTS.md`.
- [Install](docs/install.md) states the one-time **Open Anyway** step for the unsigned Mac
  installer as part of the install, lists every installer option, and documents the gateway's
  Network setting (`abstractgateway network`). `service install` examples no longer pass `--host`,
  which would store `localhost` over a chosen Network mode.
- [Architecture](docs/architecture.md) has a Mermaid component diagram of the released packages.
- README and docs link to each component's GitHub repository.
- `llms-full.txt` now carries the pages the docs index links, including Troubleshooting and the
  installer implementation plan, and no longer includes backlog items or the Agent Skills research
  notes. `python scripts/gen_llms_full.py --check` fails when it is stale or when a docs page is
  missing from the index.

## [0.3.1] - 2026-09-24

A patch release that pins abstractcore 2.15.1 and abstractgateway 0.4.2: download cancels are
recorded and a download that stops on its own says why; the "may not fit" warning states the
totals it compared; one Install button per app; the Assistant appears as an app.

### Changed (pins)

- **abstractcore 2.15.1** (was 2.15.0), **abstractgateway 0.4.2** (was 0.4.1) and
  **AbstractRuntime 0.4.34** (was 0.4.33; abstractgateway 0.4.2 requires it, and it passes who asked
  for a download cancel to AbstractCore), in the base install and in the `apple` / `gpu` extras
  (`abstractgateway[apple|gpu]==0.4.2`). The bootstrap scripts install
  `abstractgateway[<profile>,tray]==0.4.2`. The other pins are unchanged: abstractagent 0.3.13,
  AbstractMemory 0.3.0, abstractsemantics 0.0.5, abstractvoice 0.11.4, abstractvision 0.3.29,
  abstractmusic 0.1.15, abstractassistant 0.5.0. Unchanged too: `abstractgateway-console` 0.8.0
  and the browser apps (continuum 0.3.0, entity 0.2.0, flow 0.3.20, code 0.4.2, observer 0.1.12).
- Container images released with it: `ghcr.io/lpalbou/abstractgateway:0.4.2` (and `0.4.2-gpu`)
  and `ghcr.io/lpalbou/abstractcore-server:2.15.1`.

### What the new pins bring

- **Downloads.** A download that stops on its own is never reported "cancelled": a cancel records
  who asked for it (console, API, CLI, another process), and a download that ends says why in one
  plain sentence (a dropped connection, a Hub error, a full disk, a restart). The download stops
  when the process that started it exits. In the console, a stray click no longer cancels a
  download: Cancel asks first ("Stop this download?").
- **Fit warning.** A model's "may not fit" warning states the two totals its verdict compared: the
  total need (weights plus working memory and cache) and the memory a model can use (the ceiling
  minus the part kept free for the system).
- **Apps.** Each app card has one **Install** button; the card then offers **Open** (and **Open in
  Terminal** for Code, whose install brings the terminal app along).
- **The Assistant is an app.** AbstractAssistant, the desktop menu-bar app, has its own card in
  the gateway console: install it and open it from there (on the gateway's computer).

## [0.3.0] - 2026-09-24

A Mac install that needs no Terminal knowledge (a `.pkg` or a double-click `.command`, and an
uninstaller), install failures explained in plain words, and the meta-package pins abstractcore
2.15.0 and abstractgateway 0.4.1.

### Changed (pins)

- **abstractcore 2.15.0** (was 2.14.0) and **abstractgateway 0.4.1** (was 0.3.0; 0.4.0 was never
  published), in the base install and in the `apple` / `gpu` extras
  (`abstractgateway[apple|gpu]==0.4.1`). The bootstrap scripts install
  `abstractgateway[<profile>,tray]==0.4.1` and, with `--with-console`, `abstractgateway-console`
  0.8.0 (was 0.7.0). The other pins are unchanged: AbstractRuntime 0.4.33, abstractagent 0.3.13,
  AbstractMemory 0.3.0, abstractsemantics 0.0.5, abstractvoice 0.11.4, abstractvision 0.3.29,
  abstractmusic 0.1.15, abstractassistant 0.5.0.
- Browser apps released with it (`--with-apps`, `npx`): `@abstractframework/continuum` 0.3.0 (was
  0.2.0) and `@abstractframework/entity` 0.2.0 (was 0.1.0); flow 0.3.20, code 0.4.2 and observer
  0.1.12 are unchanged.
- Container images released with it: `ghcr.io/lpalbou/abstractgateway:0.4.1` and
  `ghcr.io/lpalbou/abstractcore-server:2.15.0`.
- Workspace scripts (`scripts/lib/packages.txt`): abstractgateway depends on abstractcore directly,
  so `deps.sh` and `build.sh` order it after abstractcore.

### Added

- **A Mac install that needs no Terminal knowledge.** `scripts/lib/build_macos_installer.sh`
  builds `AbstractFramework-Installer.pkg` (payload-free, "install for me only", no password) and
  `AbstractFramework-Installer-macOS.zip` (`Install AbstractFramework.command` and
  `Uninstall AbstractFramework.command`). Both open the same `install.sh` in Terminal with a
  banner, so every step stays visible and logged; the browser opens AbstractFramework, signed in,
  at the end. The script signs and notarizes the `.pkg` when given a Developer ID
  (`AF_PKG_SIGN_IDENTITY`, `AF_NOTARY_PROFILE`); without one it says the build is unsigned.
- **`scripts/uninstall.sh`**: asks before removing anything, removes the login item, the running
  gateway and the gateway tool, and asks separately whether to delete your data (`--purge`) and,
  when the installer added uv, uv with its Python and download cache (`--remove-uv`, about
  2.5 GB after an Apple Silicon install). `--yes` runs without questions.
- **`install.sh --interactive`** asks whether to start AbstractFramework at login (default yes; a
  previous "no" is remembered) and, on `--uninstall`, the data and uv questions. Questions go to
  the terminal, so it works through `curl | sh`. Answering "no" after an earlier "yes" removes the
  login item and starts the gateway in the background.

### Changed

- **Every install failure says what to do next, in plain words.** `install.sh` checks internet
  access to PyPI before changing anything (naming the proxy when one is set), recognises a
  connection that drops mid-install, stops on folders it cannot write (with the exact
  `sudo chown` fix), restarts itself natively when Terminal runs under Rosetta on Apple Silicon
  (and explains the Terminal setting when piped), warns on macOS older than 13, and says why an
  Apple Silicon Mac on macOS 13 gets the light profile. `install.ps1` has the same network check
  and messages.
- **Re-runs repair and stay quiet.** A gateway command that no longer starts (an interrupted or
  damaged install) is reinstalled in place; a registered, running, unchanged login item is left
  alone instead of restarted; an already-configured shell profile no longer produces a
  `uv tool update-shell` warning. The health wait is 180 s (the first start loads the engines) with
  a progress line every 15 s.
- **The gateway's Network setting decides where it listens, not the installer.** `install.sh` and
  `install.ps1` pass only `--port` to `abstractgateway service install`, so re-running the
  installer keeps a "Local network" choice. Without a login
  item (background mode) they store the setting first (`abstractgateway network set localhost
  --port N` when nothing is stored; a stored mode is kept and only the port aligned) and start plain
  `abstractgateway serve`. Gateways without the `network` command keep the old
  `serve --host 127.0.0.1 --port N`. The login item itself runs plain `serve` from
  abstractgateway 0.4.1.
- The installer ends with a short plain-language summary (where AbstractFramework is, that it
  starts at login, the menu-bar icon, how to remove it) before the technical details.
- `docs/install.md` is rewritten from a non-technical user's point of view (download, what you
  will see, a table of every failure message and what to do, how to remove it); the one-line,
  options and profile material follows under "Advanced". README and getting-started match.
- **llama.cpp GGUF is back in the one-line install, without a compiler.** `install.sh` and
  `install.ps1` take `llama-cpp-python` from upstream's prebuilt wheels for every profile, light
  included: Metal 0.3.28 on Apple Silicon, CPU 0.3.35 on glibc Linux x86_64/aarch64 and Windows
  x64 (`--find-links` on the package page of abetlen's wheel index, `--constraints
  uv-constraints.txt`, `--no-build-package llama-cpp-python` so the PyPI sdist is never built).
  Where no wheel exists (Intel Mac, musl Linux, Windows on ARM) or the wheel install fails, the
  script installs without it and prints `GGUF (llama.cpp) skipped: no prebuilt wheel for this
  machine; re-run with --full after installing a C compiler`. The summary's `GGUF:` line says what
  was installed. `--full` builds llama.cpp from source, in the light profile too.

### Known limitations

These are unchanged from 0.2.1. The one-line installer is not affected by the first two: it
installs the gateway, not `abstractassistant`, and builds pure-Python source packages.

- A plain `pip install abstractframework` on Linux builds `evdev` from source (a C compiler and
  kernel headers), through `abstractassistant` 0.5.0 → `pynput`.
- `langdetect`, `antlr4-python3-runtime`, `encodec` and `transformers-stream-generator` are
  published as source only; they are pure Python and build without a compiler.
- `abstractframework[gpu]` on Linux needs glibc 2.35 or later (Ubuntu 22.04+): `mlx[cuda13]`,
  pulled by `abstractvision[all-gpu]` through `mlx-gen`, has only `manylinux_2_35` wheels.
- `AbstractFramework-Installer.pkg` is not signed with an Apple Developer ID: macOS asks you to
  allow it once (**Open Anyway** in **System Settings > Privacy & Security**). The one-line install
  is not affected.

## [0.2.1] - 2026-09-24

Patch release: the one-line install works on a machine without a C compiler, and the
meta-package pins abstractvoice 0.11.4. Everything else is unchanged from 0.2.0.

### Changed

- **abstractvoice 0.11.4** (was 0.11.3). It takes voice activity detection from
  `webrtcvad-wheels`, which ships prebuilt wheels for macOS arm64, Linux and Windows, instead
  of `webrtcvad`, which is source-only on PyPI and needs a compiler. This is the pin that made
  `pip install abstractframework[apple]` build `webrtcvad` from source. The other pins are
  unchanged: abstractgateway 0.3.0, abstractcore 2.14.0, AbstractRuntime 0.4.33.

### Fixed

- **One-line install needs no compiler.** On a Mac without Xcode Command Line Tools the gateway
  install failed building `webrtcvad` from source, and `llama-cpp-python`,
  `stable-diffusion-cpp-python` and `aec-audio-processing` would have failed next. `install.sh` and
  `install.ps1` now run `uv tool install` with `--with 'webrtcvad-wheels>=2.0.14'`, an overrides
  file (`uv-overrides.txt` in the gateway data directory) that drops `webrtcvad`, keeps `vllm` to
  Linux and leaves out the three compiled extras, plus `--no-build-package` for those packages so
  a missing wheel fails fast instead of starting a compiler. The install runs from the data
  directory and names the file relatively, because uv splits an `--overrides` value at whitespace
  (`Application Support`). On macOS, Linux and Windows the preflight says when no compiler is
  present, and that this is fine; the summary says what was skipped.

### Added

- **`--full` (Windows: `-Full`)** keeps the compiled extras (llama.cpp GGUF, stable-diffusion.cpp,
  echo cancellation) and builds them from source. It needs a C/C++ compiler and stops before
  installing when none is found.

## [0.2.0] - 2026-09-23

Install the framework with one line, sign in to the gateway console with a one-time link, and
manage local models and engines from the console, the terminal or the command line.

### Added

- **One-line install.** `scripts/install.sh` (macOS, Linux) and `scripts/install.ps1` (Windows 10
  22H2+ / 11, PowerShell 5.1 and 7) install uv and Python 3.12 when needed, install the pinned
  gateway as a uv tool (`abstractgateway[<profile>,tray]==0.3.0`, profile picked from the machine),
  register it to start at login (`abstractgateway service install`), start it on `127.0.0.1`,
  wait for `/api/health`, and open the console through a one-time sign-in link. No admin rights
  and no system Python are needed:

  ```bash
  curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | sh
  ```

  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1 | iex"
  ```

  Options: `--profile`, `--port`, `--with-apps` (Node.js through `nodejs-wheel`), `--with-ollama`,
  `--with-lmstudio`, `--with-console`, `--with-code-cli`, `--with-core-cli`, `--no-service`,
  `--no-open`, `--pin`, `--print` (dry run), `--uninstall [--purge]`. Re-running upgrades or
  repairs in place. See [Install](docs/install.md).
- **First-run wizard.** Through the pinned gateway 0.3.0, a bare `abstractgateway serve` binds
  `127.0.0.1`, creates the admin user and prints a one-time console link; the console's first-run
  guide sets up a local engine, a default model that fits the machine, and the apps.
- **Models and Engines in both entry points.** Through the pinned AbstractCore 2.14.0 and gateway
  0.3.0, `abstractcore serve` and `abstractgateway serve` both offer **Models** (catalog with a fit
  verdict for this machine, installed models with sizes, download, delete) and **Engines**
  (detect and install Ollama, LM Studio, MLX, llama.cpp; every install shows its command first)
  in their web consoles, their terminal consoles (`abstractcore-console`,
  `abstractgateway-console`) and on the command line (`abstractcore models|engines`,
  `abstractgateway models|engines`). `abstractcore serve` gains a web console at `/console`.
- **Engine installs** from the console or the bootstrap flags (`--with-ollama`,
  `--with-lmstudio`) use each vendor's official installer.
- `abstractframework doctor` checks the Python range (3.10–3.13), macOS 14+ on Apple Silicon for the
  `apple` profile, uv, Node.js 18+ (system or `nodejs-wheel`), free disk, and reads the gateway
  health (`ABSTRACTGATEWAY_URL`), `abstractgateway-config status --json`, Ollama and LM Studio
  reachability with read-only requests. New `--no-network` and `--timeout`; checks can report
  `info`.
- `CRATE_RELEASE_VERSIONS` lists the crates released with this version; `get_release_profile()`
  returns them under `crates`.
- Workspace scripts for source checkouts:
  - `scripts/lib/packages.txt`: one inventory of the 30 published packages (21 repositories) with
    registry names, sub-paths, dependency tiers and edges, read by every workspace script.
    `scripts/deps.sh` prints the tiers with their edges and reverse dependencies (`rdeps`) and
    validates the inventory against the package files (`check`).
  - `scripts/push.sh` (dry run by default, `--yes` to push `main`, never forced) and
    `scripts/pull.sh` (fetch + fast-forward only), grouped by tier.
  - `scripts/status.sh --registry` compares local versions with PyPI, npm and crates.io;
    `--versions` and `--tiers` add the local versions and the dependency view.
  - `scripts/build.sh` builds every package in tier order, including the Rust crates
    `abstracttui`, `abstractcore-console`, `abstractcode` and `abstractgateway-console`. New
    `--plan` and `AF_VENV_DIR`; `--python/--npm/--rust` combine; the script exits non-zero when a
    selected build fails.
  - See [Workspace scripts](docs/workspace-scripts.md).

### Changed

- The release profile pins the packages released on 2026-09-23. `pip install abstractframework`
  (and the `apple` / `gpu` extras) installs exactly these versions:

  | Registry | Package | 0.1.12 | 0.2.0 |
  |---|---|---|---|
  | PyPI | `abstractgateway` (`[apple]`, `[gpu]` in the profiles) | 0.2.30 | **0.3.0** |
  | PyPI | `abstractcore` | 2.13.42 | **2.14.0** |
  | PyPI | `AbstractRuntime` | 0.4.32 | **0.4.33** |
  | PyPI | `abstractassistant` (`[apple]` on macOS, `[gpu]` in the profiles) | 0.5.0 | 0.5.0 |
  | PyPI | `abstractagent` | 0.3.13 | 0.3.13 |
  | PyPI | `AbstractMemory` | 0.3.0 | 0.3.0 |
  | PyPI | `abstractsemantics` | 0.0.5 | 0.0.5 |
  | PyPI | `abstractvoice` | 0.11.3 | 0.11.3 |
  | PyPI | `abstractvision` | 0.3.29 | 0.3.29 |
  | PyPI | `abstractmusic` | 0.1.15 | 0.1.15 |
  | npm | `@abstractframework/flow` | 0.3.20 | 0.3.20 |
  | npm | `@abstractframework/code` | 0.4.2 | 0.4.2 |
  | npm | `@abstractframework/observer` | 0.1.12 | 0.1.12 |
  | npm | `@abstractframework/continuum` | 0.2.0 | 0.2.0 |
  | npm | `@abstractframework/entity` | 0.1.0 | 0.1.0 |
  | crates.io | `abstractgateway-console` | 0.6.0 | **0.7.0** |
  | crates.io | `abstractcore-console` | — | **0.2.0** (new) |
  | crates.io | `abstractcode` | 0.5.1 | 0.5.1 |
  | crates.io | `abstracttui` | 0.6.0 | 0.6.0 |
  | GHCR | `ghcr.io/lpalbou/abstractgateway` | 0.2.30 | **0.3.0** |
  | GHCR | `ghcr.io/lpalbou/abstractcore-server` | 2.13.42 | **2.14.0** |

  `RELEASE_VERSIONS`, `NPM_RELEASE_VERSIONS`, `CRATE_RELEASE_VERSIONS`, `abstractframework doctor`,
  the bootstrap scripts and the generated `docs/installers/install-manifest.json` follow the same
  matrix.
- `abstractgateway serve` and `abstractcore serve` bind `127.0.0.1` by default when no auth is
  configured (pinned packages). See the gateway and AbstractCore changelogs for the details.
- Install manifest schema version 2: new `bootstrap` section (gateway pin, Python version, extras
  per profile, script URLs, flags); `post_install` is console-first (`abstractgateway serve` on
  `127.0.0.1`, `/console`, claim link, service) and no longer lists `abstractcore --config`.
- `docs/installers/` describes the script bootstrap and the gateway console as the install
  experience (ADR-0038) instead of a GUI installer manager with signed per-app packages.
- Linux ARM64 installs no longer need a C compiler with the pinned gateway. Older gateway pins
  (`--pin 0.2.x`) still need `gcc` to build `psutil`; the installer warns during preflight.
- The AbstractCore server container image is documented under its published name,
  `ghcr.io/lpalbou/abstractcore-server`.

### Known limitations

- `install.ps1` is exercised in CI on Windows; the login entry created by
  `abstractgateway service install` on Windows is experimental.

## [0.1.12] - 2026-09-23

### Changed

- The release profile now pins the packages released on 2026-09-23. `pip install abstractframework`
  (and the `apple` / `gpu` extras) installs exactly these versions:

  | Registry | Package | 0.1.11 | 0.1.12 |
  |---|---|---|---|
  | PyPI | `abstractgateway` (`[apple]`, `[gpu]` in the profiles) | 0.2.28 | **0.2.30** |
  | PyPI | `abstractassistant` (`[apple]` on macOS, `[gpu]` in the profiles) | 0.4.11 | **0.5.0** |
  | PyPI | `abstractcore` | 2.13.38 | **2.13.42** |
  | PyPI | `AbstractRuntime` | 0.4.29 | **0.4.32** |
  | PyPI | `abstractagent` | 0.3.12 | **0.3.13** |
  | PyPI | `AbstractMemory` | 0.2.6 | **0.3.0** |
  | PyPI | `abstractsemantics` | 0.0.4 | **0.0.5** |
  | PyPI | `abstractvoice` | 0.10.18 | **0.11.3** |
  | PyPI | `abstractvision` | 0.3.26 | **0.3.29** |
  | PyPI | `abstractmusic` | 0.1.13 | **0.1.15** |
  | npm | `@abstractframework/flow` | 0.3.19 | **0.3.20** |
  | npm | `@abstractframework/code` | 0.3.9 | **0.4.2** |
  | npm | `@abstractframework/observer` | 0.1.11 | **0.1.12** |
  | npm | `@abstractframework/continuum` | — | **0.2.0** (new) |
  | npm | `@abstractframework/entity` | — | **0.1.0** (new) |
  | crates.io | `abstractcode` | — | **0.5.1** |
  | crates.io | `abstractgateway-console` | — | **0.6.0** |
  | crates.io | `abstracttui` | — | **0.6.0** |
  | GHCR | `ghcr.io/lpalbou/abstractgateway` | — | **0.2.30** (`0.2.30-gpu` experimental) |
  | GHCR | `ghcr.io/lpalbou/abstractcore` | — | **2.13.42** |

  `RELEASE_VERSIONS`, `NPM_RELEASE_VERSIONS`, `abstractframework doctor` and the generated
  `docs/installers/install-manifest.json` follow the same matrix. The manifest now lists the
  Continuum console and the Entity manager as npm apps, and the Apple profile states its
  macOS 14+ prerequisite.
- All three profiles resolve on Python 3.10, 3.11, 3.12 and 3.13 (Python 3.13 is now a declared
  classifier). In the `apple` and `gpu` profiles, F5-TTS voice cloning needs Python 3.11+.
- AbstractCode is a Rust terminal client (`cargo install abstractcode`, or a prebuilt binary from
  its GitHub release) plus the browser client `npx @abstractframework/code`. It is no longer a
  Python package, so the meta-package does not install it.
- Documentation describes the released framework: the release matrix, per-profile Python and OS
  requirements, the gateway's built-in web console at `/console` and the terminal console
  (`cargo install abstractgateway-console`), the npm apps, the Rust clients and the container
  images.

### Added

- Performance work shipped through the pinned packages: live prefill and generation progress for
  LLM calls (streamed through the gateway ledger and shown by AbstractCode), and a much lower
  per-turn orchestration overhead for chat workflows on the gateway, including on large run
  stores. Restart a running gateway to pick these up.
- Source-checkout tooling:
  - `scripts/af.sh` / `scripts/af-local.sh` and `scripts/start.sh` / `scripts/start-local.sh`
    start the gateway first, then the browser apps, in one terminal. A supervisor keeps the gateway
    running across app failures, restarts crashed apps within a bounded budget, and stops
    everything cleanly on Ctrl-C. `start-local.sh` builds only when you pass `--build`
    (`--build=light|apple|gpu|auto`).
  - Launchers for the Continuum console (`scripts/console[-local].sh`) and the Code Web UI
    (`scripts/code[-local].sh`).
  - `scripts/clone.sh` clones every released sibling repository, including AbstractCamera,
    AbstractContinuum, AbstractEntity, Abstract3D, AbstractUIC and AbstractTUI, into lowercase
    directories. `scripts/build.sh` builds the Rust crates (`--rust`), the new npm apps and
    AbstractCamera, and when an editable install cannot be resolved it asks `uv` to name the
    conflicting requirements.

### Fixed

- Gateway launchers wait for the previous gateway process to exit and check the runner lock before
  starting, so a restarted gateway always runs its workflows.

### Known limitations

- The `abstractcore[all]` extra cannot be resolved on any platform. The framework profiles do not
  use it; use `abstractcore[all-apple]` or `abstractcore[all-gpu]` instead.
- The full local-engine profile extras are named `all-apple` / `all-gpu` in AbstractCore,
  AbstractVoice, AbstractVision, AbstractMusic, AbstractMemory and Abstract3D, and `apple` / `gpu`
  in AbstractRuntime, AbstractAgent, AbstractGateway and AbstractAssistant. In AbstractCore,
  `apple` / `gpu` currently mean the MLX-only / vLLM-only subsets. A later release will align
  every package on `apple` / `gpu` for the full profile, keeping the old names as aliases for one
  release.

## [0.1.11] - 2026-06-14

### Changed

- Repinned the root release profile to `abstractassistant==0.4.11` after the follow-up Gateway history/message-id patch so the meta-package only points at the final published assistant build from this release wave.

## [0.1.10] - 2026-06-14

### Changed

- Synced the root Light, Apple, and GPU release profile to the published framework wave:
  `abstractgateway==0.2.28`, `abstractassistant==0.4.10`, `abstractcore==2.13.38`,
  `AbstractRuntime==0.4.29`, `abstractagent==0.3.12`, `abstractvoice==0.10.18`,
  `abstractvision==0.3.26`, `@abstractframework/flow==0.3.19`, and
  `@abstractframework/observer==0.1.11`.
- Regenerated the installer manifest and package/version guards from the root release profile so CLI doctor/manifest checks, install docs, and profile tests all match the published package set.

## [0.1.9] - 2026-06-06

### Changed

- Updated root Light, Apple, and GPU release pins to consume the permissive PDF stack:
  `abstractgateway==0.2.27`, `abstractcore==2.13.35`, `AbstractRuntime==0.4.28`,
  and `abstractvision==0.3.22`.
- The root install profiles now inherit Runtime's always-installed `pypdf` and
  `reportlab` PDF read/write path while keeping PyMuPDF-family dependencies out
  of default installs.

## [0.1.8] - 2026-06-03

### Changed

- Updated the root release profile pins and generated installer manifest to use
  `abstractgateway==0.2.26`, `abstractcore==2.13.32`, `AbstractRuntime==0.4.27`,
  `abstractagent==0.3.11`, `abstractcode==0.3.9`, `abstractassistant==0.4.9`,
  `abstractvision==0.3.19`, `abstractmusic==0.1.13`, and
  `@abstractframework/flow==0.3.18`.
- Updated Gateway/Flow install and auth docs to use Gateway user auth and the
  generated `default/admin` browser-login token instead of legacy
  `ABSTRACTGATEWAY_AUTH_TOKEN` examples for browser sign-in.
- Documented the breaking Gateway defaults cleanup for the next Gateway release:
  Gateway no longer reads `config/capability_defaults.json` overlays and uses
  only Core config files (`config/abstractcore.json`) for baseline and
  per-runtime capability defaults.

## [0.1.7] - 2026-05-31

### Added

- Added the `abstractframework` CLI with `doctor` checks for Python/package
  version consistency and `manifest` commands for installer manifest generation
  and drift checks.
- Added a generated installer manifest and schema under `docs/installers/`,
  derived from the root release pins and covering the Light, Apple, and GPU
  profiles.
- Added a public install chooser that explains Light as the remote-first full
  framework profile, with Apple and GPU as hardware-local profiles.

### Changed

- Moved installer application source out of the root framework repository into
  the standalone `AbstractInstallers` repository. The root package remains the
  release profile, documentation hub, and manifest source of truth.
- Updated local source helper scripts to use `--light` as the canonical
  remote-first profile name while keeping `--base` as a compatibility alias.

### Removed

- Removed the tracked `abstractinstallers/` prototype source tree from the root
  `AbstractFramework` repository and package source distribution.

## [0.1.6] - 2026-05-31

### Changed

- Bumped the pinned framework release set:
  `abstractcore==2.13.31`, `AbstractRuntime==0.4.26`,
  `abstractagent==0.3.10`, `abstractgateway==0.2.23`,
  `abstractflow==0.3.17`, `abstractcode==0.3.8`,
  `abstractassistant==0.4.8`, `AbstractMemory==0.2.6`,
  `abstractsemantics==0.0.4`, `abstractvoice==0.10.17`,
  `abstractvision==0.3.18`, and `abstractmusic==0.1.12`.
- Propagated the MLX-Gen `0.18.8` vision runtime floor through AbstractVision and AbstractCore so Apple Silicon installs can use the latest Wan 2.2 video runtime support.
- Included the Gateway multi-user/session control-plane release boundary, including per-user runtimes, admin user management, provider endpoint profiles, and cross-app hosted Gateway URL/session guards.

## [0.1.5] - 2026-05-29

### Changed

- Refactored the meta-package install profiles to only support:
  `pip install abstractframework` (remote-first),
  `pip install "abstractframework[apple]"`, and
  `pip install "abstractframework[gpu]"`.
  Removed legacy profiles like `all`, `backend`, `all-apple`, and `all-gpu`.
- Aligned the meta-package pins with the current repo package versions and their
  revised profile wiring (Gateway-first stack + Flow + CLI app).
- Bumped the pinned framework release set:
  `abstractcore==2.13.30`, `AbstractRuntime==0.4.25`,
  `abstractagent==0.3.9`, `abstractgateway==0.2.21`,
  `abstractflow==0.3.16`, `abstractcode==0.3.7`,
  `abstractassistant==0.4.7`, `AbstractMemory==0.2.6`,
  `abstractsemantics==0.0.4`, `abstractvoice==0.10.17`,
  `abstractvision==0.3.17`, and `abstractmusic==0.1.12`.
- Installed the full Python ecosystem by default (including `abstractassistant`), and
  upgraded it to hardware-local profiles via `abstractframework[apple]` / `[gpu]`.
- Updated the macOS installer manifest to install `abstractframework[apple]` for the full framework.

### Documentation

- Revised the core documentation set for a clearer “two entry points” mental model (AbstractCore SDK vs AbstractGateway control plane), plus a more practical onboarding flow for authoring/deploying `.flow` bundles and monitoring/scheduling runs with AbstractObserver.
- Removed stale install instructions suggesting `abstractgateway[http]` (and `abstractgateway[http,telegram]`) are required for HTTP/SSE or Telegram bridge support; the base `abstractgateway` install already includes the server stack and these extras are compatibility aliases.

## [0.1.4] - 2026-05-26

### Changed

- Bumped the pinned framework release set:
  `abstractcore==2.13.25`, `abstractruntime==0.4.21`,
  `abstractagent==0.3.7`, `abstractflow==0.3.13`,
  `abstractgateway==0.2.17`, `abstractmemory==0.2.6`,
  `abstractsemantics==0.0.4`, `abstractvoice==0.10.16`,
  `abstractvision==0.3.12`, `abstractmusic==0.1.11`, and
  `abstractassistant==0.4.5`.
- Updated the global install profile wiring (core default extras, Gateway/Memory
  extras, and Apple/GPU aggregate profiles) to match the current gateway-first
  release set.
- Tightened repo hygiene so local-only artefacts and sibling projects (venvs,
  caches, and independent repos like SmartNote / AI-Space) stay out of
  AbstractFramework version control and distribution sources.
- Scoped pytest discovery to the root `tests/` folder to avoid collecting tests
  from sibling checkouts that are present locally for orchestration.

### Added

- Added installer documentation and scaffolding under `abstractinstallers/`,
  including:
  - A macOS Tauri v2 installer-manager prototype (`abstractframework-macos`)
  - An AbstractCore installer script + GUI prototype (`abstractcore`)
  - A Tauri init template for future installers (`tauri-init-template`)
- Added helper scripts for orchestration and local dev:
  `scripts/commit.sh`, `scripts/gateway-flow.sh`, and `scripts/gateway-flow-local.sh`.
- Added a root-level install-profile pin alignment test:
  `tests/test_install_profiles.py`.
- Expanded ecosystem docs (ADRs, guides, scenarios, installers pages, and
  backlog entries) to reflect current gateway-first deployment patterns.

### Removed

- Removed an internal memory summary artefact that should not have been tracked.

## [0.1.3] - 2026-05-08

### Changed

- Bumped the pinned framework release set for the install-profile alignment:
  `abstractcore==2.13.12`, `abstractruntime==0.4.8`,
  `abstractagent==0.3.2`, `abstractgateway==0.2.4`,
  `abstractmemory==0.2.4`, `abstractsemantics==0.0.3`,
  `abstractvoice==0.9.2`, `abstractvision==0.3.3`, and
  `abstractmusic==0.1.1`.
- Added native hardware aggregate extras:
  `abstractframework[apple]`, `abstractframework[gpu]`,
  `abstractframework[all-apple]`, and `abstractframework[all-gpu]`.
  The `apple` and `gpu` root profiles delegate to the matching full Gateway
  deployment profile; the `all-*` profiles pin the whole ecosystem.
- Documented the Python-vs-Docker split: Python installs can use native Apple
  and GPU profiles, while Docker remains the lightweight Gateway server image
  plus the explicit NVIDIA server image.

## [0.1.2] - 2026-02-12

### Changed

- **Bumped `abstractcore` pin from `2.11.8` to `2.11.9`**
- **Fixed `abstractgateway` pin from `0.2.1` to `0.1.0`** (aligned with actual repo version)
- **Bumped framework version from `0.1.1` to `0.1.2`**

### Documentation

- **Comprehensive documentation overhaul** surfacing 21 previously hidden capabilities:
  - Added "What Can You Build?" section to README with 12 concrete use cases
  - Added "Key Capabilities in Depth" section with code examples (MCP, structured output, streaming, voice, vision, glyph compression, embeddings, server, scheduling, event bridges, CLI apps, evidence/provenance)
  - Enhanced docs/README.md as a welcoming hub with "What's Possible" capability overview
  - Updated docs/architecture.md with MCP integration, evidence/provenance, scheduled workflows, split API/runner, and media pipeline architectures
  - Added 3 new getting-started paths: MCP Integration (Path 13), Structured Output (Path 14), OpenAI-Compatible Server (Path 15)
  - Added 17 new FAQ entries covering MCP, structured output, streaming, async, glyph compression, embeddings, server mode, CLI apps, snapshots, interaction tracing, voice cloning, GGUF models, scheduled workflows, event bridges, split API/runner, SQLite backend
  - Enhanced docs/api.md with "Where to Find Specific APIs" navigation table
  - Updated docs/glossary.md with 9 new terms (Snapshot, History bundle, Provenance, Evidence, MCP, Event bridge, Structured output, Glyph compression, Interaction trace)
  - Updated llms.txt with full ecosystem repo list and enriched descriptions

## [0.1.1] - 2026-02-04

### Added

- **Unified release profile API metadata** in `abstractframework/__init__.py`:
  - `RELEASE_VERSIONS` (pinned package versions for global profile)
  - `CORE_DEFAULT_EXTRAS` (default AbstractCore extras installed by this release)
  - `get_release_profile()` helper

### Changed

- **Global `abstractframework==0.1.1` profile is now full-stack by default**:
  - Pins and installs all ecosystem Python packages together:
    - `abstractcore==2.11.8`
    - `abstractruntime==0.4.2`
    - `abstractagent==0.3.1`
    - `abstractflow==0.3.7`
    - `abstractcode==0.3.6`
    - `abstractgateway==0.2.1`
    - `abstractmemory==0.0.2`
    - `abstractsemantics==0.0.2`
    - `abstractvoice==0.6.3`
    - `abstractvision==0.2.1`
    - `abstractassistant==0.4.2`
  - Installs `abstractcore` with `openai,anthropic,huggingface,embeddings,tokens,tools,media,compression,server`
  - Installs `abstractflow` with `editor`
- **Docs repositioned to a single-entrypoint experience**:
  - `README.md` now leads with one-command install and pinned version table
  - `docs/README.md`, `docs/getting-started.md`, and `docs/faq.md` now describe the full-release install path first
  - Added a dedicated "create more solutions" section in `README.md` for `.flow`-based specialized agent deployment
- Updated `scripts/install.sh` to install `abstractframework==0.1.1` directly
- Updated status output in `abstractframework.print_status()` to point to one-command full install

### Technical (not user-facing)

- Switched `pyproject.toml` dependency strategy from open-ended/minimal constraints to pinned ecosystem versions for deterministic global installs

## [0.1.1] - 2026-02-04

### Added

- Initial release of AbstractFramework as an **Agentic OS** — an open-source operating system for AI agents
- Positioned as a complete, end-to-end infrastructure with no black boxes and no external dependencies
- Comprehensive documentation:
  - `README.md` - Main entry point and overview
  - `docs/getting-started.md` - Installation and setup guide
  - `docs/architecture.md` - System design and components
  - `docs/configuration.md` - Environment variables reference
  - `docs/faq.md` - Frequently asked questions
- Installation script (`scripts/install.sh`)
- Meta-package with optional dependencies:
  - `abstractframework[all]` - Full installation
  - `abstractframework[backend]` - Backend services only
  - Individual component extras

### Components

Python packages (PyPI):
- abstractcore - LLM abstraction layer
- abstractruntime - Durable execution engine
- abstractagent - Agent framework
- abstractflow - Workflow orchestration
- abstractcode - AI coding assistant backend
- abstractgateway - HTTP API gateway
- abstractmemory - Temporal triple store (KG substrate)
- abstractsemantics - Semantics registry + KG assertion schema helpers
- abstractvoice - Speech-to-text & TTS
- abstractvision - Image & video processing
- abstractassistant - High-level assistant API

JavaScript packages (npm):
- abstractobserver - Gateway-only observability UI (Web/PWA)
- @abstractframework/ui-kit - Shared UI components
- @abstractframework/panel-chat - Chat panel components
- @abstractframework/monitor-flow - Flow monitoring components
- @abstractframework/monitor-gpu - GPU monitoring widget
- @abstractframework/monitor-active-memory - Memory explorer components
