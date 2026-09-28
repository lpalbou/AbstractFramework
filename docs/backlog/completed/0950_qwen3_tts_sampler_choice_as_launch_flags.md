# 0950 — Qwen3-TTS predictor/sampler choice as CLI flags and plugin settings

> Package: abstractvoice
> Type: task
> Created: 2026-09-27
> Priority: low
> Labels: voice, qwen3-tts, flags, next-wave
> Status: completed 2026-09-28 — released in abstractvoice 0.13.0 (tag `v0.13.0` → `1cdd727`)
> Moved: `planned/0950_qwen3_tts_sampler_choice_as_launch_flags.md` → `completed/0950_qwen3_tts_sampler_choice_as_launch_flags.md` on 2026-09-28

## Summary

abstractvoice 0.12.0 made the Qwen3-TTS predictor and sampler (`auto`/`reference`, `multinomial`/`exponential`)
fields on `Qwen3TTSSettings` (the update had added env-var switches, which violate the operator's
flags-not-env rule, and they were converted). The CLI, the web example and the AbstractCore plugin always use
the defaults; the optional exponential sampler is reachable only from Python. Expose both as launch flags and
plugin settings.

## Why

Operator standing rule: new switches are CLI launch parameters / settings, never environment variables. Found
by the voice release worker (~1.5–2 h).

## Current code reality (abstractvoice 0.12.0)

- `Qwen3TTSSettings(predictor=..., sampler=...)`, validated at model load; no CLI/REPL/web/plugin surface.

## Scope

### In scope

- `--qwen-predictor` / `--qwen-sampler` (names per the CLI's conventions) on the CLI and REPL; plugin settings
  keys; web example controls; docs.

### Out of scope

- Changing defaults.

## Acceptance criteria

- [ ] Each surface sets the choice; invalid values rejected before weights load; tests RED when removed.

## Receipts

- Voice worker report 2026-09-27.

## Implementation (wave 2, 2026-09-28) — pending release

abstractvoice branch `wave2/voice` (worktree `untracked/wave2/voice`), local commits, no version bump;
stays planned until the release lands: `05f6748` the Qwen3-TTS predictor/sampler choice on every
surface (CLI, REPL, web example, plugin settings); `339c09f` docs and CHANGELOG [Unreleased].

## Completion (2026-09-28)

Released in abstractvoice 0.13.0: the Qwen3-TTS codebook predictor and sampler choice on every surface (launch flags, REPL,
web example, AbstractCore plugin settings), validated before Transformers loads (`1cdd727`). Pinned by root
abstractframework 0.6.0.
