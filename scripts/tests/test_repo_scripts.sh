#!/usr/bin/env bash
# =============================================================================
# Sandbox tests for clone.sh / status.sh / commit.sh / push.sh / pull.sh /
# build.sh (npm path) — real git, real npm, ZERO network, zero workspace writes.
# =============================================================================
# Builds a throwaway workspace under $TMPDIR:
#   - bare "GitHub" remotes on disk; a private git config rewrites
#     https://github.com/ to them (url.<base>.insteadOf), so clone.sh runs its
#     real code path offline
#   - a copy of THIS scripts/ directory whose packages.txt is replaced by a
#     3-package manifest: alpha (npm, tier 0), beta (npm, tier 1, build
#     fails on purpose), and the root meta-package
#
# Proves: clone.sh clones root + siblings; status groups by tier; commit.sh
# commits per repo; push.sh is a dry run by default, pushes with --yes, never
# pushes a diverged branch; pull.sh --dry-run moves nothing, pull.sh
# fast-forwards; build.sh --npm builds in tier order and exits 1 when a
# package fails.
#
# Run: bash scripts/tests/test_repo_scripts.sh      (KEEP_WORK=1 keeps the sandbox)
# =============================================================================

set -u

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$(dirname "$TEST_DIR")"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/af_repo_scripts_test.XXXXXX")"
WORK="$(cd "$WORK" && pwd -P)"
cleanup() {
    if [[ "${KEEP_WORK:-0}" == "1" ]]; then echo "sandbox kept: $WORK"; else rm -rf "$WORK"; fi
}
trap cleanup EXIT

# Isolated git: no user/system config, remotes rewritten to the sandbox.
export GIT_CONFIG_NOSYSTEM=1
export GIT_CONFIG_GLOBAL="$WORK/gitconfig"
export HOME="$WORK/home"
mkdir -p "$HOME"
cat >"$GIT_CONFIG_GLOBAL" <<EOF
[user]
    name = af-test
    email = af-test@example.invalid
[init]
    defaultBranch = main
[url "file://$WORK/remotes/"]
    insteadOf = https://github.com/
[advice]
    detachedHead = false
EOF
unset ABSTRACTGATEWAY_AUTH_TOKEN AGORA_API_KEY VIRTUAL_ENV 2>/dev/null || true
export NO_COLOR=1 npm_config_audit=false npm_config_fund=false npm_config_update_notifier=false

PASS=0
FAIL=0
check() {
    if [[ "$2" == "0" ]]; then
        echo "  PASS: $1"; PASS=$((PASS + 1))
    else
        echo "  FAIL: $1"; FAIL=$((FAIL + 1))
    fi
}
q() { "$@" >/dev/null 2>&1; }

echo "== repo script sandbox tests (work dir: $WORK) =="

# --- seed remotes ------------------------------------------------------------------
mkdir -p "$WORK/remotes/lpalbou" "$WORK/seed"
seed_repo() {
    # seed_repo <GitHubName> <populate-function>
    local name="$1" fn="$2" dir="$WORK/seed/$1"
    mkdir -p "$dir"
    q git -C "$dir" init
    "$fn" "$dir"
    q git -C "$dir" add -A
    q git -C "$dir" commit -m "initial"
    q git init --bare "$WORK/remotes/lpalbou/$name.git"
    q git -C "$dir" push "$WORK/remotes/lpalbou/$name.git" main
}
populate_root() {
    cp -R "$SCRIPTS_DIR" "$1/scripts"
    rm -rf "$1/scripts/__pycache__" "$1/scripts/lib/__pycache__"
    printf '[project]\nname = "abstractframework"\nversion = "0.0.1"\n' >"$1/pyproject.toml"
    printf 'alpha/\nbeta/\n' >"$1/.gitignore"
    cat >"$1/scripts/lib/packages.txt" <<'EOF'
# test manifest
alpha             | alpha | lpalbou/Alpha             | npm  | . | npm  | @aftest/alpha     | 0 | -
beta              | beta  | lpalbou/Beta              | npm  | . | npm  | @aftest/beta      | 1 | alpha:dep
abstractframework | .     | lpalbou/AbstractFramework | meta | . | pypi | abstractframework | 2 | beta:pin
EOF
}
populate_alpha() {
    cat >"$1/package.json" <<'EOF'
{ "name": "@aftest/alpha", "version": "1.0.0", "private": true,
  "scripts": { "build": "node -e \"require('fs').writeFileSync('built.txt', 'ok')\"" } }
EOF
    echo "built.txt" >"$1/.gitignore"
    echo "node_modules/" >>"$1/.gitignore"
}
populate_beta() {
    cat >"$1/package.json" <<'EOF'
{ "name": "@aftest/beta", "version": "1.0.0", "private": true,
  "scripts": { "build": "node -e \"console.error('intentional failure'); process.exit(3)\"" } }
EOF
    echo "node_modules/" >"$1/.gitignore"
}
seed_repo AbstractFramework populate_root
seed_repo Alpha populate_alpha
seed_repo Beta populate_beta

