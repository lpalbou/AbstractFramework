# 1151 — One UI component contract across AbstractTUI, AbstractUIC and a shared Swift package

> Package: AbstractUIC (the contract + web components), AbstractTUI (terminal), AbstractAssistant (iPhone `AssistantKit`, Watch; a new shared Swift package), AbstractAvatar (the first shared catalog)
> Type: architecture
> Created: 2026-11-08
> Priority: medium
> Labels: ui, shared-components, swift, avatar

## Operator ruling (2026-11-08 ~05:00)

Asked whether hiding the experimental avatars applies to the Apple Watch's hard-coded Swift picker (34 designs):
"create a backlog item to harmonize abstracttui, abstractuic and the swift package for shared UI components (if there
is one; if not, we must create one)."

## Current code reality (2026-11-08)

- **Web**: AbstractUIC (`ui-kit`, `panel-chat`) is the shared component set; apps consume it (ADR 0053 rule 4).
- **Terminal**: AbstractTUI has its own widgets (avatar, modal, chat) with the same words where they were ported by
  hand; it reads the AbstractAvatar core directly.
- **Apple**: the iPhone app has Swift packages `AssistantKit`, `AssistantPush` and the Watch has `AbstractGatewayClient`
  (networking); there is NO shared Swift UI package: the Watch's design picker is a hard-coded Swift list of 34 designs,
  its orbs are Swift originals (the AbstractAvatar `watch-*` designs are ports of them), and the avatar "ready" status
  decided tonight (7 designs) reaches neither app automatically.
- **Avatar catalog** is the first component with a machine-readable contract (`catalog.json`: keys, status, retired
  map, schema) that all three surfaces could read.

## Scope (to design first)

1. **A contract, not a port**: for each shared component (avatar picker/renderer, the model picker with reasoning + MTP
   rules, the permission card Deny / Allow / Allow All, the entity card, the working indicator, the chat composer), one
   machine-readable description of states, words and rules lives in AbstractUIC (JSON/TS source of truth, generated
   docs), and each surface implements it: web (kit), terminal (AbstractTUI), Apple (a new `AbstractUIKit` Swift package
   shared by iPhone and Watch, replacing the hard-coded lists).
2. **Avatar first**: the three surfaces read the same `catalog.json` (status, retired map, default) — the Watch package
   through the AbstractAvatar crate's C ABI or a generated Swift list with a test that fails when the catalog changes.
3. **Conformance tests per surface** against the contract (words, offered choices, defaults), run in each repo's CI.
4. **Not in scope**: pixel parity between surfaces; re-drawing the Watch's Swift orbs in the core (avatar backlog 0001).

## Acceptance (when scheduled)

- [ ] The Watch and iPhone offer exactly the avatar designs the catalog marks ready; a catalog change fails their test.
- [ ] One source of words for the permission card and the model picker across web, terminal and Apple.
- [ ] A new shared component is added to the contract first, then to each surface.
