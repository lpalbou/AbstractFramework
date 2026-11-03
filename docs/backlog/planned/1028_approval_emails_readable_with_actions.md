# 1028 — Approval emails a person can read and answer from the inbox

> Package: abstractgateway (facts from abstractruntime's wait payload)
> Type: feature
> Created: 2026-10-18
> Priority: high
> Labels: email, approvals, end-user-copy, branding, security

## Summary

The "needs your action" email the gateway sends when a run waits for a person is not an email a
non-technical person can act on. Today it says `“visual_react_agent_basic-agent_0_0_5_81795ea9_node-2”
waits for your approval before running fetch_url. Open the console to approve, deny or answer.`, a
run id, a loopback console link and the sentence about the notification setting. It must become a
branded, well-formatted email that states the context (which workflow or entity, started by whom,
when), the exact question or tool call, the options, and buttons that answer from the email itself:
Approve, Deny, Approve all (as the console's Accept all), or one button per choice of a question. One
email per wait, never one per retry.

## Why

Operator, 2026-10-18 (screenshot of the inbox: eight near-identical emails for the same node): "they
are absolutely not for end users, it is unreadable by a non-technical person. It doesn't explain the
context, what is the question(s), and the options to answer; in fact, there should be direct buttons
to deny, approve, approve all, like always. or it is asking for multiple choices, then have buttons to
answer for each of these choices. But the point is, this should be a very well formatted email, with
some graphics from AbstractFramework branding... and being very clear on the context, the date, the
question(s) and the option(s) to answer and with links (as buttons?) to answer from the email itself."

Not done on the spot because answering from an email is a security feature, not a template change:
it needs signed one-time action links, a route that applies the decision as the recipient, expiry
bound to the wait, single use, audit, and a landing page that confirms what was done.

## Current code reality

- `abstractgateway/src/abstractgateway/mail/notifications.py` `render_notice(kind, facts)`: for
  `approval_needed` the facts carry `title` (the run's title, today a node id), `wait_kind`
  (`tool_approval` | `ask_user`), `tools` (names only), `ref` (run id); the HTML body is the text
  wrapped in `<p>` tags. The 0.15.8 test notice (`_render_test_notice`) has the first styled template
  and the safe console-link rule (`_console_link`: configured public origins only, never a raw header).
- The console's approval UI already offers Approve, Deny and **Accept all** for tool calls and the
  choices of an `ask_user` wait; its decision routes live in `routes/gateway.py` (decision handling
  near `_decision…`) and `entity_session_tools.py` (`approve…`, `deny…`); the Watch app uses them.
- Notices are queued with an idempotency key per wait (`enqueue(key, …)`), yet the inbox shows one
  email per retry of the same node: the key must be the wait id, not the attempt.
- The runtime's wait payload (AbstractRuntime, `ask_user` / `tool_approval` waits) carries the
  question text, the choices, the tool name and arguments; the gateway does not pass them to the
  notice today.

## Scope

### In scope

1. **Content.** Subject: `[AbstractFramework] <workflow or entity name> needs your answer` (never a
   node id). Body, in this order: who asks (workflow or entity display name, the automation or session
   it belongs to, who started it), when (the wait's time in the recipient's time zone), what is asked
   (for a tool call: the tool's plain-language label and a readable summary of its arguments, e.g. the
   URL for `fetch_url`, the command for `execute_command`, recipient and subject for `send_email`; for a
   question: the question text and each choice), then the actions, then a short "why you receive this"
   line and the console deep link to that exact wait. Plain-text twin with the same facts and the same
   links as URLs.
2. **Actions from the email.** Buttons that are signed one-time links to
   `GET /api/gateway/email-actions/{token}`: the token (random, stored, not derivable) binds the wait
   id, the decision (`approve`, `deny`, `approve_all`, or `choice:<n>`), the recipient account and an
   expiry equal to the wait's own; a link is single use, applies the decision through the existing
   decision code path as that account (same authorization, same audit line as the console), and lands
   on a small branded page saying what was done, with a link to the console. A used, expired or
   unknown token lands on a page saying so, with the console link; nothing else is revealed. No GET
   with side effects from a mail client's prefetch: the landing page confirms with one click
   (`POST`), the email button only opens it.
3. **Branding.** One shared HTML template for every notice kind (test, approval, result, failed):
   AbstractFramework wordmark and colours inline (no remote images, no tracking), readable in light and
   dark mail clients, buttons as bulletproof table links, text version always present.
4. **One email per wait.** Idempotency key = wait id; a retry of the same node re-uses the wait and
   sends nothing new; a decision taken in the console invalidates the email's tokens.
5. Settings: the existing "Approval needed" notification switch covers it; no new setting.

### Out of scope

- Replying to the email as a way to answer (mail ingestion stays out; the Reply-To note remains).
- Notifications for channels other than email (the Watch and the consoles already show the wait).

## Acceptance criteria

- [ ] An `ask_user` wait with three choices produces one email naming the entity, the time, the
      question and three buttons; clicking one and confirming applies that choice to the run as the
      recipient, and the run continues; the email's other links then land on "already answered".
- [ ] A `tool_approval` wait produces Approve / Deny / Approve all with the tool's label and a
      readable argument summary; Approve all behaves exactly like the console's Accept all.
- [ ] Tokens expire with the wait, are single use, and are refused for any other account; every
      decision is audited like a console decision.
- [ ] Eight retries of the same node produce one email.
- [ ] The HTML renders without remote resources; the text part carries the same facts and links.
- [ ] Tests: renderer facts, token lifecycle (use, reuse, expiry, wrong account), decision application,
      idempotency per wait; a browser test of the landing page.

## Dependencies, ADR state and next step

Depends on the runtime wait payload exposing the question, choices and tool arguments to the gateway
(check `abstractruntime` wait records; add a typed projection if the gateway only sees names today).
ADR impact: none expected (the decision path and its authorization are reused); if the signed-link
token store needs a durable policy for expiry or audit, write it as an ADR before implementing.
First step: an agent reads the two decision routes and the wait payload, then implements 1-5 in a
gateway worktree with the tests above.
