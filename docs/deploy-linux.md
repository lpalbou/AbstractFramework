# Deploy an AbstractFramework gateway on a fresh Linux server

The sequence below was run end to end on a fresh Ubuntu 24.04 cloud instance (4 vCPU, 26 GB RAM, one
NVIDIA Quadro RTX 5000) with AbstractFramework 0.11.17. Each step shows the line to expect. Run the
commands as your normal user (here `ubuntu`), not as root. `<server>` is the server's address.

## One command

On a fresh Ubuntu server, as your normal user with `sudo`:

```bash
curl -LsSf https://abstractframework.ai/install.sh | sh -s -- --server --gpu --tailscale-funnel
```

- `--server` installs the same matrix as below, asks nothing, runs the gateway as a systemd user
  service, turns lingering on (`sudo loginctl enable-linger`), and ends with the address, the
  **setup code** and the next steps.
- `--gpu` (GPU servers) installs the NVIDIA driver first when `nvidia-smi` is missing and `lspci`
  sees an NVIDIA GPU (step 2 below, done for you). Then reboot and run the same command again: it
  keeps everything and adds the CUDA build of llama.cpp.
- `--tailscale-funnel` installs Tailscale when missing, prints its login URL and waits while you
  authorize the server, publishes the gateway with
  `tailscale funnel --bg --https=443 http://127.0.0.1:<port>` and allows its
  https address as a browser origin. Funnel and HTTPS must be allowed for your tailnet (Tailscale
  prints the link to allow them when they are not).

The command is idempotent: run it again to repair or upgrade; each part is checked first. The end of
its output:

```text
  This server
    Public address: https://<server>.<tailnet>.ts.net/console
    Setup code: moose bicycle honey camel ankle agent
    Next: open the address, choose the admin password and give the setup code ("Set up your gateway");
          the setup guide then opens (engines, default models, apps). Again: abstractgateway claim --code
```

Open the public address from any browser: the console asks for the admin password and the setup code,
signs you in and opens the setup guide (gateway 0.18.0 and later; see the gateway's
`docs/first-run.md`). Without `--tailscale-funnel`, use the SSH tunnel of step 5.

The steps below are the same install by hand.

## 1. Prerequisites

- Ubuntu 22.04 or 24.04, x86_64, a user with `sudo`, SSH access with a key.
- About 15 GB free disk for the gpu profile, plus your models. No firewall port to open (step 5).

## 2. NVIDIA driver (GPU servers only)

Skip this step on a server without an NVIDIA GPU: the installer then picks the light profile.

```bash
nvidia-smi                       # "command not found": no driver yet, continue
sudo apt-get update && sudo apt-get install -y ubuntu-drivers-common
sudo ubuntu-drivers install      # installs the recommended driver (595-open here)
sudo reboot
```

After the reboot, `nvidia-smi --query-gpu=name,driver_version --format=csv` shows the GPU and a
driver of 580 or newer (`Quadro RTX 5000, 595.99.02`), which PyTorch 2.11 (CUDA 13) needs.

## 3. Install

```bash
curl -LsSf https://abstractframework.ai/install.sh | sh
```

Expected: `✓ profile: gpu (nvidia-smi found a GPU ...)` and, about 2-10 minutes later,
`AbstractFramework is ready.` with `Gateway: abstractgateway[gpu]==0.17.0 (gpu profile)`. The start at
login question can be left unanswered: step 4 sets it up. Then open a new SSH session (or
`source ~/.bashrc`) so `~/.local/bin` is on PATH.

```bash
curl -s http://127.0.0.1:8080/api/health    # {"status":"healthy","service":"abstractgateway",...}
```

## 4. Run the gateway as a service

```bash
abstractgateway service enable          # start at login [on]: a systemd user unit
sudo loginctl enable-linger "$USER"     # keep it running without an open SSH session, start at boot
sudo reboot
```

Do not skip the second line: without lingering, a systemd user service stops when your last SSH
session ends and does not start at boot (`loginctl show-user "$USER" -p Linger` answers
`Linger=no`). After the reboot, `systemctl --user is-active abstractgateway` answers `active`.

## 5. Open the console from your computer

