# 0895 — MLX has no idle/TTL unload: design one if wanted

> Package: abstractcore (providers/mlx_provider.py, providers/process_residency.py); abstractruntime (llm_client.py); abstractgateway (models load route, console)
> Type: improvement
> Created: 2026-09-26
> Priority: low
> Labels: memory, mlx, residency

## Summary

A loaded MLX model stays resident until someone ejects it. Mission M1 measured it: a load with
`ttl_s: 20` was accepted, and 60 s later the model was still at 16.3 GB. M2 made the option honest
(`ttl_s`/`keep_alive` are now reported as unsupported instead of silently accepted) but did not add an
unloader. If the operator wants idle unload for in-process engines, it needs a design; until then the
explicit eject (console, tray, CLI) is the only way to free memory.

## Why

M1 F2 ("the idle/TTL eject path does not exist for MLX"); REVIEW/08 S6 ("the operator asks for a TTL,
the console says OK, and the model stays pinned forever") — fixed as reporting, not as behaviour.

## Current code reality (2026-09-26; abstractcore `3c6e5ea` + uncommitted streaming edits; abstractruntime `bdebd0c` + staged edits)

- `abstractcore/abstractcore/providers/mlx_provider.py` l.3818–3826: "MLX has no idle/TTL unload:
  `ttl_s`, `keep_alive` … reported as `unsupported_options`".
- `abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py` l.4108
  `_IN_PROCESS_TIMED_OPTIONS = ("ttl_s", "keep_alive")` (reported on every load path, runtime `6969d17`).
- Only Ollama honours `keep_alive` (server side). No timer/unloader exists in core, runtime or gateway.

## Scope

### In scope

- Decide whether idle unload is wanted (operator). If yes: an idle timer per resident model that
  calls the existing process-wide eject (`eject_unclaimed`), skipped while a call is in flight or the
  model is locked/claimed; a gateway setting with three doors (web, terminal, CLI); the console shows
  "unloads after N min idle".

### Out of scope

- Changing explicit eject semantics; Ollama/LM Studio server-side TTLs.

## Dependencies

- Residency claims (0897) so an idle timer cannot eject a model another client still claims.

## Expected outcomes

- Either a documented "no idle unload" decision, or idle unload that frees Metal memory measured by
  `vmmap` (IOAccelerator) after the idle window.

## Acceptance criteria

- [ ] Operator decision recorded.
- [ ] If implemented: hermetic test — load, idle N s, model ejected, IOAccelerator back to baseline;
      a locked model survives.

## Validation

- M1 method: `untracked/missions-2026-09-25/M1/run_m1.py` (TTL probe step) against a hermetic gateway.

## Evidence

- `untracked/missions-2026-09-25/M1/REPORT.md` (criterion 3, F2)
- `untracked/missions-2026-09-25/M2/REPORT.md` (`cf8caae`; Review 08 fixes)
- `untracked/missions-2026-09-25/REVIEW/08-memory.md` (S6)

## ADR status

- ADR impact: None (ADR-0026 no-silent-caps is already satisfied by the reporting).

## Receipts

- None yet.
