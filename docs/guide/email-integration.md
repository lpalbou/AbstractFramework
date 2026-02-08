# Email Integration (Inbound IMAP -> Events, Outbound SMTP Defaults)

This guide explains how to use framework-native email tooling:

- Outbound: `send_email` with centralized SMTP defaults (no repeated host/user per call)
- Inbound: gateway email bridge polls IMAP and emits durable `email.message` events into stable sessions, with
  artifact-backed attachments

## Minimal outbound configuration (SMTP defaults)

Configure on the process that executes tools (gateway local tools, CLI host, or tool worker):

```bash
export ABSTRACT_EMAIL_SMTP_HOST="smtp.example.com"
export ABSTRACT_EMAIL_SMTP_USERNAME="me@example.com"
export ABSTRACT_EMAIL_SMTP_PASSWORD_ENV_VAR="EMAIL_PASSWORD"
export EMAIL_PASSWORD="..."
```

Then a minimal tool call can be:

```json
{ "name": "send_email", "arguments": { "to": "you@example.com", "subject": "Hello", "body_text": "Hi!" } }
```

## Minimal inbound configuration (gateway email bridge)

Configure IMAP + enable the bridge on the gateway host:

```bash
export ABSTRACT_EMAIL_BRIDGE=1
export ABSTRACT_EMAIL_IMAP_HOST="imap.example.com"
export ABSTRACT_EMAIL_IMAP_USERNAME="me@example.com"
export ABSTRACT_EMAIL_IMAP_PASSWORD_ENV_VAR="EMAIL_PASSWORD"
export ABSTRACT_EMAIL_POLL_SECONDS=60
```

Recommended for v0: auto-start a workflow per thread/session:

```bash
export ABSTRACT_EMAIL_FLOW_ID="<bundle_id>:<flow_id>"
```

## Workflow wiring

Create a flow that:
1. handles `email.message` (On Event; scope `session`)
2. reads `payload.email.*` (subject/from/body and artifact-backed attachments)
3. optionally opens attachments via `open_attachment(artifact_id=...)`
4. replies with `send_email(...)`

## See also

Gateway maintenance docs mention the bridge and email inbox endpoints:
- https://github.com/lpalbou/abstractgateway/blob/main/docs/maintenance.md