# --- clone.sh (fresh setup mode, real URLs rewritten to the sandbox) -----------------
WS="$WORK/ws"
bash "$WORK/seed/AbstractFramework/scripts/clone.sh" "$WS" >"$WORK/clone.out" 2>&1
check "clone.sh exits 0" "$?"
[[ -d "$WS/.git" && -d "$WS/alpha/.git" && -d "$WS/beta/.git" ]]
check "clone.sh cloned the root and both siblings (lowercase dirs)" "$?"
grep -q "Cloned:  3" "$WORK/clone.out"
check "clone.sh reports 3 clones" "$?"
bash "$WS/scripts/clone.sh" >"$WORK/clone2.out" 2>&1
grep -q "Updated: 2" "$WORK/clone2.out"
check "clone.sh re-run fast-forwards the existing siblings" "$?"

# --- status.sh -------------------------------------------------------------------------
bash "$WS/scripts/status.sh" >"$WORK/status.out" 2>&1
check "status.sh exits 0" "$?"
awk '/Tier 0/{t=0} /Tier 1/{t=1} /Tier 2/{t=2} /^  alpha /{a=t} /^  beta /{b=t} /^  abstractframework /{r=t}
     END{exit !(a==0 && b==1 && r==2)}' "$WORK/status.out"
check "status.sh groups alpha/beta/root into tiers 0/1/2" "$?"

# --- commit.sh + push.sh -----------------------------------------------------------------
echo "change" >"$WS/alpha/CHANGE.md"
bash "$WS/scripts/commit.sh" "test: alpha change" >"$WORK/commit.out" 2>&1
check "commit.sh exits 0" "$?"
[[ "$(git -C "$WS/alpha" log -1 --format=%s)" == "test: alpha change" ]]
check "commit.sh committed the dirty repo with the shared message" "$?"
[[ "$(git -C "$WS/beta" rev-list --count HEAD)" == "1" ]]
check "commit.sh left the clean repo alone" "$?"

REMOTE_ALPHA_BEFORE="$(git -C "$WORK/remotes/lpalbou/Alpha.git" rev-parse main)"
bash "$WS/scripts/push.sh" >"$WORK/push-dry.out" 2>&1
check "push.sh (dry run) exits 0" "$?"
grep -q "would push ↑1" "$WORK/push-dry.out"
check "push.sh dry run lists alpha as 'would push ↑1'" "$?"
[[ "$(git -C "$WORK/remotes/lpalbou/Alpha.git" rev-parse main)" == "$REMOTE_ALPHA_BEFORE" ]]
check "push.sh dry run pushed nothing" "$?"

bash "$WS/scripts/push.sh" --yes >"$WORK/push.out" 2>&1
check "push.sh --yes exits 0" "$?"
[[ "$(git -C "$WORK/remotes/lpalbou/Alpha.git" rev-parse main)" == "$(git -C "$WS/alpha" rev-parse main)" ]]
check "push.sh --yes pushed alpha main to its remote" "$?"

