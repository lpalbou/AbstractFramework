# Evidence for backlog 1031

Captured 2026-10-18. Screenshots are demo fixtures; private mail/document content and
credentials are not exported. The physical test replayed existing authorized ledgers;
it did not send mail, open new mailbox messages, run a new agent, browse websites or
modify files. It exports action counts only.

| File | Meaning |
|---|---|
| iphone-package-tests.log | Full Swift package: 135 AssistantKit + 76 client tests = 211 passed. Ten new source-projection cases. |
| native-initial.json | Initial six native scenarios: five passed, one test-selector failure (SwiftUI Link is exposed as a Button). |
| native-web-final.json | Corrected web scenario: one passed, zero failures/skips. All six distinct scenarios now pass. |
| physical-history.json | One physical iPhone saved-history test passed. |
| remote-history.json | Actual conversation: one changed file and one sent email; zero file reads/email reads/searches/pages; zero issues. |
| phone-install.json | Normal signed 0.6.13 (21), no test plugins, installed/launched. |
| review.md | Independent adversarial findings, fixes, evidence and final approval. |
| file-actions.png, zero-hidden.png | Positive-only file/mail/source actions, no session-total folder count masquerading as answer activity. |
| files-read.png, write-edit-receipts.png | File collections and separate recorded read/skim/write/edit operations. |
| web-actions-scrolled.png | Complex answer strip scrolls to web categories. |
| searches.png, search-leads.png | Skim/full queries and result leads, explicitly distinct from fetched pages. |
| page-redirect.png | Requested/final URL and recorded fetched content. |

Native scenarios cover file read/change lists and excerpts, independent zero directions,
write/edit receipts, workspace-browser handoff with actual Markdown preview, web search
versus page receipts, scrolling, and existing completed activity/approval regressions.
One native selector correction was required; no application change was needed for that
failure. The final web case also includes the singular result grammar refinement.
Repeated native build exits 75 yielded to Watch until a window became available. Only
the phone's device build products were cleared for its known stale-framework cache.

Commands (from `abstractassistant/`):

```sh
swift test --package-path phone/iphone/Packages/AssistantKit --jobs 1
python3 phone/iphone/scripts/build.py --ui-test SIMULATOR_ID --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testOptionalFileActionsShowRecordedReadsAndChangesAndOpenWorkspace --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testWebSearchAndPageReceiptsStaySeparateAndScrollable --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testZeroMailDirectionsAndUnusedSourcesAreHiddenIndependently --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testCompletedActionsAreCompactAndOpenAnswerActivity --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testSessionWorkspaceMarkdownAndHierarchyPreview --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testChildApprovalIsVisibleInConversationAndOffersThreeChoices
python3 phone/iphone/scripts/build.py --live-media-test DEVICE_ID --team TEAM --only-testing AbstractAssistantPhoneTests/LiveGatewayMediaTests/testReplaySavedSentEmailReceipts
python3 phone/iphone/scripts/build.py --device DEVICE_ID --team TEAM
python3 scripts/update_llms_full.py --check
```

Original xcresult bundles remain in the ignored phone build directory. Summaries, demo
screenshots, filtered live counts and review are durable here. SHA256SUMS covers the set.
