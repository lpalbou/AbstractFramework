# Avatar conversation implementation — mission and handoff

Authorized by the operator on 2026-11-01 after checkpoint root `30bcc40`.
This file is the shared goal/test/ownership record across context compactions. Re-read it before
changing scope. Update it at bounded integration milestones. Do not mistake a worker summary for
verified integration. Root owns integration and final delivery; one independent adversary reviews.

## Product invariant

Create a SECOND OPTIONAL VIEW over agent AND entity work; keep existing chat and technical views
intact. The avatar is the point of contact, dominating the scene. Two or three subtitle lines
communicate public discoveries, choices, reasons, uncertainty and questions in plain adult language.
Scroll to history/final. Natural replies can redirect actual ongoing work. Animation/voice correspond
to real status. Existing permissions and privacy boundaries remain authoritative. No mandatory KG,
AbstractNote pipeline, new scheduler, hidden reasoning exposure or blanket notification hook.

## Scope authorized

Implement roadmap1088/1089/1092/1093/1094/1095, starting with a complete web path and shared reusable
semantics. Native Watch adoption follows the validated contract. Structured knowledge1090 and
scientific Koine review remain later, separate work;1091 only where needed for evidence correctness.
Existing Assistant desktop changes present at intake are unrelated and must be preserved.
No package publication, OS persistence or external messaging is authorized/needed.

## Workers and owned writes

- root: UIC/shared conversation/avatar UI; Code/Assistant web/Entity host integration; Flow UI;
  docs/backlog/ADR lifecycle; live/browser validation and final synthesis.
- cache_trace: AbstractAgent opt-in public brèves and question adapter; focused tests/docs.
- provenance_arch: Runtime/Gateway durable question waits, indexes/resume/API support; tests/docs.
- prior_art: INDEPENDENT ADVERSARY, read-only review of contracts, real diffs and visible UX.

Never overwrite another owner's work. Coordinate seam changes in messages and record below.
Clean package HEADs are the before-change checkpoint; follow nested commit rules with scoped commits.
Do not publish or stage unrelated desktop dirt. Hub whoami failed with connection refused; no retry
loop/listener/alternative hub. Browser skill's Node execution tools are absent; use existing project
Playwright as explicitly reported fallback when live artifacts are ready.

## Initial seams (confirmed by root)

- `_runtime.conversation.enabled` opts in, fixed at run/turn start. Disabled preserves legacy behavior.
- Ordinary actor response.content may include ONE explicit `<public_update>` JSON block containing
  text + known prior source_call_ids. No extra inference per tool. Never publish parsed reasoning fallback.
  Strip marker from final displayed reply, preserve authored context/cache stability, emit `public_update`
  with stable id/run/session/iteration/source refs. Reject malformed, oversized or unknown refs explicitly.
  Exact parser/escaping validation remains under adversarial review before final acceptance.
- ASK_USER optional payload.question `{importance:essential|clarification, timeout_s?, fallback?}`.
  Essential has no timeout/fallback. Clarification requires120–300 seconds + nonempty declared fallback.
  Legacy absent-question behavior unchanged. UI uses wait.details.question `{id,purpose:conversation,
  importance,published_at,deadline,fallback}` plus existing prompt/choices/free_text.
- Expiry returns `timed_out:true`, fallback and question{id,outcome:expired}, NO fabricated user response.
  Agent treats it as host-attributed no-answer/fallback information. Silence never grants approval.
- New question generation resolves once under existing single-writer process authority. Preserve original
  deadline through manual pause; no auto-continue while paused, resolve overdue only on explicit resume.
  Retain late input with exact original identity; don't apply it to a newer wait. No distributed claims.
- Avatar option/config start propagation and Entity visit route must be verified, not assumed. No raw
  generic entity steering bypass; entity public output must preserve existing privacy screening.
- Foreground configurable approval/question/completion cues use actual revisions, not history playback.
  Background delivery remains existing authorized Notify/attention policy (ADR0041).

## Acceptance scenarios (required)

1. Default chat/technical mode behaves as before; switch views preserves messages, uploads and work.
2. Single actor: meaningful public update → typed/voice correction → real next action changes.
3. Entities: optional view works on supported visit/Flow route; protected diary/reasoning never leaks;
   busy/refused/retry states preserve text, source/actor/session scope is correct.
4. Subtitles2–3lines; reading/history/reply pins content; latest follow resumes intentionally; final
   response/evidence are reachable; large text/reduced motion/keyboard/muted audio work.
5. Asking vs approval vs listening distinct. Critical wait indefinite. Clarification announced fallback,
   timeout120–300s, server race/late/repeat-node/restart/pause tests. Never silence=consent.
