# 1107 — Compare converts numeric text exactly when the other side is a number or boolean

> Package: AbstractRuntime
> Type: task
> Created: 2026-11-03
> Priority: high
> Labels: flow, compare, typed-values, adr-0049

## Summary

AbstractRuntime 0.17.0's Compare refuses number-vs-text (commit dfc078a). Values arriving at run time as text (start inputs, LLM output, forms) would make flows fail. Decision (architect report `untracked/release-2026-11-03/architect-compare-compat.md`, option B): when one side is a number or boolean, the text side is converted with the exact number grammar (int/float text, ASCII, finite, no `_`, no `0x`, no empty); other text is refused loudly; text-vs-text unchanged. ADR 0049 §6 amended to say so.

## Why

Operator 2026-11-02: "that is stupid, we must have automatic conversion". 806 saved flows and 12 automations on the live gateway were scanned read-only: none compares text with a number today; the exposure is run-time values.

## Scope

### In scope

- `_exact_from_text` next to `_compare_kind` (builtins.py ~439) replacing the refusal loop (~485-492); fixture table in tests/test_visual_compare_typed_values.py shared with Flow; changelog fragment; troubleshooting.md, workflow-bundles.md, llms; ADR 0049 §6 amendment (root).

### Out of scope

- Converting text-vs-text; `None` comparisons (release note only).

## Acceptance criteria

- [ ] `"10" == 10` true, `"abc" < 3` refused with the typed error, text-vs-text unchanged; tests red without the conversion.

## Receipts

- W3 queued 2026-11-03 03:00.
