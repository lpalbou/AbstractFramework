# 1039 — Trigger envelope in CloudEvents names with a structured event input

> Package: runtime
> Type: feature
> Created: 2026-10-25 12:50:00 +0200
> Priority: P1
> Labels: events-and-attention, runtime, triggers, cloudevents

## Summary

`TriggerEnvelope` adopts the CloudEvents 1.0 attribute names additively (`id`, `type` = `abstract.<source>.<version>`, `source` = the connection URI, `time`, `subject`, `data`, `datacontenttype`, `dataschema`) plus extensions (`bindingid`, `connectionid`, `correlationid`, `dedupekey`, `sequence`, `recordedtime`, `expirytime`, `traceparent`, `abstracttrust`), and the occurrence run receives the envelope as structured input (`input_data["event"]`) beside the prompt header. Existing keys keep being emitted for one release.

## Why

The operator wants triggers native to the framework with a clean interface on the source, the reason and useful metadata (series, occurrence). CloudEvents is the established envelope standard; today the envelope reaches the occurrence only as a prompt header, never as data a flow can read.

## Scope

### In scope

- Additive fields on `TriggerEnvelope` (`triggers/protocol.py`) and their population by `schedule@1/2`, `manual@1`, `email.received@1`, the new `webhook.received@1` and `feed.item@1`.
- `subject` per source (Message-ID, feed item id, webhook id), `dedupekey` mapped to `EventInbox.dedupe_key`, `sequence` = inbox seq, `abstracttrust` carrying `adapter_delivers_untrusted`.
- Series metadata for schedules: `data.series = {rule, occurrence, scheduled_at, next_at, coalesced}`.
- `build_prepared` adds `input_data["event"] = envelope` (CloudEvents form).

### Out of scope

- Changing the prompt header format.
- Removing the old keys in this release.

## Current code reality

- `abstractruntime/src/abstractruntime/triggers/protocol.py:44-54`: `TriggerEnvelope{event_id, source_id, source_version, fired_at, payload, binding_id}`.
- `triggers/schedule.py`: coalesced ticks carry `{tick, scheduled_at, coalesced?}` in payload.
- `automations/controller.py:253-262`: envelope rendered as a prompt prefix only; `:547` `adapter_delivers_untrusted`.

## Acceptance criteria

- [ ] An occurrence's `input_data.event` validates against a CloudEvents 1.0 JSON schema and carries the extensions above.
- [ ] Every built-in source populates `subject` and `dedupekey`; schedule populates `data.series`.
- [ ] Old keys still present; a test asserts both forms for one release.

## Testing

- `cd abstractruntime && python -m pytest tests -q -k 'trigger or envelope or schedule'`

## References

- Round-2 finding 4.
- CloudEvents 1.0 spec, Standard Webhooks spec (signing).

## Receipts

- design note: `untracked/design/attention-triggers-replay-2026-10-25.md` (two adversarial rounds)
