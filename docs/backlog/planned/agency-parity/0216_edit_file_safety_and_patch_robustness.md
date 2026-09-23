# 0216 — edit_file Safety and Patch Robustness

**Status**: Implemented + tested (2026-07-07); follow-ups resolved 2026-07-08
**Date**: 2026-07-07
**Priority**: High (silent-corruption risk + weak-model edit reliability)
**Components**: abstractcore (common_tools edit_file, unified-diff apply, lint/parse guards)

## Summary
Make `edit_file` safe-by-default and its patch application robust: a single replacement by default
with an ambiguity failure instead of silent replace-all, context-anchored + offset-tolerant
unified-diff application, and pre-write parse-refuse extended beyond Python.

## ADR status
- Governing ADRs: ADR-0016 (tool-calling pipeline), ADR-0026 (no silent behavior on budget/limits).
- ADR impact: None expected.

## Context / current code reality
Verified 2026-07-07:
- `edit_file` (`common_tools.py:7097`) supports literal find/replace, regex, range-replace, and a
  single-file unified-diff mode (`replacement=None` → `pattern` is the patch, `:7226-7267`).
- **`max_replacements` defaults to `-1` (replace ALL)** (`:7102`). Every doc example overrides to 1,
  but the default silently rewrites every occurrence of an ambiguous literal pattern.
- Unified-diff apply is hand-rolled: `_parse_unified_diff` (`:6754`), `_apply_unified_diff`
  (`:6808`). It positions by the hunk `old_start` line number and requires **exact** context/removal
  lines with **no offset fuzzing** (`:6833-6847`) → drifted line numbers produce "Context mismatch".
- Pre-write safety: Python edits are refused if they introduce a `SyntaxError` via `ast.parse`
  (`:7192-7199, 7549-7601`), with a one-shot indentation auto-repair. Other languages get a
  ruff/regex "lint notice" only, no hard refuse.
- `flexible_whitespace=True` (`:7107`) already retries indentation-insensitive matching on exact-
  match failure (`:7422-7439`).

## Problem
1. Replace-all default can silently corrupt a file when the model gives an ambiguous pattern.
2. Line-number-anchored, non-fuzzy diff application fails on the line-drift weak models routinely
   produce, wasting iterations ("Context mismatch").
3. Parse-refuse (a genuine strength over Codex) covers only Python; JSON/YAML/other broken edits go
   through.

## What we want to do
Default to a single, unambiguous replacement; locate diff hunks by matching context (not trusting
header line numbers) with bounded offset tolerance; and extend cheap pre-write validation to more
formats.

## Requirements
1. **Default `max_replacements=1`.** If a literal/regex pattern matches multiple sites and the caller
   did not explicitly opt into "all", **fail with a clear message** naming the match count and asking
   for more unique context — never silently replace all. Keep an explicit opt-in for all-occurrences.
2. **Context-anchored diff application**: locate each hunk by matching its context/removal lines in
   the file, ignoring the header line numbers; tolerate ±N line offset; reuse the existing
   whitespace-flexible matching. Only fall back to strict positioning when context is genuinely
   ambiguous, and report why on failure.
3. **Extend parse-refuse**: add stdlib-based pre-write validation for JSON and YAML (refuse edits
   that make them unparseable), and keep the pluggable path for other languages. Preserve the Python
   `ast` guard and indentation auto-repair.
4. Any bounded preview/notice must follow ADR-0026 marking.

## Non-goals
- Not adopting a full Lark grammar for patches (Codex parity is the goal, not the exact mechanism);
  context-anchored application is sufficient and simpler.
- Not changing `write_file` full-file semantics.
- Weak-model string→type coercion for `use_regex`/`preview_only` is covered by item **039** (arg
  coercion), not duplicated here — but this item must not regress once 039 lands.

## Dependencies and related tasks
- **039** (arg coercion) — the `use_regex="false"`/`preview_only="false"` truthiness bug is fixed
  there; coordinate so `edit_file` receives correctly typed args.
- Shares `common_tools.py` with 0215 (execute_command) — coordinate.

## Expected outcomes
- An ambiguous single-pattern edit fails safely instead of rewriting all matches.
- A unified diff with slightly wrong line numbers still applies via context matching.
- A JSON/YAML edit that would break parsing is refused pre-write, like Python today.

## Validation
- Unit: pattern matching 3 sites with default args → error naming count, file unchanged; same with
  explicit all-occurrences → all replaced. Diff with header line numbers off by ±3 but correct
  context → applies. JSON edit introducing a syntax error → refused, file unchanged.
- Live (endpoint `http://127.0.0.1:8317/v1`): a multi-edit task on a real file with a weak model;
  measure edit success rate + retries before vs after.

## Progress checklist
- [x] Default max_replacements=None → exactly-one-match required; ambiguity failure names count +
      line numbers; explicit -1/0 = all; N >= 1 = first N. (33 tests in
      `test_common_tools_edit_file_safety_and_patch_robustness.py`.)
- [x] Context-anchored, offset-tolerant diff application (`_find_hunk_anchor`: unique-match at any
      offset; header positioning + bounded ±200-line tolerance only for ambiguity; whitespace-
      flexible retry tier; actionable failure reasons).
- [x] JSON/YAML pre-write parse-refuse (`_EDIT_FILE_PARSE_GUARDS`); Python `ast` guard +
      indentation auto-repair preserved.
- [x] FOLLOW-UP RESOLVED (2026-07-08, maintainer-directed): **CRLF preservation** — reads now keep
      real line endings (`newline=""`), matching runs on LF-normalized text, and the file's
      dominant style is restored at the write boundary (both find/replace and diff writes, with
      `newline=""` so Windows never double-translates). CRLF files stay CRLF; mixed-endings files
      normalize to the dominant style with an explicit note; CRLF patterns match; preview never
      writes; the Python syntax guard still fires on CRLF files.
- [x] FOLLOW-UP RESOLVED (2026-07-08): **`-- `-prefixed deletion lines** — the hunk-body collector
      counts old-side lines against the header-declared old_len and only treats a `--- ` line as a
      new file header once the old side is consumed. Deleting SQL/Lua `-- comment` lines and `---`
      markdown rules now applies; genuine multi-file diffs are still refused. (Counts stay hints
      for anchoring; they only arbitrate this prefix collision, and a miscount fails safe.)
      12 tests in `test_common_tools_edit_file_crlf_and_dash_lines.py`; full edit_file corpus
      68 passed; abstractcore tools suite 279 passed.
- [ ] Live success-rate A/B on a weak model (deferred; the 0220 live wave exercised edit-adjacent
      flows but not an edit_file-specific success-rate comparison).

## Guidance for the implementing agent
Preserve the existing Python `ast` refuse + indentation auto-repair (a real strength). Coordinate
`common_tools.py` edits with 0215 and rely on 039 for typed args.
