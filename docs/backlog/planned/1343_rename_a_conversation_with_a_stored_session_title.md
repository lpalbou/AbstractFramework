# 1343 — Rename a conversation: a stored session title on the gateway, editable from the sidebar

> Package: abstractgateway (session title route + `/runs` field), abstractuic (ui-kit SessionCard rename slot), abstractcode (web, then TUI)
> Type: feature
> Created: 2026-11-24
> Priority: normal
> Labels: sessions, conversations, titles, rename, sidebar, web, gateway

## Summary

Let a person rename a conversation. Today a conversation has no name of its own: every client shows its
first message. This item adds the smallest durable piece: a per-session title the owner sets through the
gateway (stored beside the archive mark, served on every `/runs` row), a rename affordance on the shared
`SessionCard`, and the AbstractCode web sidebar wiring (Enter saves, Escape cancels, empty restores the
automatic title). Every client that reads `/runs` can then show the same name.

## Why

Operator, 2026-11-24: "is there a clean solution so that a user could rename the name of a session?
if there is a clean and simple way to do it, then do it. if it's too complex or would require to release
more packages, then just create a backlog item."

It cannot be done in the web app alone: the released gateway (0.23.0) stores and serves no session title,
and the sidebar row is the shared ui-kit card, which has no edit slot. A web-only rename would be a local
label (what AbstractAssistant does, "on this device"), lost on other devices and clients, so it is not the
clean solution.

## Current code reality (audited 2026-11-24, gateway 0.23.0 installed and live, sibling `main` checkouts)

### abstractgateway

- No route sets a session title or label. The live 0.23.0 OpenAPI lists, for sessions, only `archive`,
  `unarchive`, `mentions`, `prompt_cache/*`, `tool-policy` and `workspaces` writes; no path matches
  title / label / rename.
- `GET /runs` (`src/abstractgateway/routes/gateway.py:10393`) rows carry no title: the live row keys are
  `actor_id, automation_id, created_at, current_node, error, is_draft, is_scheduled, kind, legacy, limits,
  notices, occurrence_index, parent_run_id, pause_reason, paused, paused_at, repeat_of, resumed_at, role,
  run_id, run_lifecycle, schedule, session_id, session_kind, status, updated_at, waiting, workflow_id,
  workspace_root`. Archived rows are marked at `gateway.py:10851`; `session_totals` is added at
  `gateway.py:10867-10869` (the page-level per-session map a `session_titles` map would sit beside).
- The closest precedent is the archive mark: `src/abstractgateway/session_archive.py:1-17` (a per-plane
  JSON file `<data_dir>/session_archive.json` with `sessions` + `history`, atomic writes, unreadable =
  error) and `src/abstractgateway/routes/session_archive.py:67-133` (owner-or-admin, 404
  `session_not_found` via `session_exists`, audited `session.archived`). Tests:
  `tests/test_session_archive.py`.
- `title` in `gateway.py:12799-12850` is the Observer's saved chat-thread artifact
  (`POST /runs/{run_id}/chat_threads`), not a session title. Backlog
  `docs/backlog/proposed/0937_session_titles_written_by_the_model.md` assumes "the session's `title`
  tag"; no such tag exists for conversations on 0.23.0 (0937 depends on this item).
- `routes/account_preferences.py:188-199` is a fixed-schema preference document (default workflow per app,
  time zone), not a per-session store.

### abstractuic (ui-kit, vendored into the web app)

- `ui-kit/src/session_card.tsx:6-23` `SessionCardProps` has `title`, `onOpen`, `onArchive`, no rename.
- `ui-kit/src/compact_activity_card.tsx:25-34`: the title is a `<span>` inside the single open
  `<button>`, the only hover action is the archive button. An inline input cannot be placed there by the
  host without a kit change (an input inside a button is invalid HTML).
- The web app vendors it: `abstractcode/web/scripts/sync_sessions.mjs:16` runs
  `abstractuic/ui-kit/scripts/export_session_cards.mjs` into `web/src/vendor/abstractsessions/`
  (checked by `web/scripts/check_vendor_sources.mjs`); `web/src/vendor/abstractsessions/session_card.d.ts`
  matches the props above.

### abstractcode web

- `web/src/workspace/sidebar_cards.tsx:44-50` `conversationTitle()` = `item.prompt` else
  "Untitled conversation"; its doc comment states "The gateway serves no session title, so the opening
  message is the name."
- `web/src/workspace/catalog.ts:655-666` `promptFrom()` and `:731-738`: `prompt` is derived client-side
  from the oldest turn's `input_data` (`prompt`/`request`/`task`/...). There is no stored field to write.
- `web/src/workspace/sidebar_cards.tsx:147-167` `ConversationCard` renders the kit `SessionCard`;
  `:57-60` `searchConversations()` searches `prompt` + session id; `web/src/workspace/app.tsx:1648`,
  `:2112` use them; `web/src/workspace/archived_conversations.tsx:115` titles archived rows the same way.

### abstractcode TUI

- `tui/src/conversations.rs:4,33-45`: the card title is the opening prompt, else
  `Untitled conversation`; no rename.

### abstractassistant (existing rename, local only)

- `abstractassistant/ui/session_switcher.py:12,453-500`: in-place rename with a `QLineEdit`
  (Enter commits), "a local label".
