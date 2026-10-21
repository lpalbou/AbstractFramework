# 1037 — Rich conversation sharing with original files

Local/uncommitted iPhone work; baseline 0.6.17 (25), installed target **0.6.18 (26)**.
No Gateway API/package deployment, publication or Watch source/product changes.

## Behavior and ownership

- New conversation is mint, semibold and visibly accented above history; preserves responder/guards.
- Navbar Share captures loaded user/assistant messages and public attachment references at tap.
- Original artifacts plus successful recorded write/edit files are downloaded through existing
  public artifact/workspace routes. Owning child run resolves the workspace; no unrelated tree copy.
- Files appear after the message that attached/generated them. Images have inline downsampled
  copies (first 12, max 1,000 pixels/320 points) in the rich transcript; originals remain unchanged.
- One transcript provider offers flat RTFD, HTML and plain text; original files have typed file
  providers. Attributed messageBody metadata supports formatted Mail handoff. Bold/italic,
  headings/lists/code/links/tables are rendered. HTML is escaped and does not fetch remote content.
- Repeated names/content deduplicate, name collisions get suffixes. Maximum 100 originals/200MB
  combined; missing file, incomplete activity or over-limit fails explicitly, not a partial share.
- Conversation recordings/read-aloud are excluded, generated media remain explicit attachments.
- Owned tmp/AbstractAssistant/exports/UUID copies survive receiver reads and are deleted at native
  activity completion/cancellation, with fallback deinit/startup cleanup. Originals are untouched.
- Before/after await account/session guards discard old results, including old-account401 errors.

## Validation

**235 package tests passed** (159 AssistantKit + 76 client): [log](package-verified.log).
Five new export tests cover actual image/Markdown bytes and placement, unrelated file exclusion,
name collisions, deduplication, missing/outside paths and cancellation cleanup. The initial new
fixture compared directory URLs with different directory hints; corrected to normalized path
comparison, with initial failure retained in [log](package-initial-fixture-failure.log).

**Five native tests passed**, zero failures/skips/runtime warnings:
[summary](native-summary.json), [log](native-verified.log). Three hosted tests cover rich Markdown,
RTFD image roundtrip, HTML escaping, actual HTML provider data and original PNG provider bytes,
lease lifetime/idempotent cleanup, and a gated old 401 arriving after an account/context switch.
Two UI journeys cover New accent, toolbar/share navigation and multi-speaker share/Copy.
No independent post-test pasteboard content inspection is claimed.

Parent and adversary directly inspected:

- [Mint New conversation](new-conversation.png)
- [Native formatted transcript and inline image before the following answer](rich-transcript.png)
- [Conversation title in native share sheet](native-share-sheet.png)

The first [preview](initial-plain-text-preview.png) said Plain Text; per-item metadata fixes its
label without changing the rich/file alternatives. [Independent review](adversarial-review.md).

**One physical saved-session export test passed**:
[summary](device-summary.json), [log](device-verified.log), [counts only](saved-history-counts.json).
It retrieved existing public runs, ledgers, artifacts and workspace files using Keychain credentials
in place, built an 18-message export containing one image plus one document, then verified cleanup.
No private transcript/files/credentials were copied to the workstation; no new agent/tool/media
run was requested. The opt-in device test initially failed compilation for an optional prompt;
fixed with the same empty-string handling as output text; [initial log](device-initial-compile-failure.log).
The passing device result reports an existing AVAudioSession main-thread responsiveness warning
at app startup; export itself passed. No new audio capture/playback code is part of this item.

Normal signed **0.6.18 (26)** built with no test PlugIns, installed and launched:
[metadata](normal-app.json), [build](normal-build.log), [install](install.json), [launch](launch.json).
One low-priority guarded iPhone job at a time; Watch retains priority.

## Practical limits and unverified destination behavior

Mail/Notes have not been opened as configured receiving destinations in these checks. UIKit
receives rich alternatives/messageBody plus original file providers; each receiver decides
layout/representation and whether to place originals inline or as attachments. Native UIKit
rendering/provider fidelity is proven, final Mail/Notes layout is not. No test messages sent.

Only loaded messages are shared. Produced files are identified by confirmed write/edit receipts,
not unobservable shell side effects; deleted/unavailable files stop preparation. Workspace files
are their current saved versions, not historical byte snapshots. Internal voice is excluded.
These bounds are documented in the phone README and architecture.

Apple primary references:

- [Attributed message body](https://developer.apple.com/documentation/uikit/uiactivityitemsconfigurationmetadatakey/messagebody)
- [Activity item configuration](https://developer.apple.com/documentation/uikit/uiactivityitemsconfiguration)
- [Sharing copies of data](https://developer.apple.com/documentation/uikit/collaborating-and-sharing-copies-of-your-data)

## Reproduction

From abstractassistant:

```sh
swift test --package-path phone/iphone/Packages/AssistantKit --jobs 1
python3 phone/iphone/scripts/build.py --ui-test SIMULATOR_ID \
  --only-testing AbstractAssistantPhoneTests/ConversationSharingTests \
  --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testDirectToolbarExposesActionsWithSettingsRightmost \
  --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testSharedConversationIncludesBothSpeakers
python3 phone/iphone/scripts/build.py --live-media-test DEVICE_ID --team TEAM_ID \
  --only-testing AbstractAssistantPhoneTests/LiveGatewayMediaTests/testSavedRichConversationExport
python3 phone/iphone/scripts/build.py --device DEVICE_ID --team TEAM_ID
```

Device verification requires an existing saved session containing a document/image. Credentials
stay inside the device. Install the final normal build after hosted device verification.
