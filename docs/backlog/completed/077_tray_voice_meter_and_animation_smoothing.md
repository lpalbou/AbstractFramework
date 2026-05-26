# Backlog: Tray voice meter + animation smoothing

## Summary
Improve tray icon feedback by driving the speaking animation from real audio levels, smoothing the thinking animation to stop flicker, and fixing tray click behavior after voice interrupts.

## Why
- Speaking status should reflect real audio output for better UX clarity.
- The current thinking spinner flickers and looks unstable.
- Single-click should reliably reopen the bubble after a voice interrupt.

## Scope
### In scope
- Tray speaking animation driven by live audio levels (local + gateway TTS).
- Smooth, non-flickering thinking animation.
- Robust single-click behavior after double-click voice stop.

### Out of scope
- New voice selection UI or backend voice catalogs.
- Changes to gateway audio APIs.

## Dependencies
- AbstractVoice audio player chunk callbacks.
- Gateway TTS wav payloads for meter extraction.

## Expected outcomes
- Speaking icon animates based on real audio amplitude.
- Thinking spinner is smooth and non-flickering.
- Single-click reliably opens the bubble after voice stop.

## Full Report
- **Summary**: Added a real audio meter pipeline to the tray speaking animation, replaced the flickering thinking spinner with a smooth dot spinner, and made single-click open the bubble if voice pause/resume fails after a stop.
- **Implementation**:
  - Added voice meter callbacks in `abstractassistant/ui/qt_bubble.py` and `QtBubbleManager`, wired to `AbstractAssistantApp.update_voice_meter`.
  - Implemented audio meter emission in `abstractassistant/core/tts_manager.py` (from AbstractVoice audio chunks) and `abstractassistant/core/gateway_voice_manager.py` (from WAV envelope).
  - Updated `abstractassistant/utils/icon_generator.py` to support a meter-driven speaking animation and a smoother thinking spinner rendered at 2x and downsampled.
  - Hardened tray single-click behavior in `abstractassistant/app.py` to fall back to opening the bubble when voice pause/resume fails.
- **Tests**: Not run (not requested).
