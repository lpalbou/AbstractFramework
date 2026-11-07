# 1135 — Make the difference between AbstractCode and AbstractAssistant clear

> Package: AbstractCode, AbstractAssistant, AbstractFramework (docs, site)
> Type: product / documentation (direction recorded, not scheduled)
> Created: 2026-11-07
> Priority: medium
> Labels: product-direction, docs, observability

## Operator note (2026-11-07)

"One of the issues I have is the difference between AbstractCode and AbstractAssistant. We will need to make that
clearer in the future, and in terms of functionalities / observabilities."

## Summary

Both apps are clients of the same gateway sessions (one session pool for all clients, operator ruling
2026-09-27), both have a web app, voice, an Avatar view and (soon) phone apps; AbstractCode also has a terminal
client. A person cannot tell from the apps or the site which one to use for what, nor what each shows about a run
(observability: tool calls, findings, approvals, ledger replay, workspace files).

## To do when scheduled

1. Write down, in one page shared by both READMEs and the site, what each app is for and for whom, from the
   code as it is: a feature/observability matrix (conversations, automations, tools and approvals, workspace and
   files, findings, replay, voice, avatar, devices: desktop, web, terminal, iPhone, Watch).
2. Decide with the operator where each app should differ (and where they should share kit components instead of
   diverging), and record it as an ADR if it becomes a rule.
3. Align the site (code.html, assistant.html, the home page) and both apps' first-run copy with that page.

## Related

1134 (talking to entities from both apps), feedback ruling "one session pool for all clients".
