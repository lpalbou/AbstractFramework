# 1053 — Cloud drive triggers (Google Drive first, Dropbox later)

> Package: gateway, runtime
> Type: feature
> Created: 2026-10-25 21:25:00 +0200
> Priority: P2
> Labels: events-and-attention, triggers, files, oauth

## Summary

The same `files` occurrence as 1052 from a cloud drive: Google Drive through the Google sign-in client the gateway already needs for Gmail (one more scope, `drive.readonly`, the Drive changes API with a page token per connection, so no polling of folders); Dropbox later through its own app registration (`/files/list_folder/longpoll` + cursor). Files arrive as `File` records with `artifact` filled only when the connection asks for content and the size is under the artifact limit.

## Why

Operator ask 2026-10-25. Depends on the Google OAuth client being registered on the gateway (1050, operator decision) and on 1052 for the `File` type and the Flow nodes.

## Non-goals
- Writing to the drive from a flow (a later verb set like the mail verbs).
- OneDrive, iCloud Drive.

## References
- 1052, 1050 (Google OAuth client), `abstractgateway/mail/accounts.py` (the OAuth flow to reuse).
