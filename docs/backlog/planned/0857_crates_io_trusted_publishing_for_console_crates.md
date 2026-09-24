# 0857 — crates.io trusted publishing for the console crates

> Package: abstractcore (console-tui → abstractcore-console), abstractgateway (console-tui → abstractgateway-console)
> Type: task
> Created: 2026-09-23
> Priority: normal
> Labels: release, crates.io, ci

## Summary

`abstractcore-console` 0.2.0 (first publish) and `abstractgateway-console` 0.7.0 were published
to crates.io manually with a local cargo token, because crates.io trusted publishing can only be
configured for a crate that already exists. Future versions should publish from each repo's
release workflow through OIDC, like the PyPI and npm packages.

## Scope

### In scope

- Configure the crates.io trusted publisher (GitHub repo, workflow file, environment) for both
  crates.
- Make each release workflow publish its crate on the crate's tag and skip cleanly when the
  version already exists.
- Remove the need for a local cargo token in the release runbook (`abstract-release` skill).

### Out of scope

- Other crates (abstracttui, abstractcode) unless they share the same gap.

## Acceptance criteria

- [ ] The next patch of each crate publishes from CI with no local token.
- [ ] Release docs describe the tag format and the trusted-publisher setup.

## Status update 2026-09-25 (post-release trace)

Still open. `abstractgateway-console` 0.8.0 (2026-09-24) was again published locally with cargo
credentials: crates.io API shows `published_by: lpalbou` and no trusted-publishing data for 0.8.0
and 0.7.0; the release ledger says the CI crate job has no trusted publisher for
lpalbou/AbstractGateway (`release.yml`, environment `crates-io`). No STATUS addendum records the
owner configuring it on the evening of 2026-09-24. The configuration itself cannot be read without
the owner's crates.io session; verify with the next crate release from CI.
