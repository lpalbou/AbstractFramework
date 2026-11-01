# 1096 — Shared rounded multiline composer as the default chat composer in every host

> Package: abstractuic, abstractcode, abstractassistant, abstractentity, abstractflow, abstractgateway
> Type: task
> Created: 2026-11-01
> Status: Completed
> Completed: 2026-11-01
> Priority: P2
> Labels: conversation, composer, ui-kit, release-order
> Work-item id: abstractframework-1096
> Owner: framework

## Summary

The rounded multiline composer introduced for Avatar mode (1088 follow-up, `ChatComposer
variant="compact"`) becomes the ONE default composer of AbstractUIC panel-chat and of every
chat surface that consumes it: Code web, Assistant web, Entity (chat drawer and meet console),
Flow (authoring assistant, code assistant, run waiting input, follow-up), the Gateway console
(sandbox, docs assistant, entity chat) and the docs assistant drawer. The former flat layout
survives only as an explicit `variant="legacy"`. Hand-written textareas in hosts are replaced
by the shared component so keyboard, IME, attachment, busy/stop and accessibility rules live
once.

## Why

Operator, 2026-11-01, on the Code Avatar screenshot: "i want this to become the new DEFAULT
design for every chat in abstractuic and wherever it is used (docs assistant, regular chat,
etc). use an adversarial subagent for review and completeness. ensure clean, simple, efficient
and robust abstraction, implementation and integration." The Codex session that started the
work (`codex-session-01a191a0…`) was cut off mid-task with uncommitted edits in five repos; the
2026-11-01 review (`untracked/review-compact-composer-default-2026-11-01.md`) found Code, Flow
and the Gateway console no longer compiling or initialising against that tree.

## Current code reality (2026-11-01, before this item)

- panel-chat `chat_composer.tsx`: `variant?: "default" | "compact"`, compact opt-in; Attach
  button rendered by `WorkflowChat` and `DocsAssistantPanel` separately; Stop/cancel in the
  left `actions` slot.
- Code/Assistant/Entity vendor panel-chat as source copies (`scripts/sync_conversation.mjs`);
  their `--check` pins the copy to its own manifest and does not notice UIC moving ahead.
- Flow consumes `@abstractframework/panel-chat` from npm (`^0.5.0` in the lock).
- Gateway console: `console_islands.py` is GENERATED from the ui-kit islands bundle; the
  entity chat used its own `<textarea>` + Send button and keydown handler.
- Entity `meet_console.tsx` keeps a hand-written `mc_composer` textarea.

## Scope

### In scope

- panel-chat 0.7.0: `ChatComposerVariant = "compact" | "legacy"`, compact when omitted;
  composer-owned Attach (`onAttach`, `attachLabel`, `attachDisabled`, `attachPending`);
  `trailingActions` slot (right of the field, beside Send) and `WorkflowChat
  composerTrailingActions`; `submitKey: "enter" | "mod-enter"`; `canSubmit`; `textareaId`;
  `ariaDescribedBy`; fallback auto-grow refactor. Check scripts updated so a removed behaviour
  fails them.
- ui-kit 0.9.11: `mountChatComposer` island for plain-HTML hosts; sandbox mic in the trailing slot.
- Code web: re-vendor; VoiceTools in the trailing slot; no `composerVariant` branching.
- Assistant web: re-vendor; chat-mode mic in the trailing slot; host CSS styles the compact
  composer once.
- Entity: re-vendor; `meet_console.tsx` composer replaced by the shared component; dead CSS removed.
- Flow: the three components on the shared composer; `package.json` on `^0.7.0`; orphaned CSS removed.
- Gateway: entity chat on the composer island; `console_islands.py` re-synced to kit 0.9.11;
  the drift pin green; changelog fragment.
- Per host: tsc, unit suites, built-browser checks at 1280×800 and 390×844 (44 px targets,
  Attach/mic/Send/Stop present once).

### Out of scope

- Publishing panel-chat 0.7.0 / ui-kit 0.9.11 to npm and updating Flow's lock: a separate
  operator go (per-release rule). Until then Flow is verified against a locally packed tarball.
- The Avatar subtitle redesign (rolling realtime captions, Markdown rendering, evidence
  bubbles): proposed 1097.
- Any change to approval/permission controls or task forms, which keep their own inputs.

## Dependencies

- panel-chat 0.7.0 built locally (done 2026-11-01); hosts re-vendor from the local checkout.
- Flow's npm resolution needs the publish (out of scope) before its lock can move.

## Acceptance criteria

