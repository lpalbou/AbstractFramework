# 1035 — Cycle graph and tool call details

Implementation is local and uncommitted. Scope is the iPhone app and its AssistantKit/client
fixtures; no Gateway/Runtime endpoint or deployment changes were required.

## Behavior and inspection

- Cycles opens **Agent cycles**, a connected progression within each agent run. Model details,
  times and public outputs expand inside cards; tools/approvals attach to the preceding cycle
  within the same run. Parallel runs have independent lanes. Routing/generation is separate.
- Tools opens **Tool calls**, an individual searchable call collection. Each row expands to
  timing, recorded input, public output and owning step/run. Multiple/repeated calls preserve
  their identities and numbers under search. Missing input is distinct from explicit `{}`.
- Approval hands remain amber after resolution. Tool icons are lavender throughout relevant
  app actions and live/history detail; failed status stays red independently of tool identity.
- Structured credential fields are hidden recursively before display. Raw malformed arguments,
  private control fields and model reasoning are not shown. Redaction does not inspect secrets
  embedded in ordinary command/URL/document strings. Display truncation is explicit.

Inspected native screenshots:

- [Connected cycles and resolved amber approval](cycle-graph.png)
- [Expanded cycle with public output and timing](cycle-expanded.png)
- [Tool collection](tool-list.png)
- [Redacted tool input and public output](tool-input-output.png)
- [Failed tool: lavender identity, separate red status](tool-failure.png)
- [Routing/generation history remains expandable](generation-details.png)
- [Live tool input/output remains available](live-tool-details.png)

## Validation

**228 package tests passed** (152 AssistantKit + 76 AbstractGatewayClient). Five new tests
exercise independent agent lanes, repeated provider call IDs, preserved start/completion
association, missing/explicit-empty inputs, nested credential fields, malformed JSON, bounded
formatting, retained cycle ordinals and late completion after eviction.
[Package log](package-tests.log).

Final native simulator run: **3 passed, 0 failed, no runtime warnings**.
[Summary](native-summary.json), [log](native-verified.log).
The initial run exposed a parent accessibility identifier overriding child disclosure IDs;
removed it. A subsequent media regression tapped a moving row during collapse animation;
settled that transition before tapping. Both failed iterations are retained in
[native-initial.log](native-initial.log) and
[native-navigation-pass-media-race.log](native-navigation-pass-media-race.log).
Apple SDK build/version diagnostics remain present in logs; final XCTest runtimeWarnings is empty.

[Independent source/native review](adversarial-review.md): Approved with retention/wording
findings adopted. Physical verification and installation receipts are appended below.

## Reproduction

From `abstractassistant`:

```sh
swift test --package-path phone/iphone/Packages/AssistantKit --jobs 1
python3 phone/iphone/scripts/build.py --ui-test SIMULATOR_ID \
  --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testCycleGraphAndToolCallsHaveDistinctDestinationsAndDetails \
  --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testHistoricalActivityExplainsRoutingAndMediaWithTime \
  --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testLiveActivityExpandsAndShowsToolResults
python3 phone/iphone/scripts/build.py --live-media-test DEVICE_ID --team TEAM_ID \
  --only-testing AbstractAssistantPhoneTests/LiveGatewayMediaTests/testSavedCycleGraphAndToolInputs
```

The physical test is opt-in/read-only and uses the phone’s saved connection; credentials stay
in its Keychain. Only aggregate counts are exported. No new agent run, tool execution or media
request is created. All native jobs used the one-job iPhone guard and isolated DerivedData;
Watch source and build products were not modified.

## Physical saved-history proof

The named physical iPhone test passed: **12 cycles, four tool calls, four calls with recorded
input, four approvals, zero history issues**. [Counts](device-history-counts.json),
[XCTest summary](device-summary.json), [build/test log](device-test.log).
The test verified that every grouped tool belongs to the graph lane’s run and cycle ID.
It read saved history only; it did not execute an agent or tool.

The hosted test launch reports the existing AVAudioSession main-thread activation warning.
No activity assertion or history request failed; this task does not claim to fix that audio
startup warning. Device compilation also reports existing Swift optional-pattern and Apple
SDK version diagnostics. The final simulator tests report no XCTest runtime warnings.

## Normal device installation

Normal signed **0.6.16 (24)** built successfully, with no test PlugIns in its bundle.
[App metadata](normal-app.json), [normal build](normal-build.log).
Installation and launch both returned success on the named iPhone:
[install receipt](install.json), [launch receipt](launch.json).
The test-hosted app was replaced by this normal build. Changes remain uncommitted.
