# 0221 — Unified Prompt-Caching Strategy (widest provider compatibility)

**Status**: Wave 1 implemented + live-verified (2026-07-08); waves 2-3 planned
**Date**: 2026-07-08
**Priority**: High (cost + latency + fleet LLM capacity)
**Components**: abstractcore (providers, model_capabilities assets), abstractruntime (key derivation — already correct), abstractgateway (endpoint profiles, wave 2)

## Summary
One caching strategy that works across OpenAI, Anthropic, OpenRouter, OVH/vLLM, LM Studio,
Ollama, and local MLX/GGUF. Grounded in an adversarial design review (2 sub-agents; one report
delivered, its audit half re-verified in code) plus live falsification tests. The core insight:
**mechanism knowledge belongs on the provider class** (each mechanism IS an implementation);
the model registry carries only tuning values; endpoint quirks (OVH rejecting the key field)
belong in endpoint profiles/learned markers — the same model served by OVH vs self-hosted vLLM
behaves differently, so a model-keyed design cannot express the truth.

## Mechanism matrix (per-row evidence labels — CORRECTED per audit: "verified" previously
## covered rows that are documentation inference)
- LIVE-verified rows: OpenAI (real cached_tokens), Anthropic (haiku-4.5 only; n=2-3 falsification
  calls; TTL and 1h tier doc-only), OVH field-rejection (the 400 + drop-retry, live).
- DOC-INFERENCE rows (no live cache measurement exists): OVH/vLLM server-side APC actually
  producing hits, LM Studio/llama.cpp slot reuse, Ollama context reuse, OpenRouter pass-through.
  Treat these as expectations until a live probe lands (wave 2).
- **OpenAI**: implicit prefix caching >= 1024 tokens; `prompt_cache_key` is an official routing
  field (forwarded); hits in `prompt_tokens_details.cached_tokens`. LIVE: 60.9% of input served
  from cache in a real ReAct run (gpt-5-mini, 2026-07-08).
- **Anthropic**: EXPLICIT `cache_control` breakpoints (<=4), ~5min TTL refreshed on hit; writes
  1.25x, reads 0.1x. See "Wave 1 findings" — the old mapping was an active cost increase.
- **OpenRouter**: inherits openai_compatible (key forwarded); Anthropic-via-OpenRouter caching
  is OFF today (no cache_control injection) — wave 3.
- **OVH / vLLM**: server-side automatic prefix caching, no request field; OVH 400-rejects
  `prompt_cache_key` (drop-retry-suppress fallback shipped 2026-07-08).
- **LM Studio / llama.cpp / Ollama**: server-side prefix/slot reuse; nothing to send; byte-stable
  prefix (0212) is the whole contract.
- **Local MLX / HF / GGUF**: framework-owned KV control plane keyed by `prompt_cache_key`
  (blocs, exact renderers) — already shipped, unchanged.

## Doc-verified facts (platform.claude.com + developers.openai.com, checked 2026-07-08)
- Anthropic pricing: 5m write 1.25x, 1h write 2x, read 0.1x — "caching pays off after just one
  cache read for the 5-minute duration". TTL refreshed on hit.
- Anthropic minimum cacheable prompt: **4,096 tokens for Haiku 4.5** (and Opus 4.5/4.6),
  1,024 for Sonnet 4.5/4.6/5 + Opus 4.8, 2,048 for Haiku 3.5. Below minimum: request runs
  normally, nothing cached, `cache_creation_input_tokens=0` — explains the earlier 2.8k-token
  "no-op" observation. Motivates the `prompt_cache_min_tokens` registry field (wave 2).
- Anthropic's own docs describe the exact trap the old code hit: "Automatic caching
  [top-level cache_control] places the breakpoint on the last cacheable block, which in this
  structure is the one that changes every request... place the breakpoint at the end of the
  static prefix, not on the varying block." Our head breakpoint is the documented fix.
- Anthropic budget: max 4 breakpoints; a 5th is an API 400 → the provider now DEFERS to any
  caller-placed cache_control (system/messages/tools scanned) before adding its own.
- 20-block lookback: hits are found within 20 positions behind a breakpoint — head-only
  placement is immune (the head is one boundary); matters for wave-3 roving message
  breakpoints.
- OpenAI: implicit caching >=1024 tokens, hits in 128-token increments; `prompt_cache_key`
  is combined with the ~256-token prefix hash for ROUTING stickiness (a coding customer went
  60%→87% hit rate adding it); **~15 requests/min per prefix+key** before overflow to other
  machines (each = one cold miss). Session-scoped keys keep per-key RPM naturally low —
  relevant to fleet admission (entity-society thread).