# Diverge beta: a commit lands on the remote from elsewhere, and one locally.
q git clone "https://github.com/lpalbou/Beta.git" "$WORK/other-beta"
echo "remote" >"$WORK/other-beta/REMOTE.md"
q git -C "$WORK/other-beta" add -A
q git -C "$WORK/other-beta" commit -m "remote beta change"
q git -C "$WORK/other-beta" push origin main
REMOTE_BETA="$(git -C "$WORK/remotes/lpalbou/Beta.git" rev-parse main)"
echo "local" >"$WS/beta/LOCAL.md"
q git -C "$WS/beta" add -A
q git -C "$WS/beta" commit -m "local beta change"
bash "$WS/scripts/push.sh" --yes --fetch >"$WORK/push-div.out" 2>&1
[[ "$?" != "0" ]]
check "push.sh --yes exits 1 when a repo diverged" "$?"
grep -q "DIVERGED" "$WORK/push-div.out"
check "push.sh reports beta as DIVERGED" "$?"
[[ "$(git -C "$WORK/remotes/lpalbou/Beta.git" rev-parse main)" == "$REMOTE_BETA" ]]
check "push.sh never force-pushed the diverged branch" "$?"

# --- pull.sh -----------------------------------------------------------------------------
q git clone "https://github.com/lpalbou/Alpha.git" "$WORK/other-alpha"
echo "upstream" >"$WORK/other-alpha/UPSTREAM.md"
q git -C "$WORK/other-alpha" add -A
q git -C "$WORK/other-alpha" commit -m "upstream alpha change"
q git -C "$WORK/other-alpha" push origin main
ALPHA_LOCAL_BEFORE="$(git -C "$WS/alpha" rev-parse main)"
bash "$WS/scripts/pull.sh" --dry-run --only alpha >"$WORK/pull-dry.out" 2>&1
check "pull.sh --dry-run exits 0 for a fast-forwardable repo" "$?"
grep -q "would fast-forward main ↓1" "$WORK/pull-dry.out"
check "pull.sh --dry-run reports 'would fast-forward main ↓1'" "$?"
[[ "$(git -C "$WS/alpha" rev-parse main)" == "$ALPHA_LOCAL_BEFORE" ]]
check "pull.sh --dry-run moved nothing" "$?"
bash "$WS/scripts/pull.sh" >"$WORK/pull.out" 2>&1
[[ "$?" != "0" ]]
check "pull.sh exits 1 while beta is diverged" "$?"
[[ "$(git -C "$WS/alpha" rev-parse main)" == "$(git -C "$WORK/remotes/lpalbou/Alpha.git" rev-parse main)" ]]
check "pull.sh fast-forwarded alpha" "$?"
[[ "$(git -C "$WS/beta" log -1 --format=%s)" == "local beta change" ]]
check "pull.sh left the diverged beta untouched" "$?"

# --- build.sh --npm (tier order, failure propagates) ----------------------------------------
if command -v npm >/dev/null 2>&1; then
    bash "$WS/scripts/build.sh" --npm --plan >"$WORK/plan.out" 2>&1
    awk '/^    alpha /{a=NR} /^    beta /{b=NR} END{exit !(a && b && a < b)}' "$WORK/plan.out"
    check "build.sh --plan lists alpha (tier 0) before beta (tier 1)" "$?"
    AF_BUILD_LOG_DIR="$WORK/build-logs" bash "$WS/scripts/build.sh" --npm >"$WORK/build.out" 2>&1
    [[ "$?" == "1" ]]
    check "build.sh --npm exits 1 when a package build fails" "$?"
    [[ -f "$WS/alpha/built.txt" ]]
    check "build.sh --npm built alpha" "$?"
    grep -q "intentional failure" "$WORK/build.out"
    check "build.sh --npm shows the failing build's log tail" "$?"
    grep -q "failed (exit 3)" "$WORK/build.out" && ! grep -q "npm:     2 npm packages built" "$WORK/build.out"
    check "build.sh --npm reports beta's real exit code and does not count it as built" "$?"
else
    echo "  SKIP: npm not found — build.sh --npm sandbox checks"
fi

echo ""
echo "== results: $PASS passed, $FAIL failed =="
[[ "$FAIL" == "0" ]]