- [x] panel-chat: build, strict `tsc`, all `scripts/check_*.mjs` and the compact browser check pass.
- [x] ui-kit: islands `tsc`, `check_islands`, `check_sandbox_chat` pass; bundle contains `mountChatComposer`.
- [x] Code: `sync --check`, `tsc`, build, 502 vitest, avatar/approval/voice/compact-settings browser specs pass; phone + desktop screenshots.
- [x] Assistant: `tsc`, build, 63 vitest, `test:experience`; `test:layout` has 52 pre-existing failures unrelated to the composer (see residuals).
- [x] Entity: `tsc`, build, 601 vitest, `avatar.e2e` and the new `e2e:meet`; old→new control map recorded in the lane report.
- [x] Flow: `tsc`, lint, 1318 vitest, build against packed 0.7.0; authoring, code-assistant, waiting, Continue and Follow Up boxes screenshot-checked.
- [x] Gateway: `console_islands_sync` and `console_theme_sync` run; 39 console tests pass (drift pins, responsive, offline, entity composer incl. a real-bundle assertion and the close-during-send case); `sandbox_chat.mjs` and an entity Talk check pass against a disposable gateway with no JS error.
- [x] Independent adversarial review: UIC diff (approve with fixes, all applied) and final cross-repo review (approve with fixes, all applied except the two publish-dependent blockers below).
- [x] Docs/changelogs updated per repo via coredoc (UIC README/api/console-islands/llms/llms-full/CHANGELOG; CHANGELOG entries in Code, Assistant, Entity, Flow, Note, Continuum, Observer; gateway changelog fragment; Entity CONTRIBUTING); versions bumped (panel-chat 0.7.0, ui-kit 0.9.11, UIC lockfile).
- [x] Commits recorded below; no production restart or publish.

## Receipts

- Review of the inherited state: `untracked/review-compact-composer-default-2026-11-01.md`.

## Completion report (2026-11-01)

Also in scope, found by the final review: `abstractnote` (web Capture), `abstractcontinuum`
(team page, advisor drawer) and `abstractobserver` (run chat, automation discussion) carried
uncommitted edits from the same Codex session using 0.7.0 props; they were finished and verified
against the packed tarball (Note 181 tests, Continuum 538, Observer 692; tsc and build green).

| Repository | Commit | State |
|---|---|---|
| abstractuic | `0fa614a` | panel-chat 0.7.0, ui-kit 0.9.11, docs, checks |
| abstractgateway | `fc44a8ae` | console composer island, islands/themes re-synced |
| abstractcode | `2731cd2` | re-vendored, trailing voice tools, legacy CSS removed |
| abstractassistant | `e409a79` | re-vendored chat + docs drawer, host CSS reduced |
| abstractentity | `eb0dc4e` | drawer + meet console, `e2e:meet` |
| abstractflow | uncommitted | `^0.7.0`; lock still 0.5.0 until publish (`npm ci` would fail) |
| abstractnote, abstractcontinuum, abstractobserver | uncommitted | `^0.7.0` / ui-kit `^0.9.8`; relock after publish |

Decisions taken during the work: `ChatComposerVariant = "compact" | "legacy"` (`"default"` removed,
`"compact"` an alias of the default); the trailing slot is the one placement for voice controls
(the `.af-voice-mic` auto-margin hack is gone); Flow's Follow Up keeps Ctrl/Cmd+Enter because it
starts a run, the waiting input and Continue send on Enter; Entity's drawer Attach is the
composer's own; the small-avatar-while-request rule applies at every viewport height (the kit's
only named height breakpoint is 500 px).

Remaining operator action: publish panel-chat 0.7.0 and ui-kit 0.9.11 (abstractuic tag), then
relock and commit Flow, Note, Continuum and Observer (`npm install --package-lock-only`, their
`check:lock`), and raise Entity's own `@abstractframework/panel-chat` pin (`^0.6.4`, used for the
`entity_view.tsx` docs drawer and CSS) to `^0.7.0`. No deployment was performed; the managed
apps and the live gateway still run the pre-task builds.

Residual follow-ups (not blockers), to triage into their repos' backlogs:
- Code e2e harness configures the gateway/app through `ABSTRACTCODE_E2E_*` environment variables;
  operator rule: settings are `--param` or config, never env (move to Playwright config/CLI args).
- Code: pre-existing failing e2e specs `archived`, `automation_tools`, sidebar "round 4",
  `workspace` (strict-mode duplicate text), unrelated to the composer.
- Assistant: `test:layout` has 52 pre-existing failures (example link under 44 px, Conversation/Avatar
  toggles at 31 px); `index.css` also imports panel_chat.css from the npm 0.6.4 package on top of the
  vendored CSS (duplicate load).
- All hosts: `sync_conversation.mjs --check` pins the vendored copy to its own manifest and cannot
  see UIC moving ahead; Assistant's `sync_docs_assistant.mjs --check-source` can, but `build` runs
  only `--check`.
- Gateway: `scripts/changelog.py check` still stops on the pre-existing malformed
  `changelog.d/0980-resources-dashboard.md`; a retried failed send adds a second "you" line.
- AbstractNote phone top bar: the account button is cut off at 390 px (pre-existing).
- UIC browser check measures ≥36 px on a 390 px viewport without touch emulation, so the 44 px
  coarse-pointer rule is only covered by SSR/CSS checks.
