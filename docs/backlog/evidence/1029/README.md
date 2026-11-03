# Evidence for backlog 1029

Captured 2026-10-18. No email was sent for this task. Native screenshots show demo
addresses/content. The physical test replays the existing saved conversation using the
phone's saved credential in place. Only counts/completeness are exported; actual email
bodies, subjects, recipients, message IDs and credentials remain on the phone/Gateway.

| File | Meaning |
|---|---|
| iphone-package-tests.log | Final full Swift package: 119 AssistantKit + 76 client tests = 195 passed. Includes ten receipt projection/replay tests. |
| native-ui.json | Three native UI cases passed: envelope/count/receipt, compact actions without email, child approval regression. |
| native-email-final.json | Receipt UI recheck after final visual refinement: one passed, no skips/failures. |
| physical-replay.json | One actual iPhone read-only saved-conversation replay test passed. |
| remote-receipts.json | One confirmed send, one complete receipt (sender/recipients/subject/body/time), zero issues. No private message content. |
| phone-install.json | Normal signed 0.6.11 (19) installation and launch result, without test plugins. |
| email-count.png | Envelope/count in the existing answer action row. |
| sent-receipt.png | Readable receipt with sender/recipient/time/subject/body and collapsed technical details. |
| reply-receipt.png | Replies use the same receipt design. |

Screenshots were visually inspected. The first physical compile encountered stale
phone-only package framework products (`Extra argument emailFixture`); removed only
`phone/iphone/build/DeviceDerivedData/Build` and rebuilt successfully. Watch source and
build outputs were untouched. Guarded native builds keep one job and yield to Watch.

Validation commands (from `abstractassistant/`):

```sh
swift test --package-path phone/iphone/Packages/AssistantKit --jobs 1
python3 phone/iphone/scripts/build.py --ui-test SIMULATOR_ID --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testSentEmailReceiptsShowMessageRecipientsAndRecordedTime --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testCompletedActionsAreCompactAndOpenAnswerActivity --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testChildApprovalIsVisibleInConversationAndOffersThreeChoices
python3 phone/iphone/scripts/build.py --live-media-test DEVICE_ID --team TEAM --only-testing AbstractAssistantPhoneTests/LiveGatewayMediaTests/testReplaySavedSentEmailReceipts
python3 phone/iphone/scripts/build.py --device DEVICE_ID --team TEAM
python3 scripts/update_llms_full.py --check
```

Native `.xcresult` bundles remain in the ignored phone build directory; summaries/screenshots
are preserved here. A final one-line change merges earlier mail fields when a completion
row has only partial arguments; its regression test and the full 195-test run passed before
the final normal build. The physical and UI proofs precede that conservative retention
change. `SHA256SUMS` covers this durable evidence set.