On your own computer, keep this tunnel open (use `-L 18080:127.0.0.1:8080` and port 18080 below if
port 8080 is taken on your computer):

```bash
ssh -N -L 8080:127.0.0.1:8080 ubuntu@<server>
```

On the server, make a one-time sign-in link (valid 10 minutes, works once):

```bash
abstractgateway-config claim-url --base-url http://127.0.0.1:8080
# http://127.0.0.1:8080/console#claim=agclaim_...
```

Open that link in your browser. Expected: the console, signed in as `default/admin`, on the setup
guide ("Welcome to your gateway"). The admin token, for the apps and the API, is in
`~/.local/share/abstractgateway/auth/bootstrap-admin-token`.

## 6. A first local model

On a server, use llama.cpp: the installer put it in (the CUDA build on an NVIDIA GPU, `GGUF:` in its
summary), with no app to run. The setup guide may recommend LM Studio (`lmstudio · qwen/qwen3.5-9b`):
that is a desktop app, not installed here; skip its recommendation and choose the model below. A
small GGUF model that runs on the GPU through llama.cpp (2.5 GB):

```bash
abstractgateway models catalog --fits | grep GGUF        # what fits this server
abstractgateway models download huggingface "unsloth/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M"
# done: snapshot cached at ~/.cache/huggingface/hub/models--unsloth--Qwen3-4B-Instruct-2507-GGUF/...
abstractgateway-config set-default output.text --provider huggingface --model unsloth/Qwen3-4B-Instruct-2507-GGUF
abstractgateway-config set-default input.text  --provider huggingface --model unsloth/Qwen3-4B-Instruct-2507-GGUF
# Set execution-host capability default: output.text  (then input.text)
```

Local voice is installed, but not its default voice: until you download it once, speech
synthesis answers an error (`Supertonic 3 artifacts are not available locally`). The installer's
summary prints the same line:

```bash
abstractgateway models download supertonic supertonic-3   # done: Supertonic 3 assets cached
```

## 7. Apps and a first chat

In the console: **Apps** > **Install** on Observer, Continuum, Code, Entity and Flow Editor (the
first install also installs Node.js for the gateway, about 20 s in all). Then **Open** on Code,
type a question and press Enter. Expected: the answer, and under it the token count and time. The
apps open at `http://127.0.0.1:8080/apps/<app>/` through the same tunnel.

## 8. Uninstall

```bash
curl -LsSf https://abstractframework.ai/uninstall.sh | sh     # answer y; data and uv: Enter keeps them
# expected (this uninstaller's messages; the 0.11.17 test above removed the unit by hand):
# · a login service was turned on after the install (it starts this install's gateway): removing it
# · lingering is on for ubuntu (...); if you turned it on only for the gateway: sudo loginctl disable-linger ubuntu
# Done.
sudo loginctl disable-linger "$USER"   # only if nothing else needs it
```

The uninstaller stops and removes the service from step 4 (`systemctl --user is-enabled
abstractgateway` then answers `not-found`). It never runs `sudo`, so it prints the lingering line
instead of running it. Kept on purpose: `~/.local/share/abstractgateway` (your data; add
`--purge` to delete it), `~/.cache/huggingface` (models), `~/.cache/uv` (about 14 GB with the gpu
profile; `--remove-uv` removes uv and its cache).

## 9. A second gateway on the same host

A second gateway, for a test release next to the one in use for example, is an **instance**: a
self-contained gateway with its own name. Install it with `--instance NAME` and its own `--port`:

```bash
curl -LsSf https://abstractframework.ai/install.sh | sh -s -- --server --instance fresh --port 8443 --tailscale-funnel
# test a wheel the release has not published yet: add --from /path/to/abstractgateway-<version>-py3-none-any.whl
```

The instance name gives everything its own copy; nothing is chosen by hand and nothing is shared with
the default gateway:

