# Deploy an AbstractFramework gateway on a fresh Linux server

The sequence below was run end to end on a fresh Ubuntu 24.04 cloud instance (4 vCPU, 26 GB RAM, one
NVIDIA Quadro RTX 5000) with AbstractFramework 0.11.17. Each step shows the line to expect. Run the
commands as your normal user (here `ubuntu`), not as root. `<server>` is the server's address.

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

After the reboot, `systemctl --user is-active abstractgateway` answers `active`.

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

A small GGUF model that runs on the GPU through llama.cpp:

```bash
abstractgateway models catalog --fits | grep GGUF        # what fits this server
abstractgateway models download huggingface "unsloth/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M"
# done: snapshot cached at ~/.cache/huggingface/hub/models--unsloth--Qwen3-4B-Instruct-2507-GGUF/...
abstractgateway-config set-default output.text --provider huggingface --model unsloth/Qwen3-4B-Instruct-2507-GGUF
abstractgateway-config set-default input.text  --provider huggingface --model unsloth/Qwen3-4B-Instruct-2507-GGUF
# Set execution-host capability default: output.text  (then input.text)
```

Local voice (Supertonic text-to-speech) needs its weights once:

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
# Done.
systemctl --user disable --now abstractgateway; rm -f ~/.config/systemd/user/abstractgateway.service
systemctl --user daemon-reload
sudo loginctl disable-linger "$USER"
```

The last three lines remove the service from step 4 (`systemctl --user is-enabled abstractgateway`
then answers `not-found`). Kept on purpose: `~/.local/share/abstractgateway` (your data; add
`--purge` to delete it), `~/.cache/huggingface` (models), `~/.cache/uv` (about 14 GB with the gpu
profile; `--remove-uv` removes uv and its cache).

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

**The installer skipped the terminal console and `abstractcode`.** Building them needs a C compiler:
`sudo apt-get install -y build-essential`, then the install line again. Installing the Code app in
the console also installs a prebuilt `abstractcode`. vLLM needs the same compiler.

**The setup guide recommends `lmstudio · qwen/qwen3.5-9b`.** LM Studio is a desktop app; on a
server, use a GGUF model as in step 6.

**Speech synthesis fails with `Supertonic 3 artifacts are not available locally`.** Download the
voice weights: `abstractgateway models download supertonic supertonic-3`.

**`Failed to create llama_context` from the OpenAI API (`/v1`).** The GPU is full with another copy
of the model. Free it with
`abstractgateway models unload --provider huggingface --model <model>` and retry.
