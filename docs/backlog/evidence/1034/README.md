# iPhone direct toolbar and reliable activity counts — 1034

Final normal signed **0.6.15 (23)** installed/launched on the iPhone, no test plugins.
Changes remain uncommitted. One existing adversarial reviewer approved the reviewed scope.

| Evidence | Result |
|---|---|
| package-tests.log | **147 AssistantKit + 76 GatewayClient = 223 passed**; five new gated task lifecycle cases. |
| native-initial.json | Three passed: direct actions, compact completed activity, independent zero mail/source suppression. |
| native-refined.json | Two passed: refined spacing/direct controls and empty historical activity without zero badges/placeholders. |
| native-final.json | Two passed: final normal toolbar and long entity name, all actions hittable/ordered, title clear of history control. |
| physical.json | One physical saved-history test passed; no skips/failures. |
| saved-history-counts.json | Nine saved answers resolved after cancelling each row waiter; sent email 1, changed file 1, zero issues. |
| phone-install.json | Sanitized normal build/install/launch receipt. |
| review.md | Independent source/UX review and primary agent's subsequent physical receipt. |
| direct-toolbar.png / long-title.png | Final directly accessible controls, gear farthest right, normal/long titles fit. |
| positive-counts.png / empty-history.png | Positive-only action strip; one unnumbered accessible Activity action for empty/missing history. |

An initial long-name probe failed and exposed real intrinsic title overflow. The title Text
was explicitly bounded (full name retained as accessibilityValue); final native test passed.
Earlier normal-title capture also prompted tighter spacing. These were application layout
refinements, not ignored test failures. Native guard yielded twice with exit 75 when Watch
work began; no Watch source, products, SDK state or build priority was changed.

Store-owned tasks coalesce by run, survive cancelling one/all view callers and guard
publication/cleanup with cache epoch and task UUID. All reset paths invalidate pending work;
new live completion cancels older replay. Five deterministic gated regressions cover these
behaviors, stale authentication and explicit retry. Partial positive counts retain their +
coverage marker; unavailable history has a reachable retry instead of a fake zero/ellipsis.

Physical proof read only existing authorized public run history/ledgers. It did not execute
an agent, send/read new email, generate media, modify user files or export content/credentials.

Commands from abstractassistant/:

```sh
swift test --package-path phone/iphone/Packages/AssistantKit --jobs 1
python3 phone/iphone/scripts/build.py --ui-test SIMULATOR --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testDirectToolbarExposesActionsWithSettingsRightmost --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testDirectToolbarRemainsReachableWithALongEntityName
python3 phone/iphone/scripts/build.py --live-media-test DEVICE --team TEAM --only-testing AbstractAssistantPhoneTests/LiveGatewayMediaTests/testReloadSavedAnswerCountsAfterRowCancellation
python3 phone/iphone/scripts/build.py --device DEVICE --team TEAM
python3 scripts/update_llms_full.py --check
```

Original native xcresult bundles remain in ignored phone build storage. Durable summaries,
public demo screenshots and counts-only physical/install reports are retained here.
