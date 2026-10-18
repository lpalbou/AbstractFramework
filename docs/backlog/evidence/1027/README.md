# Evidence for framework backlog 1027

Captured 2026-10-18. These are durable copies of the investigation results previously
kept under `/tmp` and the ignored iPhone build directory. No credential values or private
endpoint connection fields are included. Run IDs identify only the verification runs
created for this task; access to them still requires the owning gateway account.

| File | Provenance and meaning |
|---|---|
| remote-discovery.json | Phone-hosted authenticated discovery, filtered to profile IDs/scope, package versions and output modality routes. No endpoint URLs, API keys or fingerprints. |
| remote-failure-nodes.json | Actual remote run/ledger projection: router completes, generate_image fails three times, for bundle 0.0.12 and 0.0.13. |
| remote-voice-generation.json | Actual remote 0.0.13 voice generation; 412,478-byte WAV downloaded and decoded on iPhone; references restored. |
| published-before.log | Original six-case probe against extracted published Runtime 0.10.3 / Core 2.26.3 / Vision 0.3.34: six failures with the matching endpoint lookup error. |
| published-after.log | Same six cases with patched Runtime: six passes. Only final HTTP response is stubbed; no live generated image is claimed. |
| runtime-focused-original.log | Original reviewer run: 13 passes, three warnings, covering media-only clients, resolver contract and real Vision integration. |
| published-before-recheck.log | Independent follow-up recheck with inherited provider environment removed: six expected failures. |
| published-after-recheck.log | Same isolated follow-up recheck with patched Runtime: six passes. |
| workspace-vision-recheck.log | Additional mixed-workspace probe: seven passes, six failures because the workspace Vision backend requires OPENAI_API_KEY rather than consuming the injected profile. This is a compatibility limit, not a successful integration run. |

The reusable integration probe is committed in
`abstractruntime/tests/media_endpoint_profile_probe.py`; its dependency-light counterpart
is `test_media_host_endpoint_resolver.py`. Final probes prohibit real socket connects and
provider subprocesses. The original six-case probe was copied outside Runtime's test tree
to avoid its `conftest.py` prepending the sibling Core checkout over the published Core.

A fresh run with the operator shell environment inherited printed a provider credential
in a failed assertion. That log was redacted, excluded here, and the operator was notified
to rotate the credential. Rechecks remove inherited provider environment variables. No
production credential belongs in fixtures, command arguments, reports or backlog files.

See the item for commands, commits, acceptance criteria and the remaining deployment gate.

Additional client/workflow records: `gateway-revision7-tests.log` (35 passed),
`assistant-revision7-tests.log` (17 passed), `iphone-package-tests.log` (168 passed),
and the three xcresult summary JSON files (native media 10 passed, final preview 1 passed,
physical live voice 1 passed, zero skipped). The three PNG screenshots are demo fixtures;
they show rendering/playback only and are not remote-image generation proof.
