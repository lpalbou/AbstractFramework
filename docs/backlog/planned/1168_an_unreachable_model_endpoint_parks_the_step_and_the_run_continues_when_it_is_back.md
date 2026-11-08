# 1168 — An unreachable model endpoint parks the step; the run continues when the endpoint is back

> Package: AbstractRuntime (the LLM_CALL handler and its retry/park contract; ledger event), AbstractGateway (endpoint reachability probe, the circuit breaker policy for connect failures, health and the console's "waiting for" state), AbstractUIC panel-chat (the run status says what it waits for), AbstractCore (supplies the typed network error: base_url, exception class, measured duration; the core owner's patch of 2026-11-08)
> Type: feature (resilience)
> Status: planned
> Created: 2026-11-08
> Priority: P1 (operator ruling 2026-11-08, relayed by the core owner)
> Labels: resilience, providers, endpoints, runs, breaker

## Operator ruling (2026-11-08, after the 10:44 incident)

"The gateway should be resilient to that sort of failure and just consider it as a step not done, that needs to
continue when possible."

Context: at 10:44 the Code run's model call could not open a connection to the inference machine at 192.168.1.7:1234
for about four minutes (three TCP connect timeouts, 226 s; the machine runs only LM Studio and is on again), the error was mis-classified as a configured timeout, the run failed and
the circuit breaker refused the endpoint for 60 s (root 1164, 1167). The operator's reading: an unreachable endpoint is
a transient condition for the run, not a failure of the run.

## Scope

1. **Recognise it**: core's patch classifies connect failures as a typed network error carrying `base_url`, the
   exception class and the measured duration (type and fields to be published by the core owner when the patch lands;
   the runtime imports that type and fails loudly if it is absent, no string matching).
2. **Park, do not fail**: on that error the LLM_CALL handler parks the step in a durable wait
   (`wait_key=endpoint_unreachable:<base_url>`, reason "the model endpoint <base_url> did not answer; waiting for it")
   with the attempt recorded in the ledger (duration, exception class). The run stays `waiting`, resumable, visible
   in listings like any other wait; nothing is lost; cancel works as usual.
3. **Resume when back**: the gateway probes parked endpoints with backoff (5 s → 60 s cap, one probe per endpoint,
   not per run) and resumes every step parked on it when a probe succeeds; a manual "retry now" exists on the run
   (command) and in the console's Models page. The circuit breaker does not open on connect failures (the park replaces
   it); it keeps its role for application errors.
4. **Say it where the person looks**: the run status bar reads "Waiting for the model endpoint 192.168.1.7:1234 (off or
   unreachable since 10:44)"; Observer and the tray's attention use the same wait kind as an informational wait, not a
   failure; health lists endpoints currently unreachable and the number of parked steps.
5. **Bounds**: a parked step older than the run's own wait budget (if the workflow declares one) ends as today with the
   whole history of attempts in the ledger; by default it waits.
6. Tests (hermetic): a fake endpoint that refuses connections → the step parks with the typed reason; bringing the
   endpoint up resumes the run and the reply arrives; the breaker never opens; the status text names the endpoint;
   removing the park turns the test red.

## Out of scope

Application-level provider errors (4xx/5xx with a body), model-side timeouts on a reachable endpoint (ADR-0027 governs
those), multi-endpoint failover (root 1152).

## Related

Root 1158 (scalability; this is its resilience half for endpoints), 1164 (the message and the typed error), 1167 (MTP
default degrade), ADR-0027 (timeouts), gateway 1012/1013 (entity waits use the same durable-wait machinery).
