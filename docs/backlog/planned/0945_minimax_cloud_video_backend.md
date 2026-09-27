# 0945 — Cloud MiniMax video (Hailuo / H3) as an image-video provider

> Package: abstractvision, abstractcore, abstractgateway
> Type: task
> Created: 2026-09-27
> Priority: normal
> Labels: video, cloud-provider, next-wave

## Summary

Add MiniMax's cloud video API as a provider for `output.video` routes, so machines that cannot run local video
(every non-Apple host, and Macs below about 96 GiB) have a real video option. MiniMax's API is asynchronous:
create a task, poll it, then download the file — nothing in the framework speaks that shape today.

## Why

Operator, 2026-09-27: the model installer should propose video generation "(eg wan or minimax)"; for the cloud
path: "create a backlog planned item" (not this release). Linux/Windows hosts currently get `output.video`
unavailable with the reason "use an OpenAI-compatible video endpoint".

## Current code reality (2026-09-27)

- AbstractVision's OpenAI-compatible backend is synchronous and expects the video in one response; it cannot
  drive a task-id-and-poll API.
- No MiniMax key in AbstractCore's provider key maps (`abstractcore/config/manager.py:278-286`, `:656-664`).
- Plugin routing: `abstractvision/.../abstractcore_plugin.py:485`, `:804`; server `abstractcore/server/vision_endpoints.py:2483`.
- Estimate from the video worker: about 2–3 days.

## Scope

### In scope

- `abstractvision/backends/minimax.py`: create task → poll (bounded, cancellable) → fetch → store artifact; v1
  (Hailuo) and v2 (H3) models; typed errors (quota, auth, content policy, timeout) surfaced verbatim.
- `MINIMAX_API_KEY` wiring like the other providers (settings/console first; env only as the existing
  provider-key convention); provider appears in both consoles' provider screens and the video route editor.
- Cost/latency stated in the console before a run (the web and terminal consoles already show route tests).

### Out of scope

- Local MiniMax-H3 (0944). Any other cloud video vendor.

## Acceptance criteria

- [ ] A real generation through the gateway sandbox with a MiniMax key (operator-provided), artifact stored.
- [ ] Poll loop bounded and cancellable; tests with a recorded fake server cover success, failure, timeout.
- [ ] Both consoles can select `minimax` for `output.video` and test it.
- [ ] Released bottom-up (vision → core → gateway → root).

## Receipts

- Video worker report 2026-09-27; release ledger `untracked/release-2026-09-27/PLAN.md`.