## Operational proof through the REAL ReAct loop (2026-07-08)
- **Anthropic haiku-4.5** (full default toolset → 5,022-token stable head, above the 4,096
  minimum): call 1 `cache_write_tokens=5022`; calls 2-3 `cached_input_tokens=5022` each.
  Net token-equivalent saved vs uncached: **+7,784** on a 3-call run (0.9×reads − 0.25×writes).
  Cost-safety [CORRECTED per adversarial review — TTL blind spot]: the write premium is paid
  once per session **per 5-minute-TTL window** (the TTL refreshes on hit, so back-to-back agent
  turns keep one write; but any inter-call gap > TTL — ask_user waits, tool-approval modals,
  human-paced sessions — re-pays the 1.25× head write with no intervening read). A gap-heavy
  session degenerates toward write-per-gap; break-even needs ≥1 read within each TTL window.
  The measured +7,784 is the back-to-back best case. Consequence for wave 2: the
  "write >> read" alarm must be cadence-aware (gap-adjusted), or it will fire on healthy code
  in slow sessions.
- **OpenAI gpt-5-mini** (same loop): cached_input_tokens 0 → 2560 → 2688 → 2816 — GROWING
  with history (deep-history reuse works; the 0212 "plateau" nuance was block-rounding on
  small growth, corrected there).
- Heads BELOW the model minimum (e.g. 3-tool agents on haiku): silent no-op, zero extra cost,
  zero benefit — by Anthropic design; wave-2 registry field will make this predictable.

## Full call-site audit (adversarial subagent, 2026-07-08 — maintainer-ordered)
CACHED (per-call session-scoped key via the runtime LLM_CALL handler, pipeline verified into
provider requests): flagship ReAct, VisualFlow llm_call/agent nodes, AbstractFlow authoring,
AbstractCode (`_runtime.prompt_cache` modes), AbstractAssistant local host. CACHED (instance
default via `prompt_cache_set(key, make_default=True)`, `base.py:5019`): `CachedSession`
(auto key), `acore` CLI. PER-REQUEST FORWARDING (correct for shared instances): AbstractCore
Server `/chat/completions` + `/v1/responses`, AbstractEndpoint.

UNCACHED on hosted providers (top 3 by volume):
1. **Entity loops** (`identity/chat.py:801/860/903/1174` generate bare; `life.py:1139-1146`;
   gateway `entity_chat.py:84-91` adapter passes `params=None`). CRITICAL NUANCE: a key alone
   is INSUFFICIENT — the driver mutates the system head every turn (`chat.py:786-796`,
   presence + MEMORIES block before history), so OpenAI prefix dies at byte 1 and an Anthropic
   head breakpoint would RE-WRITE at 1.25x per turn (the exact leak class fixed tonight).
   Fix = stable head restructure (runtime lane, flagged on agora) + key.
2. **MEMORY_COMPACT summarization** (`factory.py:199-203` hands the SHARED agent provider to
   BasicSummarizer; map-reduce re-sends instruction prefixes per chunk, uncached).
3. **SmartNote ingest** (`smartnote/gateway/ingest.py:244+`, per-chunk repeated prefixes).

`create_llm` construction-param verdict (audit + design-attack subagents, converged): hybrid,
A-primary. IMPLEMENTED 2026-07-08: `create_llm(..., prompt_cache_key="...")` is consumed by the
provider registry (never reaches provider `__init__`) and sets the instance default via
`prompt_cache_set(key, make_default=True)` with a direct-slot fallback for keyed providers and
a `#FALLBACK` warning (never an error) when the provider/model lacks caching. Explicit per-call
keys still win, including explicit `None` (`base.py:4952-4955`; test-pinned). GUARD implemented:
`MultiLocalAbstractCoreLLMClient._create_client` STRIPS `prompt_cache_key` from pooled
llm_kwargs with a `#FALLBACK` warning (pooled instances serve all runs/sessions; per-call
injection is their contract; `llm_client.py`). 5 new tests; providers 376 + runtime 944 green.
The design attack's honest verdict on cross-session key sharing: benign-to-suboptimal on
OpenAI (routing-only) and Anthropic (key value never sent — it only enables breakpoints);
the ONE real correctness hazard is MLX's shared mutable KV cache, which the strip-guard and
session-scoped derivation both protect.
ENTITY LANES NOT WIRED YET, deliberately: the audit proved the entity system head mutates
every turn (`chat.py:786-796`), so a key alone buys nothing on OpenAI and would COST on
Anthropic (head re-write per turn). Runtime owns the prelude restructure (flagged on agora,
entity-society seq 22); the one-kwarg wiring lands after it.

## Silent-skip traps (audit finds; wave-2 hardening candidates)
- No `session_id` → derived injection silently skips (`effect_handlers.py:918-919`); raw REST
  starts without session_id run full-price with no warning.
- OVH rejection latch is instance-lifetime: one misbehaving server de-keys a POOLED gateway
  client until restart (`openai_compatible_provider.py:519-523`); `#FALLBACK` warns once.