| | default gateway | instance `fresh` |
| --- | --- | --- |
| Program (uv tool environment) | `~/.local/share/uv/tools/abstractgateway` | `~/.local/share/abstractgateway-fresh/tool/abstractgateway` |
| Commands | `~/.local/bin/abstractgateway` (on PATH) | `~/.local/share/abstractgateway-fresh/bin/abstractgateway --instance fresh` (not on PATH) |
| Data dir | `~/.local/share/abstractgateway` | `~/.local/share/abstractgateway-fresh` |
| AbstractCore config (model routes, provider keys) | `~/.abstractcore/config` | `~/.local/share/abstractgateway-fresh/core-config` |
| Port | 8080 | the `--port` given (required) |
| App ports | 3001-3006, fallback 3100-3199 | 3001+200N-3006+200N, fallback 3100+200N-3199+200N (N = the instance's slot, 1 for the first one) |
| systemd user unit | `abstractgateway.service` | `abstractgateway-fresh.service` |
| Funnel | `https://<server>.<tailnet>.ts.net` (https 443) | `https://<server>.<tailnet>.ts.net:8443` (`--funnel-https-port`: 443, 8443 or 10000) |

The slot is assigned once in `~/.config/abstractgateway/instances.json` and kept, so the same name
always gets the same app ports. The console shows the instance name in its title and sidebar, and
`GET /api/gateway/about` returns it (`instance`). The installer refuses a gateway too old to know
instances: it would write the default gateway's login service.

Address the instance with its command and `--instance`:

```bash
G="$HOME/.local/share/abstractgateway-fresh/bin/abstractgateway --instance fresh"
$G service status           # the unit abstractgateway-fresh.service
$G claim --code             # its setup code
journalctl --user -u abstractgateway-fresh.service -f
```

Upgrade it with the same command (the port is remembered). Remove it, and only it, with
`curl -LsSf https://abstractframework.ai/uninstall.sh | sh -s -- --instance fresh` (`--purge` also
deletes its data dir; the caches, `~/.abstractassistant`, `~/.abstractcode` and uv stay). To rebuild an
instance and keep its accounts, copy `<data dir>/auth` aside first and put it back before the
instance's first start: `users.json` holds the accounts and their password hashes.

## FAQ

**`nvidia-smi: command not found`, or `sudo: ubuntu-drivers: command not found`.** Cloud images
often ship without the driver and without `ubuntu-drivers`. Run step 2.

**The gateway stops when I close SSH, or does not start after a reboot.** A systemd user service
runs only while you are logged in unless lingering is on: `sudo loginctl enable-linger "$USER"`.

**Can I open port 8080 instead of tunnelling?** Keep the default. The gateway binds `127.0.0.1`
only, so nothing is exposed even with the firewall off. To serve other machines, choose it in the
console's **Network** page, which explains the risks first.

**`bind: Address already in use` when opening the tunnel.** Port 8080 is taken on your computer:
use `ssh -N -L 18080:127.0.0.1:8080 ubuntu@<server>` and pass `--base-url http://127.0.0.1:18080`
to `claim-url`.

**The sign-in link says it expired, or I lost the token.** Make a new link with
`abstractgateway-config claim-url --base-url http://127.0.0.1:8080`; the token itself stays in
`~/.local/share/abstractgateway/auth/bootstrap-admin-token`.

**The installer skipped the terminal console and `abstractcode`.** Cloud images often ship without a
C compiler, and cargo needs one to build them; the installer says so before it starts (`no C
compiler: the terminal console and AbstractCode's terminal client ... are skipped`) and again in its
summary. Fix: `sudo apt-get install -y build-essential`, then the install line again. Installing the
Code app in the console also installs a prebuilt `abstractcode`. vLLM needs the same compiler the
first time it starts a model.

**The setup guide recommends `lmstudio · qwen/qwen3.5-9b`.** LM Studio is a desktop app and is not
installed on a server; use llama.cpp with a GGUF model as in step 6. (The guide does not yet
recommend the engine that is installed. The llama.cpp card's "CPU on Linux" is also wrong when the
installer's summary says `GGUF: ... cu130`: the CUDA build is in, and the model runs on the GPU.)

**Speech synthesis fails with `Supertonic 3 artifacts are not available locally`.** Download the
voice weights: `abstractgateway models download supertonic supertonic-3`.

**`Failed to create llama_context` from the OpenAI API (`/v1`).** The GPU is full with another copy
of the model. Free it with
`abstractgateway models unload --provider huggingface --model <model>` and retry.
