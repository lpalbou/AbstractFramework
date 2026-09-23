# Installers

This directory documents how AbstractFramework is installed on a user's machine: a one-line
bootstrap script per OS that provisions the gateway with [uv](https://docs.astral.sh/uv/), and
the gateway's web console (`/console`) as the guided setup UI. The user-facing instructions are in
[Install](../install.md); these pages explain the design, the contracts and the security model
behind them. The decision is recorded in
[ADR-0038](../adr/0038-script-bootstrap-and-gateway-console-install.md).

## Document map

- [`strategy.md`](strategy.md): the install model and why it is script + console.
- [`user-journeys.md`](user-journeys.md): what happens step by step on macOS, Linux and Windows,
  for first install, apps, engines, upgrade and uninstall.
- [`components.md`](components.md): each component, how it reaches the machine, and what the
  bootstrap does with it.
- [`security-and-os-blocks.md`](security-and-os-blocks.md): Gatekeeper, SmartScreen, execution
  policy, sudo/UAC prompts, loopback binding, and where code signing still applies.
- [`release-and-manifest.md`](release-and-manifest.md): the generated install manifest
  (`install-manifest.json`, schema v2) and how releases update it.
- [`operations-and-support.md`](operations-and-support.md): data and log locations, health
  checks, troubleshooting.
- [`implementation-plan.md`](implementation-plan.md): what is delivered and what comes next.
- `install-manifest.json` / `install-manifest.schema.json`: the generated manifest and its schema.

## Scripts

| OS | Script | One-liner |
|---|---|---|
| macOS, Linux | [`scripts/install.sh`](../../scripts/install.sh) | `curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh \| sh` |
| Windows 10 22H2+ / 11 | [`scripts/install.ps1`](../../scripts/install.ps1) | `powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1 \| iex"` |
