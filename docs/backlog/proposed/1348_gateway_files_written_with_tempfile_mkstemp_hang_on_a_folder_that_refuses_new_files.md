# 1348 — Gateway files written with tempfile.mkstemp hang on a folder that refuses new files

> Package: abstractgateway (json_store.py and the modules listed below)
> Type: bug
> Created: 2026-11-25
> Priority: normal
> Labels: robustness, windows, storage, atomic-writes, gateway

## Summary

On Windows, `tempfile.mkstemp` retries a create refused with `PermissionError` up to `TMP_MAX` times
(2,147,483,647) while the folder exists, so a write into a folder that refuses new files (a read-only folder,
Windows Controlled Folder Access, an access-list deny) spins instead of failing. AbstractGateway 0.24.0 moved the
three session stores (archive, titles, kinds) onto `src/abstractgateway/json_store.py`, whose temp file is
created exclusively in ONE attempt with bounded retries and locks, and that fixed the hang of archiving and of
an account's first conversation list. About twenty other modules still write through `mkstemp` and keep the hang.
This item moves each atomic JSON or text write onto the shared primitive.

## Why

A hang is worse than an error: the request never answers, a worker thread is lost, and on the event loop the
whole gateway stops. The archive hang was a user-visible defect of released versions (AbstractGateway 0.24.0
CHANGELOG, "Fixed"); the same pattern remains in account, mail, push, entity, workflow and MCP settings.

## Current code reality (audited 2026-11-25, abstractgateway `origin/feat/session-title` 1532e978; Python 3.12)

- CPython `tempfile._mkstemp_inner`: on `PermissionError`, `if _os.name == 'nt' and _os.path.isdir(dir) and seq
  < TMP_MAX - 1: continue`; `os.TMP_MAX` is 2147483647 on Windows.
- `src/abstractgateway/json_store.py:1-19`: the shared store (cached reads, one writer per file and a
  `<file>.lock` across processes within `LOCK_WAIT_S` = 5 s, one exclusive temp file per write, bounded retries of
  a sharing violation, orphan temp files removed). Used by `session_archive.py`, `session_titles.py` and
  `session_kinds.py`.
- `git grep -n mkstemp -- src/abstractgateway` lists 20 modules (21 call sites):
  - `admin_accounts.py:115`, `automation_attention.py:99`, `automation_pause_reasons.py:49`,
    `core_endpoint.py:164`, `entity_appearance.py:65`, `entity_skills.py:169`, `entity_voice.py:103`,
    `gateway_pointer.py:95`, `mail/accounts.py:114`, `mcp_registry.py:195`, `model_host_http.py:87`,
    `push/settings.py:197`, `routes/entities.py:6577`, `self_update.py:908`, `session_identity.py:81`,
    `session_workspaces.py:64`, `workflow_deprecations.py:61`, `workflow_governance.py:57`: write a temp file
    next to the target, then replace it (atomic JSON or text writes).
  - `routes/gateway.py:7937` (a `.flow` upload staged in a temp folder) and `workflow_catalog.py:501` (a
    catalog upload staged in the bundle folder): staging files, not replace-in-place documents.
- The model test: `tests/test_session_titles.py:489`
  `test_a_folder_that_refuses_new_files_is_an_immediate_error_not_a_hang` (the store's folder refuses new
  files after a first successful write; the call must answer 500 at once).

## Scope

### In scope

- Move each atomic JSON or text write listed above onto `json_store.py` (or a small shared `atomic_write`
  extracted from it): one exclusive temp-file attempt, bounded retries of a sharing violation, the target
  replaced atomically, errors naming the file relative to its data folder.
- For the two staging uses, create the temp file with a single exclusive attempt as well (or check the folder
  can take a new file first), so a refused folder is an immediate error.
- Where a write runs on the event loop, move it off the loop as the session stores do.
- One parametrised test, modelled on the write-refused-folder test, over every migrated writer: the folder
  refuses new files, the call fails at once with its error, the existing file is unchanged.
- A guard test: `mkstemp` does not appear in `src/abstractgateway` outside the shared primitive.

### Out of scope

- The search's fuzzy pass does not reach stored conversation titles: a title is matched by whole words and
  substrings only (`routes/conversation_search.py:55-60` `_holds`; title hits carry `"fuzzy": False`, `:78`).
  Small, same area (backlog 1343); file it as its own item when it is picked up.
- Changing what any of these files contain.

## Acceptance criteria

- [ ] `git grep -n mkstemp -- src/abstractgateway` finds nothing outside the shared primitive (guard test).
- [ ] For each migrated writer, a folder that refuses new files makes the call fail within a second with a
      clear error, and the previous file is intact.
- [ ] Two gateway processes writing the same document lose no change (as `json_store.py` guarantees today).
- [ ] No migrated write runs on the event loop.

## Testing

- `python -m pytest tests/test_session_titles.py tests/test_session_archive.py tests/test_atomic_writes_refused_folder.py -q` (abstractgateway; the last file is new)
