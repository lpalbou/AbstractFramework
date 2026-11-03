# 1027 — Restore media endpoint resolution and verify remote iPhone images

> Package: abstractruntime
> Type: bug
> Created: 2026-10-18
> Priority: P1
> Labels: media, endpoint-profiles, iphone, deployment, regression

## Summary

Finish the image-generation repair discovered while enabling image and voice attachments
in the iPhone Assistant. Runtime fix `80a1887` is committed and passes the regression probe
against the deployed Core/Vision versions. The remote gateway has not received that fix,
and live remote image generation/editing has not passed. This item stays in `planned/`
until deployment and end-to-end verification are recorded. Local implementation is not
remote completion.

This is a retrospective record: the implementation commits below were made before a
backlog item existed. The operator requested this missing trace on 2026-10-18. Do not
rewrite that sequence as if planning or release/deployment approval preceded the work.

## Why

Operator: “where iss your $backlog item ? if you didn't create one with all the evidences
and what you did, do it now”. The original request was to select the Assistant orchestrator
on iPhone, generate images/voice through the gateway's configured providers, and attach
the outputs to AI messages with in-app previews. The operator restricted live modalities
to images and voice, requested one adversarial reviewer, prioritized Watch development,
and instructed this session to ignore Agora.

## Current code reality

Audited on 2026-10-18:

- The remote gateway advertises shared enabled profile `airelays`, image model
  `gpt-image-2`, and configured image-generation/editing defaults. Its reported versions
  are Runtime 0.10.3, Core 2.26.3 and Vision 0.3.34. See the filtered
  [discovery capture](../evidence/1027/remote-discovery.json). Version metadata alone
  does not prove exact running source; an extracted published-version probe independently
  reproduces the failure.
- Real remote runs `0995340a-c904-4a31-b60e-8c835466dfd1` (bundle 0.0.12) and
  `45a19a0f-ae62-4931-9bf6-94c2e3843585` (0.0.13) complete `route_call`, then fail
  `generate_image` after three attempts. The initial investigation wrongly attributed
  the failure to routing; ledger inspection corrected that diagnosis. See
  [run/ledger evidence](../evidence/1027/remote-failure-nodes.json).
- The error comes from Vision's endpoint-profile resolver:

  ```text
  Unknown or disabled endpoint profile 'endpoint:airelays': neither the host's endpoint-profile resolver nor AbstractCore's provider profiles know it.
  ```

