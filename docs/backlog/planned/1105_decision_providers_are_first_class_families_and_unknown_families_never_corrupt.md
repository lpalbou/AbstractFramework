# 1105 — Decision providers are first-class provider families; an unknown family never makes a config "corrupt"

> Package: AbstractCore
> Type: task
> Created: 2026-11-03
> Priority: high
> Labels: config, providers, decision, data-safety

## Summary

abstractcore 2.32.0 logs `Unsupported provider family 'typesafe'` when loading the operator's `~/.abstractcore/config/abstractcore.json` (a saved hosted-Jev connection) and writes `abstractcore.json.corrupt-<stamp>.bak` (six copies on 2026-11-03). `typesafe`/`systemone` are abstractcore's own decision providers (`abstractcore/decision/engines/remote.py`). Register them wherever families are enumerated, and make the loader keep and report an unknown family instead of treating the file as corrupt.

## Why

Operator 2026-11-03: "i have no idea what that is, but this must not happen".

## Scope

### In scope

- Root cause (commit) of the family gap; registration in loader/registry/`/v1/models`/console cards; loader keeps unknown entries untouched and writes nothing; tests red today; changelog fragment.

### Out of scope

- Changing the backup mechanism for genuinely unparsable JSON.

## Acceptance criteria

- [ ] A config with a `typesafe` connection loads cleanly; a config with an invented family loads, keeps the entry, logs one sentence, writes no file.

## Receipts

- W3 running 2026-11-03 03:05 (worktree abstractcore/untracked/wt-w3-typesafe).
