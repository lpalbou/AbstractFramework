# 0931 — Automations v3: packaged connectors (file, email, build, journals), calendar scheduling, automatic summaries, constrained fetching

- **Status:** proposed
- **Created:** 2026-09-26
- **Area:** abstractruntime (trigger sources as plugins), abstractgateway (email bridge as a source), abstractcode (build events), apps
- **Design:** untracked/design/automations-PLAN.md §5 (v3) and the "Growing context" limits discussed in untracked/design/astra/DIALOGUE.md

## Summary
Candidates after 0929: trigger-source plugins shipped by their owning packages through `abstractruntime.trigger_sources` (file changed;
email received via the gateway's email bridge; program built from AbstractCode; search/journal feeds), richer calendar scheduling (cron,
time zones, weekday rules; today `every` is a fixed interval and "daily at 8" is `start_at` + `1d`, which drifts across DST), an automatic
rolling-summary turn for growing mode (`context.growing.summary`, reserved in v1's schema), and a GET-only constrained `fetch_url` for
discussions if the operator wants a restricted discussion profile (in v1 discussions have the target's normal tools).

## Not decided
Which connector first; whether summaries are controller-owned or stay target-owned (v1: target-owned rolling note).

## Related
0928, 0929, 0930.
