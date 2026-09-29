# 0983 — Follow-ups after root 0.6.2 (one upgrade path)

> Package: abstractgateway (self_update); abstractcore (capability routes); abstractframework (installers)
> Type: task
> Created: 2026-09-28
> Priority: normal
> Labels: installer, self-update, follow-up

## Summary

What the one-upgrade-path work (0982) left open, from `untracked/one-upgrade-note.md` §3 and §6 and
the 0.6.2 staging.

## Items

1. **GitHub API rate limit for the update check (gateway).** The installer-install check resolves
   root `main` to one commit through `api.github.com` (60 unauthenticated requests per hour per IP;
   the check is cached 1 h). An exhausted limit reads "GitHub … answered HTTP 403", in band. Decide
   whether a shared NAT (office, CI) needs a documented troubleshooting entry or a different
   resolution path; never an exception either way.
2. ~~**Stored image route on an 8 GB Mac is not flagged (core).**~~ **Done** in abstractcore 2.19.0
   (`47b1ba9`): a saved image or video route whose catalog model does not fit is flagged
   `route_unavailable` (grid, `config defaults`, `apply-recommended`) with the recommendation's
   reason, from the same fit verdict; the saved routes are never changed. Root 0.6.2 pins 2.19.0.
3. **Hand-started gateway on the recorded port, without `--no-start` (root installer).** A plain
   re-run still treats a gateway it did not start (no pid file, not the login item) as another
   program and moves to the next free port (`--no-start` keeps the port since 0.6.2). Consider
   recognising a gateway that serves this install's data dir (its health or pointer) before moving.
4. **pwsh coverage (root).** The install.ps1 behaviour tests are skipped without PowerShell 7; the
   `-NoStart` kept-port rule is covered statically only. Run the pwsh tests on a machine or CI job
   that has `pwsh`.
5. **Update log length (gateway).** The job keeps the last 200 installer lines; the full log is the
   newest `<data dir>/logs/install-*.log`. Consider a link or path in the console's Update log.

## Acceptance criteria

- [ ] Each item fixed with a test that goes RED without it, or closed with a recorded decision.

## Receipts

- `untracked/one-upgrade-note.md` §3, §6; `untracked/wave4-STAGE.md`.
