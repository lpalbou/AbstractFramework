# 1005 — Web search failures lose their cause: self-throttling, a bot block reported as "no results", diagnostics dropped

> Package: abstractruntime, abstractcore, abstractagent
> Type: task
> Created: 2026-10-10
> Priority: high
> Labels: tools, web-search, observability, runtime

## Summary

In a real AbstractCode session, most of an agent's parallel `skim_websearch` / `web_search` calls failed with
"No results found from DuckDuckGo HTML endpoint." Investigation (read-only, 2026-10-10) found four causes
that stack: the runtime's parallel tool execution makes the search tools throttle themselves; the HTML
fallback reports DuckDuckGo's bot challenge as "no results"; the runtime then drops the tool's structured
failure (the real error, the backends tried, the hint), so neither the agent nor the person can tell
"blocked, slow down" from "nothing exists"; and the model narrowed its own searches. The third cause is an
architecture defect that affects every tool reporting failure as a JSON string, not only search.

## Why

Operator, 2026-10-10, on the session screenshot: "Why do we have those 'no results found'? do we have a
problem somewhere in our architecture." Then: "if and only IF it is an easy fix, then fix it now,
otherwise, create a $backlog item for it." Not an easy fix as a whole: three packages, a release of
each, and one design decision (how parallel searches are throttled). Two parts are small (see Scope).

## Evidence

- Session `acode-dd819e7205e8`, run `3f734ef7-ce24-49ce-a96c-fd3bf7ec9d46` (gateway on :8080, read-only
  `GET /runs/{id}/history_bundle`). Cycle 1: seven parallel `skim_websearch` calls, six failed. Cycle 2: six
  parallel `web_search` calls, one failed. The same query succeeded in one call and failed in another.
- What the model received for a failure (tool message in the run's scratchpad):
  `[skim_websearch]: Error: No results found from DuckDuckGo HTML endpoint.` — nothing else.
- Reproduction with the gateway's own Python (`untracked/day-review/deploy/venv`, ddgs 9.16.0,
  abstractcore 2.26.0 from the deploy worktree), one call at a time:
  - `ddgs.text` is nondeterministic: "RTX 4090 24 Go occasion France prix livraison Paris" returned 9 results
    with `timelimit="d"` and raised `DDGSException: No results found.` without a time limit, seconds apart.
  - `site:leboncoin.fr …` raised "No results found." with and without a time limit.
  - With `timelimit="d"`, a `site:ebay.fr` query returned a single `www.bing.com/aclick` ad link. In the
    session, a "successful" eBay search returned only Bing ad links (one advertised wigs).
  - The HTML fallback (`https://duckduckgo.com/html/`, User-Agent `AbstractCore-WebSearch/1.0`): two queries
    answered HTTP 200 with 9–11 result links; one answered **HTTP 202** with an "anomaly" challenge page and
    zero result links. `raise_for_status()` does not raise on 202.

## Current code reality (2026-10-10)

1. **Self-throttling.** `abstractruntime/src/abstractruntime/integrations/abstractcore/tool_executor.py`:
   `web_search` and `skim_websearch` are in `_PARALLEL_SAFE_TOOL_NAMES` (line 34) and run in a thread pool of
   up to `_PARALLEL_TOOL_MAX_WORKERS = 8` (line 54; [0214](agency-parity/0214_parallel_readonly_tool_execution.md), parallel read-only tools). Each call builds
   its own `DDGS()`; ddgs 9.x `backend="auto"` shuffles about a dozen engines (Bing, Brave, Google, Mojeek,
   Yandex, Yahoo, …), always tries Wikipedia and Grokipedia first, then two engines at a time
   (`ddgs/ddgs.py` `_get_engines`, `_search_sync`). One agent cycle therefore fires a dozen or more
   simultaneous scrapes from one IP, then the HTML fallbacks on top.
