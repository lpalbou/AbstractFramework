# 1164 — A generation that fails in 0.01 ms is reported as "timed out after 7200.0s"; the breaker then blocks the endpoint

> Package: AbstractCore (`abstractcore/providers/base.py` ~1218-1290 `_timeout_message` / `_looks_like_timeout`, `core/retry.py` circuit breaker; the core agent's package, filed here for the owner), AbstractGateway (model-host log carries no traceback for a provider failure)
> Type: defect (ADR-0027 §1: the surfaced duration and the responsible knob must be accurate)
> Status: planned
> Created: 2026-11-08
> Priority: P1 (the operator watched his inference machine idle while the ledger said a two-hour timeout)
> Labels: providers, timeouts, observability, circuit-breaker

## What happened (2026-11-08, Code web conversation run `c00883d1…`, react child `d03dc6d9…`, mind `endpoint:compat-theforge-nvidia` / `qwen/qwen3.8-27b` on LM Studio at 192.168.1.7:1234)

- 10:44:46 the operator approved an `execute_command` from the tray; the run resumed and issued a `reason` call.
- model-host.log: `10:48:32 [ERROR] OpenAICompatibleProvider: Generation failed for qwen/qwen3.8-27b: openai-compatible
  API error: timed out after 7200.0s (configured timeout; set timeout=None …) (latency: 0.01ms)`; again at 10:49:18
  (0.00 ms); 10:49:21 `Circuit breaker open for OpenAICompatibleProvider:qwen/qwen3.8-27b`; three more generations
  refused on the open breaker at 10:50:10-13. The run failed. The ledger says the same.
- Nothing reached the inference machine (the operator: "I have the inference machine in front of me, it's not thinking
  at all"); `GET http://192.168.1.7:1234/v1/models` answered at 11:30.

So the request failed before any network I/O, and the message blamed a two-hour timeout that never elapsed.
`_looks_like_timeout` falls back to a string match ("timeout"/"timed out" in the exception text), and
`_timeout_message` then prints the CONFIGURED total as if it had been spent. The real exception type is not logged
anywhere (model-host.log prints the mapped message only).

## Scope

1. Never print a duration that did not elapse: the message states the measured latency and the exception class
   (`openai-compatible API error before the request was sent (0.01 ms): <ExceptionType>: <text>`); the configured
   bound is named only when the measured latency is within 5 % of it.
2. The string fallback in `_looks_like_timeout` does not classify a failure as a timeout when the measured latency is
   under 1 s; such failures are surfaced as what they are.
3. The model host logs the exception class and the first frames of the traceback for every provider failure (one
   line each, bounded), so the next instant failure is diagnosable without a reproduction.
4. The circuit breaker (5 failures / 60 s recovery by default) is reported to the client with the time left and the
   failures that opened it, and the gateway's Models page shows an open breaker per endpoint.
5. Find and fix the instant-failure cause itself: reproduce with the same provider path (the model host's provider
   pool for an `endpoint:` profile, prompt of 57 messages with large tool outputs) — candidates: the request body
   exceeding a client-side limit, the pool handing out a closed client, the profile's `timeout` kwarg rejected.

## Related

Root 1158 (scalability, observability of the model host), the 2026-08-02 LM Studio incident recorded in the same code
(the misattribution hid it for weeks), root 1160.

## Exchange with the core owner (2026-11-08 12:05)

Confirmed in `providers/base.py` (`_looks_like_timeout` ~1274 string fallback; `_timeout_message` prints the configured
total). Agreed fix: a duration is printed only for a real timeout type or a measured elapsed time; otherwise
`<provider> API error: <ExceptionClass>: <message> (failed after X ms, before the Ys timeout)`; the exception class and
module are logged at WARNING on the normalisation path. Facts handed over: no original exception text exists in any
log; the runtime issued the call at 10:44:46 and saw the failure at 10:48:32 while core measured 0.01 ms, so the wait
happened in the model-host child before the provider timer (an MLX snapshot fetch ran in the same minutes); the
admission half is root 1167 (gateway). Also agreed: the `embeddings.manager` "partially initialized" error is a race in
`process_residency.py:421-424` (module in sys.modules while another thread still executes it), fixed by a getattr
check for `registered_embedding_managers`. Retracted by the framework seat: the "tools import cycle" was the
workspace-root namespace-package pitfall, not a cycle.

## Corrected (2026-11-08 12:45)

Not instant: the ~0 ms is a measurement bug on core's failure path (`base.py:5766-5771` uses the current time as the
start time), and the 226 s matches three macOS TCP connect timeouts (75 s each) against an unreachable
192.168.1.7, i.e. `httpx.ConnectError` / `OSError errno 60 "Operation timed out"` mis-classified by the string fallback.
Core's patch: connect failures classified NETWORK with the measured duration and the target base_url; type-first
classification; exception class logged; true elapsed on failure lines; the same tightening in `core/retry.py:289`.

## Closed on the cause (2026-11-08 13:00)

The core session relayed that the operator had switched the inference machine off around 03:00-04:00; to the framework session the operator said at 12:55 that forge is on and runs only LM Studio (nothing of ours runs there). What the evidence shows on its own: this Mac could not open a TCP connection to 192.168.1.7:1234 for about four minutes from 10:44 (three 75 s kernel connect timeouts); the reason on the path or on that machine is not recorded anywhere and needs nothing from forge.
His ruling for the gateway/runtime half: an unreachable endpoint is a transient condition, the step waits and resumes
when the endpoint is back instead of failing the run and opening the breaker — root 1168. Core publishes a typed
network error (base_url, exception class, measured duration) that the runtime consumes for that park.

Operator, 13:05: "it is possible that indeed theforge was off during that time. probability 75%. but can't be certain." The
connect-timeout diagnosis is consistent with that and needs no further proof; the fix is the message and the park (1168).
