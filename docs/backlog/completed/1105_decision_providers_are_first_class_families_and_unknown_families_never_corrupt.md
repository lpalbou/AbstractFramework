# 1105 — Decision providers are first-class provider families; an unknown family never makes a config "corrupt"

> Package: AbstractCore
> Type: task
> Created: 2026-11-03
> Priority: high
> Labels: config, providers, decision, data-safety
> Status: Completed
> Completed: 2026-11-03 (recorded; shipped in abstractcore 2.32.0 and 2.33.0)

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

- [x] A config with a `typesafe` connection loads cleanly; a config with an invented family loads, keeps the entry, logs one sentence, writes no file.

## Receipts

- W3 running 2026-11-03 03:05 (worktree abstractcore/untracked/wt-w3-typesafe).

## Completion report (2026-11-03)

- `64cd7dba` "Provider profiles accept every HTTP provider the registry knows (TypeSafe, System One)" (tag
  `v2.32.0`) and `f60b856a` "A profile row this Core cannot load (unknown provider family) is skipped and said, kept
  verbatim on save; never a corrupt-config quarantine" (tag `v2.33.0`).
- `tests/config/test_provider_profile_unknown_family_kept.py`: an unknown family loads, writes no
  `.corrupt-*.bak`, says so in the log; a save keeps the row exactly; the decision providers are profile families.
