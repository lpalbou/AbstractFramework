# 0874 — AbstractCore's default MLX model id names a repository that does not exist

> Package: abstractcore (providers/registry.py, endpoint/app.py)
> Type: bug
> Created: 2026-09-25
> Priority: normal
> Labels: models, mlx, defaults

## Summary

The MLX provider's registry default and the `abstractcore-endpoint --model` default were
`mlx-community/Qwen3-4B`, a Hugging Face repository that does not exist, so a user who relies on
the default gets a download/load failure. The published repository is
`mlx-community/Qwen3-4B-4bit`.

## Current code reality (checked 2026-09-25 ~01:20 CEST)

- Released abstractcore 2.15.1 (`v2.15.1`): `providers/registry.py` l.222
  `default_model="mlx-community/Qwen3-4B"`; `endpoint/app.py` l.1167 likewise.
- Local `main` of abstractcore carries the fix as commit `cb2c160` "fix(mlx): the default MLX model
  id names a published repo" (registry, endpoint, READMEs, example, new
  `tests/providers/test_mlx_default_model_id.py`), **not pushed and not released** at the time of
  this trace (main ahead of origin by 3).

## Scope

- Push the fix, release it in the next abstractcore patch, and follow with the root pin in a
  floor-pinned root patch only if the root pin must move for other reasons (a default-id fix alone
  does not need a root release).

## Acceptance criteria

- [ ] `git -C abstractcore show v<next>:abstractcore/providers/registry.py | grep Qwen3-4B-4bit`.
- [ ] The test asserts the default id exists in the catalog seed (no network needed).
- [ ] CHANGELOG entry under the released version.

## Testing

- `python -m pytest abstractcore/tests/providers/test_mlx_default_model_id.py -q`

## ADR status

- ADR impact: None.

## Receipts

- `untracked/coredoc-2026-09-25/STATUS.md` (abstractcore row); abstractcore commit `cb2c160`.
