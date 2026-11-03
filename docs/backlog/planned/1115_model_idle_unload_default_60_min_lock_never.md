# 1115 — Idle unload of loaded models: 60 minutes by default, a kept-loaded model never unloads

> Package: AbstractCore (mechanism), AbstractRuntime (relay), AbstractGateway (setting, flag, UI, lock persistence)
> Type: task
> Created: 2026-11-03
> Priority: high
> Labels: memory, residency, models, next-wave
> Ships: the NEXT wave, bottom-up, as AbstractCore 2.34 → AbstractRuntime 0.18 → AbstractGateway 0.21 → root pins
> Supersedes: [0895](../deprecated/0895_mlx_idle_ttl_unload.md); answers question 2 of [1076](../proposed/1076_model_scheduling_and_memory_management.md); a slice of [0991](0991_model_residency_and_gpu_memory_management.md)

## Summary

A model loaded in the framework that no call has used for the idle-unload time is unloaded from memory. The default is
60 minutes. A model kept loaded ("Keep loaded", the existing lock) never unloads this way, and its lock survives
restarts. A call that is running on the model, queued for it, or loading it is never interrupted. The next call loads
the model again.

## Why

Operator, 2026-11-03 (verbatim): "a model loaded in the framework ... must have a default TTL of 60mn. if the model is
never used for 60mn, it must automatically unload from memory. this must be customizable and in particular, in
gateway, when a model is 'locked', it means TTL is infinite and it can't unload as long as the lock is not removed."

Operator rulings, 2026-11-03:
- The default is 60 minutes.
- The setting is customizable through the launch flag `abstractgateway serve --model-idle-unload MINUTES` and the
  stored gateway setting `models.idle_unload_minutes`. The flag wins over the stored value, which wins over the
  default; `0` never unloads. There is no environment variable.
- Keep loaded (the lock) means the model never unloads, and the lock **persists across restarts**.
- It ships in the next wave as Core 2.34, Runtime 0.18 and Gateway 0.21.

Today nothing unloads a model that sits unused. Core reports it as absent: `mlx_provider.py:4543-4551` ("MLX has no
idle/TTL unload"); runtime `llm_client.py:4282-4314` warns that the model "stays loaded until it is unloaded". The only
idle reaper in the tree frees GGUF slot contexts, never weights (`gguf_slots.py:275-292`).

## Design (architect option C: Core mechanism, host policy)

Read first: `untracked/release-2026-11-03/architect-model-ttl.md`, a verified file:line map of every unload, lock and
last-used path, with the alternatives and charter verdicts. Option C was chosen: Core owns the reaper, last-used and
the safety rules; the host passes one number through a runtime setter; the gateway owns the setting, the flag, the UI
and lock persistence. The lock is the existing claim. This follows Core ADR 0010's split and 0991's rule of no second
scheduler.

### AbstractCore 2.34 (mechanism)

- `providers/generation_cancel.py:267-282`: stamp `last_used_at` on every `begin`/`end`, with or without a cancel event.
  Today `begin(None)` returns before stamping, so a call without an event is neither stamped nor counted in flight.
- `providers/mlx_provider.py`: set `_PRIVATE_CANCEL_EVENT_FOR_EJECT = True` (as HuggingFace does) so every MLX call is
  tracked in flight. Report the native runtime's pending and active requests as in use (open point U3 below).
- `providers/process_residency.py`:
  - `resident_model_states()` (`:371`) gains MLX (`mlx_residency` holders) and embeddings rows with the same fields
    (`held_bytes`, `last_used_at`, `in_use`, `locked_by`). A `building` claim counts as in use.
  - New: `set_idle_unload(seconds: Optional[float])` and `idle_unload_s()`, default `3600.0`; `None` or `0` turns it off.
  - New: `reap_idle(now=None)`. It runs under `residency_lock()` and takes `load_lock()` non-blocking (the tick is
    skipped while a load runs). For every state that is not locked, not in use and idle at least the window, it
    re-checks, then calls `eject(backend, model, reason="idle")`. The eject is process-wide, with gc and
    `clear_cache`, then `_release_torch_device_cache()`. It logs `unloaded <model> after <N> min idle; freed <GB>`.
  - One daemon thread, started lazily by the first in-process load, ticking every `min(60 s, idle/4)`. An
    `idle_unload_at` helper for rows returns `last_used_at + idle`, or None when the model is locked, the setting is
    off, or the model is in use.
  - Admission gate (open race U2): an idle eject passes `cancel=False`. Holders then refuse while anything is in
    flight instead of cancelling (`base.py:5741` `_stop_inflight_before_unload` gains `cancel: bool = True`).
    `begin()` registers under `residency_lock()`, so no call can start between the reaper's check and its eject.
  - `eject_unclaimed` cannot be the idle path: every pooled model carries a pool claim (`process_residency.py:240-249`).
    The reaper uses ADR 0010's rule (locks and in-use only), like `make_room`.
- New `docs/adr/0012-idle-unload.md`, amending 0010: idle is a second eviction trigger under 0010's rule (locks and
  in-use); the default is 60 minutes; Core owns the mechanism and the host the policy; an idle eject never cancels and
  is always process-wide.
- Docs: rewrite `docs/memory-management.md:433-435` and the `mlx_provider.py:4543-4551` docstring and warning.

### AbstractRuntime 0.18 (relay)

- `integrations/abstractcore/llm_client.py`: `set_model_idle_unload(seconds)` on `LocalAbstractCoreLLMClient` and
  `MultiLocalAbstractCoreLLMClient`, forwarding to Core (remote/gateway clients: `_optional_control_unsupported`). The
  `set_` name makes the model host replay it after a child restart (`model_host.py:689-700`).
