# 1211 — Adopt Avatar 0.2 across the TUI and console family

> Package: AbstractAvatar, AbstractTUI, AbstractCore console, AbstractGateway console, AbstractCode terminal
> Type: task
> Created: 2026-11-13
> Priority: P1
> Labels: release, compatibility, rust, avatars

## Summary

Coordinate the public AvatarStyle migration rather than changing one Cargo floor in isolation.
Framework recovery 1209 asks the operator whether this migration belongs in the current wave.

## Current code reality

- Avatar 0.2 is published; TUI 0.8 still declares Avatar `^0.1.0` and locks 0.1.0.
- TUI's readiness allowlist explicitly awaits replacement with `AvatarStyle::ready()` after the
  dependency upgrade (d742fce). Existing ready-style behavior is implemented manually.
- TUI publicly re-exports AvatarStyle, while Avatar 0.2 removed variants. Adoption changes TUI's
  public surface and likely needs TUI 0.9 with matching graph/mermaid extension versions.
- Code terminal depends on TUI 0.8; Core and Gateway consoles still depend on TUI 0.7.1. Each
  consumer needs source/build verification and an explicit release decision.
- Old TUI maint/round15 implementations are already superseded on main. A dirty validation
  worktree contains an obsolete absolute-path Avatar override; it is not a release candidate.

## Proposed route

Port to the public Avatar readiness API; remove the copied list; update affected enum uses and
public exports; verify extension and console consumers before cutting the base. Publish bottom-up.
Estimate: 4–10 hours Rust migration/validation, plus any Core/Gateway publishing overhead.

## Decision

Pending operator scope answer. Recommendation: preserve compatible existing dependency lines for
the recovery and schedule the breaking family migration as a coordinated cut. Never represent
Avatar 0.2 as already adopted by these consumers.

## Receipts

- `untracked/release-recovery-2026-11-13/review-remaining-repos.md` (independent source review).
