# 021 — Fix ACE‑Step latent_channels UnboundLocalError

## Summary

Fixed a runtime crash in the ACE‑Step backend:

```
UnboundLocalError: cannot access local variable 'latent_channels' where it is not associated with a value
```

## Why

`reference_mode="zeros"` referenced `latent_channels` before it was assigned, which caused the CLI run to fail before generation.

## Report

### What changed

- `abstractmusic/src/abstractmusic/backends/acestep_v15.py`
  - Moved `latent_channels = int(silence.shape[-1])` earlier so it is defined before `reference_mode` branching.

### Tests

Per user request, **no additional tests** were run.

## Outcome

CLI runs no longer crash at `refer_latents` initialization.

