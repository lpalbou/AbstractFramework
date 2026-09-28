# 0978 — Automation failures name the cause and the fix (expired provider credential example)

> Package: abstractgateway, abstractruntime, abstractobserver, abstractuic (ui-kit automation panel), abstractcode, abstractassistant
> Type: task
> Created: 2026-09-28
> Priority: high
> Labels: automations, errors, ux, providers, observer

## Summary

When an automation fails because of the model provider, the user must be told in one sentence what failed and what to do. Today they get a generic sentence and a run id and have to dig through the ledger.

Operator example (2026-09-28, Observer 0.1.14, gateway 0.6.x): two automations created from Observer ("do your daily research on AI consciousness/awareness", "investigate today's news", both every 12 hours) failed. The row, the occurrence card and the detail all said only:

> "#2 failed after 3 attempts" — "The agent stopped because the model provider rejected the request (HTTP 401). Full details are in the run ledger (run 5ddeea80-…)." — "2 provider call(s) have missing responses or errors."

The real cause: the API key of the **airelays** endpoint profile had expired. Nothing on the page named the endpoint profile, the provider, the model, or the fix (update the key in Providers). Finding it in Observer was slow.

## Why

- A 401/403 from a provider is not a transient failure: retrying it 3 times wastes calls and time, and the automation will keep firing and failing every 12 hours until someone notices.
- The same root cause failed two automations; each showed the same vague text separately.
- "2 provider call(s) have missing responses or errors" does not say which calls, which provider or what the error was.
- The detail shows two different run ids (the occurrence run and the ledger run) without saying which one holds the error.

## Current code reality (2026-09-28)

- Released today: gateway 0.7.0, Observer 0.2.0 (Edit, icons, brief feedback), ui-kit 0.1.15 automation panel. The operator was still on the previous versions; the new Observer and chat may improve parts of this (re-check first).
- Error text is produced by the runtime/agent failure summary and shown verbatim by the kit automation panel and Observer.

## Scope

### In scope

1. **Classify provider failures** at the runtime/gateway boundary: authentication (401/403, expired or invalid key), quota/billing (402/429 with quota), rate limit (429), model not found (404), server error (5xx), network/timeout. Auth, quota and model-not-found are **non-retryable**: fail at the first attempt.
2. **Name everything in the failure record**: endpoint profile name (e.g. `airelays`), provider family, model, HTTP status, the provider's own error message (redacted of secrets), and the call that failed.
3. **Say the fix** in plain words, per class: "The API key for endpoint profile 'airelays' was rejected (HTTP 401): it may have expired. Update it in Settings → Providers, then Run now." Link to the Providers screen in the web console (and the TUI equivalent).
4. **Automation state**: after a non-retryable provider failure, mark the automation as needing attention ("Needs your action: provider key rejected") instead of silently waiting for the next tick; optionally pause it (operator decision: pause vs keep schedule).
5. **One cause, one notice**: when several automations fail for the same endpoint profile, the list and the console show one grouped notice ("2 automations failed: the 'airelays' key was rejected").
6. **Observer / kit panel / Code / Assistant**: show the classified message first (card title), the raw details behind "Run details", and make clear which run id holds the failed call.
7. Replace "N provider call(s) have missing responses or errors" with a list naming each call's provider, model and error.

### Out of scope

- Automatic key refresh or rotation.
- Regex/NLP parsing of free-text error messages (operator rule): classify on HTTP status and structured provider error fields only.

## Acceptance criteria

- [ ] With an endpoint profile whose key is invalid, an automation run fails after ONE attempt and its card reads, in one sentence, which endpoint profile's key was rejected and how to fix it.
- [ ] The automation shows "needs your action" in Observer, Code (TUI + web), Assistant and the web console until the key is fixed or the automation is run successfully.
- [ ] Two automations on the same failing profile produce one grouped notice.
- [ ] No secret appears in any message or log.

## Validation

Hermetic: a fake OpenAI-compatible server returning 401/403/429/404/500 per case; an endpoint profile pointing at it; automations created through the gateway API and checked in Observer and the TUI. Tests red before the change.

## Receipts

- Operator report and screenshot, 2026-09-28 15:23 (Observer Automations page).
