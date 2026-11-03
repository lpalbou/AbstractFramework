# 1067 — One-command server deployment (`install.sh --server`)

> Package: abstractframework (root installers, docs/deploy-linux.md), abstractgateway (`service enable`, network settings)
> Type: task
> Status: implemented, acceptance pending (2026-10-28: `install.sh --server [--gpu] [--tailscale-funnel]`, tests/test_install_sh_server.py, docs/deploy-linux.md#one-command; with gateway 0.18.0 it prints the setup code instead of a claim link; the fresh-VM acceptance run on the OVH box waits for the respawned instance. Deviation: after a driver install the run continues and ends with "reboot, then run the same command again" rather than refusing; a FAILED driver step warns and continues on CPU)
> Created: 2026-10-28
> Priority: normal
> Labels: installer, linux, server, tailscale, deployment, first-run
> Related: docs/deploy-linux.md (the manual baseline), 1060 (gateway security standing duty), gateway 0957 (linger hint), gateway 0958 (setup recommends an installed engine), gateway 0964 (first connection sets the admin password)

## Summary

The fresh-Linux sequence that worked on 2026-10-28 (OVH box; evidence `untracked/release-closing/ovh-test.log`
in the framework root checkout) is a dozen manual steps: the installer, `loginctl enable-linger`,
`abstractgateway service enable`, the NVIDIA driver step, Tailscale install + `tailscale up` + Funnel, the
gateway's origins / proxy settings for the public address, then the first claim link. It becomes ONE
idempotent command, `install.sh --server [--tailscale-funnel] [--gpu]` (or a `deploy-linux.sh` the installer
hands off to), that ends by printing the public address and the one-time sign-in link, and nothing else a
person must copy.

## Why

Operator (2026-10-28): the manual sequence is documented (`docs/deploy-linux.md`) and proven, but every step is
a place to stop; a server deployment should be a command whose end state is "open this address, sign in".

## Scope

### In scope

- `install.sh --server`: runs the installer's Linux path, enables lingering and the user service, applies the
  gateway network mode for a server (`lan` or `internet` behind Tailscale), sets origins / trust-proxy for the
  Funnel address, prints the address and the claim link (or, after gateway 0964, "set the admin password").
- `--tailscale-funnel`: installs Tailscale when absent, logs in (prints the auth URL and waits once), serves
  the gateway over Funnel, records the address in the gateway's network settings.
- `--gpu`: the NVIDIA driver / CUDA preflight from the OVH run (detect, install or print the exact command,
  pick the CUDA llama.cpp build, refuse to continue with a half-installed driver).
- Idempotent: re-running reports what is already done (the installer's `--print`/rerun summary pattern,
  `tests/test_install_profiles.py::test_install_ps1_rerun_says_what_it_finds_and_keeps_the_choices` is the model).
- `docs/deploy-linux.md` stays the manual baseline and gains the one-command section; `docs/install.md` links it.

### Out of scope

- Windows / macOS server modes; cloud-provider images (a later item).

## Acceptance

- A fresh Ubuntu 24.04 VM (OVH-class, with and without a GPU): one command, end state = the console reachable at
  the printed address, signed in through the printed link; the OVH log's manual steps are no longer needed.
- Rerun on the same box: no change, a summary of what is in place.
- Secrets never printed beyond the one-time link; the token stays in its `0600` file.
