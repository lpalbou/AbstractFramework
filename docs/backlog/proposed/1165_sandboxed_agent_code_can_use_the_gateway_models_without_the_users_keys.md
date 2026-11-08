# 1165 — Code an agent runs in its sandbox can use the gateway's models without reading the user's keys

> Package: AbstractGateway (`/v1` route, run-scoped credentials, `workspace_browse.BUILTIN_DENY_HOME_RELPATHS`), AbstractRuntime (the command sandbox host hands the credential to the process), AbstractCore (`create_llm("endpoint:<profile>")` resolution)
> Type: feature (design first)
> Status: proposed
> Created: 2026-11-08
> Priority: P2
> Labels: sandbox, security, providers, agents

## What the operator saw (2026-11-08 11:14, Code web)

The agent wrote a program that calls `create_llm("endpoint:compat-theforge-nvidia", model="qwen/qwen3.8-27b")` and
reported: the profile lives in `~/.abstractcore/config/abstractcore.json`; "my sandbox cannot read that file —
PermissionError: Operation not permitted"; "the local gateway on :8080 requires an API key and I have no key to
send". It asked the operator for the gateway's key.

## Why it is so today (by design, not a bug)

`~/.abstractcore` holds provider API keys, so it is in the gateway's built-in deny list for every run's tools and for
the command sandbox (`workspace_browse.py:366-372`, with `.ssh`, `.aws`, `.gnupg`, `.kube`, the Keychain, the other
AbstractFramework config folders). An admin may turn the list off with the stored setting `workspace_builtin_deny`,
which hands every agent the user's keys: not what anyone wants by default. The "Everything else: read-only" policy in
Code's Folders panel applies on top of that deny list, not instead of it.

## The gap

Agent code therefore has NO sanctioned way to use a model: the user's profiles are (rightly) hidden, and the
gateway's `/v1` route wants a token the agent does not have. The agent's only honest move is to ask the person for a
key, which is the wrong direction.

## Proposal

- Each run that may execute code receives a run-scoped credential (short-lived, revoked at run end, bound to the
  run's principal and model budget) in the sandbox environment, e.g. `ABSTRACT_GATEWAY_URL` + `ABSTRACT_GATEWAY_TOKEN`
  (credentials are the one place an environment variable is allowed, operator rule 2026-09-24).
- `create_llm("endpoint:<profile>")` inside a sandbox resolves through the gateway (`/v1` with that credential), never
  through the user's config file; the gateway applies the run's model policy and records the calls on the run's ledger
  like any other generation (one pool, no second client: Core ADR 0011 / runtime 0866).
- The agent's tool descriptions say so ("to call a model from your code, use the gateway at $ABSTRACT_GATEWAY_URL;
  your run's credential is in the environment").
- Out of scope: giving agents the user's provider keys; sandbox escape of any kind.

## Open questions for the operator

- Budget: the run's own model budget, or a separate one for code the agent writes?
- Which models: the run's mind only, or every model the gateway serves to that principal?
