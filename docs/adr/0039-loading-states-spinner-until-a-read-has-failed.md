# ADR-0039: Loading States — A Spinner Until the Data Is In, an Error Only Once the Read Has Failed

## Status
Accepted (2026-10-18)

## Dates
- Proposed: 2026-10-18
- Accepted: 2026-10-18

## Context

Every client of the framework (the web console, Observer, Flow, the Assistant on the desktop,
iPhone and Apple Watch, the TUIs) reads its data from a gateway over a network that is sometimes
slow: a public gateway answers some lists in 5 to 20 seconds, a watch's radio takes seconds to
come up after launch, and a busy server times out now and then. A screen that shows an error at
the first failed request, or an empty state ("None yet", "No conversations yet") before its first
read has answered, tells people something false: the data exists and arrives a moment later, and
the error disappears on its own. People then distrust every message the app shows.

## Decision

1. **Until a read has answered, a screen shows that something is coming.** It shows a spinner
   where the content or number will be, and an animated "Loading…" where a line of text will be.
   It never shows an empty state, a zero or a placeholder that reads as data.
2. **A read is retried before it is reported.** A failure that another try may not meet is a
   timeout, a lost or refused connection, or a server error (5xx, 408, 429). Such a read is tried
   again, 3 tries in all with a short back-off (1 s, then 3 s). The spinner stays up through the
   tries. A refusal (401, 403, 404 or another 4xx) or an unreadable answer is final at once. The
   retry lives in the client library, in one place, so every screen inherits it.
3. **An error is shown only once every try has failed,** in the place of the content that could
   not be read, in plain words, with a way to try again (Retry, or pull to refresh).
4. **Connection status follows the same rule.** A client says the gateway is unreachable only
   after repeated failures over a sustained period (on the Apple Watch: 3 failed polls over at
   least 20 s). Until then it says "Connecting…". Once connected, a single failed refresh keeps
   the data on screen and is retried quietly.
5. **Writes are not retried silently.** An action (send, start, archive, save) is sent once. Its
   failure is reported as soon as it happens, because repeating a write could repeat its effect.
6. **Request timeouts fit the call.** A request that is known to be slow (a full list of
   automations, full answers) gets a timeout sized from measurements on a public gateway, not the
   client's default.

### Before / after

An Apple Watch automation page reads its six latest results over a watch's radio:

- Before: the single request timed out at 20 s, the page showed "Couldn't load the latest
  result. Retry" in amber, and the results arrived a moment later on their own.
- After: the request has 60 s and is tried up to 3 times. The page shows a spinner until the
  results are in, and shows "Couldn't load" only if all three tries failed.

### Decision boundaries

- This ADR governs reads a person waits on (lists, pages, counts, media). Background refreshes of
  data already on screen keep the data and retry quietly; they never replace it with an error.
- It does not make writes idempotent or retry them. That would need an idempotency contract on
  the gateway route, which is a separate decision.
- It does not hide failures. After the last try the error is shown, in the place of the missing
  content, with a way to try again. Nothing falls back to stale or placeholder data that is
  presented as current.

## Consequences

### Positive
- People see an error only when there is one, so they can trust the messages they do see.
- One retry in each client library covers every screen of that client, including future ones.

### Negative
- On a gateway that is really down, the error appears later: up to 3 tries of the request's
  timeout plus 4 s of back-off.
- A read that the server performs but does not answer in time is performed again. This is
  acceptable only because reads have no side effects (writes are excluded).

### Neutral
- Each client library carries its own retry, because the clients are written in different
  languages (Swift, TypeScript, Python, Rust). The rule is shared; the code is not.

## Enforcement

- Each client library has one choke point for gateway requests, where GETs are retried as above.
  Screens must not add their own error-on-first-failure path around it.
- Code review: a new screen that reads data shows a spinner (or an animated "Loading…") until the
  read answers, never an empty state before its first answer, and an error only from the read's
  final failure. A screen that does not follow this rule cites this ADR in its review comment.
- A new slow route gets a timeout measured on a public gateway, written next to the call with
  the measurement.
- Completion reports for client work state which screens were checked against this ADR.

## Validation

- Apple Watch (`abstractassistant/watch/apple`):
  - `RetryTests` (SwiftPM) cover the retry rules: a dropped connection and a 503 followed by an
    answer succeed after 3 tries; three 503s fail only after 3 tries; a 404 fails at once; a POST
    is sent once. With the retry disabled, the first two tests fail.
  - UI tests cover the screens: `HomeLoadingUITests` (a slow, failing first read shows a spinner
    and never an error), `HomeConnectingUITests` ("Connecting…" while starting, unreachable only
    after 20 s), and `LiveHomeUITests` (against a live gateway, no error while a page loads).
- Other clients: the same two-sided check (a read that fails then answers shows no error; a read
  that keeps failing shows one after the tries), added when the client adopts this ADR.

## Adoption

- Apple Watch app: conforms (`LiveGatewayClient.request` retries reads; screens keep spinners
  through the tries).
- Web console, Observer, Flow, Assistant desktop and iPhone, TUIs: not yet audited. The ADR
  applies to new screens now and to existing screens as they are changed; an audit per client is
  follow-up work.

## Backlog links

- Originating work: the Apple Watch 0.3.0 loading and connection fixes (release notes in
  `abstractassistant/watch/apple/CHANGELOG.md`, Fixed).
- Adoption: one audit item per client is to be filed when that client is next worked on.

## Related

- [ADR-0014](0014-runtime-authority-timeouts.md) (runtime authority timeouts): server-side timeouts. This ADR covers client reads.
- The Apple Watch choke point: `LiveGatewayClient.request` and `isTransient` in
  `abstractassistant/watch/apple/Packages/AbstractGatewayClient/Sources/AbstractGatewayClient/GatewayClient.swift`.
