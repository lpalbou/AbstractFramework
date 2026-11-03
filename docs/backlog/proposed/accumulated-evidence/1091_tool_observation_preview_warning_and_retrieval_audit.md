# 1091 — Tool observation preview warning and retrieval audit

> Package: abstractcore, abstractruntime, abstractagent, abstractgateway, abstractcode
> Type: task
> Created: 2026-10-31
> Status: proposed
> Priority: P1
> Labels: decision-gate, awaiting-user-confirmation, adr-0026, tool-results, observability
> Work-item id: abstractframework-1091
> Owner: framework

## Summary

OPERATOR DECISION GATE (never assignable): audit preview/selection warnings and full-output access
from tool production through the model-visible observation and user view. **Requires user
confirmation before implementation.** Coordinate the existing authorized 0961 source fix without
resetting its prior operator ruling or claiming that every preview is currently silent.

## Current code reality

- Core `tools/common_tools.py:execute_command` bounds rendered stdout/stderr at 20,000/5,000
  characters. It appends explicit truncation prose and returns `stdout_truncated` /
  `stderr_truncated` plus full streams. A log warning is not the only ADR-permitted signal.
- The local `_truncate`/`_keep_tail` helpers need an ADR-0026 source-tag audit; not every clipping
  site currently carries the literal `#[WARNING:TRUNCATION]` next to its implementation.
- Runtime EvidenceRecorder stores command streams as artifacts and adds references; ReAct prefers
  `output.rendered`. Structured flags/references do not automatically accompany that text into
  the next model call. Verify end-to-end visibility/retrieval rather than infer it from storage.
- EvidenceRecorder has a three-tool default allowlist, not universal coverage for skim/search/list.
- Example run command outputs were NOT truncated. Its other tools returned bounded inventories,
  search slices and degraded web leads. These policies need their own accurate scope/limit wording.
- Agent's independent 200k-character structural clamp is already tracked in 0961, with the
  2026-10-08 ruling to fix binary/oversize results at source before removing the clamp.

## Proposed scope

Trace one oversized stdout/stderr result, a large search/skim result and an artifact-backed result
through producer, durable evidence, observation formatting, payload sanitization, Gateway and WUI.
Check attribution (component/configured cause), marker/flag survival, an actionable full-output
handle, retrieval authorization and absence of unlabelled content loss. Distinguish omitted items
from sliced item content and declared degraded retrieval. Record actual cut sites and exact sizes.

Memory/extraction/provenance critical paths must follow ADR 0026: do not feed an incomplete preview
as if it were the full source. Chunk/read the durable source or explicitly retain partial coverage.
Do not silently remove all limits or force arbitrarily large model prompts as a preview repair.

## Acceptance criteria

- [ ] User confirms the audit/implementation scope before product changes.
- [ ] Every audited lossy site has the ADR tag and an attributable observable warning.
- [ ] Exact preview/full sizes, omission cause and reference to retrievable full content survive.
- [ ] The acting model can discover partial content and request authorized full content explicitly.
- [ ] Backend/UI consumers retain flags without requiring nontechnical users to read raw logs.
- [ ] Critical structured extraction refuses or handles incomplete inputs without false completeness.
- [ ] Results are folded into 0961 when overlapping; no competing clamp-removal mandate is created.

## Testing

After confirmation: `python -m pytest abstractruntime/tests/test_evidence_recorder.py abstractruntime/tests/test_evidence_recorder_post_policy_envelope.py`
and `python -m pytest abstractagent/tests/test_react_loop_truncated_output_retry.py`.
Add an end-to-end observation/payload test with stdout >20k, stderr >5k, timeout tail, search limits,
artifact retrieval and a model-visible warning assertion. Verify untruncated small results stay intact.

## Dependencies, promotion and ADR state

Accepted root ADR 0026 applies unchanged. Existing 0961 remains its own authorized scope; this new
proposal does not revoke or broaden it. See 1088/1089 for presentation/extraction consequences.
The registered `adr` skill already exists in AbstractSkill with a validation record; no duplicate
registration is needed. No new ADR, exception or warning-policy relaxation is adopted here.

## Receipts

Current source inspection and exact-run measurements: `../../evidence/1088/README.md`.
