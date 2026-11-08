# 1169 — Endpoint park, the gateway and kit halves: a prober resumes parked steps; health and the status bar name the endpoint

> Package: AbstractGateway (per-endpoint reachability prober, resume of `endpoint_unreachable:<base_url>` waits, health detail, console Models page), AbstractUIC panel-chat (the status bar reads "Waiting for the model endpoint …")
> Type: feature (the second half of root 1168)
> Status: proposed (operator 2026-11-08 14:00: "not for this release")
> Created: 2026-11-08
> Priority: P2
> Labels: resilience, endpoints, runs

## Summary

Root 1168's runtime half is live since the 13:30 restart (runtime da03304): a connect failure to a model endpoint parks
the model call as a durable signal wait keyed `endpoint_unreachable:<base_url>`, with the attempt on the ledger, and a
`resume` command re-issues the identical call. Until this item lands, the resume is MANUAL: the kit shows the parked
run as "Waiting for an event" with its event card; pressing Send event (empty JSON) resumes it once the endpoint is
back. This item makes it automatic and names the endpoint where the person looks.

## Scope

1. A per-endpoint prober in the gateway: when any run parks on `endpoint_unreachable:<base_url>`, one probe per
   endpoint (not per run) with backoff 5 s → 60 s cap; on success every parked step on that endpoint is resumed.
2. Health lists endpoints currently unreachable with the number of parked steps and the time since; the console's
   Models page shows the same with a "Retry now" action.
3. Kit: the status bar reads "Waiting for the model endpoint 192.168.1.7:1234 (unreachable since 10:44)" for this
   wait kind; Observer and the tray treat it as an informational wait, not an approval and not a failure.
4. Tests (hermetic): a fake endpoint that refuses connections parks the run; bringing it back resumes it without a
   click; the status text names the endpoint; health shows the count.

## Related

Root 1168 (runtime half done 2026-11-08), 1164 (the typed error), 1158 (scalability; the harness).
