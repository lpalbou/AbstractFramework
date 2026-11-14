# 1209 — Complete the release code scope and synchronize the release handoff

> Package: AbstractFramework, AbstractSkill, AbstractMemory, AbstractUIC, AbstractAssistant, AbstractCode, AbstractRuntime, AbstractGateway, AbstractEntity
> Type: task
> Created: 2026-11-13
> Priority: P0
> Labels: release, integration, documentation

## Summary

Recover the code omitted from the 0.14.0 handoff, account for valuable existing branches and
worktree changes, complete their required consumers, and deliver a clean, tested candidate.

## Why

Operator: "backlog updates, it's ok. but codes, that's not ok" and "ensure every valuable commits
is considered and merged onto main ? if you have doubts on if something should be merged, analyze
and ask me now". Lower-package publishing and routine integration are authorized. Root and website
publication remain separate operator decisions after personal candidate testing.

## Current code reality

- Initial audit: 23 normal main checkouts, 19 local-only commits in eight repositories; no behind
  or diverged main. Memory, UIC, Assistant and Code contain pending product code. Other ahead
  commits are backlog/receipts. Four checkouts contain unrelated untracked outputs.
- Published root 0.14.0 pins Assistant 0.18.3 and panel-chat 0.9.13. Local Assistant is 0.19.0 and
  panel-chat 0.9.14; neither local version is published. Local packs of 0.9.14 fail Code's snapshot
  provenance check; an isolated Code build from registry dependencies passes.
- Memory's resolution replay metadata has no Runtime projection writer yet. Gateway close notices
  and the Entity Questions lens still need integration (1206). Publishing the pending halves alone
  would leave the user-visible fix unfinished.
- Current remote-main CI is red in Agent (historical Runtime visibility failure) and Gateway
  (summon preemption assertion and concurrent module-snapshot teardown).
- Independent branch/worktree reviews distinguish source-equivalent history from genuine omissions.
  Reports are preserved under `untracked/release-recovery-2026-11-13/`; uncertain scope was put to
  the operator before cuts. Original branches and worktrees are preserved.

## Scope

### In scope

- Prepared local-main product changes and their necessary consumer integration, coredoc updates,
  generated llms files, tests, fresh versions and registry validation.
- Branch/worktree disposition table, including selected orphan tests and confirmed fixes.
- Strengthen the bundled/installed release skills and the pending-release guard so a clean tree
  with local-only commits cannot be accepted as a finished release.
- Diagnose and repair release-blocking CI; validate each integrated tree before pushing.
- Local deployment, website preview and a report of the tested candidate for the operator.

### Decision boundaries

- Operator accepted the recommended scope on 2026-11-14: retain the security/language/Core
  feature and breaking TUI deferrals, recover confirmed hidden Apple fixes, complete the 1206
  chain and CI repairs. The older Code composer redesign and optional fast-list work remain deferred.
- The same wave includes bounded Hugging Face discovery, reliable Windows login registration,
  and a macOS tray Exit that the workspace supervisor respects.
- Never merge private/operator branches, old release pins, rejected experiments or superseded code
  merely because their hashes are absent from main. Record the source evidence and disposition.
- Backlog-only changes need no gratuitous registry cut. Unrelated generated/private outputs are
  preserved outside source checkouts, with their paths recorded.

## Acceptance criteria

- [x] Every valuable code candidate has an evidence-backed disposition and every uncertain scope
  decision has the operator's answer.
- [ ] Required writers, replay paths and UI consumers are integrated and tested end to end.
- [ ] Every in-scope source commit reaches live remote main; package artifacts match those sources.
- [ ] Version sources, changelogs, external docs, package skills and generated llms files agree.
- [ ] Required local gates, independent review and exact-commit remote CI pass; registry versions
  are visible before dependent publication.
- [ ] All normal checkouts are on main, clean, zero ahead/behind after the final pull sweep; the
  full workspace build passes and the local candidate and website preview are reviewable.
- [ ] Root and website publishing await the operator's separate release decision.

## Receipts

- Initial live audit: `/tmp/af-release-audit-20261113.md` and accompanying JSON evidence.
- Initial actual pull sweep: `/tmp/af-release-recovery-pull-initial.log`, 23 repositories,
  zero fast-forwards, zero attention errors.
- Scope sweep: `/tmp/af-release-recovery-scope.json` (37 packages, planned backlog discovery).

- AbstractSkill procedures/gate: local gate 11 pass on 5ccbbf1, independent review approved after
  two bypass fixes; PR #9 merged eed7ccd and normal main immediately pulled; main CI43502051822
  green; tag v0.3.12 publishing.
- Root console pin contract salvaged from PR #70; three tests pass, including a wrong-pin mutation
  and a tag-vs-checkout fixture. Assistant operational skill/docs prepared; CLI version/help and
  unreachable-gateway path verified in a disposable HOME; nine existing CLI tests pass.

- AbstractSkill 0.3.12 released from main eed7ccd: release43502223686 green, PyPI visibility
  confirmed, GitHub release and docs deployed. Normal checkout remains clean/synchronized.
- Agent unchanged main passed its full fresh local matrix (Python3.10/3.11/3.12 and build),
  four pass in1m09s. One historical failed-install revalidation requested after registry visibility
  was confirmed; no new package cut or retry-to-green loop.

- Agent exact-main CI42756303625 attempt2 GREEN; no Agent code was changed or republished.
- Assistant fresh review found attachment loss on failed-mention retry; both palette and worker
  paths reproduced red. Working-tree fix and31test suite preserve the new file and unanswered
  recipients; package item1210 tracks real-Gateway proof, gates and eventual main integration.

- Remaining-repository review found the Avatar0.2→TUI/console consumer migration; proposed1211
  records its breaking public API, consumer versions and4–10hRust estimate. Fifth scope answer
  pending. Camera/3D have no pending source; old TUI implementations are already ported.

## Operator scope accepted 2026-11-14

The operator accepted the recommended scope: complete prepared code and1206 consumers, Gateway CI repairs, confirmed Apple fixes; preserve the explicit governance/language/Core-feature/TUI migration deferrals and the Code composer prototype. No optional fast-list expansion.

Additional required Gateway fixes in the same cut: Hugging Face Console searches must not flood endpoints; enabled Windows startup must work; macOS tray Exit must not trigger relaunch. The Hugging Face investigation may require the owning Core catalog mechanism; its fix is authorized, while unrelated Core features remain deferred.
