# Security policy

## Reporting a vulnerability

Please do not open a public GitHub issue for a security problem. Email
`contact@abstractframework.ai` with the subject **"Security report: AbstractFramework"** and
include, as far as you can:

- the affected versions (`pip show abstractframework`, `abstractgateway --version`, or the release
  tag) and the install path (Mac installer, one-line script, `pip install`, container);
- what an attacker can do, and under which configuration (for example the gateway's Network
  setting: `localhost`, `lan` or `internet`);
- steps to reproduce, or a proof of concept;
- relevant logs, with tokens and keys removed.

You will receive an acknowledgement, and we will agree with you on a timeline for a fix and a
release. Tell us if you would like to be credited in the release notes.

## Scope

This repository covers the `abstractframework` meta-package, the installers
(`scripts/install.sh`, `scripts/install.ps1`, `scripts/uninstall.sh`, the Mac installer package)
and the workspace scripts. A problem in a component (AbstractGateway, AbstractCore, an app) is
best reported through that component's own security policy; if you are unsure where it belongs,
report it here and we will route it.

## Supported versions

Security fixes land in the latest `abstractframework` release and its pinned components. Upgrade
by re-running the installer, or with `pip install -U abstractframework`.

## Hardening references

- [Gateway security](docs/guide/gateway-security.md): auth, users and exposure.
- [OS security and installation blocks](docs/installers/security-and-os-blocks.md): Gatekeeper,
  SmartScreen, execution policy and loopback binding.
