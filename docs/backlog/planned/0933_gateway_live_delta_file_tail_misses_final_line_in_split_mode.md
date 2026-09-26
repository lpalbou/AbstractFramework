# 0933 — Gateway split mode: the live-delta file tail can miss the runner's final line (delta_end never seen)

- **Status:** planned (not started; pre-existing in 0.5.0 and 0.5.1)
- **Created:** 2026-09-27
- **Area:** abstractgateway (`live_deltas.py`, `_FileTail.read_lines`)

## Summary
When the gateway's API and runner run as separate processes, the API-side subscriber tails the runner's live-delta file. `_FileTail.read_lines`
can close the file before reading the last line the runner wrote, and that line is the `llm.delta_end` that marks the run's stream as
finished, so a subscriber may never see the end of a streamed reply. Surfaced by the flaky test
`tests/test_live_deltas_hub.py::test_api_role_subscription_tails_the_runner_file` (failed 2 of 8 CI jobs on 2026-09-26; passes on rerun).

## Scope
Read the open file once more before closing it in `_FileTail.read_lines`; make the test deterministic (write the final line, then assert
the subscriber receives `delta_end` without relying on timing). Out of scope: changing the split-mode transport.

## Validation
The test passes 20/20 in a loop; a deliberate removal of the extra read turns it red deterministically.

## Related
0932 (release trace where it surfaced); streaming design (abstractgateway 0.5.0 `LiveDeltaHub`).
