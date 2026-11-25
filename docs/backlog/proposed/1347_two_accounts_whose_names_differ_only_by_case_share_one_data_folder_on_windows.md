# 1347 — Two accounts whose names differ only by letter case share one data folder on Windows

> Package: abstractgateway (security/principal.py, users.py, service.py)
> Type: bug
> Created: 2026-11-25
> Priority: normal
> Labels: security, accounts, windows, isolation, gateway

## Summary

On Windows (NTFS is case-insensitive), the accounts `alice` and `ALICE` are two accounts of the gateway but one
folder on disk, `<data dir>\users\<tenant>\alice`. Each lists, renames and archives the other's conversations,
because the per-account session stores and run data live in that folder. The account name is never folded to
one case: not when the folder name is built, and not when a duplicate is checked. Only an admin can create such
a pair. Found on 2026-11-25 by the adversarial review of the session-title route (backlog 1343); pre-existing.

## Why

Account isolation is the gateway's first security property (`docs/security.md`, "Tenant and user isolation").
An admin who creates `Alice` next to an existing `alice` by mistake gives both people each other's conversations
and files on Windows, and on macOS's default case-insensitive volumes too, with no warning.

## Current code reality (audited 2026-11-25, abstractgateway `origin/feat/session-title` 1532e978)

- `src/abstractgateway/security/principal.py:58-64` `safe_principal_component`: strips, replaces characters
  outside `[A-Za-z0-9_.@-]` (`_SAFE_COMPONENT_RE`, `:9`) and keeps the case; no case folding.
- `src/abstractgateway/service.py:527-533` `_config_for_principal`: the account's folder is
  `base.data_dir / "users" / tenant / runtime_id`, both from `safe_principal_component`, so `alice` and `ALICE`
  are different strings naming the same NTFS folder.
- `src/abstractgateway/users.py:296-297` `key` is `f"{tenant_id}:{user_id}"`, case-sensitive; the duplicate
  check on create is `if rec.key in records` (`:666-667`); the runtime-folder check compares
  `(rec.runtime_id or rec.user_id) == runtime0` (`:579`, and `:840` on update), case-sensitive.

## Scope

### In scope

- Refuse, at create and rename of an account, a user id or runtime id that equals an existing one when both
  are case-folded (`str.casefold()`), on every OS (the data may move between machines), with a sentence naming
  the existing account.
- A startup check that reports existing pairs that already share a folder (names only, no merge), so an admin
  can resolve them.
- Tests: create `alice` then `ALICE` is refused; a runtime id differing only by case is refused; the startup
  check lists a pair written directly into `users.json`.

### Out of scope

- Renaming or merging existing folders automatically.
- Case-folding display names or emails.

## Acceptance criteria

- [ ] Creating `ALICE` while `alice` exists in the same tenant answers an error naming `alice`; nothing is
      written.
- [ ] Updating an account's runtime id to one that equals another account's when case-folded is refused.
- [ ] A gateway whose `users.json` already holds such a pair says so at startup and in the console's accounts
      page, naming both accounts.
- [ ] Two accounts with different names still get different folders (no regression).

## Testing

- `python -m pytest tests/test_gateway_admin_users_kind_and_entity_guards.py tests/test_account_names_case_folded.py -q` (abstractgateway; the second file is new)
