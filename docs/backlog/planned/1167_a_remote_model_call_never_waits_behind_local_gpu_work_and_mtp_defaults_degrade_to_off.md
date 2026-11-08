# 1167 — A remote model call never waits behind local GPU work; a stored MTP default degrades to off instead of failing

> Package: AbstractGateway (model host child: admission and serialisation between local loads/generations and remote endpoint calls; capability defaults applied to runs), AbstractRuntime (LLM_CALL handler backstop for `SpeculationUnavailableError`), AbstractCore (the lock or deadline on the provider path that raised in 0.01 ms; root 1164 covers the message)
> Type: defect ×2 (same morning, same minutes)
> Status: planned
> Created: 2026-11-08
> Priority: P1 (operator 2026-11-08: "I have the inference machine in front of me, it's not thinking at all")
> Labels: model-host, admission, speculation, mtp, providers

## What happened (2026-11-08, the operator's gateway, from the ledgers and model-host.log)

1. 10:42-10:43: six Assistant runs (`abstractassistant-orchestrator`, session `sess_f7ac1b7d…`) failed at once with
   `SpeculationUnavailableError: The openai-compatible provider has no native MTP adapter
   (speculation.require_acceleration=True)`. The model was a remote endpoint (`endpoint:compat-theforge-nvidia`,
   `qwen/qwen3.8-27b`); the gateway applied a stored `native_mtp` speculation default (console.py ~9720 writes
   `{mode: "native_mtp", num_draft_tokens, require_acceleration: true}`) to a provider that cannot do it. The
   operator's ruling of round 4 was "fall back to MTP off if MTP was selected by mistake; the MTP dropdown is off and
   disabled for a non-MTP model" — the UI half landed, the call-time backstop did not.
2. 10:44:46 → 10:48:32: the Code conversation's `reason` call (same remote endpoint) was issued by the runtime and
   failed 3 min 46 s later, yet core's telemetry recorded `latency: 0.01ms` and the message read "timed out after
   7200.0s". The time was spent inside the model-host child before the provider's own timer started; in the same
   minutes the child fetched an MLX snapshot (`Fetching 13 files` ×2 between 10:49:18 and 10:50:10;
   `Jundot/Qwen3.8-27B-oQ4e-mtp` had been unloaded at 05:38:59). A remote HTTP call to another machine waited behind
   local GPU work, then died on a lock or deadline whose text classified as a timeout (root 1164 for the message and
   the exception class). The circuit breaker then refused the endpoint for 60 s and the run failed.

## Scope

### Runtime backstop (small, first)

- In the LLM_CALL handler: when the provider raises `SpeculationUnavailableError` and the request carried a
  `speculation` setting, retry once without it and record a ledger notice ("speculation requested (native_mtp, N draft
  tokens) but the openai-compatible provider has no native MTP adapter; generated without it"); the replay view shows
  the notice; never fail for this reason alone. Tests red-without.

### Gateway admission (the real fix)

- The model-host child keeps local GPU work (MLX/HF loads and generations, residency unloads) on its own serialised
  lane; remote endpoint calls (`endpoint:` profiles, `openai-compatible`, hosted providers) never take that lane and
  never wait on its lock. Measured: a remote call issued during a local 27B load answers within the remote's own
  latency.
- The capability-defaults application does not attach a `native_mtp` speculation to a run whose provider family has no
  adapter (the same rule the console's dropdown applies), so the backstop above is the exception, not the path.
- Health and the console show the child's lanes: what holds the GPU lane now, how many remote calls are in flight.

### Core (coordinated with the core owner, 2026-11-08)

- The exception class is logged on every provider failure; no duration is printed that did not elapse (root 1164).

## Validation

- Hermetic model host with a fake slow local load and a fake remote endpoint: the remote call returns during the
  load; the ledger shows no timeout; an MTP default on a remote run yields one notice and a reply.

## Refined after reading the code with the core owner (2026-11-08 12:30)

- The 3 min 46 s between the runtime's `llm_call started` (10:44:46) and the logged failure (10:48:32) is best
  explained by core's retry loop (`core/retry.py:289` classifies any exception whose text contains "timeout" as a
  retryable TIMEOUT and backs off between attempts), wrapping an exception that fired at the provider's first
  statement (0.01 ms) on every attempt; the second runtime attempt (10:48:33 → 10:49:18) had fewer retries before the
  breaker opened. So the wait was not admission: the runtime's local generate lock is MLX-only
  (`llm_client.py:690-706`), the model-host child executes requests sequentially per connection but the gateway hands
  each request an idle connection (`model_host.py:1409-1432`, pool of 16), and the child's host lock guards only the
  client registry (`model_host_child.py:61,342,353`).
- The exception type is still unknown; nothing logs it. Core's patch (exception class and module logged at WARNING;
  type-first classification; no configured duration printed for a 0 ms failure; the retry classifier tightened the
  same way) is what names it the next time. Until then, a retry in Code after the breaker's 60 s shows whether it
  recurs; if it does, the model-host log carries the class.
- Scope of this item therefore: (1) the gateway capability default never attaches `native_mtp` to a provider family
  without an adapter (core degrades default-sourced requests, 2026-11-08 agreement); (2) the runtime surfaces core's
  `speculation.applied=false` as a ledger notice; (3) remote endpoint calls keep their own lane in the model host as
  designed above, verified by the hermetic test, even though this incident did not prove a queue; (4) health shows the
  model host's lanes.

## Corrected by the core owner (2026-11-08 12:45): a connect timeout, not a queue and not a retry loop

- core's `generate_with_telemetry` logs ~0 ms on EVERY failure (`providers/base.py:5766-5771` passes the current time
  as start time on the failure path), so "latency: 0.01ms" says nothing; core's retry backoff is at most ~3 s in total
  (3 attempts, 1 s initial, cap 60 s, jitter).
- What matches the 226 s exactly: macOS's kernel TCP connect timeout of 75 s × 3 attempts = 225 s (+ ≤3 s backoff).
  The exception is `httpx.ConnectError` wrapping `OSError` errno 60 "[Errno 60] Operation timed out": the string
  fallback classified it as a timeout, the message printed the configured 7200 s, the retry classifier retried it, and
  the breaker opened on the accumulated failures. The 45 s second attempt fits a host coming back. The inference
  machine (192.168.1.7) was therefore unreachable from this Mac between about 10:44 and 10:49; this Mac did not sleep
  (its power assertions were held throughout) and no network event of its own was found in its logs, so the cause is
  on the inference machine's side or the path to it — the operator can say whether it was asleep or off the network.
- Consequence: the admission theory is withdrawn for THIS incident (a remote-lane design remains part of 1158's
  measurements, not a defect here). Core's patch adds: connect failures (errno 60/61/64/65, `httpx.ConnectError`)
  classified NETWORK with "could not connect to <base_url> (<ExceptionClass>: <text>) after <measured> s"; the string
  fallback only when no type information exists; the exception class logged on every normalisation; the true elapsed
  time on the failure line (root 1164).
- This item keeps: the gateway capability default never attaches `native_mtp` to a provider family without an adapter;
  the runtime surfaces core's `speculation.applied=false` as a ledger notice. The hermetic remote-lane test moves to
  1158.

