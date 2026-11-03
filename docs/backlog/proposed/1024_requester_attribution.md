# 1024 — Requester attribution: every run says who asked for it, through what, on whose behalf

> Package: abstractruntime, abstractgateway, abstractobserver (then abstractcode, abstractassistant, abstractflow for the client hint, optional)
> Type: feature
> Created: 2026-10-15
> Priority: high
> Labels: governance, observability, identity, decision-gate, adversarial-review-required
> Track: governance (proposed; builds on 1019–1023)

## Summary

OPERATOR DECISION GATE (never assignable): seven questions below, asked 2026-10-14, unanswered.
No run on the gateway says who requested it. `actor_id` is the RUNNER SELECTOR (`"gateway"` on every
gateway-started run; the runner ticks only that value; summon/agora runs park under
`"gateway:…-pending"` until flipped; children inherit it), never the requester. The gateway resolves
the principal on every request and discards it at run start; only catalog starts keep a signed copy
in `_runtime.workflow_policy.principal`; automation definitions keep no readable creator; the model
is told its user is "gateway" (or the host's OS login). The audit log pairs principal and run id
for root HTTP starts only (618 of 8,759 live runs, 7%). The Observer therefore shows nobody on a
Needs-you card (operator 2026-10-14: "if I am an admin looking at this, I want to know which user").

## Proposed direction (after the adversarial review — `../planned/governance/evidence/REQUESTER-adversary.md`)

- A runtime-owned attribution slot `vars._meta.requester = {user_id, tenant_id, source, token_fingerprint, via, on_behalf_of, at}`:
  `user_id`/`tenant_id` = the gateway principal; `source` = how it authenticated (`legacy-token`,
  `user-registry`, `loopback-ephemeral:<label>`, …, the real enum); `via` derived SERVER-SIDE from the
  route and the auth (never from a client header); `on_behalf_of` for relays (Telegram chat, agora);
  `at` = a DETERMINISTIC time (for occurrences `fired_at`, frozen at admission next to
  `automation_title`), never `now()` in a digested field (occurrence replay identity).
- Stamped ONCE at the gateway's start funnel (`BundleHost.start_run`, contextvar principal for HTTP,
  explicit kwarg for Telegram/agora/scheduler/discuss), which also strips any client-supplied
  `_meta.requester` (the schedule wrapper embeds client `_meta` unstripped today).
- Inherited by ONE runtime helper at all five child-spawning paths (START_SUBWORKFLOW, MEMORY_COMPACT,
  run_facade children, bundle-host listener children, the scheduled wrapper's target), each with a
  test that deletes the call and goes red.
- Indexed in both stores (`requester_user_id`, `requester_tenant_id`, `requester_via`; JSON sidecar
  version bump, sqlite ALTER + backfill), projected on list rows and detail and `/host/runs`.
- `_detect_runtime_user` (abstractruntime llm_client) reads the requester into `trace_metadata`; the
  OS-login fallback is dropped (1021 row 18).
- Automations: `created_by` on the definition; occurrences carry the creator at the admitted revision;
  "Run now" by another user is on the audit line and the command receipt, not on the run.
- Observer: `requester` on cards and in the (i); "unknown (before attribution)" for old rows; backfill
  of the 7% from the audit log only if ruled.
- `actor_id` keeps its meaning; a later wave may rename it `executor_id`.
- Cost (honest): runtime 3 d, gateway 2–3 d, Observer 1 d; release runtime → gateway (floor-pinned)
  → Observer in one wave; an old runtime under a new gateway must hide the field, not half-show it.
- Interim, if speed matters more: a per-plane `session_owners` record written at first start covers
  almost every session-bearing run with no runtime change, but cannot say "on whose behalf".

## Decision gates (operator, asked 2026-10-14)
1. Is "who" an ACCOUNT or a HUMAN? Under the static token the console, scripts and the tray are all "admin": accept, with source and token fingerprint shown, or require registry users?
2. Occurrences: requester = creator at the admitted revision, always, even when someone else clicks Run now?
3. A discussion forked by B on A's automation = B; an entity visit continued by B = B per turn?
4. May the model be told the requester: id, display name, or nothing?
5. `via` server-derived only, or also a client-claimed hint rendered as "claimed"?
6. Back-fill the 7% from the audit log, "unknown (before attribution)" elsewhere, or no back-fill?
7. Full slot now across the three repos, or the session-owner interim first?

## Promotion criteria
- The seven answers; then `planned/governance/1024_…` with the runtime item first.

## Validation ideas
- Skew matrix (runtime old/new × gateway old/new × Observer); replay-identity test for occurrences; the five inheritance paths each mutated once; a forged `_meta.requester` on `/runs/start` and on the schedule wrapper is stripped (test).

## Receipts
- `../planned/governance/evidence/REQUESTER-proposal.md` (findings F1–F7 with file:line) and `REQUESTER-adversary.md` (2 P0 / 8 P1 / 6 P2, GO-with-changes, inheritance table, skew matrix, 7 % backfill measurement).
