# Independent adversarial review

## 2026-10-31 — Final rendering, scheduling, context and cache review

Execution: same independent adversarial reviewer; no subagents/source edits/publishing/Apple changes. Current core source13e81e09b65e28b84b4dfa4ce58313bf0d5ee4bc5f8478baa582d084b5e8d059, Wasmd576a6a584f09c6b9a124c93476c7a73a69ae9e147014e2d26dda5974273c067.

Observed independently: Rust core15 pass; artifact/source checker passes; all569 Apple tracked hashes preserved and Apple git trees clean. Read premultiplied source-over/additive RGBA, bounded antialiasing and surfaces; inspected matched five-design ×seven-state before/after sheets. Wave/Hover/Rings/Eye significantly richer; Halo fuller. No Swift pixel-equivalence claim.

UIC negative tests: abort while Wasm compilation held creates no canvas or handle;32 invalid-palette construction failures leak no handles; shared-module16-handle limit enforced and recovered after disposal. Actual Chromium gallery: moving all canvases5000px offscreen stops painting through real IntersectionObserver and restoring resumes; synthetic document.hidden/visibilitychange stops/resumes; actual host theme-button pointerdown not prevented; no JS errors. Parent complete current-module44×7/quality/DPR/lifecycle browser receipt consumed. High512px presentation is CPU-expensive/opt-in; native matched160px median0.839→1.857ms is richer rendering, not an across-the-board speedup.

Context blocker found and fixed: malformed mutable ContentHit head could panic unchecked drag range slice. Shared hit validation and source.get now guard it, clear owned capture, and avoid RefCell guard crossing clear. Independently rerun TUI9 source-selection tests +8 real Driver tests and Code8 full-root tests: all pass. External /tmp/avatar-adversary-selection probe covers later plain/formatted words, combining marks, emoji/CJK/bidi controls, wrapping, Word→Sentence→Word original anchoring, invalid UTF8/overflow hit mutation, and actual cross-table drag/context clearing. Code only stages quoted context into preserved draft; explicit normal submit remains required. Custom user-card/tool/JSON drawing remains unmapped screen-copy fallback under1086.

Final TUI cache: full key includes style/pose/normalized audio/time/gaze/cols/rows/resolved mosaic mode/material tokens/transparency. Early cache-hit return precedes Frame construction, sampling and mosaic conversion. Placement omitted correctly. Theme owns packed material ramps; graphics owns final RGBA composition. Independently22 Avatar tests pass including five forced full-tree repaint cache hits and theme/size/mode/transparency/clock/gaze/hidden invalidation and underlay restoration; both widget lints +theme material test pass from newly compiled feature-enabled binary. No blocker remains.

ADR0044/1083/1084 preserve canonical visit/work/personal/sleep, separate optional sleep stage/activity/expression/persona, leave authority outside visuals and keep v1 stable.1085 correctly defers widget-owned native terminal images until clipping/occlusion custody is designed.

Final verdict: Approved for current local source/integration scope. This is not registry publication, signed desktop deployment, unsupported-platform validation, GPU/battery-efficiency, exact Swift visual parity, or semantic selection of arbitrary custom drawing approval.
