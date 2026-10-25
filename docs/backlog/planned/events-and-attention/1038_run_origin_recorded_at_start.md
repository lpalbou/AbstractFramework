# 1038 — Run origin recorded at start

> Package: runtime, gateway
> Type: feature
> Created: 2026-10-25 12:50:00 +0200
> Priority: P1
> Labels: events-and-attention, runtime, gateway, origin

## Summary

Every run records who or what started it, once, in one shape: `_meta.origin = {kind: person|trigger|agent|system, actor: <principal id>, client: <interface>, ref: {automation_id?, occurrence_index?, event_id?, origin_run_id?}}`, stamped by the host at start; `StepRecord.actor_id` carries the principal instead of the constant `gateway`. Chat sessions (a person, manually) and triggered runs (any source) become distinguishable from stored data.

## Why

The operator asked for an explicit distinction between chat sessions, automations and trigger-started runs. Today four overlapping vocabularies exist (`run_attribution.py` SESSION_KINDS and ROLES, `history_bundle._classify_turn`, gateway `session_kinds.py`) and none records who started a run; `actor_id` is `"gateway"` for every person-started run although the principal is in hand.

## Scope

### In scope

- `_meta.origin` written by `/runs/start` (person), by the automation controller's `build_prepared` (trigger, with `automation_id`, `occurrence_index`, `event_id`), by SCHEDULE_RUN (agent, with `origin_run_id`), by bridges (system).
- `actor_id` = principal id on person-started runs and the occurrence runs.
- `run_attribution` reads origin; `history_bundle._classify_turn` folds onto `run_attribution` (its `scheduled` branch is legacy).
- Exposed on `GET /runs/{id}`, in session turns, and in the per-user event stream's `run.started` pointer.

### Out of scope

- A new session kind vocabulary (automation stays the durable binding; the occurrence is the trigger-started run).
- Copying the trigger envelope into every run (pointer to the controller ledger record only).

## Current code reality

- `abstractgateway/src/abstractgateway/run_attribution.py:32-33` derives kinds from inline `vars._meta` at index time.
- `abstractgateway/src/abstractgateway/routes/gateway.py:9297` stamps `actor_id="gateway"`; the principal is available at `:9127`; the scheduled wrapper at `:9668` does the same.
- `abstractruntime/.../automations/controller.py:600-608` builds the occurrence input (`_meta.automation_title`, `_meta.occurrence`); the envelope is recorded at `:741-742` as `automation.admitted.trigger_envelope`.

## Acceptance criteria

- [ ] A person-started run shows `_meta.origin.kind == "person"` with their principal id and `actor_id` equal to it.
- [ ] An occurrence shows `origin.kind == "trigger"` with `automation_id`, `occurrence_index`, `event_id`.
- [ ] Existing runs without origin still classify as before (no regression in `run_attribution` tests).
- [ ] The turn classifier has one source of truth (`run_attribution`).

## Testing

- `cd abstractruntime && python -m pytest tests -q -k 'controller or attribution'`
- `cd abstractgateway && python -m pytest tests -q -k 'attribution or runs_start'`

## References

- Round-2 finding 1 in the design note.
- [0993](../0993_one_ledger_replay_many_views.md)

## Receipts

- design note: `untracked/design/attention-triggers-replay-2026-10-25.md` (two adversarial rounds)