- Local rows (`_local_residency_record`, `:4960-4995`) add `last_used_at`, `idle_unload_at` and `idle_unload_s`.
- The `ttl_s` warning text (`:4282-4314`) names the idle-unload setting instead of "stays loaded until it is unloaded".
- `host_facade.py` exposes the setter.

### AbstractGateway 0.21 (policy, UI, lock persistence)

- **Flag.** `--model-idle-unload MINUTES` on `serve` and `runner` (`cli.py:_add_model_host_args`). Help text: "Unload
  a model no call has used for MINUTES; 0 never unloads; a model kept loaded never unloads. Default 60."
- **Stored setting.** `models.idle_unload_minutes` in `runtime_config.py`, resolved flag > stored > default 60 with a
  `source`, in the `resolve_exec_runner` shape. It is written through the existing admin runtime-config door and
  `abstractgateway config get|set`.
- **Applied** by calling `set_model_idle_unload` on the gateway's clients at boot and on every change, in both
  model-host modes. A runtime without the setter is reported as "idle unload needs AbstractRuntime >= 0.18" (the
  `RuntimeTooOld` pattern, `core_config.py:1497-1503`), never ignored silently.
- **Lock persistence (operator ruling).** A Keep loaded lock is recorded by the gateway (admin-only, like the lock
  routes `routes/gateway.py:28936-28960`, `security/authorization.py:171-175`) and re-applied after a model-host
  restart and after a gateway restart. Today a lock lives only in the process (`llm_client.py:5094-5106`) and is not
  replayed (`model_host.py:689-700`). Unlock removes the record.
- **Rows.** `/models/loaded` passes through `last_used_at` and `idle_unload_at`.
- **Console.** The Models row (`console.py:12100-12168`) gets one muted line: "Unloads after 60 min unused", "Unused
  for 12 min, unloads in 48 min", or, when locked, "Kept loaded: never unloads". Settings get one number field with
  its source pill. The TUI Models tab (`console-tui/src/store.rs`) gets the same line and a settings entry. The tray
  gets nothing new; its eject already explains locks.
- **Docs.** The gateway models/settings page, and one line in the root `docs/` install and FAQ pages.

### Open points

- **U2, the admission race.** A call that begins between "not in use" and the eject would be cancelled by today's
  holders. The `begin()` gate above closes it, but it is not yet proven that taking `residency_lock()` in `begin`
  cannot deadlock against a stream body or the MLX native runtime's own lock. Fallback if the proof fails: refuse
  while in flight and retry next tick, without the gate (a tiny window), or move the gate into the provider's load
  lock.
- **U3.** It is unverified whether MLX native-runtime pending requests are visible as in use before `begin` runs.
- **Lock persistence and boot.** Does a persisted lock load its model at boot (warm after a restart, one model at a
  time under the memory rules), or only re-lock it on its next load? To be decided with the operator before the
  gateway slice.

## Out of scope (phase 2, separate items)

- Voice, image and music engines (abstractvoice, abstractvision, abstractmusic plugin residency). They expose no
  last-used today (U4); each must report `last_used_at` and in-use per resident engine and join the reaper (0991 row
  3). Until then the operator's "any model" is met for text and embeddings only.
- Per-model idle times; per-load `ttl_s` for in-process providers (not asked).
- External servers (LM Studio, Ollama) keep their own TTLs; a lock already sets Ollama `keep_alive=-1`.

## Consequences to document (migration)

- The 60-minute default applies on upgrade with no action.
- After an unload, the first call pays the load and a full prefill: in-memory prompt caches go with the weights.
- Hourly automations sit on the boundary: some runs find the model warm, some cold. Keep loaded or a larger value
  avoids it.
- A drafter or decision model is unloaded with its target (`mlx_provider.py:4581-4584`) and comes back with it.
- `0`, or Keep loaded, restores today's behaviour.

## Acceptance criteria

Every test below must go red without its rule. They use fakes, load no model and never reach :8080.

- [ ] Core `tests/providers/test_idle_unload_unit.py` (fake clock):
  - an idle unlocked model is ejected after the window;
  - a locked model (claim `locked: True`, server-runtime lock) survives;
  - an in-flight call survives and is never cancelled;
  - a queued slot and a `building` claim survive;
  - the tick is skipped while `load_lock()` is held;
  - `0`/`None` turns the reaper off;
  - MLX and embeddings rows are reaped;
  - `last_used_at` is stamped on a call without a cancel event;
  - a call that begins during a reap waits and then reloads (no cancel; a thread test that fails on deadlock);
  - the eject is process-wide and `clear_cache` is called;
  - deleting the reaper, or dropping the lock check, turns the suite red.
- [ ] Runtime: the setter forwards to Core and has a `set_*` name; rows carry the three fields; the `ttl_s` warning
  text names the setting.
- [ ] Gateway:
  - the setting resolves flag > stored > default with its source;
  - the setter is applied at boot and on change, and replayed after a model-host restart;
  - the lock survives a model-host restart and a gateway restart (scratch data dir);
  - the routes are admin-only;
  - the console row strings and the TUI row parse are covered.
- [ ] Real-weights proof on the operator's machine, under `untracked/gpu.lock`, on a scratch data dir and port with
  the admin token unset. A small MLX model with `--model-idle-unload 1`:
  - idle for 90 s, the row is gone and `vmmap --summary` IOAccelerator is back to baseline (sampled at least 1 s after
    the reap);
  - with Keep loaded it is still resident after 3 minutes, and after a gateway restart it is still locked;
  - a call started at 59 s completes.
- [ ] Core ADR 0012 accepted; 0991 slice table updated; release notes in all three packages name the default and how
  to change it.
