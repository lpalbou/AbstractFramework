# Bug: the OpenAI-compatible gateway drops Anthropic `cache_control`, and two more defects seen on 2026-10-25

Reported by the RAGnarok side after a prompt-caching verification. Gateway under test: `http://127.0.0.1:8080/v1` (abstractgateway, OpenAI-compatible route `openrouter/anthropic/claude-haiku-5.5`). Reference: the same requests sent directly to `https://openrouter.ai/api/v1` with model `anthropic/claude-haiku-5.5`.

## 1. `cache_control` is not forwarded (prompt caching never happens through the gateway)

**Request shape** (OpenAI chat completions; the marker sits inside a system content part, which is the shape both Anthropic and OpenRouter document):

```json
{
  "model": "openrouter/anthropic/claude-haiku-5.5",
  "max_tokens": 16,
  "temperature": 0.1,
  "messages": [
    {"role": "system",
     "content": [{"type": "text", "text": "<static prefix, ~9,700 tokens>",
                  "cache_control": {"type": "ephemeral"}}]},
    {"role": "user", "content": "Reply with the single word: beta."}
  ]
}
```

**Observed through the gateway**, two identical calls a few seconds apart:

| call | prompt_tokens | prompt_tokens_details.cache_write_tokens | prompt_tokens_details.cached_tokens |
|---|---|---|---|
| 1 | 9,759 | 0 | 0 |
| 2 | 9,759 | 0 | 0 |

**Observed directly on openrouter.ai**, same body, same model:

| call | prompt_tokens | cache_write_tokens | cached_tokens | cost |
|---|---|---|---|---|
| 1 | 9,760 | 9,742 | 0 | $0.001222 |
| 2 | 9,759 | 0 | 9,742 | $0.000101 |

Same result on a 1.7k-token prefix (write 1,718 → read 1,718) and a 3k-token one (2,957 → 2,957). So the request is correct and the provider honours it; the gateway either strips `cache_control` from content parts when it rebuilds the message list, or flattens `content` arrays to strings before forwarding. Either way every call pays full price and the gateway's `prompt_tokens_details` reports zeros, which hides the loss.

**Expected:** forward `cache_control` on system and user content parts unchanged (OpenRouter spec: https://openrouter.ai/docs/features/prompt-caching; Anthropic: https://platform.claude.com/docs/en/build-with-claude/prompt-caching), and pass through `prompt_tokens_details.cached_tokens` / `cache_write_tokens` (and `cache_discount` if present) from the upstream response.

**Suggested test:** the two-call pair above against any Anthropic model; assert call 2 reports `cached_tokens > 0`. Minimum cacheable prefix is per model (Haiku 5.5 / Sonnet 5.5 / Opus 5.5: 512 tokens; Haiku 4.5: 4,096).

## 2. HTTP 500 `argument of type 'NoneType' is not iterable` on a short-output JSON request

Request: same shape as above, system prompt = an entity-extraction ontology (~1.9k tokens) asking for a JSON answer, `max_tokens: 60`, `temperature: 0.1`, model `openrouter/anthropic/claude-haiku-5.5`. Reproduced twice, ~2 s after sending (upstream was reached). Direct to openrouter.ai the same request answers 200.

Likely cause: Claude 5.5 spends hidden reasoning tokens; with a small `max_tokens` the upstream reply has `finish_reason: "length"` and `message.content: null` (OpenRouter returns `completion_tokens_details.reasoning_tokens` > 0 and empty content). The gateway then iterates over `content` as if it were a string/list. Expected: pass the reply through as is (content `null` or `""`, `finish_reason: "length"`), never a 500.

## 3. Connections left half-open to the local relay (127.0.0.1:8317)

While the gateway was in use, `lsof` showed an established socket from the `airelays` process to `127.0.0.1:8317` that never closed, and shortly after, the relay started answering `429 ip_temporarily_blocked: Too many invalid authentication attempts from this IP` to every client on the machine, including ones with a valid key. We could not prove the gateway produced the invalid-auth attempts (it may be unrelated retry traffic), but it is the only other process that was talking to the relay at the time. Worth checking: connection reuse/close on error paths, and whether a failed upstream call is retried with a missing or different bearer.

## Environment

- Gateway: abstractgateway at 127.0.0.1:8080, `/v1/models` lists `openrouter/anthropic/claude-haiku-5.5`; `/v1/messages` answers 404 (fine, not needed).
- Client: OpenAI python SDK 1.x via httpx, no streaming, no tools.
- Date: 2026-10-25.