- `abstractassistant/core/llm_manager.py:517,536,747-751`: title = local label, else the gateway's opening
  prompt; `rename_session` writes `session_cache.set_label` only. `docs/faq.md:97`: "The pencil renames a
  session on this device." Assistant backlog `0853` (`:124-128`) planned the local override as a stopgap.

### abstractobserver

- No rename or session title.

## Smallest design

1. **Gateway** (`session_titles.py` + route, modelled on `session_archive.py`):
   `PUT /api/gateway/sessions/{session_id}/title` with `{"title": "..."}` (trimmed, single line, capped
   e.g. at 120 chars); an empty or missing title clears it (back to the automatic name). Owner or admin,
   404 `session_not_found` like archive, answers `{session_id, title, changed}`, audited
   `session.titled`. Stored per plane in `<data_dir>/session_titles.json`
   (`{"schema": "gateway_session_titles_v1", "sessions": {sid: {title, set_at, set_by}}}`), unreadable =
   500, never "no titles". `GET /runs` adds `session_title` on each row of a titled session (or a
   page-level `session_titles` map next to `session_totals`); keyword search
   (`routes/conversation_search.py`) also matches it. Additive only: older clients ignore the field.
2. **ui-kit**: `SessionCard` / `CompactActivityCard` gain an optional `onRename?: (title: string) => void`
   (plus `renameTitle`). When set: a "Rename" hover action next to archive, and F2 / double-click on the
   row, swap the open button's title for an `<input>` outside the button (Enter saves, Escape or blur
   cancels, empty saves "" = restore automatic title); focus returns to the open button. Re-export through
   `export_session_cards.mjs`.
3. **AbstractCode web**: `catalog.ts` reads `session_title` into `SessionSummary.title`;
   `conversationTitle()` = `title` else `prompt` else "Untitled conversation";
   `searchConversations()` also searches `title`; `ConversationCard` passes `onRename`, which `PUT`s and
   optimistically updates the catalog (error shown on the row like the archive error); the chat header and
   archived rows use the same `conversationTitle()`. Re-sync the vendored kit.
4. Follow-ups (separate items, not required here): TUI rename, Assistant moving its local label to the
   gateway title (migrating existing labels), and 0937 writing model titles only when no person-set title
   exists.

Releases: abstractgateway (minor, new route + field), abstractuic ui-kit (minor, new optional prop),
@abstractframework/code (web) after both. The web change must degrade on an older gateway: no
`session_title` field and a 404/405 on `PUT .../title` hides the rename action (feature-detect via the
OpenAPI / discovery the app already reads, or the first 404 disables it with a plain message).

## Scope

### In scope

- Gateway: stored per-session title, `PUT /sessions/{session_id}/title`, served on `/runs`, searched,
  audited, tests.
- ui-kit: optional rename affordance on `SessionCard`, keyboard accessible, tests.
- AbstractCode web: show, search and edit the stored title in the Conversations sidebar (and the archived
  list / chat header show it); docs `docs/web.md`, CHANGELOG, `llms-full.txt`.

### Out of scope

- Model-generated titles (backlog 0937).
- TUI, Assistant, Observer and Apple clients adopting the title (follow-ups; they keep working unchanged).
- Renaming automations (they already have a stored title).
- Any change to runs, ledgers or the first message.

## Acceptance criteria

- [ ] `PUT /api/gateway/sessions/{sid}/title {"title": "Snake game"}` by the owner answers
      `{session_id, title: "Snake game", changed: true}`; a repeat answers `changed: false`.
- [ ] Afterwards `GET /runs?root_only=true` carries `session_title: "Snake game"` for that session's rows
      (or in `session_titles`), and the title survives a gateway restart.
- [ ] `{"title": ""}` (or whitespace) clears it; `/runs` then carries no title for the session.
- [ ] Another account's session, or an unknown id, answers 404 `session_not_found`; an over-long or
      multi-line title is trimmed/capped (or 422), never stored raw.
- [ ] An unreadable `session_titles.json` makes `/runs` and the route answer 500, not drop titles.
- [ ] Every change appends a `session.titled` audit line naming the session.
- [ ] ui-kit `SessionCard` with `onRename`: the Rename action and F2 open an input prefilled with the
      title; Enter calls `onRename(trimmed)`, Escape restores the title without a call, focus returns to
      the row; without `onRename` the card renders exactly as before.
- [ ] AbstractCode web: a renamed conversation shows its new name in the sidebar, search finds it by the
      new name, the name persists after reload and is the same in a second browser.
- [ ] AbstractCode web against a gateway without the route: no rename action is offered and nothing
      breaks.
- [ ] Clearing the name in the web app shows the first message again.

## Testing

- `python -m pytest tests/test_session_archive.py tests/test_session_titles.py -q` (abstractgateway; the
  new file covers set / repeat / clear / 404 / unreadable / `/runs` field / restart)
- `npx vitest run src/session_card.test.tsx` (abstractuic/ui-kit; a new test file for the rename slot)
- `npx vitest run src/workspace/sidebar_cards.test.tsx src/workspace/catalog.test.ts src/workspace/archive_conversation.test.tsx` and `npx tsc --noEmit` (abstractcode/web)
- Manual: a throwaway gateway from source on a scratch data dir and port, rename a conversation in the web
  app, reload, open it from a second browser profile, clear the name.