6. Per-category visual/audio (haptic where available) preferences; no stale speech/cue replay on session
   switch/reconnect/history, no implicit background side effect. Reply silences stale speech before recording.
7. Legacy tool/native/structured/final responses and prompt-cache prefix tests remain valid. Public
   messages require explicit authored channel; source IDs resolve, missing message is not fabricated.
8. Actual browser interactions/screenshots + deterministic host tests, real local-model loop if available,
   native Watch tests/build as practical. Report hardware/OS/manual limits honestly; do not claim live
   Watch/usability validation from source/simulator alone.

## Checkpoint references

- `.`: `30bcc401ae34ccb59497f885e80e2e6bda01517f`
- `abstractagent`: `781c5cd78b6bb04c7c8aee432fabf3cadd9a3278`
- `abstractruntime`: `d4f0069f7085657e0d5c6fd081a8e8a0836e7124`
- `abstractgateway`: `89b5dcaf7437101509584496e0abcd5090b75bc6`
- `abstractuic`: `d46e3877aad54f27319d5547a3a727e67d05d447`
- `abstractcode`: `7f089776f480824ec263ab242fa0c0d346dcfe9e`
- `abstractassistant`: `1274816e272f2420a3acb472bece8cb1836832d0`
- `abstractentity`: `ea9b6fbb098678b50e271b03ad2be78c5163a01a`
- `abstractflow`: `e92b92d8eb85e5fcee60bd6fd1043efd4143a783`

## Progress / next slice

- 2026-11-01: root checkpoint and clean scopes verified; unrelated desktop Assistant changes noted.
- Workers received disjoint ownership and confirmed initial public-update/question contracts.
- Next: promote authorized backlog, implement/persist UI projection and start opt-in transport;
  collect worker source changes, run focused tests and adversarial live review.

## Integration milestone1

- Agent public-message implementation committed `cec68e1`: explicit optional public protocol, durable
  completed events, preserved old prompt/tool bytes,242basic tests passed/1skip. Real models not yet tested.
- Shared panel-chat committed `248388f`, with follow-up narration/questionguard/browser work pending.
  Code/Assistant canonical artifacts synced via producer exporter, not hand-edited.
- Root Code and Assistant web second-mode wiring now compiles; legacy default remains chat.
  New-question voice/text goes through the exact pending interaction, not future-task queue.
- Runtime worker implementing durable questions+safe entity canonical routes (guidance/answer),
  explicit public projection and requestmode propagation. Need sibling-source PYTHONPATH in tests.
- Agent worker now owns native Watch ONLY. Do not stage unrelated desktop Assistant files.
- Shared UIworker approaching final slice; independent adversary must inspect actual visible artifacts
  once a slot frees. Root owns remaining host integration/Flow authoring + end-to-end liveproof.

## Integration milestone2

- Real local GGUF model acceptance PASS: initially prefers quiet Park Cafe, receives typed
  wheelchair-access correction, next native parallel batch checks BOTH places, recommends
  accessible Riverside. Four cycles,19.49s; one durable accepted human receipt. Public-only
  evidence is local-model.json; no hardware KV-hit/memory benchmark claimed.
- Adversarial round1 found disappearing human corrections, misleading nonpublic reply buttons,
  steering jargon, missing playback controls, final speech while reading, dropped question cues.
  Implemented host-provenanced durable user_guidance and replay, restricted selection, plain
  Send, separate playbackControl/microphone, onAttendedChange final-speech guards, fresh required
  attention cues during reading. Round2 underway; already fixed brève pause key preservation.
- Shared full panel-chat suite PASS after changes; realChrome sharedbrowser PASS. Code unit
  suite initially caught verb-toggle policy in new playback button; corrected to existing
  AfSwitch state presentation, rerun pending.
- Assistant browser avatar test PASS (draft switch, pinned guidance withoriginalwords, exact
  question wait, no text approval, phone composer, viewrestore), plus FULL existing voice/chat
  browser regression PASS. Fake Gateway gained the canonical sharedread-state endpoint that
  its baseline fixture lacked. Browserclosed-SSEfixture shows disconnectedcopy honestly.
- Flow Ask User authoring exposes optional question object, policy properties and explicit
  timed_out/fallback/question outputs; build and140files/1318tests PASS.
- Watch committedbc321ff with default-off mode, native model/wire tests, fullSwift client,
 231dependent iPhone tests,2native UI checks andsimulator build PASS. Physicalhardware/user
  validation remains open; no package publication or production change.
