# Optional avatar conversation delivery — 2026-11-01

The operator authorized source development after checkpoint `30bcc40`. The second view is
implemented in Code web, Assistant web, Entity driver/Flow and native Watch. Ordinary chat and
technical views remain the default. Choose **Avatar** in web chat; Watch has **Settings → Avatar
conversation**. Start a request in that mode to enable authored updates. Changing an already
running legacy view cannot manufacture missing public messages.

## Delivered

- Actor-authored public discoveries, choices and uncertainty in the ordinary continuation,
  with source identities and durable events. No per-tool extraction model call, graph or Note
  ingestion pipeline. Native tool/batch contracts and stable prompt-prefix behavior retained.
- Avatar plus two/three subtitle lines, reading/reply pins, public history and final files/results.
  Current-tree child actors retain their identity in quoted replies. Default drafts/files and
  permission controls remain. Existing Assistant microphone/playback level feedback is reused;
  Code's installed voice API supplies microphone level and actual playback state.
- Original human words and accepted receipts, command correlation distinct from sidecar sequence,
  correct entity ownership/attribution and fresh recall. Acceptance never implies adoption.
- Essential questions, a declared 120–300 second clarification deadlines/fallback, durable original
  question identity, strict cutoff, restart/pause/cancel recovery and retained late replies.
  A timeout is a host outcome, never a fabricated user answer or permission.
- Chronological question/answer/expiry/late-reply history, explicit bounded-window notices,
  independent foreground cues and silent restoration. No private entity diary/reasoning exposure,
  generic visit steering bypass or hidden background notifier.

## Evidence

| Check | Result and scope |
|---|---|
| Real local model | PASS: four-cycle GGUF fixture, public preference→human wheelchair correction→next native batch checks both venues→accessible final choice; 19.49 s. [Public record](local-model.json). |
| Agent | 242 basic tests passed/1skip, plus explicit parser/native-batch/source/cache-prefix contracts. |
| Runtime | 191 focused legacy/new tests passed ; 110 question/public/replay tests after identity refinements. |
| Gateway | 68 wider tests passed; 16 focused owned-visit/history tests after refinements. |
| Code | 501 unit tests and built-Chrome test against disposable real Gateway passed. |
| Assistant web | 63 unit tests, full existing voice/chat/catalog browser checks and avatar interaction browser checks passed; actual public brève playback pause/resume, gain feedback and child reply identity exercised. |
| Shared UIC |Full panel-chat suite plus real Chrome reading/history/reply/preference/cue checks passed; file-only, private-data, pause and current-tree referent regressions covered. |
| Flow authoring |Build and 140 files / 1,318 tests passed; Ask User exposes policy and explicit expiry outputs. |
| Entity |Build and 60 files / 601 source tests passed; actual built driver+Flow+reconnect/browser tests, privacy and phone caption/composer geometry. Ignored old worktree tests excluded, not altered. |
| Apple | 220 Gateway client tests, 231 dependent iPhone tests, 17 focused conversation tests; native build, 3/3 Watch UI tests and 1/1 exact reopening lifecycle pass. Simulator coverage only. |
| Independent adversary |Final approved verdict after original reply/history/playback/cue/identity gaps and native fixture conflict were fixed. Reviewer independently read xcresults and inspected source/screenshots. |

Counts are separate suites and reruns, not a summed unique-test total. Root integration logs live
under `/tmp/avatar-*`; source harnesses remain in their owning repositories. These synthetic
fixtures do not demonstrate physical-device or general model-quality performance.

## Remaining validation and operating limits

Physical Watch microphone, audio/haptics, background behavior, VoiceOver and human usability
remain under 1095. Manual large-text/accessibility checks remain under 1088. Quantitative KV-hit,
token/memory and matched baseline latency comparisons remain under 1089; one GGUF run does not
prove MLX/HF/backend parity. Structured KG/AbstractNote 1090 and broad tool-warning audit 1091 are
still separately proposed. Existing raw tool/evidence storage is preserved.

Gateway question arbitration retains existing process-local single-writer authority; there is
no distributed lock guarantee. Public windows are bounded and omissions are shown. No package
publication, production restart/deployment, external notification or machine persistence occurred.
The global Gateway changelog validator still rejects the pre-existing malformed
`abstractgateway/changelog.d/0980-resources-dashboard.md`; the added fragment validates on its own.

Coredoc skill decisions: existing Agent/Runtime/Gateway/UIC/Code operating skills were updated.
No Entity/Assistant-web/Flow-only skill was created for GUI launchers. The root ADR skill is
registered in AbstractSkill's existing registry. Hub access was unavailable (connection refused),
so no hub mirror was silently claimed; local files are the delivery record.

## Final source checkpoints

| Repository | Final local commit |
|---|---|
| Agent |030a480|
| Runtime |098dc87|
| Gateway |7fadab1c|
| UIC |b77f474|
| Code |5ab8c1d|
| Assistant web + Watch |10891de (Watch fc775ac)|
| Entity |57ac918|
| Flow |32bd7ae|

All eight working trees were clean at final audit. The three web producer manifests match
canonical UIC source hashes. Disposable test servers were stopped; the existing unrelated
local stack was left running.

## Visual evidence

- [Code avatar and final history](code-avatar-history.png)
- [Entity phone composition](entity-avatar-phone.png)
- [Entity question and fallback history](entity-question-history.png)
- [Watch question and late-reply history](watch-question-history.png)

[Mission and implementation handoff](implementation.md). [Roadmap](../../proposed/accumulated-evidence/README.md).

## 2026-11-01 follow-up: visible requests and compact composer

The Avatar view shows the actual pending question or approval ahead of subtitles and
history. While a request is open, a small avatar sits beside its status; long tool
details scroll inside the request. The existing decision controls and permission
callbacks are reused. An empty subtitle placeholder no longer competes with a request.

AbstractUIC exposes `ChatComposer variant="compact"` and
`WorkflowChat composerVariant="compact"`. This rounded multiline composer grows with
the draft, retains attachment/voice/Stop actions, and uses a circular Send button.
Code selects it in Avatar mode; Conversation mode retains the original composer.
The focused compact field uses the outer composer's focus ring.

Validation: full panel-chat suite and compact native/fallback input browser checks
passed; Code's 501 unit tests and two built-Chrome tests against a disposable real
Gateway passed. Request geometry was checked at 1280×800, 1000×650 and 390×844, with
an actionable approval and the real prompt visible. Shared checks cover a six-tool
batch, actual question submission, and no permission before an explicit click.
Independent adversarial checks also covered deep history and scrolling to the last
target. Assistant/Entity built browser regressions and all three host builds passed.
Canonical source and artifact hashes match all three consumers.

- [Request in a short desktop window](code-avatar-request-desktop.png)
- [Request on a phone](code-avatar-request-phone.png)
- [Compact composer with three text lines](code-compact-multiline.png)

This follow-up preserves the remaining manual accessibility, physical-device and
quantitative performance validation listed above. No publication or production
service restart was performed.
