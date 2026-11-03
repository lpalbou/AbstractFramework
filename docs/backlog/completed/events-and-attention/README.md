# Events and attention track

## Status
Completed 2026-10-25 (all eleven items built, tested, deployed locally, documented; nothing published). Completion reports at the end of each item. Built in parallel lanes from the operator's 2026-10-25 request; two adversarial
architecture rounds recorded in `untracked/design/attention-triggers-replay-2026-10-25.md`.

## Purpose
Let anything (a time, an email, a feed item, an external webhook, a run ending) start work, and reach the
person on whatever they carry, with one explainable record. Triggers are native to the runtime (sources,
connections, CloudEvents-shaped envelopes); the gateway owns connections, the per-user event stream and
delivery; Flow designs what runs on an event; the apps consume one stream.

## Decisions carried
- One `origin` on every run; automations are the durable binding, the occurrence is the trigger-started run (1038).
- The ledger is the run truth; the per-user stream holds only what is not a step (1046).
- Sources are types; connections are per-user instances (1040/1041).
- A wake is a one-shot automation bound to the caller's session; the new run is a turn in the same session (1045).
- Not in v0: a bus beside the ledger, the session index and reducer corpus (0993), the admission queue (0991), APNs (1049), WebSub, CalDAV, geofences.

## Items
- [1038](1038_run_origin_recorded_at_start.md) run origin (runtime, gateway)
- [1039](1039_trigger_envelope_in_cloudevents_names_with_a_structured_event_input.md) CloudEvents envelope + `input_data.event` (runtime)
- [1040](1040_trigger_connections_per_user_instances_of_a_source.md) trigger connections (runtime)
- [1041](1041_connections_api_and_the_console_triggers_page.md) connections API + console page (gateway)
- [1042](1042_webhook_source_with_signed_ingress.md) webhook source + signed ingress (gateway, runtime)
- [1043](1043_feed_source_rss_and_atom_poller.md) feed source (runtime)
- [1044](1044_several_mailboxes_per_user_read_only_at_minimum.md) N mailboxes per user (core, gateway, runtime)
- [1045](1045_schedule_run_effect_and_the_schedule_run_tool.md) SCHEDULE_RUN + `schedule_run` (runtime, agent)
- [1046](1046_per_user_event_stream_with_catch_up_and_sse.md) per-user event stream + cap fix (gateway)
- [1047](1047_event_consumers_in_the_apps_and_the_flow_trigger_interface.md) app consumers + Flow interface
- [1048](1048_end_to_end_examples_tests_and_documentation_for_events_and_attention.md) E2E examples + coredoc
- proposed: [1049](../../planned/1049_apple_push_relay_for_watch_and_phone.md) Apple push relay
- proposed: [1050](../../proposed/1050_events_and_attention_follow_ups.md) follow-ups named by the lanes
