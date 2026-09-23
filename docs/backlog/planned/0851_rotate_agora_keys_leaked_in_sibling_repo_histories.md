# 0851 — Rotate agora API keys leaked in sibling repositories' pushed histories

> Package: abstractframework (workspace; AbstractSkill, AbstractUIC, AbstractObserver, AbstractFlow, AbstractCore, abstractagent, abstractassistant)
> Type: task
> Created: 2026-09-23
> Priority: high
> Labels: security, decision-gate

## Summary

OPERATOR DECISION GATE (never assignable): agora hub API keys were committed in
`.cursor/mcp.json` and pushed to GitHub in several sibling repositories before the
2026-09-23 release hygiene untracked the agent-harness files. The files are no longer in the
trees, but the keys remain readable in each repository's public history. The keys must be
rotated, and the owner must decide whether to also rewrite those histories.

## Why

A key in a pushed commit stays valid for anyone who reads the history until it is rotated.
Untracking the file does not revoke anything.

## Current code reality

Keys found in pushed history (prefixes only; see each package's release report):

| Repository | Key prefix | Seat / hub |
|---|---|---|
| AbstractSkill | `agora_4c6023…` | local hub |
| AbstractUIC | `agora_d379ce…` | local hub |
| AbstractObserver | `agora_623c1b…` | local hub |
| AbstractFlow | `agora_24a80c…` | local hub |
| AbstractCore | `agora_28e598…` | local hub |
| abstractagent | `agora_9598fc…` | seat `agent`, `http://127.0.0.1:8765` |
| abstractassistant | `agora_e11738…` | seat `assistant`, `http://127.0.0.1:8765` |

Not pushed, local only (no history rewrite needed, but rotate if the credential is still live):

- AbstractContinuum `agora_5996…` (local backup branch and on disk).
- AbstractFramework root: the owner's local checkpoint commits tracked
  `plan_proof_out/fixture-gateway-data/` (a gateway `auth/bootstrap-admin-token`, `users.json`
  and a provider endpoint profile carrying a PAT-style `api_key`). They were squashed out before
  the 0.1.12 push and survive only in the local branch `backup/pre-release-history-root` and on
  disk.

Every affected repository now ignores `.agora/ .codex/ .claude/ .cursor/ .mcp.json CLAUDE.md
.abstractcode/`.

## Scope

### In scope

- Rotate each listed agora key on the hub (re-issue the seat key, update the local harness
  config that is now untracked).
- Decide per repository whether to rewrite history (`git filter-repo` + force-push, which
  breaks forks, tags and release provenance) or accept rotation only. Rotation is sufficient
  when the hub is loopback-only; record the decision here.
- Check the root fixture PAT: if it is a live provider credential, rotate it at the provider.
- Delete the local backup branches once no longer needed; never push them.

### Out of scope

- Changing the hub's key format or storage.

## Acceptance criteria

- [ ] Every key in the table is revoked on the hub (hub audit or seat listing as evidence).
- [ ] History-rewrite decision recorded per repository.
- [ ] Root fixture credential checked and rotated if live.
- [ ] A secret scan of each repository's full history (`git log -p | grep -E 'agora_[0-9a-f]{40,}'`)
      shows only revoked keys.

## Receipts

- Package release reports in `untracked/release-2026-09-23/` (local).
