# 0940 — Observer: the Automate form's Advanced inputs refuse server-owned keys visibly (`_meta`, read-only keys, non-allowlisted `_runtime`)

- **Status:** planned
- **Created:** 2026-09-27
- **Area:** abstractobserver (`src/ui/automations.ts`, `src/ui/automate_form.tsx`)
- **Parent:** [0928](../completed/0928_automations_v1_runtime_native_scheduled_and_triggered_tasks.md)
- **Source:** review 54 O-2 (`untracked/missions-2026-09-25/REVIEW/54-observer-automations.md`); gateway side: review 52 R52-1

## Summary
The Observer's Automate form has an Advanced JSON field for extra target inputs. `clean_input_data`
(`src/ui/automations.ts:117`) passes through, as typed:
- `_meta`;
- `workspace_read_only`;
- every `_runtime` key.

Before R52-1, a pasted `_runtime.control = {paused: true}` froze that automation and stopped the others in the gateway.
R52-1 makes the gateway keep only an allowlist of client `_runtime` keys (`CLIENT_RUNTIME_KEYS` = `allowed_tools`,
`provider`, `model`, `thinking`, `speculation`, `stream`) and drop `_meta` and the read-only keys. That closes the harm.
What remains is a silent drop: the gateway logs a warning server-side, the automation is created without the keys the
user typed, and the Observer says nothing.

## Scope
### In scope
- The form refuses, before sending, any top-level `_`-prefixed key other than `_runtime`, and any `_runtime` key outside
  the gateway's allowlist. It names each refused key in the form's error. This follows the no-silent-degradation rule; it
  does not strip quietly the way `legacy_recreate_prefill` (`:453`) does.
- The allowlist is not hard-coded twice. Either the gateway advertises it (for example in
  `contracts.common.automations`), or the form reads the gateway's 422/refusal. Pick one with the gateway seat.
- A test: a pasted `_runtime.control` or `_meta` shows the refusal and sends nothing; an allowlisted `_runtime.model`
  goes through.

### Out of scope
- The gateway allowlist itself (review 52 R52-1, landing in the gateway fix set).

## Current code reality (2026-09-27)
- Observer tip `9685fe0`: `clean_input_data` at `src/ui/automations.ts:117`.
- Gateway working tree (R52-1, uncommitted at the time of writing): `automation_defaults.py` `CLIENT_RUNTIME_KEYS`,
  `SERVER_INPUT_KEYS` and `strip_server_owned_input` (returns the dropped paths and logs them).
- If the gateway later answers a create carrying dropped keys with 422 instead of dropping them, this item shrinks to
  surfacing that 422 in the form.

## Acceptance criteria
- [ ] No automation is created from the Observer with keys the user typed and the gateway silently dropped.
- [ ] The refusal names the key; the check goes RED when the filter is removed.
