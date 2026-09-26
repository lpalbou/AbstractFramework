# 0917 — Let an operator clear a saved trust-proxy switch

- **Status:** proposed
- **Created:** 2026-09-26
- **Area:** abstractgateway (network settings)

## Summary
Trust proxy follows one rule: the saved setting wins, `ABSTRACTGATEWAY_TRUST_PROXY` applies only while nothing is saved. Once a
value has been saved, nothing (CLI, console, API) can remove it; the only way back to the environment fallback is to switch it
on or off explicitly. Add `abstractgateway network set --trust-proxy default` (API `trust_proxy: null`) that deletes the saved
key, and one sentence in `docs/configuration.md` explaining that a saved switch retires the variable.

## Why
Found by the GO-gate review (untracked/missions-2026-09-25/REVIEW/24-go-gate.md, Job 25): a container operator who changes the
variable after a value was saved sees no effect and has no way to return to it.

## Current code reality
`abstractgateway/src/abstractgateway/network_exposure.py` accepts only on/off for `trust_proxy`; the resolver
(`resolve_trust_proxy`, one rule across `gateway_security.py`, `security/same_machine.py`, the status payload) reads saved > env.

## Validation
`network set --trust-proxy default` removes the key; the status reports `source: env|default` again; tests at all three sites.
