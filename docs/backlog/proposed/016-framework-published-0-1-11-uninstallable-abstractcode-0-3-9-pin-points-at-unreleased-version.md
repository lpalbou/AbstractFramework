# 016-framework: [BUG] Published 0.1.11 is uninstallable: abstractcode==0.3.9 pin points at an unreleased version

> Package: framework
> Type: bug
> Created: 2026-07-15 19:45 +0200
> Priority: P0 (public install broken)
> Labels: release, seat-code, decision-gate

## Summary

`abstractframework==0.1.11` (published 2026-06-14) pins `abstractcode==0.3.9` in
`requires_dist`, but abstractcode 0.3.9 was never published — PyPI's latest is
0.3.8. `pip install abstractframework` has failed resolution for every user
since the 0.1.11 upload. Verified 2026-07-15 by pip dry-run against the
published wheel: "No matching distribution found for abstractcode==0.3.9".

## Why

This is the partial-release drift class backlog 0168 documented (then:
root pinned a STALE gateway; now the inverse: root pinned a NOT-YET-PUBLISHED
abstractcode). The 0168 guard patched the release skill, but 0.1.11 shipped
with a forward pin anyway — the guard must also verify that every `==` pin
RESOLVES on PyPI at root-publish time, not merely that pins agree with local
repo versions.

## Evidence

- PyPI abstractframework 0.1.11 requires_dist: `abstractcode==0.3.9` (uploaded 2026-06-14T19:13:20Z).
- 0.1.10 (same day) carries the SAME broken pin — both latest versions uninstallable.
- PyPI abstractcode releases end at 0.3.8 (no 0.3.9 key, nothing yanked).
- Local `abstractcode/pyproject.toml` version = 0.3.9 (unreleased working tree).
- `pip install --dry-run 'abstractframework==0.1.11'` → "No matching distribution found for abstractcode==0.3.9" (2026-07-15).
- SEVERITY AMPLIFIER (verified dry-run, unpinned): `pip install abstractframework` does NOT fail — pip backtracks past 0.1.11/0.1.10 (and apparently past 0.1.7/0.1.6 too) and SILENTLY installs **0.1.0 from 2025-10-18**. Every fresh install since 2026-06-14 has delivered a nine-month-old framework with no error message.
- Minor, non-breaking drift found in the same audit: pinned abstractvision 0.3.26 while PyPI latest is 0.3.27 (installable, just stale).

## Fix paths (operator decision)

1. **Publish abstractcode 0.3.9** — REFINED per code's readiness answer (c2346): the CURRENT working tree is NOT a clean 0.3.9 (uncommitted +2,713/-183 incl. a breaking gateway-required startup gate → semver 0.4.0 territory; depends on unreleased sibling behavior; suites green only against editable siblings). The publishable artifact is committed HEAD `5258e1c` ("acceptable version", the operator's own checkpoint, version-stamped 0.3.9 since commit 64fddd9 of Jun 3) — AFTER code's ~15-min fresh-venv suite run against released PyPI deps. Today's breaking wave ships later as 0.4.0 in a coordinated wave with raised core/agent floors. STILL RECOMMENDED in this refined form.
2. **Hotfix root 0.1.12** re-pinned to `abstractcode==0.3.8`. Requires verifying 0.3.8 still composes with the rest of the pinned wave — riskier than it looks.
3. Both (publish 0.3.9, then a routine root bump next wave).

## Operator ruling (2026-07-15, DM)

DEFERRED to the coordinated release wave — laurent, verbatim: "oh yes, you are far behind. but let's stabilize the development of our package, then we can do an update with you with a release mentioning/pinning all the versions of the framework packages. be patient." No solo abstractcode publish now; the public install stays on the 0.1.0 fallback until the stabilization wave ships a full pinned release (this card's evidence feeds that wave). Code's fresh-venv check stood down (commons c2345 thread closed citing this ruling).

## Acceptance criteria

- [ ] Coordinated release wave ships: all framework packages published + root re-pinned to versions that EXIST on PyPI (operator-called; this card feeds it)
- [ ] `pip install abstractframework` resolves and installs the new root clean on a fresh venv (dry-run receipt attached)
- [ ] Release-skill guard extended: root publish requires every `==` pin to resolve against the live index AND suites re-proven against released deps, not editable trees (0168 follow-up; code's c2346 lesson)

## Receipts

- Audit + dry-run: framework seat, 2026-07-15 (hub c2340 DM/commons thread)
