#!/bin/sh
# Run a repository's GitHub Actions jobs on this Mac before a push: docs/ci-local.md.
#
#   scripts/ci_local.sh <repo> [--job <name>] [--ref <commit>] [--list] [--help]
#
# Exit 0: every job that could run passed and none was skipped (or --allow-skipped).
# Exit 1: a job failed, or a job could not run here without --allow-skipped. Exit 2: usage.
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
uv=$(command -v uv 2>/dev/null || echo "$HOME/.local/bin/uv")
if [ ! -x "$uv" ]; then
  echo "ci_local: uv is required (https://docs.astral.sh/uv/)" >&2
  exit 2
fi
# PyYAML for the workflow files, in uv's cached ephemeral environment; no project, no downloads
# of a Python interpreter.
exec "$uv" run --quiet --no-project --no-python-downloads --python 3.12 --with "pyyaml==6.0.3" \
  python "$here/ci_local.py" "$@"
