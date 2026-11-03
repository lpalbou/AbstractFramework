# 1033 — Hamlet voice routing and chat isolation

> Package: abstractassistant, abstractgateway
> Type: bug
> Created: 2026-10-18
> Status: Completed
> Completed: 2026-10-18
> Priority: P1
> Labels: workflow, voice, routing, observability

## Summary

Repair the proven orchestrator voice incident: an explicit Hamlet recording request was
classified as chat and its chat child returned a media-plan JSON instead of generating audio.
Establish whether router-only inputs leak into that child and verify the exact request end to end.

## Why

The operator's 19.25.15 screenshot shows JSON being displayed and read aloud instead of an
audio attachment. This is generation/orchestration failure, not an iPhone audio decoder failure.

## Current code reality

Read-only authenticated phone trace: root `75341816-9c6d-43bd-bd9e-817440752a22`, private
`abstractassistant-orchestrator@0.0.13:c53b1579`, gateway_default selection. `route_call`
returned valid mode=chat at 17:24:56 UTC; ReAct reason child `d7b92191-6bce-4eb7-982e-832efae28e30`
returned the mode=audio plan as plain content at 17:25:00 UTC. No generate_voice node ran.
Canonical schema already excludes audio, and unknown switch paths already connect to chat.
Therefore adding an audio switch case would not repair this incident.

## Scope

### In scope

- Audit router/agent input inheritance, minimal proven graph/prompt repair, regression tests
  through real runtime handlers, immutable new bundle version if necessary.
- Explicit spoken-scene request reaches voice generation and a playable artifact on iPhone.
- Link public timing/route diagnostics to [1032](1032_iphone_timed_expandable_activity.md).

### Out of scope

- Mapping arbitrary audio to speech, changing Watch, committing/publishing packages or
  installing remote Python packages without an established deployment target.

## Acceptance criteria

- [x] Exact incident cause established; router-specific instructions/schema cannot turn chat into a router.
- [x] Exact Hamlet request generates playable spoken audio with available gateway voice capability.
- [x] Ordinary chat remains ordinary chat and invalid structured routes fail or repair visibly.
- [x] Tests, one adversarial review, version/deployment evidence recorded.

## Receipts

- Read-only device test testInspectSavedVoiceIncident passed 2026-10-18; whitelisted report
  `/tmp/iphone-voice-incident.json` (no credentials/system prompts/reasoning exported).
- One existing adversarial reviewer tools_astra auditing graph inheritance and targeted tests.
- ADR impact: no new policy intended; preserve canonical workflow and typed modality contracts.

### Proven router context leak and revision 8 (2026-10-18)

The real VisualFlow LLM handler inherited `use_context=True` from OnFlowStart.
The router had closed its tools and temperature pins but not its context pin.
`make_llm_call_handler` therefore both read earlier conversation messages and
appended the internal router prompt/JSON to `context.messages`, which the chat
subflow then received. The direct child system/tools/schema pins were correct;
conversation contamination is a separate channel. The source regression failed
before the fix with two additional `route_call` context messages.

Revision 8 declares `include_context=False` on the router, preventing both reads
and writes of conversational context without changing the chat agent's own history.
Its routing instructions explicitly include named public-domain dramatic recitations
(such as the Hamlet soliloquy) as voice, never the ambiguous `audio` alias. Whether
the exact live request now classifies correctly still requires the live model proof;
a deterministic fake provider cannot establish semantic classification accuracy.

- New real-handler test: `abstractassistant/tests/basic/test_router_context_isolation.py`.
  Covers inherited defaults, explicit empty tools/no schema, and explicit tools/custom schema;
  asserts original history is unchanged, router messages absent, child settings preserved.
- Before failure: `/tmp/router-context-before.log`.
- After: 17 targeted source tests pass (`/tmp/router-context-after.log`).
- Extracted deployed Runtime 0.10.3 / Core 2.26.3: six isolation/voice tests pass
  (`/tmp/router-context-published-source.log`); no packages installed or remote config altered.
- Immutable `.0.15` bundle: revision 8, both `c53b1579` and `d5d4e5a1` entrypoints,
  SHA256 `e3f9a0aeb1b3cf831b0198483fb756c2fe648de789cdc79bbbcf6847b6ab5a17`.
  Existing `.0.13` and `.0.14` are unchanged. Builder defaults and wheel/sdist includes
  now select/include `.0.15`; source-freshness test targets the new version.
- Existing contaminated session history is not rewritten. Old visible router-like answers
  can remain in that history; a live test must state whether its session is new or reused.
- Complete HTTP/media/bundle suite on extracted published Gateway 0.15.4 / Runtime 0.10.3 /
  Core 2.26.3: **41 passed** (`/tmp/router-context-bundle-tests-published.log`).
  Mandatory `.0.15` cases exercise real runtime handlers, image editing source handoff,
  voice/music/sound bytes, artifact content HTTP, missing-provider failure and saved
  versionless entrypoint compatibility. Only provider generation is replaced.
  Workspace Gateway cannot currently import against either its installed Runtime
  (`CALENDAR_KINDS` missing) or sibling Runtime (`ensure_key_file` missing); these
  unrelated concurrent dependency mismatches were not modified.

## Completion report

Completed 2026-10-18. Exact saved root/children proved mode=chat routing followed by a chat
child emitting the screenshot's audio plan. Real-handler before/after regression proved
router history pollution, rather than a missing audio switch case. Revision 8 declares
include_context=false on the router, preserves caller chat settings/history, and explicitly
routes literary spoken recitation to voice. New immutable bundle **0.0.15** contains both
compatible entrypoints; earlier .13/.14 bytes were preserved. The shipped .15 asset is explicitly unignored for version-control review. Builder defaults, mandatory
HTTP regressions and wheel/sdist includes updated; no commit/package publication occurred.

Validation: 17 source cases, six deployed-package source cases, **41 HTTP/media/bundle cases**.
Actual remote exact Hamlet request reached voice, generated an **8,008,930-byte WAV** decoded
on iPhone, and restored the same artifact after reload. Two timed public steps projected,
no chat-reason child. Initial two physical tests and final one-test reuse check passed;
SDK warning retained honestly in evidence. Temporary downloaded bytes removed. New owned
verification session was used; already contaminated user history was not rewritten.

The corrected private bundle was uploaded/reloaded through the existing endpoint. After
successful audio proof and unchanged-preference recheck, this account's Assistant selection
was updated using existing preferences. Server stores the versionless entrypoint and
resolves .15/private; normal app API start without test override completed on .15. Other
app preference keys/global Gateway default were preserved. No remote Python deployment or
restart required. Normal iPhone **0.6.14 (22)** installed/launched with 1032.

[Exact trace, red/green tests, live proof and scope](../evidence/1033/README.md).
Independent adversarial source/visual/live-evidence verdict: Approved for this scope.

### Insight and follow-up triage

ADR impact: None; routing is an internal control step, never user conversation history.
Context read/write behavior must be pinned explicitly at that boundary. Literal audio
aliases cannot substitute for typed voice/music/sound choices. This deployed workflow fix
is per account; it is not a global roll-out to all gateway accounts. Existing historical
plan replies remain historical data. No new urgent follow-up/priority change. Remote
endpoint/dependency deployment record 1027 remains open independently; its full package
combination has not been established by this task.
