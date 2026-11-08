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

## Contract from the core owner (2026-11-08 15:00, core main 44897db3…904272da, push pending its gate)

`from abstractcore.exceptions import EndpointUnreachableError` (subclass of ProviderError): raised by every provider's
generate path when no TCP connection could be made (refused, OS connect timeout, host/network unreachable, DNS),
detected by TYPE over the cause chain. Fields: `provider`, `base_url`, `cause` (transport class path), `detail`
(≤200 chars), `errno`, `elapsed_s`, `retryable` (False when the connect itself timed out); class attribute
`counts_toward_breaker = False`; core does not retry when `retryable` is False and never records it in the breaker.
Speculation degrade: `response.metadata["speculation"] = {requested, mode, used: false, applied: false, reason:
"native_mtp_backend_unavailable", degraded_from_default: true, message, num_draft_tokens?, drafter?}`. Runtime half
started the same hour (park with `wait_key=endpoint_unreachable:<base_url>`, resume re-issues the identical call).

## Status 2026-11-08 14:10

Runtime half DONE and live since 13:30 (runtime da03304 + ed7d605): the park, the resume, the 503 rebuild, the pickle
contract. Until the gateway prober exists the resume is manual (Send event on the waiting run). The gateway and kit
halves moved to root 1169, PROPOSED, not for this release (operator 2026-11-08).

## Scope revised by the operator (2026-11-08 14:40) — next release

"That's an error (inferencer not available) that must be surfaced by the runtime through the replayable ledger,
possibly as a sort of 'gated' what-do-I-do (cancel, pause, maybe even pick another inferencer). The goal is not to solve
that at a client level only, but to have a durable exception that there was a problem, so that when we reconnect to
the client, we see it and can decide what to do."

What is live today (runtime da03304): the failure is already durable and replayable — the run parks as an EVENT wait
`endpoint_unreachable:<base_url>` with {provider, base_url, cause, detail, errno, elapsed_s, attempt, since} on the
ledger row, every client renders it from the replay view, and a `resume` re-issues the identical call. What is missing,
and becomes the scope for the next release (this item stays planned; 1169 keeps the automatic prober as its companion):

1. The wait is a person-facing DECISION, not a bare signal: `prompt` = "The model endpoint <base_url> did not answer
   (<cause>, after <elapsed> s). What do you want to do?", `choices` = keep waiting (auto-retry when it answers; the
   prober of 1169), retry now, pause the run, cancel the run, use another model (then the kit's model picker, scoped to
   the models the gateway serves to this principal). The chosen answer rides the `resume` payload and is a ledger row
   (`decision`, with who decided and when), so a client that reconnects later sees both the problem and the decision.
2. "Use another model" re-issues the call with the chosen provider/model for THIS run (persisted on the run's vars so
   later calls of the same run follow it), never silently; the ledger shows the switch.
3. Attention: Observer, the tray badge and the Assistant switcher treat it as "needs you" like an approval; the kit's
   standard decision card renders it in every app (one presentation, many clients); the status bar reads "Waiting for
   you: the model endpoint … did not answer".
4. Every other provider error class stays as today (fail with the whole error on the ledger).
5. Tests (hermetic): a fake endpoint that refuses → the decision wait with the five choices on the ledger and in the
   view; each choice does what it says and is recorded; a reconnecting client (view re-read) shows the card; the
   runtime half of 1169's prober resolves "keep waiting" without a click when the endpoint answers.

