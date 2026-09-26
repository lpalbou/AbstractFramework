# 0919 — `analyze_code` can crash the process on Python 3.9 (unclosed triple-quoted string in a truncated file)

- **Status:** proposed
- **Created:** 2026-09-26
- **Area:** abstractcore (tools)

## Summary
During the 2.16.0 release, the Python 3.9 CI job segfaulted inside CPython's `ast.parse` in
`test_a_syntax_error_on_a_file_this_tool_cut_says_so` (only after a large part of the suite had run; passes alone). It is a
CPython 3.9 parser bug on a truncated file that ends inside an unclosed `"""`, not a regression; the test is now skipped on 3.9
(abstractcore f1735a1), so nothing catches a process crash of `analyze_code` on 3.9.

## Scope
Guard `analyze_code` on Python < 3.10: pre-check the truncated source for an unclosed triple quote (tokenize) and report the
syntax error without calling `ast.parse`, or run the parse in a subprocess on 3.9. Re-enable the test on 3.9.

## Evidence
untracked/missions-2026-09-25/RELEASE-LOG.md (Phase A, abstractcore runs 36228220898 / 36229322053).

## Validation
The 3.9 job runs the test again and stays green across the full suite.
