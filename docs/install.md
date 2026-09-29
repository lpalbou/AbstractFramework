# Install AbstractFramework

Most people want AbstractFramework running on their own computer with nothing to set up by hand.
That is what the installer does: one download or one line, no admin password, and at the end
AbstractFramework opens in your web browser, already signed in. Developers who want the Python
libraries in their own environment go to [Install the Python framework](#install-the-python-framework-developers).

## Install on a Mac

You need a Mac with macOS 13 or later (Apple Silicon gets the fast local engines; they need
macOS 14), an internet connection, and about 5 GB of free disk space before models.

1. **Download** [AbstractFramework-Installer.pkg](https://github.com/lpalbou/AbstractFramework/releases/latest/download/AbstractFramework-Installer.pkg)
   (attached to every [GitHub release](https://github.com/lpalbou/AbstractFramework/releases)).
2. **Allow it once.** The package is not signed with an Apple Developer ID, so the first
   double-click shows a warning that macOS cannot verify the installer (*"… Not Opened"*, *"Apple
   could not verify …"* or *"… from an unidentified developer"*, depending on your macOS version).
   Close the warning (**Done** or **OK**), open **System Settings > Privacy & Security**, scroll
   down to **Security**, click **Open Anyway** next to the installer's name, and confirm (macOS may
   ask for your login password or Touch ID). This is the standard macOS step for software from
   outside the App Store; you do it once per download.
3. **Install.** The macOS Installer opens. Click **Continue**, then **Install**. It installs for you
   only, so the Installer does not ask for your password.
4. **A Terminal window opens** and shows each step as it happens. It asks one question:

   ```
   ? Start AbstractFramework automatically when you log in? (a per-user login item, no admin; the uninstaller removes it) [Y/n] (Enter = yes)
   ```

   Press **Return** for yes (recommended: it is then always there when you need it), or type `n`.
   You can change it later with the **Start at login** switch in the console.
5. **Wait** 2 to 15 minutes, depending on your connection. The last lines say
   `AbstractFramework is ready.` and your browser opens AbstractFramework.
6. **In the browser**, the first-run guide helps you pick an engine (it detects what this Mac can
   run and installs it with one click) and a model that fits your Mac. You can close the Terminal
   window.

Afterwards, AbstractFramework is at `http://127.0.0.1:8080/console` (bookmark it), and its icon in
the menu bar opens it and shows its status.

What it puts on your Mac, all inside your home folder: uv and a private Python 3.12 in
`~/.local`, the AbstractFramework gateway (about 2.4 GB on Apple Silicon, with the MLX engines),
uv's download cache (about 2.4 GB, reused by upgrades), your data in
`~/Library/Application Support/AbstractGateway`, and, if you said yes, a login item
(`~/Library/LaunchAgents/ai.abstractframework.gateway.plist`). Models you download later come on
top.

The package also leaves two double-clickable files in
`~/Library/Application Support/AbstractFramework/Installer`: **Install AbstractFramework.command**
(double-click it again to upgrade or repair: it runs the latest installer) and
**Uninstall AbstractFramework.command**. See [Upgrade](#upgrade).

### Or: paste one line in Terminal

On macOS and Linux, open Terminal, paste this line and press Return:

```bash
curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | sh
```

It asks the same start-at-login question in your terminal: press Return for yes or type `n`. With
no answer within 25 seconds it leaves start at login off, so an unattended run never waits.
Everything else is the same as the Mac package above. On Linux the login item is a `systemd --user`
service and the data lives in `~/.local/share/abstractgateway`.

Run from a script, a provisioning tool or CI (no terminal to ask on), the installer asks nothing:
start at login stays off on a first install (a re-run keeps what you chose before), and the summary
says how to turn it on. `--no-service` always leaves it off and asks nothing.

### Windows

Windows 10 22H2+ / 11: open PowerShell, paste this line and press Enter:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1 | iex"
```

It installs under your user account (no administrator rights) and opens AbstractFramework in your
browser. It asks whether to start AbstractFramework at sign-in, like the Mac and Linux installer:
Enter = yes, no answer within 25 seconds (or no console to ask on) leaves it off on a first install.
`-NoService` leaves it off and asks nothing.

## If something goes wrong

The installer stops at the first problem, says what happened in plain words, and says what to do.
It never leaves a half-finished install behind that a second run cannot fix: after fixing the
cause, run it again (double-click the installer again, or paste the line again) and it continues
where it stopped.

| What you see | What to do |
|---|---|
| `no internet connection: the installer could not reach pypi.org` | Connect to the internet, then run the installer again. Nothing was changed. |
| `cannot reach pypi.org through the proxy set in your environment (…)` | Your computer is set up to use a proxy that does not answer. Fix the proxy (or remove the `HTTPS_PROXY` setting), then run it again. |
| `… failed because the internet connection dropped` | Reconnect and run it again; it continues where it stopped. |
| `this Terminal runs in Intel (Rosetta) mode on an Apple Silicon Mac` | Quit Terminal. In Finder open **Applications > Utilities**, select **Terminal**, choose **File > Get Info**, untick **Open using Rosetta**, then run the installer again. (Double-clicking the installer restarts itself in the right mode on its own.) |
| `the folder … belongs to 'root', so the installer … cannot write there` | An earlier command was run with `sudo`. Run the `sudo chown -R …` line the message shows (it asks for your password once), then run the installer again. |
| `macOS … is older than the versions AbstractFramework is tested on` | A warning, not a stop. If the install then fails, update macOS in **System Settings > General > Software Update**. |
| `the Apple Silicon engines (MLX) need macOS 14 or later` | You get the light version (remote and endpoint engines). Update macOS and run the installer again to add the local engines. |
| `the installed gateway does not start … reinstalling it` | Nothing to do: an earlier install was interrupted and the installer repairs it. |
| `the gateway did not answer … within 180 s` | Restart the computer (the login item starts it) or run the installer again, then open `http://127.0.0.1:8080/console`. |
| The browser page asks for a token | The one-time sign-in link lasts 10 minutes. Run the installer again: it opens a fresh link. |
| `another AbstractFramework installer is already running` | An installer, or an **Update** from a console or the menu-bar icon, is running for this data directory. Wait until it finishes, then run the line again. |
| Anything else | Run the installer again. If it stops at the same step, report it with the log file named at the end of the message (`~/Library/Application Support/AbstractGateway/logs/install-….log`). |

## Upgrade

### Upgrade everything (recommended)

The line you installed with also upgrades and repairs. Run it again:

```bash
curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | sh
```

On Windows:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1 | iex"
```

On a Mac without Terminal, double-click **Install AbstractFramework.command** in
`~/Library/Application Support/AbstractFramework/Installer` again. It downloads and runs the latest
`install.sh`, the script of the one line, so it upgrades the same way. When GitHub cannot be
reached, it runs the copy of the installer it came with and says so. Installing the latest
[AbstractFramework-Installer.pkg](https://github.com/lpalbou/AbstractFramework/releases/latest/download/AbstractFramework-Installer.pkg)
again does the same.

The line always runs the installer of the latest AbstractFramework release. It:

- finds the existing install and says what it does. An install made by 0.6.2 or later recorded its
  release, so the line names it: `AbstractFramework <yours> found: upgrading to AbstractFramework
  <latest>`, or `AbstractFramework <yours> found: already up to date` (every part is still checked,
  and repaired when needed). An install made by 0.6.1 or earlier recorded no release, so its first
  upgrade says `AbstractFramework found (abstractgateway 0.7.1; its release was not recorded):
  upgrading to AbstractFramework 0.6.2` (with the gateway version you have);
- installs the gateway version that release pins, and every library the gateway uses
  (AbstractCore, AbstractRuntime, AbstractAgent, AbstractSkill, AbstractMemory, AbstractSemantics
  and the voice, vision, music and 3D packages) at the exact version released and tested with it ([Check your versions](#check-your-versions) shows
  how to print the list);
- rebuilds the terminal console (`abstractgateway-console`) and AbstractCode's terminal client
  (`abstractcode`) when the release pins newer versions, with the Rust toolchain from the first
  install;
- keeps your profile, port, start-at-login choice, data directory (a custom `--data-dir` too),
  Network setting, settings, downloaded models and installed apps, and the options that change what
  is installed: `--no-console`, `--no-code-cli`, `--no-core-cli`, `--no-tray` and `--full`. It
  prints the options it kept. To change one, give the opposite option: `--with-console`,
  `--with-code-cli`, `--with-core-cli`, `--with-tray` or `--no-full` (Windows: `-WithConsole`,
  `-WithCodeCli`, `-WithCoreCli`, `-WithTray`, `-NoFull`);
- restarts the gateway when anything in its environment changed, a library alone included, and
  leaves a running gateway alone when nothing changed. The macOS login item is restarted through
  launchd, a running Linux `systemd --user` service with `systemctl --user restart`, and a
  background gateway is started again. On Windows the installer stops the running gateway before it
  changes any file (Windows locks the files of a running program) and starts it again afterwards;
- never leaves the gateway stopped: when the login item cannot be registered, the gateway starts in
  the background and the summary says how to turn start at login on;
- ends with what changed, old -> new, under **Changes** (`Changes: none` when nothing moved), and
  `Upgraded: AbstractFramework <yours> -> <latest>` (`Upgraded: AbstractFramework (not recorded) ->
  0.6.2` for the first upgrade of a 0.6.1 or earlier install) or `Already up to date:
  AbstractFramework <yours>; nothing changed.`

#### Upgrading from 0.6.1 or earlier

Installs made by AbstractFramework 0.6.1 or earlier recorded neither their release nor your install
options. The first re-run says `AbstractFramework found (abstractgateway <version>; its release was
not recorded): upgrading to AbstractFramework 0.6.2`, and reads your options from what is installed: whether the terminal console and `abstractcode` are
there, whether the gateway has the tray extra and the AbstractCore commands, whether the compiled
extras were built (`--full`), and a custom data directory through the gateway pointer. It prints
what it found (`read from disk: …`) and records it for later runs. You can also repeat your
original options once on that first run. The **Update** button of gateway 0.7.1 and earlier cannot
upgrade an installer install: re-run the line once, and from gateway 0.7.2 on **Update** runs the
installer.

With `--no-start` (Windows: `-NoStart`) the installer upgrades without starting or restarting the
gateway, and says when a restart is due. It keeps this install's port even when another program
holds it.

One installer runs at a time for a data directory. A second one, for example the line re-run while
a console's **Update** is running, stops with `another AbstractFramework installer is already
running` and changes nothing; run it again when the first has finished. A run that was interrupted
(a closed terminal, a crash) leaves a lock that the next run takes over by itself.

### Upgrade only the gateway

A gateway release can reach PyPI before the next AbstractFramework release. To install the newest
gateway with the same profile, voice and llama.cpp setup:

```bash
curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | sh -s -- --pin latest
```

On Windows:

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1))) -Pin latest
```

`--pin latest` moves the gateway and its libraries to their newest releases on PyPI; `--pin 0.7.1`
installs one exact version. The libraries then follow the gateway's own requirements instead of the
release's tested versions, and the install records no AbstractFramework release. The installer
restarts the gateway as above. A later run without `--pin` returns every package to the versions
the AbstractFramework release pins.

Do not use `uv tool upgrade abstractgateway` for an installer install. The installer installs an
exact version (`abstractgateway[<profile>,tray]==<version>`), uv keeps that constraint, and
`uv tool upgrade` answers `Nothing to upgrade`. `uv tool install abstractgateway@latest` does move
to the newest version, but it replaces the whole install with the bare package: the profile extras,
the local voice packages, the AbstractCore, voice, vision and music commands and the prebuilt-wheel
overrides the installer added are gone. Use the installer.

### From the console or the menu-bar icon

The gateway's **Update** runs the same installer as the line above. You find it in three places:

- the web console: **Resources > Gateway > Version**, then **Check now**;
- the menu-bar icon: **Check for Updates…**;
- the terminal console: **F3**, then `u` to check and `U` to update.

For a gateway installed by the AbstractFramework installer on macOS or Linux:

1. The check compares the AbstractFramework release you have with the latest one. It reads the
   release from the install manifest on the framework repository's `main` branch. The version line
   reads `AbstractFramework <yours> · gateway <version> · AbstractFramework <latest> available`.
2. **Update to AbstractFramework <latest>** asks you to confirm and shows exactly what runs:
   - the address of the installer,
     `https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh`;
   - the commit it comes from and the script's sha256;
   - the command:
     `/bin/sh install.sh --yes --no-start --no-open --no-modify-path --data-dir <data dir>`.

   The gateway runs exactly the script you confirmed, and refuses to run a different one.
3. The installer runs next to the running gateway: nothing is asked, start at login stays as it is,
   and every package moves to the release's tested versions. The web console shows its output live
   under **Update log**.
4. The result is one of three:
   - **installed**: what moved (`AbstractFramework <yours> -> <latest>`, then the gateway and the
     libraries that changed), then a restart to finish (**Restart gateway…** in the web console,
     **Restart Now** in the menu-bar icon's dialog, `R` in the terminal console);
   - **already up to date**: the installer changed nothing, and no restart is needed;
   - **didn't finish**: the installer's exit code and the last lines of its log (the full log is the
     newest `<data dir>/logs/install-*.log`). The running gateway keeps running; re-run the line
     above to finish by hand.

On Windows, a running program's files are locked, so the gateway does not update itself. The check
says which release is available and shows the PowerShell line to paste; that installer stops the
gateway, upgrades and starts it again.

**Update** is for the gateway's admin only, and it runs on the gateway's own machine, also when you
use a console from another computer or over SSH.

For a gateway installed with pip, pipx or in a virtual environment, the check compares with the
newest `abstractgateway` on PyPI, and **Update to …** installs it in the background, keeping the
`apple`, `gpu` and `embeddings` extras. It updates the gateway package only: not the terminal
console, not AbstractCode's terminal client, not the apps. Restart the gateway to finish.

### Restart the gateway

The installer restarts the gateway itself when anything changed, except with `--no-start` (the
console's and the menu-bar icon's **Update**). A gateway updated while it runs keeps the previous
version until its next start. To restart it now:

- web console: **Resources > Gateway > Restart gateway…**; menu-bar icon: **Restart AbstractGateway…**;
  terminal console: `R` in **F3**;
- terminal: `abstractgateway network restart --force --token <admin token>`;
- Linux, start at login on: `systemctl --user restart abstractgateway`.

Running workflows pause at their next step and continue after the restart.

### Upgrade the apps

The browser apps (Flow, Code, Observer, Continuum, Entity) and the desktop Assistant are installed
by the gateway, so the installer does not change them. When npm has a newer version, the app's card
on the console's **Apps** page offers **Update** under **Technical details**. In a terminal:

```bash
abstractgateway apps list                # installed and latest version of every app
abstractgateway apps update code         # update one app; a running app restarts on the new version
abstractgateway apps install-tui code    # update the terminal version the Apps page installed
```

The terminal console and an `abstractcode` built by the installer are upgraded by
[re-running the installer](#upgrade-everything-recommended).

### Check your versions

```bash
abstractgateway --version                    # the installed gateway
uv tool list --show-version-specifiers       # the gateway uv tool and its pin ([required: ==0.7.2])
abstractgateway-console --version            # the terminal console
abstractcode --version                       # AbstractCode's terminal client
abstractgateway apps list                    # the apps: installed and latest
curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | sh -s -- --print-versions   # what the latest release installs
```

The web console shows the running gateway's version under **Resources > Gateway > Version**.

## Remove AbstractFramework

Double-click **Uninstall AbstractFramework.command** (in
`~/Library/Application Support/AbstractFramework/Installer` after a package install), or paste:

```bash
curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/uninstall.sh | sh
```

It asks before removing anything, then asks two more questions, both defaulting to no:

- **Also delete your AbstractFramework data**? This cannot be undone. It deletes:

  | What | macOS | Linux |
  |---|---|---|
  | Gateway data: settings, users, chats, run history, artifacts, memory, the tray's preferences | `~/Library/Application Support/AbstractGateway` | `~/.local/share/abstractgateway` |
  | The login item's logs | `~/Library/Logs/AbstractGateway` | (in the data dir) |
  | The gateway's download cache (engine installers) | `~/Library/Caches/AbstractGateway` | `~/.cache/abstractgateway` |
  | The Assistant's sessions, snapshots and preferences | `~/.abstractassistant`, `~/Library/Logs/Assistant/abstractassistant-*` | `~/.abstractassistant` |
  | AbstractCode's login and preferences | `~/.abstractcode`, `~/.abstractcode-tui` | same |

  It keeps model weights and shared caches: `~/.cache/huggingface`, `~/.abstractcore` (its
  config and its downloaded models), `~/.abstractframework`, `~/.cache/abstractvoice`, and the
  models of LM Studio and Ollama. Delete those by hand if you want them gone.
- **Also remove uv, its Python and its download cache** (about 2.5 GB)? Asked only when the
  installer is what added uv; answer no if you use uv for anything else.

It always removes the login item, stops AbstractFramework and removes the gateway (and the
Assistant, which lives in the gateway's environment), the terminal console and `abstractcode`,
including an `abstractcode` that a gateway before 0.7.1 installed in `<data dir>/apps/bin` (that
folder is removed when nothing else is in it). It also deletes the local gateway pointer,
`~/.abstractframework/gateway.json`, when it names this install's data directory. Stopping means the whole gateway process
tree: after the login item is removed it waits up to 20 seconds for every gateway process to exit
(the server, the tray, an entity's own-time loop, model downloads, the apps it started), then
stops the rest, and says which processes it stopped. It keeps Ollama and LM Studio (they have
their own uninstallers) and the one PATH line uv added to your shell profile. Without questions:
`sh uninstall.sh --yes` (keeps data), add `--purge` to delete the data and `--remove-uv` to remove
uv; `--print` shows every command and changes nothing. Windows: `install.ps1 -Uninstall [-Purge]`.

**If a folder cannot be deleted**, the uninstaller stops with an error that names the folder,
lists what is left in it and the programs that hold files there. Quit those programs (or log
out and back in); on macOS, a file shown with the `uchg` flag is unlocked with
`chflags -R nouchg <folder>`. Then run the uninstaller again: it skips what is already gone.
Each deleted location is checked once more a second later; a program that starts writing there
again after that is not detected (an uninstaller cannot outwait a writer it does not know).
A `--data-dir` given by hand is purged only when it holds a gateway file (`bootstrap.env`,
`gateway.sqlite3`, `auth/users.json`, ...) or the note a previous, interrupted purge left in it
(`.abstractgateway-purge-incomplete`); the root, your home folder and any folder that
contains it are always refused (exit 2, nothing changed).

## Advanced: what the installer does

The Mac package, the `.command` files and the one line all run the same script,
[`scripts/install.sh`](../scripts/install.sh) (Windows: `scripts/install.ps1`):

1. Checks the machine (OS, CPU, macOS 14+ for Apple Silicon, Rosetta, NVIDIA/ROCm, the folders it
   writes, internet access to PyPI, free disk, a free port) and picks a profile: `apple` on Apple
   Silicon (macOS 14+), `gpu` when `nvidia-smi` or `rocminfo` works, `light` otherwise.
2. Asks whether to start at login, whenever a person is at a terminal (`/dev/tty`, so it also works
   through `curl | sh`). Enter = yes on a first install and the previous choice on a re-run; no
   answer within `--ask-wait` seconds (default 25) keeps the previous choice, or leaves it off on a
   first install. The double-click installers pass `--interactive`, which waits for the answer
   without a time limit. With no terminal (automation) or `--yes` nothing is asked: a re-run keeps
   the previous choice (the login item's own state, so a change made with a console's **Start at
   login** switch counts), a first install leaves it off.
3. Installs [uv](https://docs.astral.sh/uv/) when it is missing, then Python 3.12 through uv.
4. Installs the gateway as an isolated uv tool, pinned to this release:
   `uv tool install --python 3.12 "abstractgateway[<profile>,tray]==0.7.2"`, from prebuilt wheels
   only (see [No compiler needed](#no-compiler-needed)), and checks that the command starts
   (reinstalling it in place when it does not). Every profile also gets local voice,
   `--with "abstractvoice[supertonic,stt]"`: Supertonic text-to-speech and Whisper speech-to-text,
   both on CPU (skipped on musl Linux and macOS before 13, where no wheels exist; Windows ARM64 gets
   Supertonic only). If those packages do not install on a system (for example glibc older than
   2.28), the gateway is installed without them and the summary says so. The same install puts
   AbstractCore's commands and those of its voice, vision and music packages on PATH next to the
   gateway's (`--with-executables-from`; `--no-core-cli` leaves them out): see
   [Commands you get](#commands-you-get).
5. Builds the terminal console, `abstractgateway-console`, with `cargo install --locked` into the
   same folder as the `abstractgateway` command (crates.io has no prebuilt binary). When cargo is
   missing, macOS and Linux get Rust from [rustup](https://rustup.rs) (minimal profile, in
   `~/.rustup` and `~/.cargo`, about 600 MB, shell profile untouched); Windows builds it only when
   Rust is already installed. It needs a C compiler; without one, or if the build fails, the
   installer says why and continues. `--no-console` skips it. AbstractCode's terminal client,
   `abstractcode`, is built the same way, with the same cargo, into the same folder (`--no-code-cli`
   skips it; under `--no-console` it is built only with a cargo already there). A failed build never
   fails the install: the installer warns once and prints the command to run by hand. Then, when
   asked for, Node.js for the browser apps, Ollama or LM Studio (flags below). See
   [Commands you get](#commands-you-get).
6. With start at login on, registers the gateway with `abstractgateway service install --port N`
   (a LaunchAgent on macOS, a `systemd --user` unit on Linux, a per-user login entry on Windows) and
   starts it. The login item runs plain `abstractgateway serve`, so the gateway's
   [Network setting](#network-setting-who-can-reach-the-gateway) decides where it listens. With
   start at login off (or `--no-service`, or on a Linux host without a user systemd session), it
   starts the gateway in the background instead and removes a login item an earlier run
   registered; the summary then says how to turn start at login on: the **Start at login** switch
   in either console (web: the Gateway section; terminal: F3), or `abstractgateway service enable`.
7. Waits up to 180 seconds for `/api/health`, then writes the local gateway pointer,
   `~/.abstractframework/gateway.json` (Windows: `%USERPROFILE%\.abstractframework\gateway.json`):
   the gateway's address on this computer, its port and data directory, never a token. Clients on
   this computer that start without a gateway address (the Assistant, AbstractCode's terminal
   client, the browser apps' servers) read it to find a gateway on a port other than 8080. The
   installer always writes it for the install it just made, a custom `--data-dir` included (it
   replaces a pointer that names another data directory). `abstractgateway serve` keeps it current
   once bound, but only when the file is absent and it uses the default data directory, or when
   the file already names its data directory, so a test gateway never takes it over.
8. Opens `http://127.0.0.1:8080/console` through a one-time sign-in link
   (`abstractgateway-config claim-url`, valid 10 minutes, this machine only). If no link can be
   created, it shows where the admin token is. The summary shows both ways to configure the
   gateway (the web console link and the terminal console command) and where the browser apps
   open: `http://127.0.0.1:8080/apps/<app>/` (the console's **Apps** page installs and opens them).
   On a remote or headless session (SSH, or Linux without a display) it offers the terminal console
   instead ("Press Enter within 25 s", signed in); no answer skips it, and `--no-open` or `--yes`
   skips the offer.

Every command is printed as it runs, and the summary lists them all. Re-running the script
upgrades or repairs the install in place (see [Upgrade](#upgrade)). The macOS package is payload-free: it copies the two
`.command` files into `~/Library/Application Support/AbstractFramework/Installer` and opens
`install.sh --interactive` in Terminal. It is built by
[`scripts/lib/build_macos_installer.sh`](../scripts/lib/build_macos_installer.sh).

### No compiler needed

By default the script never compiles anything, so you do not need Xcode Command Line Tools, gcc
or the MSVC Build Tools. It passes uv a small overrides file (`uv-overrides.txt` in the gateway
data directory; `--print` shows it) that swaps `webrtcvad` for `webrtcvad-wheels`, keeps `vllm`
to Linux, and leaves out the two compiled extras below, and it refuses to build those packages
from source, so a gap fails with a clear error instead of starting a compiler. If macOS asks you
to install the command line developer tools (an `xcode-select` prompt) during an install, cancel
the prompt, fetch the script again with the one-liner above and re-run it.

### llama.cpp GGUF models

Every profile, light included, gets in-process llama.cpp GGUF support (`llama-cpp-python`). PyPI
has only its source, so the script takes upstream's prebuilt wheel from
[abetlen's wheel index](https://abetlen.github.io/llama-cpp-python/whl/) (`--find-links` on the
package page, pinned in `uv-constraints.txt` next to the overrides file):

| Machine | Wheel |
|---|---|
| Apple Silicon Mac | `llama-cpp-python==0.3.28`, Metal (GPU offload) |
| Linux x86_64 / aarch64 (glibc) | `llama-cpp-python==0.3.35`, CPU |
| Windows x64 | `llama-cpp-python==0.3.35`, CPU |
| Intel Mac, musl Linux, Windows on ARM | no prebuilt wheel: skipped |

Where no wheel exists, or when the wheel install fails, the script installs everything else and
says `GGUF (llama.cpp) skipped: no prebuilt wheel for this machine`; `--full` then builds it from
source. The summary's `GGUF:` line says which wheel was installed. On Apple Silicon the Metal wheel
is pinned to 0.3.28, the newest Metal wheel on that index that passes uv's archive integrity
check.

### Compiled extras

Two optional engines publish no wheel on PyPI and are skipped by default: stable-diffusion.cpp
image generation (`stable-diffusion-cpp-python`) and voice echo cancellation
(`aec-audio-processing`). `--full` (Windows: `-Full`) keeps them and builds them, and llama.cpp,
from source, which takes several minutes and needs a C/C++ compiler (macOS:
`xcode-select --install`; Debian/Ubuntu: `sudo apt-get install -y build-essential`; Windows:
Visual Studio Build Tools with "Desktop development with C++"). Without a compiler, `--full` stops
before installing anything. You do not need them for MLX on Apple Silicon, for llama.cpp GGUF
models (above), for Ollama, LM Studio or other endpoint engines, or for cloud providers.

### Options

| macOS/Linux | Windows | What it does |
|---|---|---|
| `--profile auto\|light\|apple\|gpu` | `-Profile` | Override the profile choice |
| `--port N` | `-Port N` | Gateway port (default 8080; the next free port when 8080 is busy) |
| `--with-apps` | `-WithApps` | Make sure Node.js 18+ exists for running the browser apps on their own with `npx` (the console's **Apps** page installs Node.js for the apps it runs) |
| `--with-ollama` | `-WithOllama` | Run Ollama's official installer (Linux uses sudo; the script tells you first) |
| `--with-lmstudio` | `-WithLmStudio` | Install LM Studio (headless daemon on macOS/Linux, winget on Windows) |
| `--no-console` | `-NoConsole` | Skip the terminal console (`abstractgateway-console`), which is otherwise built with cargo |
| `--no-code-cli` | `-NoCodeCli` | Skip AbstractCode's terminal client (`abstractcode`), which is otherwise built with the console's cargo into the same folder |
| `--no-core-cli` | `-NoCoreCli` | Do not put AbstractCore's commands (`abstractcore` and its apps) and `abstractvoice`, `abstractvision`, `abstractmusic` on PATH |
| `--full` | `-Full` | Also build the [compiled extras](#compiled-extras) and llama.cpp from source (needs a C compiler) |
| `--no-tray` | `-NoTray` | Leave out the menu-bar icon (`tray` extra) |
| `--with-console`, `--with-code-cli`, `--with-core-cli`, `--with-tray`, `--no-full` | `-WithConsole`, `-WithCodeCli`, `-WithCoreCli`, `-WithTray`, `-NoFull` | Turn back what an earlier `--no-console`, `--no-code-cli`, `--no-core-cli`, `--no-tray` or `--full` changed (a re-run keeps those choices otherwise) |
| `--no-service` | `-NoService` | Do not start at login (asks nothing; starts the gateway in the background) |
| `--no-start` | `-NoStart` | Install or upgrade only; do not start or restart the gateway, and say when a restart is due (the gateway's **Update** uses it) |
| `--no-open` | `-NoOpen` | Do not open the browser (remote or headless session: do not offer the terminal console) |
| `--ask-wait SECONDS` | `-AskWait SECONDS` | How long a timed question waits for an answer: start at login, and the terminal console offer at the end of a remote or headless install (default 25, at most 25; `--console-wait` is an alias) |
| `--no-modify-path` | `-NoModifyPath` | Do not add `~/.local/bin` to your shell profile (`uv tool update-shell`) |
| `--pin X` / `--from PATH` | `-Pin` / `-From` | Install another gateway version (`--pin latest`: the newest on PyPI; see [Upgrade only the gateway](#upgrade-only-the-gateway)) or a local checkout |
| `--manifest PATH` | `-Manifest` | Read the gateway pin from this `install-manifest.json` |
| `--data-dir DIR` | `-DataDir` | Gateway data directory |
| `--interactive` | — | Wait for every answer without a time limit, and also ask whether to build the terminal console (and, with `--uninstall`, whether to delete data and uv); the double-click installers pass it |
| `-y`, `--yes` | — | Ask nothing, not even start at login (a first install leaves it off; a re-run keeps the previous choice) |
| `--print` | `-Print` (or `-WhatIf`) | Show the plan and every command; change nothing |
| `--print-versions` | `-PrintVersions` | Print the AbstractFramework release, the pinned gateway, its libraries, the npm apps and the crates, then exit |
| `-v`, `--verbose` | — | Show the full output of every command |
| `--uninstall [--purge] [--remove-uv]` | `-Uninstall [-Purge]` | Stop the gateway process tree, remove the service and uv tools (purge also deletes your data: see [Remove AbstractFramework](#remove-abstractframework); `--remove-uv` also removes uv, its Python and cache when the installer added uv) |

### Commands you get

Everything lands in one folder, `~/.local/bin` (Windows: `%USERPROFILE%\.local\bin`), which the installer adds to your shell profile: open
a new terminal for it to be on PATH. The summary lists them under `Commands`.

The gateway's own commands, and the two terminal clients built with cargo:

| Command | What it does |
|---|---|
| `abstractgateway` | The gateway itself: `serve`, `service` (start at login), `network` (who can reach it), `models`, `engines`, `apps` |
| `abstractgateway-config` | The gateway's admin and configuration command: `status` (readiness without starting it), `claim-url` (a new one-time console sign-in link), `defaults` / `set-default` / `clear-default` (which provider and model each capability uses), `get` / `set` / `unset` (runtime settings), `bootstrap-admin`, `init` |
| `abstractgateway-console` | The terminal console (`--gateway-url <url> --token <admin token>`); skipped with `--no-console` |
| `abstractcode` | AbstractCode's terminal client (sign it in once, see below); skipped with `--no-code-cli` |

**Sign `abstractcode` in.** It needs the gateway's admin token once. Choose one of:

- `abstractcode login --token <admin token>`, then plain `abstractcode`. The installer summary
  prints this line with your token, ready to paste (the installer does not save it for you).
  `login` checks the token and keeps it in AbstractCode's own login store,
  `~/.abstractcode/gateway.json` (readable by you only). Without `--gateway-url`, `abstractcode`
  finds this computer's gateway through the gateway pointer, on whichever port it runs.
- On the gateway's computer, SSH included: `abstractgateway apps tui-command code`. It prints a
  one-time line (valid 2 minutes) that opens `abstractcode` signed in as you, without you handling
  a token (add `--data-dir <dir>` for an install with a custom data directory; the summary shows
  it).

If `abstractcode` starts without a valid sign-in, it says so and names both ways. The admin token
is in `<data dir>/auth/bootstrap-admin-token`; `abstractgateway-config status` prints the data
directory. The gateway console's **Apps** page can update `abstractcode` in the same folder; a
re-run of the installer keeps a newer version.

The commands of AbstractCore and its voice, vision and music packages, from the gateway's own
environment (`uv tool install --with-executables-from`), so they always match the versions the
gateway runs:

| Package | Command | What it does |
|---|---|---|
| AbstractCore | `abstractcore` | AbstractCore's configuration and operations: `--config` (interactive setup wizard), `--status`, `models` (catalog, download), `engines` (detect, install), `serve` (the AbstractCore server and its web console) |
| | `abstractcore-config` | The same command as `abstractcore` |
| | `abstractcore-chat` | An interactive chat in the terminal with any provider and model (`--provider`, `--model`, `--stream`) |
| | `abstractcore-endpoint` | A single-model OpenAI-compatible `/v1` server: one provider and model loaded once per worker |
| | `summarizer` | Summarizes a document (`--style`, `--length`, `--focus`) |
| | `extractor` | Extracts entities and relationships from a document as a knowledge graph (JSON-LD or RDF triples) |
| | `judge` | LLM-as-a-judge: scores texts or files against criteria such as clarity, soundness and completeness |
| | `intent` | Analyzes the intents behind a text or a conversation, with deception indicators |
| | `deepsearch` | An autonomous research agent: searches the web and writes a sourced report on a question |
| | `abstractcore-summarizer`, `abstractcore-extractor`, `abstractcore-judge`, `abstractcore-intent`, `abstractcore-deepsearch` | The same five apps under prefixed names |
| AbstractVoice | `abstractvoice` | Voice in the terminal: a spoken chat with a model by default, plus `web` (a local web demo), `tts` (text to an audio file) and `check-deps` |
| | `abstractvoice-prefetch` | Downloads voice models ahead of time (for example `--supertonic`, `--stt`), so the first use does not wait |
| AbstractVision | `abstractvision` | Images and video in the terminal: `t2i` / `i2i` (generate or edit an image), `upscale`, `t2v` / `i2v` (video), `cli` (an interactive session), `download`, `models`, `provider-models` |
| AbstractMusic | `abstractmusic` | Music in the terminal: `t2m` (text to music), `repl`, `models` |

A package puts all of the commands it declares on PATH: uv exposes all of a package's commands or
none and cannot pick a subset, which is why the generic app names (`summarizer`, `judge`, …) come
with AbstractCore. `--no-core-cli` (Windows: `-NoCoreCli`) leaves the four packages out; the gateway
still uses them internally.

If one of those names already exists in the folder (another program's file, or another uv tool's
command, such as an earlier `uv tool install abstractcore`), uv would refuse the whole install, so
the installer leaves that package out, names the file in the way in a warning and in the summary's
`Not exposed` line, and installs everything else. Remove that file and run the installer again to
add the package.

An `abstractcode` that an earlier installer built with `--with-code-cli` is in `~/.cargo/bin`; the
installer does not touch it (delete it with `cargo uninstall abstractcode`).

Pass options through the one-liner like this:

```bash
curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | sh -s -- --with-apps --with-ollama
```

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1))) -WithApps -WithOllama
```

### Headless or remote machine

Install over SSH with the same one-liner. It asks the start-at-login question in your SSH terminal
(Enter = yes; a scripted install with no terminal leaves it off), installs local voice (Supertonic
and Whisper, on CPU) like every other install, and at the end offers to open the terminal console,
signed in ("Press Enter within 25 s"; no answer skips it, so a scripted `ssh -t` never hangs).

Later, start the terminal console on the server with the command the installer's summary prints
(your port and token filled in):

```bash
abstractgateway-console --gateway-url http://127.0.0.1:8080 --token <admin token>
```

The admin token is in `~/.local/share/abstractgateway/auth/bootstrap-admin-token` (the summary
prints the command with it filled in). The terminal console configures everything the web console
does: press `N` for the **Network** screen (who can reach the gateway: this machine, the local
network or the internet; the saved and the running setting side by side, with the addresses to
copy), `A` for **Apps**, `F3` for the gateway host (restart, update, start at login).

From your own computer, one SSH tunnel carries the web console, the API and every browser app,
because the gateway serves the apps on its own port:

```bash
ssh -L 8080:127.0.0.1:8080 <server>
```

Then open the link from `abstractgateway-config claim-url --base-url http://127.0.0.1:8080` in your
browser, and open the apps from the console's **Apps** page: each opens at
`http://127.0.0.1:8080/apps/<app>/` (`observer`, `code`, `flow`, `continuum`, `entity`). On the
server itself, the terminal console's **Apps** screen shows the same link and the tunnel command
instead of starting a browser.

### The same install by hand

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh             # Windows: irm https://astral.sh/uv/install.ps1 | iex
uv python install 3.12
uv tool install --python 3.12 "abstractgateway[tray]==0.7.2"    # [apple,tray] or [gpu,tray] for local engines
                       # (add --with and --overrides as shown by `install.sh --print` to avoid compiling)
uv tool update-shell                                          # puts ~/.local/bin on PATH; open a new terminal
abstractgateway service install --port 8080                   # or: abstractgateway serve
abstractgateway-config claim-url --base-url http://127.0.0.1:8080  # prints a one-time console link
```

### Run at login

The easiest way to turn start at login on or off is the **Start at login** switch in either
console: the web console's Gateway section, or `F3` in the terminal console. In a terminal,
`abstractgateway service` does the same (LaunchAgent on macOS, `systemd --user` on Linux, a
per-user Run entry on Windows, experimental):

```bash
abstractgateway service enable      # start this gateway at the next login (the consoles' switch)
abstractgateway service disable     # stop starting it at login (the running gateway keeps running)
abstractgateway service install --port 8080   # register the login item and start the gateway now
abstractgateway service status
abstractgateway service uninstall   # stop it and remove the login item (data is kept)
```

The login item runs plain `abstractgateway serve`, so the host and port come from the Network
setting below. Passing `--host` to `service install` stores the matching mode in that setting.

The bootstrap scripts use it by default. Gateways older than 0.3.0 (installed with `--pin`) have no
`service` command: `install.sh` then starts the gateway in the background and `install.ps1` adds a
Startup-folder shortcut. To write a login entry yourself on Linux, a user unit is enough:

```ini
# ~/.config/systemd/user/abstractgateway.service
[Service]
Environment=ABSTRACTGATEWAY_USER_AUTH=1
Environment=ABSTRACTGATEWAY_DATA_DIR=%h/.local/share/abstractgateway
ExecStart=%h/.local/bin/abstractgateway serve
Restart=on-failure

[Install]
WantedBy=default.target
```

Then `systemctl --user daemon-reload && systemctl --user enable --now abstractgateway`. On macOS
use a LaunchAgent in `~/Library/LaunchAgents/` with the same absolute command and environment
(launchd does not read your shell profile, so use absolute paths).

### Network setting: who can reach the gateway

The gateway listens on this computer only (`localhost`, `127.0.0.1:8080`) until you choose
otherwise. Change it in the web console's network panel, on the terminal console's **Network**
screen (`N`), from the menu-bar icon's **Network** menu, or in a terminal:

```bash
abstractgateway network status                      # configured vs running mode, addresses, warnings
abstractgateway network set lan                     # other devices on your local network
abstractgateway network set localhost --port 8080   # back to this computer only
abstractgateway network set internet --acknowledge-internet   # public; TLS and port forwarding are yours
abstractgateway network restart --token <admin token>   # apply it to the running gateway now
abstractgateway network addresses                   # every URL a client can use
```

A new mode or port applies at the next start: `network restart`, the console, the menu-bar icon's
**Restart AbstractGateway…**, or the next login. Keep
`localhost` unless you need another device to connect; see
[Gateway security](guide/gateway-security.md) before choosing `internet`.

### Upgrade and uninstall

- Upgrade: re-run the one-liner, or use **Update** in a console or the menu-bar icon, which runs the
  same installer; see [Upgrade](#upgrade) (`uv tool upgrade abstractgateway` does not upgrade an
  installer install: it keeps the installed version's pin).
- Uninstall: [Remove AbstractFramework](#remove-abstractframework) above,
  `curl -LsSf .../install.sh | sh -s -- --uninstall` (Windows: the script block with
  `-Uninstall`), or by hand: `abstractgateway service uninstall` (when registered), then
  `uv tool uninstall abstractgateway` (it also removes the AbstractCore, voice, vision and music
  commands it exposed) and `cargo uninstall --root ~/.local abstractgateway-console abstractcode`
  (Windows: `cargo uninstall --root %USERPROFILE%\.local abstractgateway-console abstractcode`). The uninstaller does all of
  it. Your data stays in the data directory until you delete it
  (`--purge`). See [Operations and support](installers/operations-and-support.md) for locations.

### Check the install

```bash
uvx abstractframework doctor
```

It checks Python, uv, Node, disk, the gateway (`ABSTRACTGATEWAY_URL`, default
`http://127.0.0.1:8080`), and whether Ollama and LM Studio are reachable. It only reads.

## Install the Python framework (developers)

Use the profiles below when you want every framework library in one Python environment, for
example to build on AbstractCore or AbstractRuntime directly. Choose the profile by deciding where
inference should run. The framework APIs stay the same across profiles; the profiles mainly change
whether local inference engines are installed.

### Quick chooser

| Profile | Command | Use when | Local inference stacks |
|---|---|---|---|
| Light | `pip install abstractframework` | You use cloud APIs or endpoint servers such as LM Studio, Ollama, vLLM, llama.cpp, OpenRouter, or OpenAI-compatible services. | No |
| Apple | `pip install "abstractframework[apple]"` | You are on Apple Silicon and want local MLX/Metal-capable engines as well as endpoint providers. | Yes, Apple-focused |
| GPU | `pip install "abstractframework[gpu]"` | You have a supported discrete GPU and want local GPU-capable engines as well as endpoint providers. | Yes, GPU-focused |

#### Requirements per profile

| Profile | Platforms | Python | Notes |
|---|---|---|---|
| Light | macOS, Linux, Windows | 3.10–3.13 | No local inference engines. |
| Apple | macOS 14 or later on Apple Silicon | 3.10–3.13 | MLX wheels need macOS 14+. F5-TTS voice cloning needs Python 3.11+; the rest of the profile works on 3.10. |
| GPU | Linux (and Windows where the engines publish wheels) with NVIDIA CUDA or AMD ROCm drivers | 3.10–3.13 | F5-TTS voice cloning needs Python 3.11+; the rest of the profile works on 3.10. |

A plain `pip install` of the `apple` or `gpu` profile builds the
[compiled extras](#compiled-extras) (`llama-cpp-python`, `stable-diffusion-cpp-python`,
`aec-audio-processing`) from source, so it needs a C/C++ compiler. The one-line install above
does not.

`abstractframework` 0.6.2 pins `abstractgateway==0.7.2`, `abstractassistant==0.9.1`,
`abstractcore==2.19.0`, `AbstractRuntime==0.7.1`, `abstractagent==0.3.17`, `abstractskill==0.3.0`,
`AbstractMemory==0.3.0`, `abstractsemantics==0.0.5`, `abstractvoice==0.13.0`,
`abstractvision==0.3.31`, `abstractmusic==0.1.15` and `abstract3d==0.3.1`. The `apple` and `gpu` extras select
`abstractgateway[apple|gpu]` and `abstractassistant[apple|gpu]` at the same versions
(`abstractassistant[apple]` is installed on macOS only). `abstractframework doctor` reports any
installed package whose version differs from these pins.

Light is not a reduced-functionality framework. It is the remote-first profile: multimodal input,
multimodal output, embeddings, tools, durable runs, workflows, and Gateway/Flow still work when
they are backed by remote or local endpoint providers.

## Recommended technical install

Use a clean virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install abstractframework
abstractframework doctor
```

Use `uv` if you prefer faster environment management:

```bash
uv venv
source .venv/bin/activate
uv pip install abstractframework
abstractframework doctor
```

`pipx` is useful for isolated command-line apps, but a normal venv is usually clearer for the full
framework because Gateway, Flow, Core, and local plugins share one environment.

## Light profile

```bash
pip install abstractframework
```

Choose Light when:

- you use OpenAI, Anthropic, OpenRouter, Portkey, or other hosted providers;
- you use local model servers through HTTP, such as LM Studio, Ollama, vLLM, llama.cpp, or LocalAI;
- you want the smallest and least surprising install;
- you do not want pip to install MLX, CUDA, Diffusers, or local model-runtime stacks.

The Light environment takes about 0.9 GB in a fresh Python 3.12 environment. Most of it is
AbstractCore's light setting, which includes the Office-document parsers, the built-in tools and
the voice, vision, music and 3D plugins with their remote backends; it installs no local engine.

After install, run `abstractframework doctor`, start the gateway and configure providers in its
console (see [Start the gateway](#start-the-gateway-and-apps)).

## Apple profile

```bash
pip install "abstractframework[apple]"
```

Choose Apple when:

- you are on Apple Silicon;
- you want local Apple/MLX-capable inferencers in addition to endpoint providers;
- you accept larger downloads and platform-specific native dependencies.

Then run `abstractframework doctor`.

## GPU profile

```bash
pip install "abstractframework[gpu]"
```

Choose GPU when:

- you have a supported GPU stack and drivers;
- you want local GPU-capable inferencers in addition to endpoint providers;
- you accept larger downloads and platform-specific native dependencies.

Then run `abstractframework doctor`.

## Apps and tools outside pip

The browser apps and the Rust terminal tools are not Python packages, so no profile installs them.
Run or install them next to the Python stack:

| Tool | Command | Version released with 0.6.2 |
|---|---|---|
| Gateway web console | built into `abstractgateway`: open the link `abstractgateway serve` prints (`http://127.0.0.1:8080/console#claim=…`) | 0.7.2 |
| Core web console | built into `abstractcore`: open the link `abstractcore serve` prints (`http://127.0.0.1:8000/console#claim=…`) | 2.19.0 |
| Core terminal console | `cargo install abstractcore-console` (Rust 1.87+), then `abstractcore-console` (uses the `abstractcore` command) | 0.4.1 |
| Gateway terminal console | built by the installer (`--no-console` skips it), or `cargo install abstractgateway-console` (Rust 1.87+); then `abstractgateway-console --gateway-url http://127.0.0.1:8080 --token <admin token>` | 0.11.1 |
| Flow Editor | the console's **Apps** page (opens at `/apps/flow/`), or on its own: `npx @abstractframework/flow --gateway-url <url>` | 0.4.0 |
| Code Web UI | the console's **Apps** page (`/apps/code/`), or `npx @abstractframework/code --gateway-url <url>` | 0.6.1 |
| Observer | the console's **Apps** page (`/apps/observer/`), or `npx @abstractframework/observer --gateway-url <url>` | 0.2.1 |
| Continuum console | the console's **Apps** page (`/apps/continuum/`), or `npx @abstractframework/continuum --gateway-url <url>` | 0.4.0 |
| Entity manager | the console's **Apps** page (`/apps/entity/`), or `npx @abstractframework/entity --gateway-url <url>` | 0.3.0 |
| AbstractCode terminal client | `cargo install abstractcode`, or a prebuilt binary from the [AbstractCode GitHub release](https://github.com/lpalbou/AbstractCode/releases) | 0.7.1 |

The browser apps need a running gateway. The gateway installs, starts and serves them itself, on
its own address at `/apps/<app>/` (it installs Node.js for them when it is missing); running one on
its own with `npx` needs Node.js 18 or later. `abstract3d` (pinned above) comes with
AbstractCore in every profile; the optional add-on outside the profiles installs on its own: `pip install abstractcamera`.
`abstractskill` comes with the gateway, which carries its curated skill shelf.

## Start the gateway and apps

Start the gateway and open its console:

```bash
abstractgateway serve            # binds 127.0.0.1:8080 and prints a one-time console link
```

The console's **Apps** page installs and opens the browser apps, each at
`http://127.0.0.1:8080/apps/<app>/`, already signed in. To run an app on its own instead (for
development, or against another gateway), pass the gateway's address:

```bash
npx @abstractframework/flow --gateway-url http://127.0.0.1:8080
```

Configure providers, API keys, engines and default models in the console. For library-only use
of AbstractCore, `abstractcore serve` opens the same Models and Engines screens in its own console,
and `abstractcore --config` remains available in the terminal. When you work from source, the workspace helper
scripts build and start the same services (see [Workspace scripts](workspace-scripts.md)).

Gateway-hosted browser apps use Gateway user tokens and browser sessions. Do not use the bootstrap
server token as a browser login token.

## Container deployment

For a server/VPS deployment, prefer the Gateway container rather than installing every app package
on the host:

```bash
docker run \
  -p 8080:8080 \
  -v "$PWD/runtime:/data" \
  -e ABSTRACTGATEWAY_DATA_DIR=/data \
  -e ABSTRACTGATEWAY_USER_AUTH=1 \
  ghcr.io/lpalbou/abstractgateway:0.7.2
```

This is the Light container: full framework capabilities through remote/endpoint inference, without
local MLX/CUDA stacks. On first start it creates `default/admin` and writes the login token to
`runtime/auth/bootstrap-admin-token`. Use `ghcr.io/lpalbou/abstractgateway:gpu-latest` only on an
NVIDIA host when you explicitly want the local GPU profile (pinned tags are `<version>-gpu`, published on a best-effort basis; this image is
experimental). The AbstractCore OpenAI-compatible server is also published as
`ghcr.io/lpalbou/abstractcore-server:2.19.0`.

## How installs are designed

The scripts and the gateway console are the install experience on every OS. On macOS the
double-click artefacts (a payload-free `.pkg` and two `.command` files) only launch the same
script in Terminal; they add no install logic of their own. Design, security model and per-OS
behavior are in [docs/installers](installers/README.md).

## Generated install manifest

The installer-facing contract is generated from the root release profile:

```bash
abstractframework manifest
abstractframework manifest --check docs/installers/install-manifest.json
abstractframework manifest --write install-manifest.json
```

The bootstrap scripts read `bootstrap.gateway_version` from it; other installers should consume
this manifest instead of maintaining independent package pins. Field reference:
[release-and-manifest.md](installers/release-and-manifest.md).
