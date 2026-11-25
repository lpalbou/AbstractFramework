# 1344 — The terminal client, the Assistant and the Observer show and set a conversation's stored name

> Package: abstractcode (tui), abstractassistant, abstractobserver
> Type: feature
> Created: 2026-11-25
> Priority: normal
> Labels: sessions, conversations, titles, rename, tui, assistant, observer

## Summary

AbstractGateway 0.24.0 stores a conversation's name (`PUT /api/gateway/sessions/{session_id}/title`) and
serves it as `session_title` on every `GET /api/gateway/runs` row of a renamed session and on the keyword
search's items (backlog 1343). Only AbstractCode web reads and sets it. AbstractCode's terminal client still
names a conversation by its opening prompt, the Assistant keeps a label of its own on the device, and the
Observer shows no name. A person who renames a conversation in the web app sees the old name in every other
client. This item makes each of them show the stored name and, where they offer a rename, set it on the
gateway.

## Why

Backlog 1343 put the name on the gateway so that it "follows the user" to every client; 1343 kept the other
clients out of scope ("they keep working unchanged"). Until they read `session_title`, the same conversation
has two names depending on where it is opened, and the Assistant's pencil ("renames a session on this
device") disagrees with the web app's rename.

## Current code reality (audited 2026-11-25; abstractcode `main` 118d077, abstractassistant `main` 0be6d3e, abstractobserver `main` 7f40218)

### abstractcode TUI

- `tui/src/conversations.rs:4`: "A card is its title (the opening prompt, else `Untitled conversation`)".
- `tui/src/conversations.rs:36-46` `card_title(label, _id)`: the first non-empty line of the opening prompt,
  else `UNTITLED` (`:34`, "Untitled conversation"). No `session_title` is read anywhere in `tui/`.
- `tui/src/conversations.rs:18-25` `matches_search(label, id, query)`: `"{label} {id}"` lower-cased contains
  the query, i.e. prompt + session id. Since web 0.16.4 the web also matches the stored name
  (`` `${item.title || ""} ${item.prompt || ""} ${item.sessionId}` `` in `web/src/workspace/sidebar_cards.tsx`);
  the TUI's wording test was adjusted on `feat/rename-conversation` (`tui/tests/r17w1_screens.rs`, commit
  fd31174) and says "this client does not read stored names yet".
- No rename action.

### abstractassistant

- `abstractassistant/core/llm_manager.py:517`: "Title = local label, else the gateway's opening prompt, else
  the cached transcript's"; `:536` builds the switcher row from `store.label(session_id)`.
- `abstractassistant/core/llm_manager.py:747-751` `rename_session`: "A LOCAL label for the session, shown
  instead of its opening prompt", written with `self._session_cache.set_label(sid, title)` only; nothing goes
  to the gateway.
- `docs/faq.md:96-97`: "The pencil renames a session on this device."

### abstractobserver

- No conversation name: `session_title` appears nowhere in `src/`. Its only rename is an automation's title
  (`src/ui/app.tsx:5183`, `on_rename_automation`), which is a different, already stored field.

## Scope

### In scope

- AbstractCode TUI: the card title is `session_title`, else the opening prompt, else "Untitled
  conversation"; search also matches `session_title` (the web's rule); a rename action (F2 on the focused
  card, as in the web) that `PUT`s the title, offered only when `capabilities.session_titles` is true; a
  `session_titles_error` on `/runs` shown once, as the web does.
- AbstractAssistant: show `session_title` first; the pencil sets the gateway title when the gateway
  advertises `capabilities.session_titles`, and keeps the local label only against an older gateway;
  existing local labels are offered for upload once (or migrated) without overwriting a name already
  stored on the gateway; `docs/faq.md` updated.
- AbstractObserver: show `session_title` wherever a conversation (session) is named; rename is optional.
- Each client's docs, changelog and tests; a root release that pins the new versions.

### Out of scope

- Model-written titles (backlog 0937).
- The Apple clients (their own item if they list conversations).
- Any change to the gateway route or the stored format.

## Acceptance criteria

- [ ] AbstractCode TUI: a conversation renamed in the web app shows its new name on its card after the next
      list refresh; searching for the new name finds it; clearing the name shows the opening prompt again.
- [ ] AbstractCode TUI against AbstractGateway 0.23.0 (no `capabilities.session_titles`): no rename is
      offered and cards are named as today.
- [ ] AbstractAssistant: a conversation renamed in the web app shows that name in the switcher; a rename
      from the Assistant is visible in AbstractCode web after a refresh; a local label made before the change
      is not lost and never overwrites a stored gateway name silently.
- [ ] AbstractObserver: a renamed conversation is shown with its stored name.
- [ ] Each client says once that names could not be loaded when `/runs` carries `session_titles_error`.

## Testing

- `cargo test --manifest-path tui/Cargo.toml conversations` (abstractcode; card title and search with and
  without `session_title`)
- `python -m pytest tests/basic/test_assistant_palette.py -q` (abstractassistant; session titles from the
  gateway, local label fallback)
- `npx vitest run` (abstractobserver; the session name on its cards)
