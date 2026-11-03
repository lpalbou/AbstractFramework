# Hamlet voice incident and real repair — 1033

## Observed incident

Root 75341816-9c6d-43bd-bd9e-817440752a22 used the account-visible private
abstractassistant-orchestrator@0.0.13:c53b1579, source gateway_default.
route_call at 17:24:54–17:24:56 UTC returned **mode=chat**. ReAct reason child
d7b92191-6bce-4eb7-982e-832efae28e30 at 17:24:57–17:25:00 returned the screenshot's
mode=audio plan as **plain chat content**. No generate_voice step ran. This was not an
invalid audio switch path: the audio object came from the chat child after routing.
incident-public-trace.json contains only whitelisted public steps/results for that request.
It exports no credential, system prompt, private reasoning or raw provider payload.

## Proven mechanism and repair

The router inherited use_context=true from Start. The real runtime handler read historical
conversation and appended its private routing user prompt + JSON response to context.messages.
The subsequent chat child consumed that polluted history. Its direct system/schema/tool
pins were correctly wired; context pollution was the reproduced leak. Revision8 declares
include_context=false on route_call, preventing both reads and writes, and explicitly treats
spoken literary/dramatic recitation as voice. It does not map arbitrary audio to speech.
Old visible replies remain unchanged in historical conversations.

router-before.log reproduces the leaking context. router-after.log: 17 source tests pass;
published-source-tests.log: six source isolation/voice cases on extracted deployed packages.
published-media-tests.log:**41 HTTP+real-handler media/bundle cases pass**, including .15
voice/image/edit/music/sound artifact bytes, durations/failure and entrypoint compatibility.
Provider generation alone is deterministic in those HTTP cases. Installed shared packages
were not changed; unrelated workspace facade dependency mismatches are recorded in the item.

Immutable bundle 0.0.15, revision 8, entrypoints c53b1579+d5d4e5a1:
e3f9a0aeb1b3cf831b0198483fb756c2fe648de789cdc79bbbcf6847b6ab5a17.
Older .13/.14 bytes were preserved. Builder defaults and distribution includes select .15.

## Actual remote proof

remote-hamlet.json: uploaded the corrected private .15 bundle through the existing Gateway
upload/reload API. In a new owned iphone-media-verification session, the exact original
request “generate a voice reciting a scene of hamlet” completed as root
e405c223-0e35-4404-ac6f-6c34c55eb5b6, with an **8,008,930-byte audio/wav** artifact
62ac78c44dbe4a57fdad27164344dace. iPhone AVAudioPlayer decoded positive duration; reloaded
artifact references matched. The activity projection had two timed/public steps, route voice
and generate_voice, and no chat-reason child. Temporary downloaded audio was removed.

After audio passed, the account's unchanged Assistant selection was updated through the
existing preferences endpoint. The server stores the versionless value
abstractassistant-orchestrator:c53b1579 and resolves its effective private version to .15.
Other preference keys were preserved; intervening different selections would be left alone.
The subsequent **ordinary app API start**, without a test workflow override, completed on
.15: final rerun root d1638008-5b70-4851-ad18-051bc78318e0. This changes this account's Assistant
selection across clients; the global Gateway default was not changed. No remote Python
package update/restart was performed or required for this workflow fix.

First physical batch: two passed (incident trace+actual generation). Final physical-final.json:
one passed, zero failures/skips, rechecking the existing generated run and ordinary selection.
A hosted AVAudioSession SDK main-thread warning remains recorded, including after detached
test decode; no functional failure observed or warning-fix claim made.

Normal signed iPhone 0.6.14 (22) installed/launched; receipt/review/screenshots in
[1032](../1032/README.md). Source/bundle/app changes remain uncommitted. This evidence does
not establish the deployment combination or close unrelated media endpoint item 1027.
