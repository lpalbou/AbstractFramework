# 038 — Framework Configuration Wizard (`af config`)

**Status**: Planned  
**Date**: 2026-02-15  
**Priority**: High (usability + safety)  
**Components**: abstractframework (new CLI), abstractcore, abstractgateway, abstractruntime

## Summary

Today the framework is configured via many environment variables (provider/model, gateway, integrations like Telegram).
This works for power users but is error-prone and unfriendly for external users. We need a **single, simple, cross‑platform
wizard** to configure the “whole stack” while preserving the current decoupling between packages.

## Goals

- Provide a **guided interactive setup** that configures the most common “end-to-end” flows:
  - core LLM defaults (provider/model, API keys)
  - gateway basics (auth token, data dir, bundles dir)
  - Telegram integration (transport, token/TDLib, access control defaults)
  - tool execution defaults (gateway tool mode + Telegram tool policy defaults)
- Produce configuration that works on **macOS / Linux / Windows**.
- Keep package boundaries intact: `abstractcore` stays provider/model focused; `abstractgateway` owns integrations.
- Provide **safe defaults** (fail-closed for Telegram; no accidental public bots).

## Non-goals

- Do not replace env vars; keep env vars as the “escape hatch” and highest-precedence override.
- Do not require a daemon or centralized server to manage config.
- Do not attempt to configure every possible parameter in one go; optimize for the 90% path.

## Proposed CLI

Add a new top-level command shipped by `abstractframework`:

- `af config` — run full interactive wizard
- `af config core` — configure AbstractCore defaults (provider/model, keys)
- `af config gateway` — configure gateway basics (dirs, auth token, allowed origins)
- `af config telegram` — configure Telegram bridge + access control + tool policy defaults
- `af config tools` — configure tool execution/approval defaults (host + Telegram UX)
- `af status` — show effective config and where it came from (file/env)
- `af env --shell bash|zsh|fish|powershell|cmd` — print exports for the current shell

Rationale:
- `abstractcore --config` already exists and is valuable, but extending it to cover gateway/integrations would blur
  ownership boundaries. `af config` can orchestrate multiple packages without coupling them at import-time.

## Config outputs (Phase 1)

Phase 1 focuses on **generating a `.env` file** plus clear instructions:

- Write a project-local file: `./.abstractframework.env` (default)
- Optional: `--output PATH`
- Optional: `--print` (no write; just stdout)

The wizard should also print OS-specific “how to load it” guidance:
- macOS/Linux: `set -a; source ./.abstractframework.env; set +a`
- PowerShell: `Get-Content .\\.abstractframework.env | % { if ($_ -match '^(\\w+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2].Trim('\"'), 'Process') } }`
- cmd.exe: emit a separate `set VAR=...` format via `af env --shell cmd`

## Config outputs (Phase 2)

Add a canonical config file in a user config directory (cross-platform):

- Use `platformdirs` (preferred) or a minimal fallback to:
  - macOS: `~/Library/Application Support/AbstractFramework/config.toml`
  - Linux: `~/.config/abstractframework/config.toml`
  - Windows: `%APPDATA%\\AbstractFramework\\config.toml`

Phase 2 also adds **auto-loading** for CLIs (`abstractgateway serve`, etc.) by reading this file unless env vars override.

## Precedence (must be explicit)

1. CLI flags (per command)
2. Environment variables
3. Project-local `.abstractframework.env` (if explicitly `--env-file` is passed)
4. User config file (`config.toml`)
5. Package defaults

## Telegram specifics (must include security)

The wizard must surface Telegram access control clearly and default to safe values:

- `ABSTRACT_TELEGRAM_DM_POLICY=allowlist`
- `ABSTRACT_TELEGRAM_GROUP_POLICY=disabled`
- Prompt for allowlisted DM `user_id` values and write `ABSTRACT_TELEGRAM_ALLOWED_USERS=...`
  - Provide a “how to discover your id” hint (`/whoami` in Telegram)
- If user selects “pairing” instead of “allowlist”, prompt for operator/admin `user_id` and write `ABSTRACT_TELEGRAM_ADMIN_USERS=...`.
- If user enables groups, prompt for allowlisted `chat_id` values and write `ABSTRACT_TELEGRAM_ALLOWED_CHATS=...`.

## Implementation approach (keep decoupling)

Implement `af config` as an orchestrator with lightweight adapters:

- **Core adapter**: uses `abstractcore.config.get_config_manager()` when available; otherwise falls back to env-only output.
- **Gateway adapter**: writes `ABSTRACTGATEWAY_*` env vars (auth token, data dir, flows dir, allowed origins).
- **Telegram adapter**: writes `ABSTRACT_TELEGRAM_*` env vars (bridge enable, transport, token/TDLib, access control).

Optional future enhancement:
- Entry-point based plugin discovery (similar to capability plugins) so integrations can contribute config steps without
  hard dependencies.

## Acceptance criteria

- Running `af config` from a fresh install can produce a working `.env` enabling:
  - gateway serving
  - Telegram bridge enabled with pairing approval
  - a usable provider/model default (or explicit instruction if not configured)
- Wizard supports non-interactive mode with flags (CI-friendly):
  - `af config telegram --dm-policy pairing --admin-users 123 ... --bot-token-env-var ...`
- Documentation updated to recommend the wizard over manual env exports.

## Notes

- `abstractframework` appears developer-oriented today, but a small `af` CLI is still useful as a reference and as a
  building block for dedicated apps/distributions.
- Dedicated apps can embed the same wizard adapters and output formats.
