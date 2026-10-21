# Evidence for backlog 1030

Captured 2026-10-18. Screenshots are demo fixtures, not private mail. The physical test
only replayed authorized existing run ledgers; no email was sent, opened on the mailbox,
or marked read/unread for testing. Credentials stay on the phone. The live report exports
counts/completeness only, never bodies, subjects, addresses or message IDs.

| File | Meaning |
|---|---|
| iphone-package-tests.log | Full Swift package: 125 AssistantKit + 76 client tests = 201 passed. Six new read projection/replay cases, plus existing send cases. |
| native-ui.json | Four UI tests passed, zero failed/skipped: 3-read/3-send collections/details, search, no-email compact actions, approval regression. |
| physical-history.json | Physical iPhone saved-history replay: one passed, no failures/skips. |
| remote-history.json | Actual saved conversation: one confirmed send with complete receipt, zero successful read_email actions, zero issues. Read collection behavior is proven by package/native fixtures; this does not claim new live mailbox reads. |
| phone-install.json | Normal signed app 0.6.12 (20), no test plugins, installed and launched. |
| directional-counts.png | Separate inward/outward envelope badges in the answer action row. |
| sent-collection.png | Three sent messages, compact subject/recipient/time/snippet rows. |
| read-collection.png | Three read messages, including HTML-only and explicit headers-only cases. |
| multiple-recipients.png | Full long subject and three recipients in an independent detail view. |
| read-message.png | Read-message detail with sender, recipient, action timestamp and body. |
| search-result-detail.png | Recipient search opens the matching message independently. |

All screenshots above were visually inspected, including search result detail. Package
read fixtures follow Core `read_email`/`MessageDetail.to_dict()` source contracts. A repeat
read updates a headers-only receipt when a body becomes available without inflating the
count; UID/mailbox/UIDVALIDITY identities remain distinct. The retained 100-message and
50,000-character body limits have visible notices.

Commands (from `abstractassistant/`, one guarded Xcode job with Watch priority):

```sh
swift test --package-path phone/iphone/Packages/AssistantKit --jobs 1
python3 phone/iphone/scripts/build.py --ui-test SIMULATOR_ID --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testSentEmailReceiptsShowMessageRecipientsAndRecordedTime --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testEmailCollectionSearchOpensTheMatchingMessage --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testCompletedActionsAreCompactAndOpenAnswerActivity --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testChildApprovalIsVisibleInConversationAndOffersThreeChoices
python3 phone/iphone/scripts/build.py --live-media-test DEVICE_ID --team TEAM --only-testing AbstractAssistantPhoneTests/LiveGatewayMediaTests/testReplaySavedSentEmailReceipts
python3 phone/iphone/scripts/build.py --device DEVICE_ID --team TEAM
python3 scripts/update_llms_full.py --check
```

Only the phone's stale device build products were cleared before the live build to avoid
the previously observed package-framework cache problem. No Watch files/build outputs
were changed. `.xcresult` originals stay in the ignored phone build directory; durable
summaries and inspected demo screenshots are copied here. `SHA256SUMS` covers this set.