- Entityworker owns Entity integration; Runtime/Gatewayworker owns entity authority and receipt
  durability. Existing unrelated Assistant desktop work grew concurrently; preserve all paths
  outside rootweb+workerwatch scopes. Hub unavailable; no CLI/server workaround installed.

## Integration milestone3

- Root Codeweb commit0ca63e1; Assistantweb026ca2f. Source/UI producer6e75b57 plus
  uncommittedtransientconnectionstate fix (Connecting… untilactuallyfailed); sync/build both
  hosts andEntity oncefinalsharedcommit. Code501tests; Assistant63tests PASS. RootFlow32bd7ae.
- Code Chrome nowPASS againstreal disposableGateway fixture18881+Code18882: defaultmode,
  draftpreserve,optinrequest,exactactualquestionresume,terminalCompleted,structuredfinalhistory,
  restoredoldchat. BackendexplicitFlow resultfallback fixedprivacy-first aftertestsurfacedmissingfinal.
- Assistant actualbuiltChrome avatarPASS includes busypublicbrèvenarrationpause/resumewithout
  resynthesis+actualspeakingpose. Defaultfullvoice/catalog44layouts/historytestPASS. FakeGateway
  streamsfiniteviewframes betweenconnections; screenshotscanreportConnecting… withouta realfailure.
- Entitye7bdd6d clean:599currentsourcetests, build, safeprivacyprojection/owneddriver/Flowroutes
  browserPASS. Phonegeometryexplicitly co-showsorb+3linecaption+composer; desktopdominantview,
  oldpane/graphstatepreserved. Oldignoreduntrackedworktree tests excluded, notdeleted/changed.
- Watch08887c7 fixesindependentreviewdurabilitygap. TaskcommandACKseq≠sidecarseq: correlate
  pendinglocalwordsbycommandUUIDandhostclient_message_id, nevertextorACKseq. Entitydirectsidecar
  sequencevalid. 215GatewaySDK,231iPhone,3nativeWatchUItests+simulatorbuild PASS. Hardwareunverified.
- Runtimeff1567f clean191focusedlegacy/newtestsPASS. Gatewayfinishingwiderselectionandcommit;
  hostclient_message_id flowtested command71/72vs sidecar1/2, identicalwordsdistinct.
- Independentfinalreviewrunning(prior_art), latestEntity/Watchcommits. Potentialremaininggap:
  driverpublicvisitstatehistoryrestorequestions/answers currentlypendingonly; safehuman guidance
  restoredbutpastquestions/answersonlyrawledger. Assessminimalpublicprojectionbeforeclaimfullhistory.
- Rootownstestservers sessions80226(disposableGateway18881),14887(Code18882); stoptheseonly
  afterfinalreview, do NOTtouchpreexisting18781. No productionservicesrestarted.
- SharedUICuncommittedfilescurrentlyconversation_model/avatar_conversation/checkscript (connecting
  state); addstatusacceptedguardalready6e75b57. Rootfinishdocs/backlogcounts/status/receipts+commits.
- PreexistingAssistantdesktopchangeswerecommittedconcurrentlyas7633fb5; rootneverstagedthem.
  Watchonlyworkercommits; webonlyrootcommit. Preserveanynewunrelateddirt.

## Final integration receipt

- Independent adversary APPROVED after verifying final native xcresults (3/3 UI plus1/1
  exact reopen), public question history, omission disclosures and file-only delivery.
- Final Runtime098dc87/Gateway7fadab1c/Watchfc775ac complete the previously noted history gaps.
  Gateway docs/skills teach these exact safe projection fields; arrays retain original order.
- Root final Code5ab8c1d/Assistant10891de/Entity57ac918 include canonical snapshot verification,
  actual voice feedback, actor-child identity and authoritative manual pause flags. Shared UIC
  b77f474 follows e615548/2c6800f; all host source-manifest hashes match canonical dist.
- Final Code real-Gateway Chrome PASS; Assistant avatarChrome PASS (actual brève amplitude,
  pause/resume without resynthesis, child source identity); shared Chrome PASS; host builds pass.
- Closed core1092/1093; remaining planned1088/1089/1094/1095 retain only their documented manual,
  quantitative and physical validation. KG/audit proposals stay gated. Counts190/78/297/2/3.
- Delivery report and public-only screenshots: delivery.md. Native fixture's live wait was
  preserved; completed-history fixture isolated solely for lifecycle check. No test failure hidden.

- Final audit: all eight package worktrees clean; source manifest hashes match; root documentation
  links/counts checked; own disposable Code/Gateway test sessions stopped successfully. Root
  checkpoint advanced concurrently to a60d0e8 for unrelated tray work, which was preserved.