2. **A bot block reported as "no results".** `abstractcore/abstractcore/tools/common_tools.py` `web_search`
   (line 4507) HTML fallback: `resp.raise_for_status()` (line 4711) lets 202 through; zero `result__a` links
   becomes `error="No results found from DuckDuckGo HTML endpoint."` (line 4777) with the hint "ddgs (the more
   reliable backend) is part of the light install. Repair with: pip install -U abstractcore" (lines 4778,
   4809), which is wrong when ddgs is installed and simply found nothing. ddgs itself raises
   "No results found." both when the query has no match and when every engine it tried answered empty
   (blocked engines often parse as empty); the tool treats that as a backend failure and falls back.
3. **Diagnostics dropped (architecture).** `tool_executor.py` `_error_from_output` (line 390) parses a JSON
   string output, detects `success: false` and returns only its `error`; `_make_result` (line 431) then sets
   `output_json = None if isinstance(output, str) else _jsonable(output)` (line 436): a JSON-string failure
   is treated as "string-only", so the payload (`ddgs_error`, `backend_attempts`, `hint`, `warnings`,
   `params`) is discarded. The agent would show it: `abstractagent/src/abstractagent/adapters/react_runtime.py`
   (around line 3196) renders `_display(output)` for a failed result whose output is a dict, else
   `error`. The run ledger and every UI (the TUI's failed tool row) carry the same bare line.
4. **Model choices** (no code defect): `time_range="d"` (past 24 h) on every price search, `site:` operators
   on marketplaces that search engines index poorly. The tool descriptions do not steer this either way.

## Scope

### In scope

- A. Runtime (`tool_executor.py`): a tool output that is a JSON object string is STRUCTURED output — keep
  the parsed object as the result's `output` on failure as on success, so the agent and the ledger see
  the tool's own explanation. Applies to every tool, with a test per shape (dict, JSON-object string,
  plain "Error: …" string, non-JSON string). Small.
- B. Core (`common_tools.py`): the HTML fallback treats any non-200 answer, or a page with the challenge
  marker and no result links, as BLOCKED, with an error that says so ("DuckDuckGo refused the request
  (HTTP 202 bot challenge): too many searches at once from this machine; retry fewer at a time") and
  no reinstall hint; the reinstall hint only when ddgs failed to import. "ddgs found nothing" and
  "the HTML page was blocked" are distinct outcomes in the payload. Small.
- C. Throttling (needs a decision): how a cycle's searches share the network. Options: run web-search
  tools sequentially (drop them from `_PARALLEL_SAFE_TOOL_NAMES`); a process-wide limit for search tools
  (for example two at a time) shared by all runs on the host; pin ddgs to a fixed engine set instead of
  `auto` (decide which engines, and whether to filter ad links such as `bing.com/aclick`). Measure each
  against the session's query set before choosing.
- D. Tool descriptions: say that `time_range` filters by the search engine's index date and narrows
  results sharply, so it is for news-like queries, not for prices or listings. No heuristics.

### Out of scope

- Rewriting a model's arguments (time_range, `site:`) behind its back.
- A paid search API or a new search provider.
- Retries hidden inside the tool: a refused request is reported as such; the agent decides.

## Acceptance criteria

- [ ] A: a failed `web_search` whose output is a JSON string reaches the agent with its `error`, `hint`,
  `ddgs_error` and `backend_attempts`; the ledger's tool result carries the same object; runtime tests
  cover the four output shapes, and deleting the fix turns them red.
- [ ] B: a stubbed HTTP 202 challenge page yields a "refused / bot challenge" error, not "No results
  found"; a 200 page with zero links yields "no results"; the reinstall hint appears only when ddgs is not
  importable; core tests cover all three.
- [ ] C: an operator decision recorded here; then, the session's 13-query set run as one cycle yields no
  refusal on this machine, measured before and after.
- [ ] D: the `time_range` description updated in core, with the `llms-full` regeneration.
- [ ] Releases in dependency order (core, runtime, agent if touched, then the root pins), each with its own
  operator go (never released without an explicit per-release go).

## Receipts

- Investigation 2026-10-10 (this item's Evidence section); scratch reproduction scripts were in the
  session's job folder and are not kept.
- Related: [0214](agency-parity/0214_parallel_readonly_tool_execution.md) (parallel read-only tool execution, the origin of cause 1), [1004](1004_follow_ups_after_rounds_15_to_17.md).
