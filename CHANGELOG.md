# Changelog

All notable changes to AbstractFramework will be documented in this file.

## [Unreleased]

## [0.6.4] - 2026-09-30

Installer fixes. Every package version is unchanged from 0.6.3.

### Fixed

- **One gateway per data directory when you re-run the installer.** A gateway of this install that
  you started yourself (for example with the summary's Start line) is recognized: it listens on the
  install's port and serves the same data directory, as its serve record
  (`<data dir>/run/gateway-serve.json`) or its `--data-dir` says. `install.sh` and `install.ps1` now
  keep that port and replace the gateway with their own start, instead of moving to the next port
  and starting a second gateway on the same data. A gateway of this install started by hand on
  another port is stopped too. With `--no-start` (`-NoStart`, the console's Update) it keeps
  running and the summary says a restart is due. A program that is not this install's gateway
  keeps the port, as before.
- **A release published minutes earlier installs at once.** The installers pass
  `--refresh-package` for `abstractgateway` and every package of the release matrix to
  `uv tool install`, so uv asks PyPI again instead of using its cached index page (which could say
  "no version of abstractgateway[gpu]==<pin>" until `uv cache clean abstractgateway`).

### Changed

- **Launch flags, not environment variables.** The summary's Start line and the background start
  use `abstractgateway serve --data-dir <data dir>` (plus `--host`/`--port` when the gateway has
  no Network setting) instead of `ABSTRACTGATEWAY_DATA_DIR=... ABSTRACTGATEWAY_USER_AUTH=1`; the
  gateway starts with user auth on by itself. Gateways before 0.3 (`--pin`) keep the environment.

## [0.6.3] - 2026-09-29

The `gpu` setting on NVIDIA machines, speech-to-text in the fresh setup, and loaded image models
that are reused. Pins: AbstractGateway 0.7.4, AbstractCore 2.19.2, AbstractRuntime 0.7.3,
AbstractVoice 0.13.2, AbstractVision 0.3.33 and Abstract3D 0.3.2; the gateway's terminal console is
`abstractgateway-console` 0.11.2, and the browser client AbstractCode web is 0.6.2. Every other
version, and the other terminal clients, are unchanged from 0.6.2.

### Added

- **The `gpu` setting on Linux + NVIDIA, rehearsed on real hardware with this release.** On
  Ubuntu 26.04 with a Quadro RTX 5000 (16 GB, driver 595.91.07, CUDA 13.2; 4 vCPU, 26 GB RAM),
  `install.sh` installed this release's candidate versions from PyPI in 3 min 1 s (AbstractGateway
  0.7.3, AbstractCore 2.19.1, AbstractRuntime 0.7.2, AbstractVoice 0.13.1 and AbstractVision 0.3.32;
  the patch releases listed under Fixed came after this run). The previous
  install had been removed with `uninstall.sh --yes --purge` and uv's download cache cleared; model
  weights, LM Studio and a Rust toolchain were already on the machine. The Python packages took 39 s
  (about 5.8 GB of wheels), llama.cpp's `cu130` build 18 s (726 MB), compiling the two terminal
  clients with cargo 110 s, and the start and health check 5 s. The install added 14.2 GB on disk.
  Its checks reported PyTorch 2.11.0 on CUDA 13.0, llama.cpp 0.3.35 (`cu130`) with GPU offload and
  Whisper on the GPU. Run again, it reported "already up to date" in 10 s. With **Use recommended
  defaults** and the model weights already downloaded:
  - text with LM Studio (`qwen/qwen3.5-9b`, Q4_K_M, 6.5 GB on the GPU): the first gateway request
    took 23 s including loading the model, the next 12 s for a 318-token answer (308 of them
    reasoning); from AbstractCore in Python about 41 tokens/s;
  - text-to-speech with Supertonic, on the processor: 1.1 to 1.4 s per sentence (3.2 s for the
    first gateway request);
  - image generation with FLUX.2 [klein] 4B through Diffusers, with model CPU offload (7.8 GB
    peak): 41 s to load the model, then 15 to 16 s per 1024x1024 image. Each gateway image request
    loads the model again, so one request takes 54 to 59 s;
  - speech-to-text did not work as installed; see Known issues below.

  vLLM 0.22.1 installs with the gpu setting but was not validated: it needs a C compiler
  (`build-essential`) the first time it starts a model, and on GPUs older than compute capability
  8.0 the `--attention-backend TRITON_ATTN` option. See
  [GPU on Linux (NVIDIA)](docs/install.md#gpu-on-linux-nvidia).
- **`install.sh` on Linux + NVIDIA** installs llama.cpp's CUDA build that matches PyTorch's CUDA
  (PyPI's PyTorch for Linux is a CUDA 13 build, which needs NVIDIA driver 580 or newer; with an
  older driver PyTorch and llama.cpp run on the processor) and keeps it only when it
  loads and offloads to the GPU; otherwise the CPU build goes back and the summary says why. At the
  end it checks that PyTorch sees the GPU and which device Whisper uses (`PyTorch:`, `GGUF:` and
  `Voice:` summary lines), and warns when no C compiler is found for vLLM.
- **`install.ps1` on Windows + NVIDIA** picks the GPU stack from `nvidia-smi` (CUDA 13 with driver
  580 or newer and compute capability 7.5 or newer, CUDA 12 with driver 525 or newer, otherwise the
  CPU), installs PyTorch's CUDA build and llama.cpp's matching prebuilt build (CUDA, then Vulkan,
  then CPU), and ends with GPU checks that replace any part that does not work with one that does.
  The Windows gpu setting is implemented and tested with simulated drivers and wheel-only
  resolves, but it has **not yet been validated on real NVIDIA hardware**. See
  [GPU on Windows (NVIDIA)](docs/install.md#gpu-on-windows-nvidia).
- **Live installer progress.** Both installers show uv's output as it comes, with a
  `still working (… elapsed; last: …)` line after 15 seconds of silence, so a multi-GB download no
  longer looks frozen. `install.ps1` announces the big downloads before they start.

### Changed

- **Only the three install settings in hints.** Every install hint across the framework names
  light (`pip install -U abstractcore`), `abstractcore[apple]` or `abstractcore[gpu]`, or says that
  a capability is not available on this machine, never a bare package or a plugin's own extra
  (AbstractCore 2.19.1, AbstractGateway 0.7.3, AbstractVoice 0.13.1, AbstractRuntime 0.7.2,
  Abstract3D 0.3.2).
- **Smaller gpu setting.** The gpu setting no longer installs MLX-Gen (AbstractVision 0.3.32):
  about 2.1 GB less on Linux, and it installs on Linux distributions with an older glibc.
- **`abstractcore[gpu]` installs on Windows with wheels only** (vLLM is Linux only;
  stable-diffusion.cpp and llama.cpp are left to the installer's prebuilt builds on Windows).
- **Recommendations on NVIDIA machines.** **Use recommended defaults** picks FLUX.2 [klein] 4B
  through Diffusers for image generation on an NVIDIA GPU (it fits a 16 GB card), and the LM Studio
  text download is `qwen/qwen3.5-9b@q4_k_m`, which LM Studio offers on Linux and Windows.
- **AbstractRuntime depends on AbstractCore's three settings** (`abstractcore`, `[apple]`, `[gpu]`),
  and `openai` 2.x is allowed across the stack, so the gpu setting resolves a current vLLM.

### Fixed

- **The approval gate shows in every client.** When the agent's tool call waits for approval, a
  browser or phone that opens the same conversation later now shows the same Allow / Deny card and
  "Approval needed" as the client that started the turn, instead of "Running a tool" and a Steer box
  (AbstractCode web 0.6.2 with `@abstractframework/panel-chat` 0.1.20; two-browser end-to-end test).
- **Speech-to-text without an OpenAI key.** Transcription runs on the configured `input.voice`
  route (for example local Whisper) and no longer needs TTS credentials (AbstractCore 2.19.1,
  AbstractVoice 0.13.1).
- **Speech-to-text in the fresh setup.** The fresh-install defaults and **Use recommended defaults**
  set speech input (`input.voice`: faster-whisper, model `base`) with text, voice and images, so a
  new install transcribes locally without an OpenAI key (AbstractCore 2.19.2, AbstractGateway
  0.7.4). An install that earlier release defaults seeded gains the route once, when it is empty; a
  route you set yourself is kept. PyAV is held below 19, which faster-whisper 1.2.1 needs to read
  audio files (AbstractVoice 0.13.2).
- **Use recommended defaults saves every route it reports**, including on a fresh install right
  after the console read the routes (AbstractCore 2.19.2).
- **Whisper on NVIDIA GPUs.** faster-whisper uses CUDA only when CUDA 12 cuBLAS loads (installed
  with the gpu setting on Linux and Windows), and otherwise runs on the CPU with a warning.
- **llama.cpp on CUDA** loads without importing PyTorch first on Linux, and a GGUF model too large
  for the GPU at its full context tries smaller contexts on the GPU before falling back to the CPU.
- **Image generation on smaller GPUs.** A Diffusers pipeline that does not fit the GPU's free
  memory loads with model CPU offload instead of failing with CUDA out of memory. When even the
  largest component does not fit (for example next to a loaded text model), it falls back to
  sequential CPU offload, which uses much less GPU memory and is slower per step (AbstractVision
  0.3.33). On the Quadro RTX 5000, FLUX.2 [klein] 4B at 768x768 and 4 steps peaked near 1.4 GB and
  took 10.9 to 15.6 s, against 13.4 to 18.5 s with model CPU offload; at about 2.3 s per step
  against 1.5 s, models that run many steps are slower with it.
- **A loaded image model is reused.** After **Load** in the console (or `POST /models/load`), image
  and video requests for that model run on the loaded pipeline instead of loading the model again
  for each request (AbstractRuntime 0.7.3, AbstractGateway 0.7.4). On the rehearsal machine,
  FLUX.2 [klein] 4B images through the gateway took 17 to 19 s each instead of 54 to 59 s. A model
  that was not loaded still runs each request in its own process.
- **Unloading an image model frees its memory.** On CUDA, FLUX.2 [klein] 4B with model CPU offload
  left 16.3 GB held after an unload; it now leaves 0.86 GB (AbstractVision 0.3.33).

### Security

- **Email connections verify TLS.** AbstractCore's mail tools (`list_emails`, `read_email`,
  `send_email`) and the gateway's email bridge check the server certificate and host name, and refuse
  before login when the check fails; a server signed by a private CA is trusted with the new
  `ca_file` field of an account (AbstractCore 2.19.2, AbstractGateway 0.7.4).
- **Automations no longer email anyone the model chooses.** With the default automatic tool
  approval, message-sending tools are no longer pre-approved: a `send_email` to your registered
  email runs unattended, any other recipient waits for your approval (AbstractRuntime 0.7.3,
  AbstractGateway 0.7.4).
- A `password_env_var` / `imap_password_env_var` that is not an environment variable name is refused
  instead of being read as the password (AbstractCore 2.19.2, AbstractGateway 0.7.4).

### Found in the rehearsal

Found in the rehearsal on the Quadro RTX 5000 described above, which ran the candidate versions. The
Fixed entries above address each one.

- **Speech-to-text failed on a fresh gpu install**, for two reasons:
  - **Use recommended defaults** did not set the speech input route (`input.voice`). With no route,
    transcription used OpenAI and failed with "OpenAI audio requires OPENAI_API_KEY".
  - PyAV 19.0.0, released on 2026-09-29, removed an option that faster-whisper 1.2.1 uses to read
    audio files. Every transcription through the gateway then failed with `open() got an unexpected
    keyword argument 'metadata_errors'`.

  With the route set to faster-whisper `base` by hand and PyAV 18, faster-whisper transcribed on the
  GPU with no OpenAI key: 1.0 to 2.3 s per gateway request, and 0.3 GB of GPU memory.
- **An image next to a loaded text model ran out of GPU memory on a 16 GB card.** LM Studio's
  `qwen/qwen3.5-9b` keeps 6.5 GB on the GPU while it is loaded. FLUX.2 [klein] needed 7.8 GB even
  with model CPU offload, so the image request failed with CUDA out of memory after three attempts
  (about 2.5 minutes). With the text model unloaded (`lms unload --all`, or the console's model
  list), the same request worked. In this case AbstractVision 0.3.33 falls back to sequential CPU
  offload (see Fixed above).
- **Use recommended defaults could skip the image route on a fresh install.** On an NVIDIA machine,
  if the button was used within a few seconds of the console reading the routes, it could report the
  image route as already set without saving it. Using it again saved it.

## [0.6.2] - 2026-09-29

One line installs, upgrades and repairs AbstractFramework, and **Update** in the consoles and the
menu-bar icon runs that same line. Pins: AbstractGateway 0.7.2, AbstractCore 2.19.0,
AbstractVision 0.3.31, Abstract3D 0.3.1 (new in the matrix: AbstractCore now installs it) and the
terminal consoles `abstractgateway-console` 0.11.1 and
`abstractcore-console` 0.4.1; every other version is unchanged from 0.6.1.

### Changed

- **One line installs, upgrades and repairs.** Re-running the install line (or double-clicking
  **Install AbstractFramework.command** again) finds the existing install and says what it does:
  `AbstractFramework <yours> found: upgrading to AbstractFramework <latest>` or `already up to
  date` for installs from 0.6.2 on, which record their release. An install made by 0.6.1 or
  earlier recorded none, so its first upgrade says `AbstractFramework found (abstractgateway 0.7.1;
  its release was not recorded): upgrading to AbstractFramework 0.6.2`.
  The summary lists what changed, old -> new, under **Changes**, and ends with `Upgraded: …` or
  `Already up to date: …; nothing changed.` `install.ps1` does the same on Windows. See
  [Upgrade](docs/install.md#upgrade).
- **Update in the web console, the terminal console and the menu-bar icon runs the installer**
  (AbstractGateway 0.7.2). For an install made by the AbstractFramework installer, the check
  compares your AbstractFramework release with the latest one, and **Update** runs the latest
  `install.sh` with `--no-start`. Before you confirm, it shows the installer's address, commit,
  sha256 and the exact command. The result says what moved and offers the restart, says
  **already up to date**, or shows why it didn't finish. On Windows, the check shows the PowerShell
  line to paste. See [From the console or the menu-bar icon](docs/install.md#from-the-console-or-the-menu-bar-icon).
- **Your install options are remembered.** A re-run keeps the profile, port, start at login, a
  custom `--data-dir`, and `--no-console`, `--no-code-cli`, `--no-core-cli`, `--no-tray` and
  `--full`, and says which ones it kept. `--with-console`, `--with-code-cli`, `--with-core-cli`,
  `--with-tray` and `--no-full` (Windows: `-WithConsole`, `-WithCodeCli`, `-WithCoreCli`,
  `-WithTray`, `-NoFull`) turn one back.
- **The libraries land on the release's tested versions.** The installer installs AbstractCore,
  AbstractRuntime, AbstractAgent, AbstractSkill, AbstractMemory, AbstractSemantics and the voice,
  vision, music and 3D packages at exactly the versions of the AbstractFramework release, not only at
  the gateway's minimums. `--print-versions` (`-PrintVersions`) lists the release and that matrix.
  `--pin latest` still installs the newest gateway and libraries, and records no release.
- **The gateway restarts whenever anything changed**, a library alone included: the macOS login
  item through launchd, a running Linux `systemd --user` service with `systemctl --user restart`,
  and a background gateway by starting it again. On Windows the installer stops the gateway before
  it changes any file and starts it again afterwards. AbstractGateway 0.7.2 fixes the macOS
  `5: Input/output error` when the login item is replaced: it waits until launchd has removed the
  previous job and retries. When the login item cannot be registered, the gateway starts in the
  background instead, so an upgrade never leaves it stopped.
- **Upgrading from 0.6.1 or earlier.** Those installs did not record their options, so the first
  re-run reads them from what is installed (the terminal console, `abstractcode`, the tray extra,
  the AbstractCore commands, a `--full` build, a custom data directory through the gateway
  pointer), says what it found and records it; you can also repeat your options once. The Update
  button of AbstractGateway 0.7.1 and earlier cannot upgrade an installer install: re-run the line
  once. See [Upgrading from 0.6.1 or earlier](docs/install.md#upgrading-from-061-or-earlier).
- **`--no-start` (`-NoStart`)** upgrades without starting or restarting the gateway and says when a
  restart is due. It keeps this install's port even when a program the installer did not start
  holds it.
- **One installer at a time.** A second installer for the same data directory (the line re-run
  while a console's Update runs, or the other way round) stops with `another AbstractFramework
  installer is already running` and changes nothing. The lock of an interrupted run is taken over
  by the next one.
- **Install AbstractFramework.command runs the latest installer** from GitHub, so double-clicking
  it again upgrades. It uses the copy it came with only when GitHub cannot be reached, and says so.
- **`--pin latest` (`-Pin latest`) upgrades an existing install** with the same profile, voice and
  llama.cpp setup (`uv tool install --upgrade`), and the summary's upgrade lines give the commands
  that work.
- **AbstractCore has three install settings** (AbstractCore 2.19.0): `pip install abstractcore`
  (light: every remote provider, the built-in tools, media inputs, the server and console, and the
  voice, vision, music and 3D plugins with their remote backends; about 600 MB for AbstractCore
  alone in a fresh Python 3.12 environment), `pip install
  "abstractcore[apple]"` (adds every local engine an Apple silicon Mac runs) and `pip install
  "abstractcore[gpu]"` (adds every local engine an NVIDIA or AMD machine runs). The earlier extra
  names still install as deprecated aliases; see AbstractCore's
  [Installation](https://github.com/lpalbou/abstractcore/blob/main/docs/installation.md#deprecated-aliases).
  `abstract3d` now comes with AbstractCore in every profile, pinned at 0.3.1.
- **Recommendations for every capability** (AbstractCore 2.19.0).
  `abstractcore models recommendations` shows the recommended model for text, image input, speech
  output, speech input, image, video and music on every kind of machine (`--host`: this one), with
  the engine, the download size, the memory need and whether it fits. On Apple silicon the fit
  estimate follows the measured GPU memory limit (about 75% of unified memory by default). The text
  tiers are unchanged: Qwen3.5 9B below 24 GB (on an 8 GB Mac it reads as tight, with a small context), Qwen3.8 27B
  from 24 GB, Qwen3.8 Flash-Next from 128 GB. A model that runs only with a small context, such as
  Qwen3.8 27B on a 24 GB Mac, says so and prints the `sudo sysctl iogpu.wired_limit_mb=…` command
  that gives it more (20480 on 24 GB, 114688 for Flash-Next on 128 GB); nothing runs it for you.
  The recommended image model is memory-gated: on an 8 GB Mac the gateway's first-run guide shows
  it as not available here, with the reason, and a saved image or video route that does not fit is
  flagged. See AbstractCore's
  [Recommended models](https://github.com/lpalbou/abstractcore/blob/main/docs/recommended-models.md).
- **Faster video by default** (AbstractVision 0.3.31). Each Wan2.2 model has its own
  speed-oriented default size: 832x480 (TI2V-5B: 121 frames at 24 fps; T2V-A14B and I2V-A14B: 81
  frames at 16 fps), and the video is decoded in overlapping tiles, so the decode no longer sets the
  memory peak. Measured on Apple silicon (MLX peaks at 832x480 with tiled decode), TI2V-5B needs
  about 16.3 GiB for text-to-video and 16.6 GiB for image-to-video (about 60 GiB at the previous
  1280x704 default), so the recommended video route is written on Macs with 32 GB of unified memory
  or more, and a 24 GB Mac is told the GPU memory limit that makes it fit. T2V-A14B and I2V-A14B
  (about 38.3 and 38.4 GiB, measured) fit a 48 GB Mac once its GPU memory limit is raised. Pass `width`, `height`, `num_frames`, `fps` and `steps` for
  another size. The memory figures are AbstractVision/mlx-gen's measurements (the engine keeps the
  text encoder and VAE in memory), not the model's own requirement.
- **Left and Right switch screens in both terminal consoles** (`abstractgateway-console` 0.11.1,
  `abstractcore-console` 0.4.1): the previous or next screen in browse mode, wrapping at both ends,
  like `Ctrl+P` / `Ctrl+N`. A focused element that uses the arrows keeps them: a text field moves
  its caret, a list or tabs bar changes its selection, a dialog keeps every key, and a focused
  scrolling pane scrolls.

### Documentation

- **[Upgrade](docs/install.md#upgrade)**: upgrading everything, the gateway only, from the consoles
  or the menu-bar icon, restarting the gateway, upgrading the apps and checking versions. README and
  Getting started lead with an **Install** section: the Mac package and the one-line commands.

## [0.6.1] - 2026-09-28

Every terminal command lands on your PATH, AbstractCode's terminal client says how to sign in, and
Run now explains itself the same way in every client.

### Changed

- **The installer puts every command line on PATH by default**, in one folder, uv's tool bin
  directory (`~/.local/bin` on macOS and Linux, `%USERPROFILE%\.local\bin` on Windows), next to
  `abstractgateway`:
  - AbstractCode's terminal client, `abstractcode`, is built whenever the terminal console is, with
    the same cargo. `--no-code-cli` (`-NoCodeCli`) skips it; a failed build never fails the install.
    With `--no-console` it is built only when a cargo of Rust 1.87 or later already exists.
  - The library commands come from the gateway's own environment: AbstractCore's (`abstractcore`,
    `abstractcore-config`, `abstractcore-chat`, `abstractcore-endpoint` and its apps `summarizer`,
    `extractor`, `judge`, `intent`, `deepsearch`, also as `abstractcore-<app>`), `abstractvoice`,
    `abstractvoice-prefetch`, `abstractvision` and `abstractmusic`. `--no-core-cli` (`-NoCoreCli`)
    leaves them out.
  - A package's commands come all together or not at all: when another program already has one of
    its names, that package is left out with a warning naming the file, and the rest installs.
  - `--with-code-cli` and `--with-core-cli` stay accepted (they are the default now).
  - The summary lists every command with what it does (`abstractgateway-config`: the gateway's
    admin command). See [Commands you get](docs/install.md#commands-you-get).
- **Signing AbstractCode's terminal client in.** The summary prints
  `Sign in (terminal, once): abstractcode login --token <token>` with your admin token, then
  `abstractcode`, and the way without a token on the gateway's computer,
  `abstractgateway apps tui-command code`. The installer never saves the token for you. Started
  without a sign-in, `abstractcode` 0.7.1 says so and prints the same lines instead of opening
  with an empty workflow.
- **Terminal apps share one folder with the gateway** (AbstractGateway 0.7.1). The console's
  **Apps** page installs and updates `abstractcode` in the same folder as the installer, so it runs
  by name. A re-run of the installer keeps an `abstractcode` newer than its pin. On Windows,
  `install.ps1` builds `abstractgateway-console` and `abstractcode` into `%USERPROFILE%\.local\bin`
  (an existing copy in `%USERPROFILE%\.cargo\bin` is left in place).
- **Uninstall** removes `abstractcode` like the console, and also the copy older gateways put in
  `<data dir>/apps/bin` (removing that folder when it is empty; other files there are kept).

### Added

- **Run now reads the same everywhere** (ui-kit 0.1.16, Observer 0.2.1, Assistant 0.9.1,
  AbstractCode terminal 0.7.1 and web 0.6.1). Every client draws Run now with the same play-in-a-circle icon and explains
  it with the same text: it runs the automation once now instead of waiting; the next scheduled run
  keeps its time (or starts right after this run if its time comes first); it does not count toward
  a run limit; it works while paused, which stays paused; and it is not available while a run is in
  progress. Pause, Resume, Stop, Edit, Archive and Discuss carry the same kind of hint. See
  [Automations](docs/automations.md).

### Changed (pins)

- **abstractgateway 0.7.1** (was 0.7.0): terminal apps in the uv tool bin folder.
- **abstractassistant 0.9.1** (was 0.9.0): the shared Run now icon and hints.
- npm: **@abstractframework/observer 0.2.1** and **@abstractframework/code 0.6.1** (both with the
  shared Run now hints, ui-kit 0.1.16).
- crates.io: **abstractcode 0.7.1** (sign-in report, "not signed in" state, Run now line).
- Unchanged: abstractcore 2.18.0, AbstractRuntime 0.7.1, abstractagent 0.3.17, abstractvoice 0.13.0,
  abstractskill 0.3.0, AbstractMemory 0.3.0, abstractsemantics 0.0.5, abstractvision 0.3.30,
  abstractmusic 0.1.15, flow 0.4.0, continuum 0.4.0, entity 0.3.0, `abstractgateway-console` 0.11.0,
  `abstractcore-console` 0.4.0 and `abstracttui` 0.6.0.

## [0.6.0] - 2026-09-28

Remote and headless machines work like a Mac: one address and one SSH tunnel reach the console, the
API and every browser app; every client finds the local gateway on its own; AbstractCode creates and
runs automations; history replay keeps whole messages up to 50,000 tokens and never cuts one.

### Added

- **Browser apps open through the gateway at `/apps/<app>/`** (AbstractGateway 0.7.0). Flow, Code,
  Observer, Continuum and Entity are served on the gateway's own address (HTTP, server-sent events
  and WebSocket), signed in with the app's gateway session, so a LAN address, a reverse proxy or one
  SSH tunnel reaches them all. The apps listen on `127.0.0.1` by default. The installer summary's
  `Apps:` line and the docs point to `<gateway>/apps/<app>/`; the console's **Apps** page installs
  and opens them. Running an app on its own with `npx … --gateway-url <url>` is the advanced
  alternative (`Standalone:` line).
- **Local gateway pointer.** After the health check the installer writes
  `~/.abstractframework/gateway.json` (Windows: `%USERPROFILE%\.abstractframework\gateway.json`),
  mode 0600: the gateway's loopback URL, port and data directory, never a token. The Assistant (the
  macOS app included), both terminal consoles, AbstractCode's terminal client and the browser apps'
  servers read it to find a gateway on a port other than 8080, and follow it when the gateway moves.
  The installer writes it for the install it just made, a custom `--data-dir` included (replacing a
  pointer that names another data directory); `abstractgateway serve` then keeps it current under
  its ownership rule. The uninstaller deletes it when it names the uninstalled data directory.
- **Automations in AbstractCode** (`abstractcode` 0.7.0, `@abstractframework/code` 0.6.0). In the
  terminal client, `/automations` lists and opens automations (runs as chat pairs, waits that need
  you, the folder, pause/resume, run now, stop, revise, archive, Discuss) and `/schedule` creates
  one; the browser client has the same in its **Automations** sidebar section. See
  [Automations](docs/automations.md).
- **Start at login from the consoles.** Both the web console (Gateway card, last setup step) and the
  terminal console (F3, the Finish step) have a **Start at login** switch that changes the login item
  without restarting the gateway.
- **The terminal console on a headless machine** (`abstractgateway-console` 0.11.0): a Network
  screen that shows the saved and the running setting and offers the restart, Apps that give the link
  and the tunnel command instead of opening a browser, voice and engine states, and the local
  gateway pointer. Neither terminal console tries to open a browser on a machine without a display.
- `--ask-wait SECONDS` (Windows: `-AskWait`) sets how long a timed question waits (default 25, at
  most 25). `--console-wait` remains as an alias.

### Changed

- **One flag for the gateway address: `--gateway-url`** in every app and terminal client
  (`--url` for the gateway terminal console and `--gateway` for AbstractCode remain as aliases). The
  installer summary and the docs use it; with `--with-apps` the installer prints
  `npx -y @abstractframework/<app>@<version> --gateway-url <gateway>` for all five apps.
- **Start at login is asked whenever a person is at a terminal**, not only with `--interactive`:
  `curl … | sh` asks it on your terminal (`/dev/tty`), Enter = yes. Nobody answering within
  `--ask-wait`, an install without a terminal (a script, CI, a provisioning tool) and `--yes` keep
  the previous choice on a re-run and leave start at login **off** on a first install (it was on);
  the summary then says how to turn it on: the **Start at login** switch in either console, or
  `abstractgateway service enable`. A re-run reads the login item's own state, so a change made
  with a console's switch is kept. `install.ps1` asks the same question on an interactive console
  (it registered the login entry without asking). `--interactive` waits for answers without a time
  limit; `--no-service` still asks nothing.
- **On a remote or headless session** (SSH, or Linux without a display) with a terminal, the
  installer offers the terminal console at the end ("Press Enter within 25 s"), signed in; nobody answering skips it, so automation never blocks.
  Over SSH it no longer opens a browser on the remote machine. `--no-open` skips both.
- **History replay keeps whole messages up to 50,000 tokens** (AbstractRuntime 0.7.0): growing
  automations, session chats, run chat, the docs assistants and entity visits replay the newest whole
  turns up to 50,000 tokens. No message is cut; the former 40-message, 24,000-character and
  per-message caps are gone. Each run records how many earlier messages were not replayed, and the
  clients say so.
- **Voice says what it can do** (AbstractVoice 0.13.0, AbstractCore 2.18.0). Voice listings name
  the providers that cannot run here and why, instead of an empty list; cloud voice providers are
  listed as needing a key until one is configured; a capability route whose engine is not installed
  reports `engine_missing` with the install command; an OpenAI key saved in the Providers screen
  reaches voice. The installer adds local voice to every install profile: Supertonic text-to-speech
  and Whisper speech-to-text (`abstractvoice[supertonic,stt]`), both CPU, from prebuilt wheels
  (skipped where no wheels exist: musl Linux / Alpine, macOS before 13; Whisper on Windows ARM64).
  Voice never fails an install: where its packages do not install the gateway is installed without
  it. The summary's `Voice:` line says what was installed, and a re-run that adds voice restarts the
  gateway to load it.
- **Observer: Edit opens the form, and a calmer Automations page** (`@abstractframework/observer`
  0.2.0). A row's **Edit** opens the automation's edit form at once, prefilled (title, task,
  interval, context, tools); action buttons carry icons; a workspace folder can be browsed from the
  browser; **Discuss** opens a chat with a fork of the automation; a run's **Ask** chat sends the
  whole conversation.
- **Apple silicon model fits account for the GPU memory limit** (AbstractCore 2.18.0): a model that
  fits once macOS raises its limit reads `needs_gpu_limit` with the exact command.

### Security

- **DNS-rebinding protection in the browser apps**: an app treats a browser as on this machine only
  when both its address and the page's host are loopback, so a rebinding page can neither reveal a
  folder nor change the gateway address. Continuum's local-only pages answer on `localhost` or
  `127.0.0.1` only. The gateway's app proxy refuses requests with another origin or an invalid host.
- **Server-held keys are spent only for authenticated requests** (AbstractCore 2.18.0): with a
  saved or environment OpenAI key, unauthenticated requests to the AbstractVoice audio routes, the
  audio and vision discovery routes, OpenAI-backed vision generation and the capability discovery
  routes get `401`, also with `ABSTRACTCORE_SERVER_ALLOW_UNAUTHENTICATED=1`; an explicit
  `X-AbstractCore-Provider-API-Key` is spent instead. The music route follows the same rule while
  the server holds a music backend key.
- The local gateway pointer is written without following links, with mode 0600, and readers reject
  a pointer that other users can write.

### Changed (pins)

- **abstractgateway 0.7.0** (was 0.6.0): apps through `/apps/<app>/`, the local gateway pointer,
  start at login from the consoles, cloud voice providers listed, the history window on every chat
  route, and the terminal console 0.11.0.
- **abstractcore 2.18.0** (was 2.17.0): `engine_missing`, `needs_gpu_limit`, the saved OpenAI key
  for voice, the key guards above, and `abstractcore-console` 0.4.0.
- **AbstractRuntime 0.7.1** (was 0.6.0): the 50,000-token history window, recorded in each run;
  images in replayed history stay images, and an image counts as a flat 512 tokens in the window.
  Library callers of `session_chat_messages` and `automation_timeline_messages` should read its
  changelog's Breaking note.
- **abstractagent 0.3.17** (was 0.3.16): ReAct sends the runtime's history window when the host
  asks for it.
- **abstractvoice 0.13.0** (was 0.12.0): engine status and unavailable-provider reasons, Qwen3-ASR
  on Transformers 5.x, Qwen3-TTS predictor and sampler flags.
- **abstractassistant 0.9.0** (was 0.8.0): the macOS app finds a gateway through the local gateway
  pointer; automation cards say their state in words.
- npm: **@abstractframework/flow 0.4.0**, **code 0.6.0**, **observer 0.2.0**, **continuum 0.4.0**
  and **entity 0.3.0**, all served through the gateway at `/apps/<app>/` and taking
  `--gateway-url`.
- crates.io: **abstractgateway-console 0.11.0**, **abstractcore-console 0.4.0** and
  **abstractcode 0.7.0**.
- The pins apply to the base install and to the `apple` / `gpu` extras. Unchanged:
  abstractskill 0.3.0, AbstractMemory 0.3.0, abstractsemantics 0.0.5, abstractvision 0.3.30,
  abstractmusic 0.1.15 and `abstracttui` 0.6.0.

## [0.5.0] - 2026-09-27

Automations, a terminal console installed by default, and a headless setup path: installing and
configuring AbstractFramework on a remote Linux server without a browser works like it does on a Mac.

### Added

- **Automations v1.** Run a workflow or the gateway's default agent again and again on a fixed UTC
  interval or on request, read every run as a chat turn, and be notified only when a run asks for
  you or fails. Create and manage them in the Assistant (session switcher, **Automations** tab), the
  Observer (**Launch → Automate**, **Automations** page) or from a workflow's automation defaults in
  the Flow editor. See [Automations](docs/automations.md).
- **The terminal console is installed by default.** The installer builds `abstractgateway-console`
  with cargo next to the `abstractgateway` command. On macOS and Linux, when cargo is missing or
  older than Rust 1.87, it adds Rust with rustup, user-scoped (`~/.rustup`, `~/.cargo`, about
  600 MB, shell profile untouched); Windows builds it when Rust is already installed. The build
  needs a C compiler; without one, or if it fails, the installer says why and continues.
  `--no-console` (`-NoConsole`) skips it; `--with-console` is accepted and has no effect. The
  uninstaller removes the console it built and keeps Rust.
- **Both consoles in the installer summary.** The summary shows the web console link and the
  terminal console command, `abstractgateway-console --url <gateway> --token-file <data dir>/auth/bootstrap-admin-token`:
  the token is read from the gateway's data dir and never appears on the command line or in the
  environment.
- **Headless or remote machine** ([Install](docs/install.md#headless-or-remote-machine)): configure
  the gateway from the terminal console on the server, or tunnel the web console over SSH.
- **The terminal console matches the web console** (`abstractgateway-console` 0.10.0): the setup
  guide for a headless first run (Connection, Setup, Engines, Providers, Routes, Models, Apps,
  Review), twelve screens including **Setup** and **A Apps**, the **F2** docs assistant, the **F3**
  host panel, every sandbox mode, entity summon and workflow import, with the same admin rules.
  `abstractcore-console` 0.3.0 adds Hugging Face search, parallel downloads, engine start/stop and
  a video filter to the shared Models and Engines screens.
- **Recommended defaults fit the machine** (AbstractCore 2.17.0): every recommended route is written
  only where its engine runs, and a route this computer cannot run says why. Video joins the model
  catalog and the recommendations (MLX-Gen Wan2.2 TI2V-5B on Apple silicon with enough memory), and
  the web console has a **Video** filter and card.

### Changed

- **App hints use launch flags.** With `--with-apps`, the installer prints
  `npx -y @abstractframework/flow@<version> --gateway-url <gateway>` (Continuum likewise); Code,
  Observer and Entity take a gateway other than `http://127.0.0.1:8080` on their sign-in screen.
  `--with-code-cli` prints `abstractcode --gateway <gateway>`.

### Changed (pins)

- **abstractgateway 0.6.0** (was 0.5.1): the Automations API, run lists attributed to automations,
  web console video and host-aware routes, and the terminal console 0.10.0.
- **abstractcore 2.17.0** (was 2.16.1): host-aware recommended defaults, video models and routes,
  `route_unavailable` on routes this computer cannot run, a voice-clone fix for local engines.
- **AbstractRuntime 0.6.0** (was 0.5.1): the durable automation controller and its occurrences.
- **abstractassistant 0.8.0** (was 0.7.0): automations in the session switcher (schedule a
  conversation, read runs as a chat, answer waiting runs, discuss a run); it finds a gateway the
  installer moved off a busy port 8080.
- **abstractvoice 0.12.0** (was 0.11.4): Qwen3-TTS checkpoint selection, directed speech and a
  steadier codebook predictor.
- **abstractvision 0.3.30** (was 0.3.29): unloading an MLX-Gen model returns its memory to the
  operating system.
- npm: **@abstractframework/flow 0.3.22** (automation defaults on workflows) and
  **@abstractframework/observer 0.1.14** (Automate mode and the Automations page).
- crates.io: **abstractgateway-console 0.10.0** and **abstractcore-console 0.3.0**.
- The pins apply to the base install and to the `apple` / `gpu` extras. Unchanged:
  abstractagent 0.3.16, abstractskill 0.3.0, AbstractMemory 0.3.0, abstractsemantics 0.0.5,
  abstractmusic 0.1.15, @abstractframework/code 0.5.0, continuum 0.3.2, entity 0.2.2,
  `abstractcode` 0.6.0 and `abstracttui` 0.6.0.

### Documentation

- **Automations guide** ([docs/automations.md](docs/automations.md)): how automations work, creating
  them from each client, two worked examples, managing them, notifications and typed waits, restart
  safety, limits and troubleshooting. A discussion about a run works in its own folder with the
  automation's folder mounted read-only.

## [0.4.2] - 2026-09-27

A patch release for the uninstaller and two package updates.

### Fixed

- **Uninstall stops the whole gateway before deleting.** Removing the login item does not wait for
  the gateway to exit, and some of its children (an entity's own-time loop, model downloads, the
  apps it started, the tray) kept writing into the data dir, so the uninstall failed with
  "Directory not empty". The uninstaller now waits up to 20 s for the whole gateway process tree to
  exit, then stops what is left and says which processes it stopped.
- **Every deletion is verified.** Each location is deleted, retried while something re-creates it,
  then checked; a folder that cannot be deleted (or comes back) stops the uninstaller with a
  listing of what remains and the programs holding it. The failure text advises running the
  uninstaller again, never the installer.
- **`--purge` removes all your local data**: besides the gateway data dir, its login-item logs and
  its download cache, it removes the Assistant's sessions, snapshots and preferences
  (`~/.abstractassistant`, the macOS preferences file and the cached preferences) and
  AbstractCode's login and preferences (`~/.abstractcode`). Model weights and shared caches are
  kept and named. The purge question names what it deletes; `--print` lists each command; a
  second run prints "nothing to do". `install.sh` accepts `--yes`.
- **Uninstall safety**: `--purge` refuses (exit 2, nothing changed) a data dir that is the root,
  your home folder or any folder above it, and a hand-given `--data-dir` that is not a gateway data
  dir (for example `~/Library` or `~/Documents`). A process is stopped only when it runs from this
  install's tool environment or is one of this data dir's apps; a stale pid file is left alone.
  `--data-dir` is made absolute once, and paths are resolved before the mount guard
  (`/tmp` vs `/private/tmp`, a linked home).
- The one-line uninstaller and the installer package's "Uninstall AbstractFramework.command" both
  carry these fixes. Known Linux limits: BusyBox `ps` (Alpine) lacks the columns the process scan
  reads, so only the systemd stop applies there; a relative `XDG_CACHE_HOME` is used as given.

### Changed (pins)

- **abstractagent 0.3.16** (was 0.3.15): the announced-tool-use text heuristic added in 0.3.15 is
  removed; the loops behave as in 0.3.14 plus the CodeAct/MemAct crash fix from 0.3.15.
- **abstractassistant 0.7.0** (was 0.6.1): the session list and transcripts come from the gateway;
  local files are a rebuildable cache. The first launch moves sessions the gateway does not know to
  `sessions-legacy/` and deletes nothing. The list shows your own sessions by default, with an
  "All gateway sessions" toggle.
- The pins apply to the base install and to the `apple` / `gpu` extras
  (`abstractassistant[apple|gpu]==0.7.0`). Unchanged: abstractgateway 0.5.1, abstractcore 2.16.1,
  AbstractRuntime 0.5.1, abstractskill 0.3.0, AbstractMemory 0.3.0, abstractsemantics 0.0.5,
  abstractvoice 0.11.4, abstractvision 0.3.29, abstractmusic 0.1.15, the browser apps, `abstractcode`
  0.6.0 and `abstractgateway-console` 0.9.0.
- Container images are unchanged: `ghcr.io/lpalbou/abstractgateway:0.5.1` and
  `ghcr.io/lpalbou/abstractcore-server:2.16.1`.

## [0.4.1] - 2026-09-26

A patch release for local MLX models and long-running flows.

### Changed (pins)

- **AbstractRuntime 0.5.1** (was 0.5.0): a wait is resumed at most once. A flow whose Agent or
  subflow node waits on a child could run that child twice when the child finished exactly as the
  runner ticked, doubling the run's time and tokens; a racing second resume is refused with a
  typed `StaleResumeError`.
- **abstractcore 2.16.1** (was 2.16.0): MLX prompts are rendered by the model's own chat template
  on every MLX lane (mlx-lm, native MTP, vision, JSON-constrained). Earlier turns keep their tool
  calls, tool results are rendered as the template renders them, and the generation prompt opens
  thinking when the template does; agent loops on Qwen3.x MLX builds with thinking on used to stop
  at the third iteration with a one-sentence announcement and no tool call. A malformed tool-call
  argument in the history never disables that renderer, and each response's metadata names the
  renderer used. Prompt-cache artifacts rendered by the previous renderer are rebuilt, not reused.
- **abstractagent 0.3.15** (was 0.3.14): fixes a crash in 0.3.13 and 0.3.14 (CodeAct and MemAct
  raised `NameError` when a delegated agent's profile set `thinking`). A reply that announces tool
  use without calling a tool, or whose tool calls could not run, is re-prompted once with the
  failed reply quoted, and ends with `stop_reason.code = "no_tool_call"` rather than being
  published as the answer; the long-reply nudge is bounded to once per step.
- **abstractgateway 0.5.1** (was 0.5.0): requires the three packages above; when two runner paths
  race to resume the same parent, the losing attempt is logged at debug level instead of as an
  error.
- **abstractassistant 0.6.1** (was 0.6.0): the Settings window opens inside the screen; the
  default screen edge gap is 12 px.
- The pins apply to the base install and to the `apple` / `gpu` extras
  (`abstractgateway[apple|gpu]==0.5.1`, `abstractassistant[apple|gpu]==0.6.1`); the bootstrap
  scripts install `abstractgateway[<profile>,tray]==0.5.1`. Unchanged: abstractskill 0.3.0,
  AbstractMemory 0.3.0, abstractsemantics 0.0.5, abstractvoice 0.11.4, abstractvision 0.3.29,
  abstractmusic 0.1.15, the browser apps (flow 0.3.21, code 0.5.0, observer 0.1.13,
  continuum 0.3.2, entity 0.2.2), `abstractcode` 0.6.0 and `abstractgateway-console` 0.9.0.
- Container images released with it: `ghcr.io/lpalbou/abstractgateway:0.5.1` (and `0.5.1-gpu`)
  and `ghcr.io/lpalbou/abstractcore-server:2.16.1`.

### Changed

- The dev build (`scripts/build.sh`) installs the sibling kit packages an app takes from npm
  (app-server, ui-kit, panel-chat, monitors) from local packs of the checkouts, so an app builds
  locally even when its kit floor is ahead of the registry. The manifests and lockfiles are left
  untouched.

## [0.4.0] - 2026-09-26

A feature release of the whole framework. The gateway picks the agent workflow for AbstractCode
and the Assistant, AbstractCode can browse the conversation's workspace, the gateway serves a
curated skill shelf, replies stream live into every client, the console opens the Assistant
already signed in, and every app has an About dialog. Ejecting a model frees its memory from the
whole gateway process. This release replaces the 0.3.3 matrix, which was prepared but never
published.

### Changed (pins)

- **abstractgateway 0.5.0** (was 0.4.3 on PyPI): the default agent workflow setting
  (`agents.default_workflow`, used by AbstractCode and the Assistant, changeable in the console or
  with `abstractgateway config set`), the conversation workspace routes (browse and preview files,
  with a built-in deny list for credential folders and the gateway data folder), the skill shelf
  seeded from `abstractskill`, opening the Assistant signed in from the console, live replies
  (`agents.streaming_default`), `GET /about`, the same-machine rule behind the app proxies, and
  About in the web console and the terminal console. Ejecting a model frees its memory from the
  whole gateway process and the memory figures show what the process really holds; gateways
  started with an earlier version must be restarted once to reclaim memory already held. The
  trust-proxy switch saved in the console now wins over `ABSTRACTGATEWAY_TRUST_PROXY`, which only
  applies while nothing is saved.
- **abstractcore 2.16.0** (was 2.15.2 in 0.3.2): framework identity for About screens
  (`abstractcore.utils.identity`), process-wide model eject and memory reporting, embeddings
  eject and reload, live-reply telemetry for MLX, and streamed and non-streamed replies that split
  thinking from the answer the same way.
- **AbstractRuntime 0.5.0** (was 0.4.35): live replies (`_runtime.stream`), workspace
  built-in deny list, deferred model ejects with diagnostics.
- **abstractagent 0.3.14** (was 0.3.13): delegated sub-agents inherit the live-reply switch.
- **abstractskill 0.3.0** (new pin): the curated skill shelf ships inside the package.
- **abstractassistant 0.6.0** (was 0.5.0): opens signed in when launched from the gateway
  console, a workflow selector that follows the gateway default, live replies, About, and window
  defaults.
- The pins apply to the base install and to the `apple` / `gpu` extras
  (`abstractgateway[apple|gpu]==0.5.0`, `abstractassistant[apple|gpu]==0.6.0`); the bootstrap
  scripts install `abstractgateway[<profile>,tray]==0.5.0`. Unchanged: AbstractMemory 0.3.0,
  abstractsemantics 0.0.5, abstractvoice 0.11.4, abstractvision 0.3.29, abstractmusic 0.1.15.
- Browser apps released with it (`--with-apps`, `npx`): `@abstractframework/flow` 0.3.21,
  `@abstractframework/code` 0.5.0, `@abstractframework/observer` 0.1.13,
  `@abstractframework/continuum` 0.3.2 and `@abstractframework/entity` 0.2.2, built on
  `@abstractframework/ui-kit` 0.1.12, `@abstractframework/app-server` 0.1.10 and
  `@abstractframework/panel-chat` 0.1.17.
- Terminal tools released with it: `abstractcode` 0.6.0 and `abstractgateway-console` 0.9.0
  (`--with-code-cli`, `--with-console`); `abstractcore-console` 0.2.0 and `abstracttui` 0.6.0 are
  unchanged.
- Container images released with it: `ghcr.io/lpalbou/abstractgateway:0.5.0` (and `0.5.0-gpu`)
  and `ghcr.io/lpalbou/abstractcore-server:2.16.0`.

### Documentation

- New [Agent sessions](docs/agent-sessions.md) page: the gateway's default agent workflow and how
  AbstractCode and the Assistant follow it, the conversation workspace (browse and preview from
  AbstractCode, the built-in deny list for credential folders and the gateway data folder), the
  curated skill shelf, live replies, and opening the Assistant signed in from the console.
- [Architecture](docs/architecture.md) adds diagrams of how a turn flows, the live-reply lane and
  the framework identity flow, plus the app proxies' forwarded-address rule and model eject.
- [CONTRIBUTING](CONTRIBUTING.md) documents the framework identity rule
  (`identity/abstractframework.json` and `scripts/check_identity_sync.py`).
- [Agent Skills](docs/guide/agent-skills.md) describes the shipped skills support; FAQ,
  Troubleshooting, Configuration and Glossary cover the new settings; gateway examples use launch
  flags (`serve --data-dir`, `network set --allowed-origins`).

## [0.3.2] - 2026-09-25

A patch release: installing the Assistant and the engines works when the data folder path
contains a space (such as the macOS Application Support folder), and the default MLX model id
names a published repository.

### Changed (pins)

- **abstractcore 2.15.2** (was 2.15.1; the default MLX model id names a published repository),
  **AbstractRuntime 0.4.35** (was 0.4.34) and **abstractgateway 0.4.3** (was 0.4.2; installing the
  Assistant and engines works when the data folder path contains a space, such as the macOS
  Application Support folder; the console page carries no maintainer comments), in the base
  install and in the `apple` / `gpu` extras (`abstractgateway[apple|gpu]==0.4.3`). The bootstrap
  scripts install `abstractgateway[<profile>,tray]==0.4.3`. The other pins are unchanged:
  abstractagent 0.3.13, AbstractMemory 0.3.0, abstractsemantics 0.0.5, abstractvoice 0.11.4,
  abstractvision 0.3.29, abstractmusic 0.1.15, abstractassistant 0.5.0. Unchanged too:
  `abstractgateway-console` 0.8.0, ui-kit 0.1.11 and the browser apps flow 0.3.20, code 0.4.2
  and observer 0.1.12.
- Browser apps released with it (`--with-apps`, `npx`): `@abstractframework/continuum` 0.3.1
  (was 0.3.0) and `@abstractframework/entity` 0.2.1 (was 0.2.0).
- Container images released with it: `ghcr.io/lpalbou/abstractgateway:0.4.3` (and `0.4.3-gpu`)
  and `ghcr.io/lpalbou/abstractcore-server:2.15.2`.

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
