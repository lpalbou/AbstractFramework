# 1106 — Sessions and automation runs are told apart by one tag, reused in the tray menu and every list

> Package: AbstractGateway
> Type: task
> Created: 2026-11-03
> Priority: high
> Labels: sessions, automations, tray, clients

## Summary

The macOS menu-bar gateway console lists running automation occurrences under Conversations → Running as if they were conversations (operator screenshot 2026-11-03 02:37). The gateway marks automation-owned sessions/runs with a tag; the tray and every other list (Assistant desktop/web/iPhone/watch, Code web/terminal, Observer, web console, TUI console) must read that same tag, never names or text.

## Why

Operator 2026-11-03: "those are misclassified as sessions whereas they are automations … normally we have a clear tag to differentiate (regular) sessions and automations. make sure the tag is in place, working and REUSED properly in that systray gateway console, but also in other places if any". Rule (2026-09-27): never filter sessions by creating client; automation runs are distinguished by the tag only.

## Scope

### In scope

- Name the tag and where it is defined (ADR/backlog); verify it on live sessions read-only; fix the tray menu model; audit every list; tests red without the tag check; changelog fragments per repo.

### Out of scope

- Changing how automations create sessions.

## Acceptance criteria

- [ ] Tray: Conversations lists no automation session; Automations shows the running occurrence; each client list reads the tag (table in the item).

## Receipts

- W5 running 2026-11-03 03:20.
