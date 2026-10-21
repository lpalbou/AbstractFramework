# Timed expandable iPhone activity — 1032

Captured 2026-10-18. Final normal iPhone 0.6.14 (22) installed/launched. Changes uncommitted.

- package-tests.log: **142 AssistantKit + 76 GatewayClient = 218 tests passed**.
- native-second.json: three passed, one history test failed because modality was omitted
  when a media result also had response text; fixed before final checks. Earlier first
  run had three passed and one new test failing due an inherited accessibility identifier;
  that parent identifier was removed. These failures are not counted as successful runs.
- native-visual-final.json: **two passed**, zero failures/skips/runtime warnings. Final
  routing/media-history and expanded-model screenshots below were visually inspected.
  Existing live tool expansion/child approval scenarios passed in native-second.json;
  compact completed-actions scenario passed in the initial four-test run.
- chronological-history.png, routing-detail.png, media-detail.png, model-detail.png:
  demo fixtures, not private conversation screenshots. All four independently reviewed.
- phone-install.json: sanitized normal signed build/install/launch receipt, no test plugins.
- review.md: findings/fixes, evidence, scope and final independent approval.

Model detail is derived from explicit public content/data and whitelisted route/usage;
no system/messages/private reasoning/raw provider payload is exported. Up to 250 rows,
4,000 characters per result with visible truncation. Times use device local time; absent
legacy fields stay unavailable. Duration is elapsed wall time, including any approval delay
for a tool, while the approval row measures the wait itself.

Physical generation/selection proof and actual incident chronology live in
[1033](../1033/README.md). The last physical rerun reused the same owned voice run rather
than generating another large WAV; downloaded temporary bytes were removed afterward.

Commands from abstractassistant/:

```sh
swift test --package-path phone/iphone/Packages/AssistantKit --jobs 1
python3 phone/iphone/scripts/build.py --ui-test SIMULATOR --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testHistoricalActivityExplainsRoutingAndMediaWithTime --only-testing AbstractAssistantPhoneUITests/PhoneUITests/testModelStepsExpandToTimingUsageAndPublicOutput
python3 phone/iphone/scripts/build.py --live-media-test DEVICE --team TEAM --only-testing AbstractAssistantPhoneTests/LiveGatewayMediaTests/testGenerateHamletVoice
python3 phone/iphone/scripts/build.py --device DEVICE --team TEAM
python3 scripts/update_llms_full.py --check
```

All native builds used the phone guard, one job, own DerivedData and Watch priority. Only
phone-generated device Build products were cleared for known stale package frameworks.
