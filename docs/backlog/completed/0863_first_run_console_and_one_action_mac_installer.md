# 0863 — First-run console and one-action Mac installer (root 0.3.0 / 0.3.1)

> Package: abstractframework (scripts/install.sh, install.ps1, uninstall.sh, `Install AbstractFramework.command`, scripts/lib/build_macos_installer.sh); abstractgateway (first-run guide, console)
> Type: feature
> Created: 2026-09-25
> Completed: 2026-09-24
> Priority: high
> Labels: install, first-run, console, release-trace

## Summary

Completed record for unplanned major work (no prior backlog item; written for traceability during
the 2026-09-25 post-release trace). A non-technical Mac user installs AbstractFramework with one
action — an unsigned, payload-free `.pkg` that opens a `.command` in Terminal, the `.command` itself,
or the one-line `install.sh` — and lands in the gateway console already signed in (one-time claim
link), where a full-page setup guide installs an engine, a model and the browser apps. An
uninstaller removes everything the installer wrote. It extends 0855 (root 0.2.0 one-line install).

## What landed

- Root (commits `c4c19e9`, `dfe0848`, `82543f1`, `04c1882`, release `1a769be`/`0565c43` = tag
  `v0.3.0`, `81966f1`/`cb29dda` = tag `v0.3.1`): `.pkg` + `.command` + `uninstall.sh`
  (`Uninstall AbstractFramework.command`), plain-language failure messages, llama.cpp from
  upstream prebuilt wheels (no compiler), the gateway Network setting seeded at install instead of a
  pinned `--host`, docs/install.md rewritten for non-technical users.
- Gateway 0.4.1 / 0.4.2 console: full-page setup guide (step rail, one primary action per card,
  inline progress, plain failures with details behind a disclosure, Technical-details toggle), app
  cards with one **Install** then **Open** / **Open in Terminal** (missions L, L2, GG, LL).
- GitHub releases `v0.3.0` and `v0.3.1` of lpalbou/AbstractFramework carry
  `AbstractFramework-Installer.pkg`, so the documented `releases/latest/download/…pkg` link answers
  (it had always 404'd before 2026-09-24).

## Completion report

- Validation (orchestrator-verified, `untracked/missions-2026-09-22/SUMMARY.md` third and fourth
  waves; mission P): scratch-HOME runs — fresh install 76 s to a signed-in console, idempotent
  re-run 1 s, damaged-install repair 16 s, offline → plain message, uninstall 4.9 GB → 20 KB;
  40/40 shell tests + 23 profile tests; console Playwright 19 passed / 1 skipped (L2), 100+
  screenshots in both themes (L), 173 tests + 11 mutants (GG), 191 tests + 18 mutants (LL).
- Release evidence: PyPI abstractframework 0.3.0 and 0.3.1 (pins core 2.15.1, gateway 0.4.2,
  runtime 0.4.34 in 0.3.1), 24/24 dry-run install matrix, real scratch install from PyPI
  (`untracked/release-2026-09-24/STATUS.md`, `abstractframework-0.3.1-ledger.md`).
- Incident fixed during the wave: the first v0.3.0 `.pkg` asset embedded the never-published
  gateway pin 0.4.0; rebuilt from the tag and replaced (STATUS addendum 22:15 CEST).
- Residual risks and follow-ups:
  - The `.pkg` is unsigned; users must click **Open Anyway** once → 0868.
  - `install.ps1` read-reviewed and CI-smoked only → 0856 (unchanged).
  - Compiled packages in the default extras still break the plain `pip` route → 0861.
  - The installer zip is built but not attached to releases (coredoc root finding; docs no longer
    claim it) — no item; revisit with 0868.
  - Installer design docs and ADR-0038 predate the payload-free `.pkg` → noted in 0868.
- ADR state: ADR-0038 (script bootstrap and gateway console install) governs; it needs a refresh
  for the `.pkg` path, recorded in 0868 rather than a new ADR.

## Receipts

- `untracked/missionP/`, `untracked/missionL/`, `untracked/missionL2/`, `untracked/missionGG/`,
  `untracked/missionLL/` (local reports).
- `untracked/release-2026-09-24/STATUS.md`, `abstractframework-ledger.md`,
  `abstractframework-0.3.1-ledger.md`.
