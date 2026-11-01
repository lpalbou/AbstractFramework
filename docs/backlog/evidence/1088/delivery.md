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

## Public permission language — 2026-11-01

The operator rejected a technical permission panel embedded in Avatar mode. The
public request now presents an ordinary action question, “Why I’m asking”, concrete
destinations, and labeled icons for Deny/Allow once. “Review details” opens the
existing detailed conversation. Tool names, JSON and standing permission settings
remain in that detailed view. Code’s public status strip also omits technical
execution details and counters. The same public presenter is used in Assistant
web and Entity; unknown requests require detailed review before approval.

The reason is the actor’s explicit public update from the same ordinary continuation
that proposed the batch. Agent binds its identity/text to unchanged proposed calls;
Runtime validates that binding and narrows it to the actual approval subset. Gateway’s
entity gate preserves the same contract. No extra inference is introduced. Nothing
is derived from private thought, a tool description, or the latest unrelated brève.
Missing reasons remain explicitly unavailable. Lineage does not prove the reason is
true, the action is necessary, or execution has occurred.

Known page-reading labels accept ordinary GET/HEAD requests. Requests with another
method, custom headers/body or unsupported arguments require detailed review. This
avoids describing a data-sending operation as merely reading a webpage. File writes
state that they can replace contents. All decisions retain the existing exact wait
target, authority, policy enforcement and retry/double-click guards.

| Verification | Result |
|---|---|
| Agent/Runtime | 96 selected checks including persisted public update→actual approval wait→resume, stale/cross-run/private context rejection, batching/subsets and disabled-mode prefix compatibility; no extra inference |
| Gateway entity gate | 22 checks, including bound reason projection/narrowing and denial without execution |
| UIC | Full panel-chat suite and public-request Chrome harness: safe/unsupported requests, two pages, six-file batch, questions, no technical/private leakage, retry/inflight/single-use |
| Code | 502 source tests; 3 built-browser tests covering real Gateway question/write approval plus an explicitly doubled two-page public explanation |
| Assistant/Entity | 63/601 source tests, built browser regressions, host builds |
| Independent adversary | Approved after inspecting actual Code screenshots at all three sizes, rerunning request checks and requiring the HTTP method/body/header classification fix |

Geometry checks require the full reason, both URLs and the decision controls visible
at 1280×800, 1000×650 and 390×844. Screenshot content below is a deterministic frontend
fixture, not a claim that a live model authored that example. The separate backend
integration exercises the real Agent→Runtime permission path with scripted actor replies.

- [Desktop public request](code-avatar-public-request-desktop.png)
- [Short-window public request](code-avatar-public-request-short.png)
- [Phone public request](code-avatar-public-request-phone.png)

Source checkpoints: Agent `80cb719`, Runtime `0f29e09`, Gateway `77a41223`,
UIC `36210cd` (browser tests `9190118`/`9155207`), Code `4fdcd74` (browser tests
`defcc37`), Assistant `00d1904`, Entity `0de365e`. Canonical source/artifact hashes
match all three web consumers. Own disposable servers on 19181/19182 were stopped.

Updated backend processes and a new Avatar task are required to author/bind new
reasons; old pending requests cannot acquire them retrospectively. No production
restart or publication occurred. Human/model-compliance, physical Watch and quantified
cache/performance validation remain separate planned work. A transient disk-full test
setup passed after removing only this task’s completed temporary fixtures; the machine
still has very little free disk space.

## Managed local deployment — 2026-11-01

At the operator’s explicit request, deployed the checked-out builds into the existing
Gateway-managed app installation: Code0.13.3 on3003, Assistant web0.0.1 on3008, and
Entity0.9.3 on3004. Local-preview receipts retain the source commits and tarball integrity;
the old Code/Entity versions and replaced Assistant installation remain available for rollback.
Backup state, packages and deployment manifest are in
`untracked/avatar-redeploy-wo_ykuhh/` in this workspace. No registry publication occurred.

Gracefully stopped and restarted the existing `ai.abstractframework.gateway` service
using its existing launch configuration. The new process40447 serves the same runtime
directory and editable Agent/Runtime/Gateway sources; no service was installed and no
conversation/authentication/model configuration was changed. Enabled apps restarted under
the gateway. The gateway health check is healthy; each app’s direct HTTP page and script
are available, and the served script bytes match the fresh build with public request/purpose
support. The gateway-mounted URLs retain their normal authentication requirement.
Live managed Code also booted in a clean Chrome context with Avatar mode present and no
JavaScript errors. Browser sign-in remains required; a new Avatar task authors new reasons.

Usual Code addresses: `http://127.0.0.1:8080/apps/code/` and `http://127.0.0.1:3003/`.
Hard refresh replaces cached frontend code. Free disk space at deployment was approximately95GiB.
