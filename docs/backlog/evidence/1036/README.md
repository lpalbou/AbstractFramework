# 1036 — Three-island navigation and conversation sharing

Local/uncommitted iPhone work. Baseline installed 0.6.16 (24); target 0.6.17 (25).

## Scope

- Native glass islands: Conversations left; Share/Files/Tools middle; Settings right.
- Responder chooser below toolbar; long names truncate without displacing actions.
- New inside Conversations preserves selected responder. Existing import/run safeguards remain.
- Per-answer Share removed; Copy/speech and file/media-specific sharing remain.
- Conversation Share captures loaded user/assistant text in order at tap, with speaker labels
  and attachment names. Export explicitly says loaded text only, attachment files excluded.
  Notices/runtime details/IDs/stats/drafts are not inputs to the export. Account/session changes
  dismiss the share sheet; empty or restoring/opening history cannot be shared.

## Validation

230 package tests passed: 154 AssistantKit + 76 client. Two new transcript tests cover
role ordering, attachment-only messages, filenames without internal artifact ownership,
notice exclusion, explicit text-only scope, empty history and immutable captured values.
[Final package log](package-verified.log).

An initial run hit an existing static URLProtocol cancellation race in MediaTransportTests:
a cancelled previous download appeared first in the next test's request list. The unchanged
suite passed in the complete rerun; [initial log](package-initial-media-stub-race.log).

Native iterations: first journey used the wrong Close label for Tools (actual identifier
`tools.close`); second expected Copy to be a Button, while iOS exposes it as a collection Cell.
Both were test-selector corrections, with the rendered share sheet and long-name layout
inspected directly. Logs retained above. A superseded test build was stopped only in its own
process group after a test edit had not applied; no unrelated Xcode process was interrupted.

Final native, clipboard and normal install receipts will be appended after validation.
No backend changes or real remote generation/tool activity are needed for this local change.

Native verification guard has yielded repeatedly with exit75 to other build activity, stopping only its own iPhone process group. Watch retains priority.

After repeated priority yields during Watch UI activity, the iPhone retry queue was replaced by a strict wait for all other Xcode processes to finish. Its named iPhone simulator was shut down while waiting, to release resources. No Watch process or products were changed.

After Watch compilation stopped and its test process remained at zero CPU for over a minute with normal memory pressure, verification resumed through the existing explicit idle-Watch guard. The guard still yields on renewed Watch activity/compilation or memory pressure.


## Completion evidence

Final native run: **three passed, zero failures/skips/runtime warnings**.
[Summary](native-summary.json), [log](native-verified.log).
Navigation test opened Files, Tools, Settings, native Share/Copy and New, then checked disabled
empty sharing. Long-name test verified truncation and New preserving the responder. A third
journey opened Share from a user/assistant conversation and invoked Copy successfully.
Multi-role text contents are verified by transcript unit tests; an external post-test pasteboard
read was unavailable because Xcode had already shut down its simulator. No separate native
clipboard-content assertion is claimed.

Inspected screenshots:

- [Three separate navbar islands](three-islands.png)
- [Long responder below the navbar](long-responder.png)
- [Empty conversation with disabled Share](empty-conversation.png)
- [Native conversation share sheet](native-share-sheet.png)
- [Share opened from user/assistant conversation](shared-conversation.png)

[Adversarial source/native review](adversarial-review.md): Approved.
Normal signed **0.6.17 (25)** built, installed and launched on the iPhone; no test PlugIns.
[App metadata](normal-app.json), [normal build](normal-build.log),
[install receipt](install.json), [launch receipt](launch.json).
No Watch source/product changes; priority yield receipts are in [priority-yields.log](priority-yields.log).
All work remains uncommitted.

## Reproduction

From `abstractassistant`:

```sh
swift test --package-path phone/iphone/Packages/AssistantKit --jobs 1
python3 phone/iphone/scripts/build.py --ui-test SIMULATOR_ID \
  --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testDirectToolbarExposesActionsWithSettingsRightmost \
  --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testDirectToolbarRemainsReachableWithALongEntityName \
  --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testSharedConversationIncludesBothSpeakers
python3 phone/iphone/scripts/build.py --device DEVICE_ID --team TEAM_ID
```

Each native phase uses one low-priority job and isolated iPhone DerivedData. Where an explicitly
identified idle Watch test coexisted, the existing guard kept yielding to Watch CPU/compilation
and memory pressure. No global/concurrent build override was used.