- In [Runtime's pooled client](../../../abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py),
  normal text clients receive the host resolver. The separate `_media_host_client()`
  originally did not; `set_provider_endpoint_profile_resolver()` also omitted an
  already-created media host. Media defaults are merged later, so the plugin can receive
  `endpoint:airelays` without the host's connection lookup. This does not establish an
  admin-sharing failure: the captured profile is shared, and text routing succeeds.
- Runtime commit `80a188723c6af862456855798fb8bf22dfbefc9f` attaches the resolver when
  creating the media host and updates a cached host on resolver changes/key rotation.
  Rebuilding the host after defaults change retains it. The commit also prevents endpoint
  specs from going into a provider subprocess that cannot carry the process-local resolver;
  that subprocess exclusion was already present in the inspected published Runtime 0.10.3
  but missing in the workspace source. No Core code change or new endpoint was needed.
- [Dependency-light tests](../../../abstractruntime/tests/test_media_host_endpoint_resolver.py)
  exercise the host contract; the explicit
  [real Vision probe](../../../abstractruntime/tests/media_endpoint_profile_probe.py)
  exercises capability-default merging, t2i/i2i backend resolution, HTTP serialization and
  stored PNG bytes. Only the final provider HTTP response is stubbed. These tests forbid
  real network connects and provider subprocesses.
- A fresh all-workspace integration run during this backlog pass revealed a version/skew
  limit: its Vision backend requires `OPENAI_API_KEY` rather than using the profile passed
  by the plugin. Seven tests pass and six plugin cases fail in that combination. The
  isolated published Core 2.26.3 / Vision 0.3.34 recheck still passes all six with patched
  Runtime. Do not generalize the six-case result to every workspace/package combination;
  record and verify the exact versions selected for release/deployment.
- iPhone `8f4f646` implements per-message image/audio artifacts, image zoom/share/reuse,
  isolated audio playback, source-image pins for edits, authenticated disk downloads,
  reload restoration and disposable caches. Version 0.6.9 (17) was installed and launched
  as a normal signed app. No test plugin remained in the installed build.
- Live remote voice succeeded: run `bd997e3e-c523-40b0-9850-4d119f618a60` produced a
  412,478-byte WAV, decoded on iPhone, with references verified after reload and in session
  artifacts. See [voice evidence](../evidence/1027/remote-voice-generation.json).

## Scope

### In scope

- Preserve the diagnosis, exact implementation commits, test boundaries and failed attempts.
- Validate the Runtime resolver fix with deployed-version dependencies and the selected
  release combination, including resolver creation order, rotation and host reconstruction.
- Identify the real server deployment mechanism, install a reviewed build containing the
  Runtime fix, and restart the actual gateway process through that mechanism.
- Re-run real t2i, follow-up i2i and voice from the iPhone; attach outputs to their AI
  messages, inspect previews/playback, and verify restoration after reopening the app.
- Record installed versions, deployment/restart evidence and new run/artifact IDs before closure.

### Out of scope

- This documentation pass does not authorize a package publication, a new server access
  mechanism, a remote upgrade or a restart. No remote deployment was performed.
- No new HTTP endpoints, copying gateway endpoint credentials into phone/Core config,
  changing admin defaults, broadening permissions, or phone-side provider resolution.
- No live music, video or sound-effect generation, Watch changes, unrelated staged changes,
  or Agora participation.

## Implementation history and receipts

| Repository | Commit | What it did |
|---|---|---|
| abstractassistant | `ca378b5` | Saved the prior iPhone version before iteration. |
| abstractgateway | `4811b089` | Shipped reproducible media workflow 0.0.12, compatible entrypoints and Gateway media tests. |
| abstractgateway | `4a540e71` | Kept mandatory shipped-bundle regressions independent of a sibling Assistant checkout. |
| abstractgateway | `28811a0d` | Added endpoint routing regression coverage. |
| abstractassistant | `8c3f4aa` | Canonical orchestrator revision 7: explicit runtime text defaults plus voice artifacts. Router inheritance improvement; it did not fix the media resolver failure. |
| abstractgateway | `bb818d5f` | Shipped immutable orchestrator 0.0.13, preserving canonical `c53b1579` and legacy `d5d4e5a1` entrypoints. |
| abstractruntime | `80a1887` | Fixed media-host resolver propagation and endpoint subprocess exclusion; added contract tests and real-plugin probe. |
| abstractassistant | `8f4f646` | Implemented and documented iPhone message media and live verification harness; installed 0.6.9 (17). |

Bundles 0.0.12 and 0.0.13 were uploaded to the verification account's registry through the
existing bundle-upload route with `overwrite=false`, `reload=true`. Existing immutable
bundles were preserved. Bundle 0.0.13 SHA-256 is
`65be4fcb6307852475d0f52a01ad8f7ac04b00f35cc8c1bcc414639d9e2eb8fd`.
Its upload/reload does not install Runtime into the server process.

One adversarial reviewer (`tools_astra`, Astra medium) isolated the actual resolver gap
and reviewed the phone changes. Findings fixed included stale account-auth callbacks,
thumbnail setup cancellation, reliable preview dismissal/rendering and accurate cache
documentation. The original broad media test replaced an earlier layer and missed the
real plugin's resolver requirement; the explicit real-plugin probe closes that test gap.
An early probe was insufficiently isolated and attempted a provider request (invalid
model, no generated media); final probes block sockets/subprocesses. The fresh shell-env
check printed a credential in an assertion; its saved log was redacted and excluded,
the operator was notified, and repeat probes cleared inherited provider variables.

## Testing

Durable results and provenance are indexed in [evidence/1027/README.md](../evidence/1027/README.md).

| Check | Recorded result | Limit |
|---|---|---|
| Published Runtime 0.10.3 / Core 2.26.3 / Vision 0.3.34 | 6 failures before; 6 passes after patched Runtime; independently rechecked | Final provider HTTP responses stubbed; no real image-generation success claimed. |
| Original focused Runtime suite | 13 passes, 3 warnings | Preserve the log; exact dependency combination matters, as shown by the mixed-workspace recheck. |
| Mixed-workspace follow-up | 7 pass / 6 fail | Open compatibility check before selecting release versions; not silently counted as green. |
| Gateway media/routing | Reviewer recorded 35 passes | Local HTTP/workflow tests, not live provider image proof. |
| Canonical workflow | Reviewer recorded 17 passes | Local source/graph validation. |
| Swift package | 168 passes (107 GatewayClient + 61 AssistantKit) | Client tests. |
| Native hosted/UI | 10 passes; final preview recheck 1 pass | Demo image/synthetic audio; screenshots do not prove remote image generation. |
| Physical iPhone, live voice | 1 pass, zero skipped | Real remote generation/download/decode/restore. |
| Physical iPhone, live images | Failed at image generation | Must pass after remote deployment before closure. |

From the workspace root, use a Python environment with Runtime's test dependencies:

```sh
python -m pytest -q abstractruntime/tests/test_media_host_endpoint_resolver.py abstractruntime/tests/test_media_only_requests_skip_text_client.py
python -m pytest -q abstractruntime/tests/media_endpoint_profile_probe.py
swift test --package-path abstractassistant/phone/iphone/Packages/AssistantKit --jobs 1
```

The second command requires the optional Vision plugin. For the deployed-version probe,
use extracted/isolated Core 2.26.3 and Vision 0.3.34; copy the committed probe outside the
Runtime test tree so its conftest cannot inject sibling packages. Select Runtime 0.10.3
for the expected-red baseline, then the patched Runtime source for green. Clear inherited
provider environment first. Neither probe needs a real key or a running model server.

For the real phone checks, follow the opt-in commands in
[iPhone BUILD.md](../../../abstractassistant/phone/iphone/BUILD.md#opt-in-live-media-verification).
Use `testGenerateImageAndEdit` and `testGenerateVoice`. They use the phone's Keychain in
place and can incur provider charges. Start a fresh verification report/session after the
server fix so the harness does not resume the old failed run. Do not delete real chats.

## Acceptance criteria

- [x] Correct the initial routing misdiagnosis with the actual failing node and error.
- [x] Commit resolver propagation for new, cached and rebuilt media hosts without leaking secrets.
- [x] Reproduce six failures against deployed-version packages and obtain six passes with the fix.
- [x] Preserve code receipts, remote run references and test logs in this backlog's evidence folder.
- [x] Implement/install iPhone image/voice attachment rendering and verify real remote voice.
- [ ] Record a passing integration check for the exact dependency combination selected for deployment; resolve or explicitly constrain the mixed-workspace Vision incompatibility.
- [ ] Record a release/build containing `80a1887`, its review and the actual remote deployment mechanism.
- [ ] Deploy that reviewed Runtime build and restart the real gateway; capture running version/source evidence.
- [ ] Generate a real remote image, edit it using the retained primary artifact, and record decoded image bytes and owning run/artifact IDs.
- [ ] Reopen the phone app and confirm both image turns and voice attachments remain on their AI messages, with working previews/playback.

## Global release state and review of the fix (framework seat, 2026-10-18)

Reviewed against the published packages and the repositories' `origin/main`:

- **A superset of this fix is already released as AbstractRuntime 0.10.4** (`30cdb75` on
  `origin/main`, PyPI 2026-10-18; backlog 1026's cascade). It (a) attaches the host's endpoint-profile
  resolver to the pooled client's media host, built before or after
  `set_provider_endpoint_profile_resolver`, and (b) stops the `LLM_CALL` handler from resolving the
  first output spec's `endpoint:<id>` as the call's text provider, which rewrote the spec to a bare
  provider family and moved the URL and key into text-client params the media path never reads
  (`_first_output_provider` / `_replace_output_provider` removed). Tests:
  `tests/test_endpoint_profile_media_specs_keep_provider.py`.
- **Commit `80a1887` is correct but incomplete, and sits on a stale base.** Its media-host resolver
  propagation is equivalent to (a); its `_spec_routes_to_endpoint_profile` subprocess exclusion
  duplicates a guard already on `origin/main` since 0.10.3. It leaves (b) in place: a media-only
  child run with no text provider of its own (the web console's sandbox) still fails with
  "Missing vision_base_url / OPENAI_BASE_URL". The two symptoms differ because the Assistant's
  orchestrator sets a text provider (so the rewrite never fires and the spec reaches AbstractVision
  without a resolver: "Unknown or disabled endpoint profile"), while the sandbox's child run has none
  (so the rewrite fires). 0.10.4 covers both paths. The commit's two test files pass unchanged against
  0.10.4 (9 passed), so they can be kept.
- The local `main` of `abstractruntime` carries three unpushed commits (`d1654ce` streamed speech
  under voice, `d9ab07a` durable named tool policies, `80a1887`) on a base behind `origin/main`;
  the local `main` of `abstractgateway` carries ten (Assistant orchestrator bundles 0.0.12/0.0.13,
  automation tool policies, media regressions) behind `origin/main` (0.15.2 to 0.15.5 released from
  worktrees); `abstractassistant` carries two. Each must be rebased onto its `origin/main` by its
  owner before any further release; `80a1887` drops out as redundant. Those features are not part of
  the 1026/1027 cascade and need their own review and release (AbstractRuntime 0.10.5 or later).
- **The deployment mechanism is the one-line installer.** AbstractGateway 0.15.5 raises the runtime
  floor to 0.10.4 and AbstractFramework 0.11.8 pins both; once 0.11.8 is on PyPI,
  `curl -LsSf https://abstractframework.ai/install.sh | sh` on the server installs runtime 0.10.4,
  restarts the gateway service and confirms the browser apps. The remaining acceptance items (real
  remote image generation and edit from the iPhone, attachments restored after reopening) are
  verified after that upgrade; record the server's reported versions with them.
- Adversarial review (2026-10-18, one reviewer): the released fix is correct and minimal for both paths;
  one internal duplication remained in the runtime's pooled client (three sites wiring a new client, a
  third enumeration in `set_provider_endpoint_profile_resolver`) and is removed in AbstractRuntime 0.10.5
  (`_adopt_client` / `_owned_clients`, net -4 lines, an end-to-end test through the handler, the pool and
  AbstractCore's capability host). Still open, pre-existing: the gateway builds the same endpoint-profile
  resolver closure twice (`hosts/bundle_host.py` and the sandbox client builder in `routes/gateway.py`);
  expose it once from `provider_endpoint_profiles` when that checkout is rebased. AbstractVoice has no
  endpoint-profile resolution (neither before nor after; the gateway offers profiles for image and video
  routes only). Recommendation for `80a1887`: drop the commit (its hunks are on origin in equivalent form
  or duplicate 0.10.3); its probe depends on AbstractVision internals and belongs under `untracked/`.
- Credential hygiene: the redacted log and the rotation request stand; `ABSTRACTGATEWAY_AUTH_TOKEN`
  exported in the operator's shell is also what broke the installer's app step in 1026 (fixed in
  0.11.4 by passing the token as a parameter).

## Dependencies, ADR state and next step

The server deployment target/access mechanism has not been supplied. There is no known
ordinary account-token API for installing server packages, and none should be invented
for this repair. First identify that mechanism and the reviewed build to deploy. The
implementation is local; package publication and remote deployment remain unverified.

Read [Runtime's AbstractCore integration](../../../abstractruntime/docs/integrations/abstractcore.md),
[iPhone media architecture](../../../abstractassistant/phone/iphone/docs/architecture.md),
and related [0204 capability resolution/policy](multimodal-capability-projection/0204_runtime_capability_intent_resolution_and_policy.md).
ADR impact: none; this restores the existing host-supplied resolver contract and adds no
new durable cross-task policy. Any future change to ownership, credential propagation or
server-upgrade authority needs its own explicit decision rather than being inferred here.
