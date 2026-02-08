# Telegram Integration (Gateway Bridge + Workflow)

This guide explains how to run a Telegram "permanent contact" that talks to an agent workflow through the gateway:

- Inbound Telegram messages -> gateway emits durable events into a `session_id`
- Outbound replies/files -> workflow calls tools (`send_telegram_message`, `send_telegram_artifact`)
- Attachments -> stored in the ArtifactStore for durable replay

## Security model choices

Telegram has two integration paths:

1. TDLib + Secret Chats (E2EE in transit; recommended)
2. Bot API (easy, not E2EE)

Even with E2EE, messages are decrypted on the gateway host and persisted to durable stores in plaintext by design. Secure
the gateway host and its storage.

## Minimal gateway configuration

Install Telegram support:

```bash
pip install "abstractgateway[telegram]"
```

Set env vars on the gateway host:

```bash
export ABSTRACT_TELEGRAM_BRIDGE=1
export ABSTRACT_ENABLE_TELEGRAM_TOOLS=1
export ABSTRACT_TELEGRAM_FLOW_ID="<bundle_id>:<flow_id>"
```

Start the gateway normally.

## Workflow wiring (VisualFlow)

Create a flow that:
1. waits for `telegram.message` (On Event; scope `session`)
2. extracts `payload.telegram.text` and `payload.telegram.chat_id`
3. generates a reply (Agent/LLM Call)
4. calls `send_telegram_message(chat_id=..., text=...)`

Inbound attachments arrive with an `artifact_id`. Send them back with `send_telegram_artifact(chat_id=..., artifact_id=...)`.

## TDLib notes (E2EE path)

TDLib requires:
- a real Telegram user account for the AI identity
- the TDLib shared library (`tdjson`) installed on the gateway host
- a persistent TDLib session directory (so you authenticate once)

Because TDLib is platform-specific, keep your setup steps close to your deployment scripts. The gateway integration code
and configuration surface live in:
- https://github.com/lpalbou/abstractgateway

