# 1052 — A folder on this computer as a trigger (files as typed records)

> Package: runtime, gateway, flow
> Type: feature
> Created: 2026-10-25 21:25:00 +0200
> Priority: P1
> Labels: events-and-attention, triggers, files

## Summary

A trigger source `file.changed@1` that watches a folder on the machine the gateway runs on (a workspace, the runtime's artifacts folder, any folder the person names) and delivers the files that were created, changed or deleted since the last check as one occurrence with a typed list, the way `email.received` delivers `messages`. Flow gets a `File` type and `files` pins (On Flow Start of a triggered flow: `files`, `folder`, `event`), with Break File from a pin drop and ForEach over the list, and the deterministic nodes Read file, Write file and Move file already in the palette take a `File`.

## Why

Operator ask 2026-10-25: "triggers on file change/created, a connector to both the user runtime artifacts and to things like Google Drive, Dropbox". A local folder is the cheap, dependency-free half and covers the runtime's own artifacts; cloud drives are 1053.

## Shape

- Connection (console Triggers → New connection → "When a file changes in a folder"): folder path (picker with the workspaces and the artifacts folder proposed, free path allowed), include subfolders (on), patterns (optional, `*.pdf`), kinds (created / changed / deleted, all on), check every (default 30 s), when added: ignore what is there / also deliver the current files.
- Occurrence inputs: `files: [File]`, `folder: string`, `event`. `File = {id (path), name, path, folder, size, modified, kind: created|changed|deleted, type (mime guess), artifact (ref when the file is ≤ the artifact limit and the connection asks for content)}`.
- Watcher: snapshot (path, size, mtime, inode) per check, diff, `max_batch` like mail; no inotify/FSEvents dependency in v1 (polling is enough at 30 s and works on every OS); the gateway refuses folders under `<data dir>/auth`, the keychain-free secret stores and the builtin deny prefixes already used for workspaces.
- Same listening/pause rules and the same "used by" status as feeds; test-fire creates a temp file in a scratch folder.

## Acceptance criteria

- [ ] A file dropped into the watched folder appears in a triggered flow's `files` within one check interval, with name, size, modified and kind.
- [ ] Run as if triggered samples the current folder (last N files by modified).
- [ ] Deleted files arrive with kind deleted and no artifact.
- [ ] Denied folders are refused at creation with a plain reason.
- [ ] Flow: Break File, ForEach over files, Read file takes a File.

## References
- 1038–1048 (events and attention), 1050; `abstractruntime/triggers/feed.py` and `email_received.py` as the pattern; ADR-0040 for any shipped example flow (drafted by an agent, published by the operator).
