# Backlog Item 036: Per-package commit script

## Summary
Add a `scripts/commit.sh` helper that commits changes in each AbstractFramework
repository with a single message, skipping clean repos.

## Reason
Working across multiple sibling repositories makes repetitive git add/commit
work error-prone. A single command reduces mistakes and keeps commit messages
consistent across packages.

## Scope
### In scope
- Add `scripts/commit.sh` with clear usage, preflight checks, and summary output.
- Commit per repository (root + siblings), skipping clean repos.
- Warn when a repo is missing or a commit fails.

### Out of scope
- Pushing commits to remotes.
- Branch management, tagging, or PR creation.
- Changes to commit hooks or git config.

## Dependencies
- Git CLI.
- Sibling repo list aligned with `scripts/clone.sh` and `scripts/status.sh`.

## Expected Outcomes
- One command commits changes per repository with a shared message.
- Clean repositories are skipped with clear output.
- Failures are reported without ambiguity.

## Implementation Plan
- Follow the existing `scripts/*.sh` banner + header style.
- Resolve repo root from the script location and validate it.
- For each repo: detect changes, `git add -A`, and `git commit -m "<message>"`.
- Summarize counts (committed, clean, missing, failed) at the end.

## Full Report
- **Summary**: Added a per-repository commit script that stages and commits changes across the root repo and siblings with a shared message, skipping clean repos and summarizing results.
- **Implementation**: Added `scripts/commit.sh` (executable) aligned with existing repo lists and root detection logic.
- **Knowledge base**: Recorded the new helper in `AGENTS.md`.
- **Tests**: `bash -n scripts/commit.sh`; `./scripts/commit.sh --help`.
