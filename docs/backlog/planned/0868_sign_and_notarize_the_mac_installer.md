# 0868 — Sign and notarize the Mac installer, then remove the "Open Anyway" step from the docs

> Package: abstractframework (scripts/lib/build_macos_installer.sh, GitHub releases, root docs)
> Type: task
> Created: 2026-09-25
> Priority: high
> Labels: install, macos, signing, release, owner-action

## Summary

`AbstractFramework-Installer.pkg`, attached to the root GitHub releases v0.3.0 and v0.3.1 and served
by the documented `releases/latest/download/AbstractFramework-Installer.pkg` link, is unsigned
(`pkgutil --check-signature`: no signature). Gatekeeper blocks it on first open and every user must
find **System Settings > Privacy & Security > Open Anyway**. Sign it with a Developer ID Installer
certificate, notarize and staple it, replace the release asset, and then update every doc place that
teaches the workaround.

## Why

The installer exists for non-technical users; a security warning on the first double-click is the
largest remaining friction in that path (SUMMARY third wave, "Needs operator signing/notarization";
STATUS owner follow-ups).

## Current code reality (2026-09-25)

- `scripts/lib/build_macos_installer.sh` already signs and notarizes when `AF_PKG_SIGN_IDENTITY`
  and `AF_NOTARY_PROFILE` are set (lines ~150–175: `SIGNED`, `NOTARIZED`), and says plainly what is
  unsigned otherwise. No Developer ID exists yet: this is the blocker.
- Doc places that describe the unsigned step (grep `Open Anyway|unsigned|Gatekeeper`): `README.md`
  (~l.30), `docs/install.md` (~l.19), `docs/getting-started.md` (~l.27), `docs/faq.md` (~l.165),
  `docs/troubleshooting.md` (~l.35–38), `docs/glossary.md` (~l.208),
  `docs/installers/user-journeys.md` (~l.9), `docs/installers/security-and-os-blocks.md`
  (l.3–20, ~83), `docs/installers/release-and-manifest.md` (~l.56), plus `llms.txt` /
  `llms-full.txt` regenerated after the edit.
- The installer design docs and ADR-0038 predate the payload-free `.pkg` (coredoc root finding).

## Scope

### In scope

- Owner: obtain the Developer ID Installer certificate and a `notarytool` keychain profile.
- Build with both variables from the release tag, verify, `gh release upload <tag> … --clobber`.
- Update the doc places above (keep a short troubleshooting entry for older unsigned downloads).
- Refresh ADR-0038 / `docs/installers/*` for the payload-free `.pkg`.
- Decide whether release CI signs (secrets in the `pypi`-style protected environment) or the owner
  signs locally; record it in the release runbook.

### Out of scope

- Windows code signing (0162 covers the broader signed-installer CI idea).
- Signing the AbstractAssistant `.app` (separate component).

## Acceptance criteria

- [ ] `pkgutil --check-signature AbstractFramework-Installer.pkg` shows a Developer ID Installer chain.
- [ ] `spctl --assess --type install -vv` accepts the downloaded file; `stapler validate` passes.
- [ ] The `latest/download` asset is the signed build (sha recorded in the release notes).
- [ ] No doc outside troubleshooting tells a user to click **Open Anyway**.

## Testing

- `curl -sLo /tmp/af.pkg https://github.com/lpalbou/AbstractFramework/releases/latest/download/AbstractFramework-Installer.pkg && pkgutil --check-signature /tmp/af.pkg`
- `spctl --assess --type install -vv /tmp/af.pkg`
- `grep -rn "Open Anyway" README.md docs/*.md docs/installers/*.md`

## ADR status

- Governing: ADR-0038 (script bootstrap and gateway console install). ADR impact: may revise
  ADR-0038 (installer shape), no new rule.

## Receipts

- `untracked/release-2026-09-24/STATUS.md` (addenda 20:55 and 22:15 CEST); coredoc root row in
  `untracked/coredoc-2026-09-25/STATUS.md`; related 0162, 0863.
