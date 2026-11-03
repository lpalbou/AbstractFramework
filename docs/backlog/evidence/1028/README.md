# Evidence for backlog 1028

Captured 2026-10-18. Screenshots use deterministic demo fixtures; they prove native
layout and interaction, not remote media generation. The live report separately verifies
the actual saved conversation on the operator's gateway using credentials kept on the
iPhone. No credential, private endpoint connection field, or document contents are copied.

| File | Meaning |
|---|---|
| iphone-package-tests.log | Full AssistantKit Swift package run: 109 + 76 = 185 tests passed. |
| native-final.json | Final simulator run: 17 passed, zero failed/skipped; file browser/preview, compact actions, live activity, approval and media regressions. |
| physical-workspace.json | Final physical iPhone read-only workspace test: one passed, zero failed/skipped. |
| remote-session-files.json | Actual existing session: discovered and downloaded `discussion-summary.md`, 769 UTF-8 bytes; one workspace; 20 conversation-audio/transcript artifacts hidden, zero remaining attachments, no issues. Run/session IDs identify the existing authorized conversation. |
| phone-install.json | Normal signed app 0.6.10 (18), without test plugins, installed and launched successfully. |
| compact-answer-actions.png | Cycles, tools and file counts beside the speaker; no completed activity card. |
| workspace-files.png | Workspace document/folder hierarchy plus explicit generated attachments, audio toggle off. |
| nested-folder.png | Child folder navigation. |
| markdown-preview.png | In-app rendered Markdown, with Share and Close. |
| conversation-audio-toggle.png | Toggle reveals read-aloud audio while intentional generated voice remains visible. |

The initial toggle UI test failed because it tapped the center of a SwiftUI row rather
than the switch; the test now taps the switch and passes. Initial native compilation
required an actor-isolated deinitializer; initial physical compilation also exposed stale
package framework products. Only the phone's own build products were removed to rebuild.
The final verification above follows those corrections. Repeated guarded build exits 75
yielded to Watch work; no Watch source/build outputs were changed by this task.

Commands (from `abstractassistant/`, one job):

```sh
swift test --package-path phone/iphone/Packages/AssistantKit --jobs 1
python3 phone/iphone/scripts/build.py --ui-test SIMULATOR_ID --only-testing TARGET/CLASS/TEST
python3 phone/iphone/scripts/build.py --live-media-test DEVICE_ID --team TEAM --only-testing AbstractAssistantPhoneTests/LiveGatewayMediaTests/testBrowseSavedConversationWorkspace
python3 phone/iphone/scripts/build.py --device DEVICE_ID --team TEAM
python3 scripts/update_llms_full.py --check
```

The native final selection was `SessionFilesTests`, `MessageMediaTests`,
`AttachmentAndVoiceTests`, and eight UI cases: compact completed actions,
workspace Markdown/hierarchy, conversation audio toggle, live tool results, child approval
with three choices, failure/connection distinction, image preview, and conversation/navigation.
Native result bundles remain under the ignored phone build directory; JSON summaries and
inspected screenshots are preserved here. `SHA256SUMS` covers the durable evidence files.
