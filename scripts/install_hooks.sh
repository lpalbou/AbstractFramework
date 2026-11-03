#!/bin/sh
# Install the AbstractFramework pre-push gate (scripts/hooks/pre-push) into repositories, opt-in:
#
#   scripts/install_hooks.sh <repo> [<repo> ...]     e.g. abstractcore abstractgateway root
#   scripts/install_hooks.sh --all                   every repository scripts/ci_local.sh covers
#
# It writes <repo>/.git/hooks/pre-push (git's own hooks directory, shared by the repository's
# worktrees) and never replaces a hook it did not write: an existing pre-push hook, or a
# core.hooksPath setting, stops it with a message. To remove the gate from a repository, delete
# that one file. docs/ci-local.md describes the gate.
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
root=$(git -C "$here" rev-parse --path-format=absolute --git-common-dir)
root=$(dirname "$root")
gate="$root/scripts/ci_local.sh"
marker="AbstractFramework pre-push gate"
[ -x "$gate" ] || { echo "install_hooks: $gate is missing (run this from the workspace's main checkout)" >&2; exit 2; }
if [ "$#" -eq 0 ]; then
  sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
fi
if [ "$1" = "--all" ]; then
  set -- abstractcore abstractgateway abstractruntime abstractagent abstractflow abstractuic \
         abstractcode abstractentity abstractobserver abstractassistant root
fi
status=0
for name in "$@"; do
  case "$name" in root|.|abstractframework) dir="$root" ;; *) dir="$root/$name" ;; esac
  if ! git -C "$dir" rev-parse --git-dir >/dev/null 2>&1; then
    echo "install_hooks: $name: no repository at $dir" >&2; status=1; continue
  fi
  if [ -n "$(git -C "$dir" config --get core.hooksPath || true)" ]; then
    echo "install_hooks: $name: core.hooksPath is set; not touching it (install by hand)" >&2; status=1; continue
  fi
  hooks=$(git -C "$dir" rev-parse --path-format=absolute --git-common-dir)/hooks
  target="$hooks/pre-push"
  if [ -e "$target" ] && ! grep -q "$marker" "$target"; then
    echo "install_hooks: $name: $target exists and is not this gate; left as it is" >&2; status=1; continue
  fi
  mkdir -p "$hooks"
  sed "s|__CI_LOCAL_SH__|$gate|" "$root/scripts/hooks/pre-push" > "$target.ci-local-new"
  chmod +x "$target.ci-local-new"
  mv "$target.ci-local-new" "$target"
  echo "install_hooks: $name: $target"
done
exit "$status"
