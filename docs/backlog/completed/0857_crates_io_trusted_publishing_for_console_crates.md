# 0857 — crates.io trusted publishing for the console crates

> Package: abstractcore (console-tui → abstractcore-console), abstractgateway (console-tui → abstractgateway-console)
> Type: task
> Created: 2026-09-23
> Completed: 2026-09-26
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

- [x] The next patch of each crate publishes from CI with no local token (gateway console 0.9.0; core console not yet re-released).
- [ ] Release docs describe the tag format and the trusted-publisher setup.

## Status update 2026-09-25 (post-release trace)

Still open. `abstractgateway-console` 0.8.0 (2026-09-24) was again published locally with cargo
credentials: crates.io API shows `published_by: lpalbou` and no trusted-publishing data for 0.8.0
and 0.7.0; the release ledger says the CI crate job has no trusted publisher for
lpalbou/AbstractGateway (`release.yml`, environment `crates-io`). No STATUS addendum records the
owner configuring it on the evening of 2026-09-24. The configuration itself cannot be read without
the owner's crates.io session; verify with the next crate release from CI.

## Completion report (2026-09-26)

- Outcome: CI publishes the gateway console crate through crates.io trusted publishing. The
  abstractgateway release run 36234261343 (tag `v0.5.0` → `3f08db2`) published
  `abstractgateway-console` 0.9.0 at 10:07:50Z UTC with trustpub data (github lpalbou/AbstractGateway,
  run 36234261343, sha `3f08db2`), checksum `3cad35b2…3406`; the registry crate equals a local
  `cargo package --locked` of the tag file for file. No local cargo token was used. The owner
  configured the trusted publisher between the 0.8.0 wave and this one (the staging review still
  expected a local publish, REVIEW/27 D2).
- abstractcore-console: its trusted publisher was already configured (REVIEW/27 D2); the crate stays
  at 0.2.0 and the core release job skipped it, so its first CI publish is still to be observed on
  the next crate version.
- abstractcode 0.6.0 also published through trusted publishing (run 36227938975), as 0.5.1 did.
- Acceptance: the first criterion holds for the gateway crate. The second (release docs describe
  the tag format and trusted-publisher setup) is not done: the `abstract-release` skill and the
  package docs do not describe the crates.io setup. Residual, documentation only; fold into the next
  edit of the release runbook.
- Record: [0921](0921_release_wave_2026_09_26.md). ADR impact: None.