- Anthropic `supports_prompt_cache()` is a model-name substring allowlist
  (`anthropic_provider.py:1129-1150`) — unmatched future model ids silently disable caching.
- `prompt_cache_binding` without `key` suppresses injection (`effect_handlers.py:874-875`);
  explicit empty-string key disables caching and wins over defaults (`base.py:4952-4955`) —
  reachable from flow pins.
- CachedSession downgrades to `off` silently if prefix prep fails (`cached_session.py:305-308`).
- Non-text outputs skip injection by design (`effect_handlers.py:1272-1273`).

## Known gaps (recorded, not silent)
- Anthropic ASYNC streaming never reported usage at all (pre-existing, chunk-level yields);
  sync streaming now normalized.
- OpenRouter+Anthropic models: still uncached (wave 3).

## Wave 1 — DONE (2026-07-08, live-verified)
1. **Anthropic cache usage extraction** (was: `cache_read_input_tokens`/`cache_creation_input_tokens`
   DROPPED — caching unprovable and input undercounted since Anthropic's `input_tokens` excludes
   cache traffic). Now `_build_usage_dict` reports inclusive `input_tokens` + normalized keys.
2. **Normalized cross-provider usage keys**: `cached_input_tokens` (read) + `cache_write_tokens`
   (write premium) on Anthropic, OpenAI, and OpenAI-compatible (when the server reports details).
   Contract: ABSENT means "mechanism cannot report", 0 means "measured zero" — regression tooling
   must not conflate them.
3. **Anthropic breakpoint fix** (the money leak). LIVE FALSIFICATION (haiku-4.5, ~30k tokens total):
   - OLD top-level `cache_control` param, agent-loop shape (volatile trailing message):
     call 1 write=7,042 read=0; call 2 write=7,043 read=0 — **full-prompt write premium every
     call, never a read**. Below the model's min cacheable size: silent no-op (0/0).
   - NEW explicit breakpoint on the last system text block (caches tools+system head; applied
     after tools/system folding, sync + async): call 1 write=6,302 read=0; call 2 write=0
     **read=6,302**. End-to-end through the framework: `cached_input_tokens: 6302` in usage.
   - Messages deliberately NOT marked in v1 (volatile tail cannot be re-read; paying 1.25x on
     it is the exact bug being fixed). 7 unit tests pin the new contract.

## Wave 2 — planned
- Endpoint-profile `send_prompt_cache_key: false` (gateway profile resolution) pre-seeding the
  provider instance marker: the ONLY persistent form of rejection knowledge (operator-declared).
  Learned rejections stay process-local — a wrong persisted negative silently kills key routing
  forever, while re-learning costs one 400 per process (asymmetry rules).
- Per-run cache hit-rate rollup in gateway ledger stats / UI token panels (normalized keys make
  this a sum). Alarm shape: write >> read on Anthropic = breakpoint regression; cached=0 by
  iteration 3 on OpenAI = prefix-stability regression (pair with 0212's structural test).
- Registry tuning fields (`prompt_caching: "supported"|"none"` veto + `prompt_cache_min_tokens`)
  in model_capabilities.json per the `unsupported_parameters` precedent; consumed by breakpoint
  placement. NOT a mechanism enum (provider-class truth; registry rot risk).
- A short caching ADR (crosses 4 packages; none governs it today).

## Wave 3 — only if evidence demands
- Roving message breakpoints (BP3/BP4 pair advancing along the transcript) for deep-history
  Anthropic reuse in long agent sessions — implement only with live write/read ratios proving
  the head-only v1 leaves real money on the table. Same for the OpenAI deep-history cap noted
  in 0212 (cached_tokens plateaus at the static head when volatile tail messages sit between
  history and appends).
- OpenRouter Anthropic-model cache_control injection.
- MLX synthesized cache metrics from KV token counts.

## Do NOT build (over-engineering, per adversarial review)
- Per-model mechanism enums across ~240 registry entries.
- Auto-persisted learned rejections (wrong-negative risk).
- Client-side prefix hashing to predict server hits; response memoization; cross-provider cache
  portability; synthetic metrics for servers that report nothing.

## Validation
- Unit: 7 Anthropic breakpoint/usage tests + 4 rejection-fallback tests + providers suite green
  (371 passed; live-vLLM file skipped, server not local).
- Live: falsification numbers above; OpenAI 60.9% cached (0212 evidence); OVH drop-retry
  verified in the 0220 live wave.
- Anthropic spend for the falsification: ~6 haiku calls, ~40k tokens total (~cents).

## Open questions (flagged, not blocking)
- Anthropic per-model minimum cacheable sizes (haiku-4.5 behaved as >2048 in one probe; the
  registry `prompt_cache_min_tokens` field should carry doc-verified values when wave 2 lands).
- Whether OVH's 400 is vLLM strictness or a fronting gateway (affects wave-2 profile defaults).
- OpenRouter's normalized cache-usage field names (verify before wave 3).
