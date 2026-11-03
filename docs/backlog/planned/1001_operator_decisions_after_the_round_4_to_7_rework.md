# 1001 — Operator decisions after the rounds 4–7 rework

> Package: abstractframework, abstractgateway, abstractvoice, abstractcore
> Type: task
> Created: 2026-10-04
> Priority: high
> Labels: decision-gate, voice, openai-api, security, supervisor

## Summary

OPERATOR DECISION GATE (never assignable): six questions raised during rounds 4–7 (2026-10-03/04)
that change defaults, security posture or scope. Nothing is built for them; each answer becomes its
own item (or a change on the 0.10.0 branches) once given. Follow-ups that need no decision:
[0999](0999_follow_ups_after_the_round_4_to_7_console_and_app_rework.md).

## Current code reality (2026-10-04)

On `round4/2026-10-03`: the gateway's speech-to-text default route is `input.voice` =
faster-whisper / `large-v3` and text-to-speech `output.voice` = supertonic / supertonic-3, served by
`GET /api/gateway/voice/defaults` and shown by the kit Voice settings as "Gateway default · …".
AbstractVoice has no mlx-whisper engine. The OpenAI API key is the caller's gateway token; the
web console keeps the token typed at sign-in in session storage (local storage with *Remember this
browser*), removed at sign-out, so the OpenAI API page can show the key (the server keeps
fingerprints only and has no reveal route; gateway `docs/configuration.md`). Admins see every account's requests in the
request log, opened to the recorded request and response with keys and tokens redacted. The
supervisor in `scripts/start-local.sh` on `main` restarts the gateway on death only; branch
`fix/supervisor-restarts-hung-gateway` (625c36b) keeps that default and adds
`--restart-on-hang`.

## Decisions

1. **Speech-to-text default on Apple.** Make faster-whisper `large-v3-turbo` the default on Apple
   Silicon instead of `large-v3` (faster, close in quality), and add a **Spoken language** setting
   (auto-detect, or a fixed language that skips detection and avoids wrong-language transcripts)?
2. **mlx-whisper engine.** Add an mlx-whisper speech-to-text engine to AbstractVoice for Apple
   Silicon (Metal), selectable as a route next to faster-whisper (CPU on macOS)?
3. **Named per-user API keys.** Build [1000](../proposed/1000_named_per_user_openai_api_keys.md)
   (endpoint-only keys with a label, revocable one by one) for the next release, or keep the gateway
   token as the key?
4. **Admins reading API request bodies.** The request log shows admins the full recorded request and
   response of every account (redacted keys). Keep that, limit admins to metadata (time, account,
   model, tokens, status) unless the account opts in, or make it a gateway setting?
5. **Token in browser storage.** The console keeps the signed-in token in session storage (local
   storage with *Remember this browser*) to fill the key card. Keep it (until 1000 removes the need),
   allow session storage only, or never keep it and show the key only right after **New key**?
6. **Supervisor kill-on-probes default.** The 2026-08-20 ruling is restart on death only. Keep it
   (hang-kill only with `start-local.sh --restart-on-hang`, as on 625c36b), or make killing a gateway
   that fails 6 health probes (at most 3 restarts an hour) the default now that the gateway has its
   own watchdog (exit 75)?

## Acceptance criteria

- [ ] Each decision answered by the operator, quoted verbatim here with the date.
- [ ] Each answer that asks for work has its own backlog item or a commit on the release branches.

## Receipts

`untracked/round4/DESIGN.md` (R5.1, R6.1), `untracked/round4/BACKLOG-R5.md`,
`untracked/round4/ADVERSARY.md` (R7-W5 gate lines), `untracked/round4/COORD.md`.
