# Scenario: Email Inbox Agent (IMAP Bridge + SMTP Replies)

Goal: ingest inbound emails as durable events and let a workflow reply (or take actions) with framework-native email tools.

## High-level architecture

- Inbound: gateway email bridge polls IMAP, stores raw + attachments as artifacts, emits `email.message` events into a
  stable `session_id` per thread.
- Outbound: workflows call `send_email` with centralized SMTP defaults (no repeating host/user per tool call).

## Step 1: Configure email accounts on the tool-execution host

Email tools are account-scoped: IMAP/SMTP host/user are configured on the process that executes tools (gateway local
tools, CLI host, or a tool worker).

For the full configuration matrix (env vs YAML vs AbstractCore config), use the canonical guide in the main framework
workspace:
- [Guide: Email integration](../guide/email-integration.md)

## Step 2: Enable the inbound email bridge on the gateway host

Minimum env vars (plus your email account config):

```bash
export ABSTRACT_EMAIL_BRIDGE=1
export ABSTRACT_EMAIL_POLL_SECONDS=60

export ABSTRACT_EMAIL_FLOW_ID="<bundle_id>:<flow_id>"   # autostart/attach a workflow per thread/session
```

Start the gateway with a persistent `ABSTRACTGATEWAY_DATA_DIR` so bridge state survives restarts.

## Step 3: Wire the workflow

Create a workflow that:
1. handles the `email.message` event
2. reads `payload.email.*` (subject/from/body and artifact-backed attachments)
3. optionally opens attachments via `open_attachment(artifact_id=...)`
4. replies with `send_email(to=..., subject=..., body_text=...)`

## Step 4: Test

Send an email into the mailbox. Expected:
- the bridge emits `email.message`
- a session-run starts (or is resumed) for that thread
- your workflow replies via `send_email`
