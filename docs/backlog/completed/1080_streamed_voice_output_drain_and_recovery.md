# 1080 — Streamed voice output drain and recovery

> Package: abstractassistant, abstractvoice
> Type: bug fix + incident investigation
> Created: 2026-10-31
> Completed: 2026-10-31
> Status: Completed (implementation verified; source changes not released or loaded in the running tray)
> Priority: high
> Labels: voice, streaming, playback, cancellation, recovery

## Summary

Investigate the desktop banner reporting that generated speech did not finish local playback.
Correct the drain contract and recover pending output without replaying the whole reply or
restarting microphone capture. The operator requested one adversarial architect; one additional
worker implemented AbstractVoice while the parent implemented Assistant and integration checks.

## Observed incident and initial code reality

The running tray PID 77339 uses `untracked/deploy/root/.venv`, the shared workspace environment.
Its `runtime/logs/assistant.log` contains the local drain timeout warning. That warning is emitted
after `_wait_for_stream_playback_drain()` expires and `_drain_audio()` stops/discards queued speech.
The log contains no progress/device detail proving whether pause, sleep or hardware initiated
this particular incident. A network or generation failure is not established by this banner.

Three defects were reproduced: pause consumed the wall-clock budget; cancellation waited for
that budget; a stale completion event succeeded despite pending/paused output. Inactive-device
reopening happened only when another chunk arrived, leaving final-chunk stalls unrecovered.

## Completed scope

- AbstractVoice owns constant-time queue accounting, a non-device-locking progress snapshot,
  callback error capture, and output-only recovery. Close precedes suffix/queue collection;
  a changed output rate converts remaining samples exactly once. Recovery cannot globally
  refresh PortAudio and invalidate the microphone.
- A stop request is visible before acquiring output-control locks. The callback becomes silent;
  opening, implicit/explicit recovery and conversion cannot restore cancelled audio. Assistant
  detaches a busy player and closes it on a worker so Qt does not wait behind an opening device.
- Assistant excludes pause, exits on cancellation/supersession, verifies actual pending output,
  and uses recent frame progress rather than a total-time limit. One recovery is permitted
  after five seconds without progress. Older players retain a pause-aware duration budget.
- Request identity is checked on the GUI thread for card/full-voice completion, including
  replay of the same card. Recovery and terminal logs contain generation/progress/state detail.
- Public voice/troubleshooting and native architecture documentation describe behavior and limits.

## Completion report

- Assistant: **237 passed**, including new drain/retirement/request-identity checks and existing
  GatewayVoiceManager, cancellation, latency, conversation, settings/output and palette tests.
- AbstractVoice: **62 passed** across recovery, continuity, resampling, device selection and
  relevant streaming/cancellation tests. Tests include different output rates, stale events,
  active/inactive stalls, failed recovery, cancellation during opening/conversion, idle device
  switching, callback/status lock inversion and immediate stop silence.
- Independent adversarial architect: **Approved**, independently ran 79 relevant checks plus
  forced callback/status and idle-route probes. It required fixes for GUI stop contention and
  stale request completion before approving.
- Real macOS output check used the actual shared Python environment and an isolated silent
  stream on **MacBook Pro Speakers**, 48 kHz. After final enqueue, the test stopped only its own
  output: 2,560 frames submitted / 21,440 pending / inactive. Assistant recovered it once:
  24,000 frames submitted / zero pending / idle, with one recovery notice. No synthesis, live
  Gateway calls, global device refresh, volume/device change or running-app restart was performed.
- Scope excludes Watch/iPhone, package publication and production restarts.

## ADR state, residual limits and release follow-up

ADR impact: none; this repairs the existing ownership boundary (Voice handles device/buffers,
Assistant handles request/UI policy), consistent with Voice ADR 0002 and Assistant ADR 0001.
Submitted hardware-buffer samples may be lost after disconnection; callback progress cannot
prove acoustic delivery. Physical hot-unplug/sleep and intelligible speech were not tested by
the silent output check. The original trigger remains unknown because the old log lacked detail.

The source changes remain local and require an **Assistant-only restart** to enter the running
tray; the Gateway need not restart. Release Voice with the new player APIs before Assistant,
raise all Assistant Voice dependency floors to that verified published version in the authorized
release wave, and validate registry-only installs. Do not claim recovery for older player APIs.
No release is authorized by this completed implementation record.
