# 1089 — Public brèves from ordinary agent continuations

> Package: abstractagent, abstractflow, abstractcore, abstractruntime
> Type: feature
> Created: 2026-10-31
> Revised: 2026-10-31
> Status: planned
> Priority: P2
> Labels: conversation, local-inference, prompt-cache
> Work-item id: abstractframework-1089
> Owner: framework

## Summary

Let an enabled avatar-conversation experience emit
short, public brèves about discoveries, choices, reasons and uncertainty in the next ordinary
model continuation. These messages are part of the first useful delivery, not an optional layer
after a tool-card UI. **Implementation authorized by the operator on 2026-11-01.**
Controlled triples and graph persistence remain optional later work in 1090.

## Baseline before implementation

Agent `logic/react.py:format_observation` and `adapters/react_runtime.py:observe_node` deterministically
format tool results. Pending batches drain before reasoning. Semantic brèves therefore need the
actor's next inference or producer-authored content, not a free decode phase inside observe.
The reason path keeps per-cycle scratchpad changes out of the system prefix. Runtime derives
session/provider/model/workflow/node cache keys. Core `docs/prompt-caching.md` documents local
KV/snapshot/fork lanes, including architectures with one mutable snapshot boundary per key.
A divergent sidecar can displace that state. Cache keys alone prove no hit.

## Proposed direction

- Freeze the enabled experience's instruction/output contract at run/turn start. After new
  observations join, allow a bounded public message alongside the normal next actions or final
  answer. Empty output is legal when nothing worth communicating changed.
- Write directly to the person: “I found…”, “I am keeping this option because…”, “I still need
  to check…”. Avoid tool narration, fabricated reasons and claims of completed work before results.
- Keep ordinary brèves nonblocking; explicit questions/approval follow 1093 and existing policy.
- Persist stable run/actor/message identities and support links underneath the plain-language
  view. Distinguish public communication from private reasoning; do not expose raw reasoning fields.
- Preserve original observations; append messages without rewriting the growing system prefix.
  No per-tool model calls, mandatory record-findings tool, or default competing same-key extractor.
- Actor replies after a user correction must express its practical consequence or ask for clarity.
  A transport receipt alone cannot claim the instruction was considered or applied.
- Start with one actor and one chosen local model/backend. Measure task/tool validity, output
  tokens, observed prefix reuse, added latency and memory. Broaden to MLX/HF/GGUF as a second
  validation stage, without blocking the first pilot on every architecture.
- Cancellation, malformed messages, final-answer handling and missed updates preserve honest
  coverage. Source links can be expanded; no source or absence of findings is silently fabricated.

## Alternatives and decision boundary

1. Deterministic activity-only copy remains a startup/waiting fallback, insufficient as the product.
2. Next-normal-continuation public messages are the preferred low-overhead semantic candidate.
3. A separate extraction Flow is reserved for measured quality/backfill needs with isolated cache.

No durable universal schema is chosen before the pilot. Reuse Note's extraction lessons without
its multi-call filing/linking workflow. First-stage output is natural-language communication;
optional controlled assertions are separately gated under 1090.

## Acceptance criteria

- [x] Operator authorized on 2026-11-01: first host/model/resource budget before execution.
- [x] Brèves reflect meaningful discoveries/choices/uncertainty in ordinary adult language.
- [x] Next actions, native tools, questions and final answers remain valid with/without a brève.
- [x] A user correction demonstrably changes subsequent behavior; generic agreement alone fails.
- [x] Original evidence, source linkage, cancellation/final messages and empty deltas remain correct.
- [ ] Pilot records exact hardware/model/build, token/latency/memory metrics and task validity.
- [ ] Stable prefix and cache misses both work correctly; broader backend results are not inferred.

## Testing

Validation: `python -m pytest abstractagent/tests/test_react_prompt_prefix_stability.py abstractagent/tests/test_react_turn_byte_stability.py`.
Run sequential matched baseline/enabled local fixtures for the selected pilot; later repeat on
MLX/HF/GGUF lanes actually supported. Compare semantic correctness, next-action validity, source
recall, added decoding and actual observed reuse. Unavailable metrics are not measured zero.

## Dependencies, non-goals and ADR state

Pair with 1088/1092; questions in 1093. Root ADRs 0007/0009/0026/0043 and Core cache contracts
apply. Permanent public fields need ADR review; 0045 and public-conversation ADR0046 are accepted.
No graph requirement, full-output deletion, hidden reasoning disclosure or implicit consent.

## History and receipts

Initial intake made semantic findings optional after presentation-only cards. The operator's
subsequent request makes authored conversational messages part of the first meaningful
experience; optional triples stay separate. Filename/ID retained. Prior council/run record:
`../../evidence/1088/README.md`. Implementation and a real local-model correction experiment are recorded below.

## Authorization and implementation tracking

The operator authorized development on 2026-11-01 after root checkpoint `30bcc40`. Earlier
confirmation gates are discharged for this scope. Preserve the existing view and add a second
view for agent and entity work. Shared mission/tests/ownership: [implementation record](../../evidence/1088/implementation.md).
No package release or deployment is implied.

## Delivery checkpoint — 2026-11-01

Development is authorized and underway; no further implementation confirmation is pending.
See the [shared implementation/test record](../../evidence/1088/implementation.md) and
[public conversation ADR0046](../../../adr/0046-optional-public-conversation-view.md).
Default chat/technical views remain available. Physical Watch and human usability validation,
and quantitative backend KV/memory comparisons, remain separate from automated/source delivery.
