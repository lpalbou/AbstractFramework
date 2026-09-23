#!/usr/bin/env bash
# =============================================================================
# Tests for the package inventory (scripts/lib/packages.txt) and its seams.
# =============================================================================
#   1. every workspace script parses (bash -n)
#   2. `deps.sh check` passes against the real checkouts, and FAILS when the
#      manifest is mutated (a dropped edge, a wrong tier, a wrong name) —
#      proof that the check is not decoration
#   3. the bash loader (repo_groups.sh) and the Python helper read the same
#      packages in the same dependency order
#   4. scripts/install.sh and install.ps1 pins == docs/installers/install-manifest.json
#      (bootstrap.gateway_version == the root pyproject gateway pin, npm apps);
#      their crate versions == the docs/install.md table
#   5. the published launchers start npm packages that exist in packages.txt
#
# Read-only: nothing in the workspace is modified. Run:
#   bash scripts/tests/test_inventory.sh
# =============================================================================

set -u

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$(dirname "$TEST_DIR")"
ROOT_DIR="$(dirname "$SCRIPTS_DIR")"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/af_inventory_test.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

PASS=0
FAIL=0
check() {
    if [[ "$2" == "0" ]]; then
        echo "  PASS: $1"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $1"
        FAIL=$((FAIL + 1))
    fi
}

echo "== inventory tests =="

# --- 1. syntax -------------------------------------------------------------------
bad=""
for f in "$SCRIPTS_DIR"/*.sh "$SCRIPTS_DIR"/lib/*.sh "$SCRIPTS_DIR"/tests/*.sh; do
    bash -n "$f" 2>/dev/null || bad="$bad ${f#"$ROOT_DIR"/}"
done
[[ -z "$bad" ]]
check "bash -n on every scripts/*.sh, lib/*.sh, tests/*.sh${bad:+ (broken:$bad)}" "$?"

# --- 2. manifest check, green then red on mutations ---------------------------------
NO_COLOR=1 python3 "$SCRIPTS_DIR/lib/af_inventory.py" check >"$WORK/check.out" 2>&1
check "deps.sh check passes on the real workspace" "$?"

mutate_and_expect_fail() {
    # mutate_and_expect_fail <label> <sed expression>
    sed -E "$2" "$SCRIPTS_DIR/lib/packages.txt" >"$WORK/packages.txt"
    if cmp -s "$WORK/packages.txt" "$SCRIPTS_DIR/lib/packages.txt"; then
        check "mutation '$1' changed the manifest (test setup)" 1
        return
    fi
    AF_PACKAGES_FILE="$WORK/packages.txt" NO_COLOR=1 \
        python3 "$SCRIPTS_DIR/lib/af_inventory.py" check >"$WORK/mut.out" 2>&1
    [[ "$?" != "0" ]]
    check "check goes RED when $1" "$?"
}
mutate_and_expect_fail "abstractruntime loses its abstractcore edge" \
    's/^(abstractruntime .*)abstractcore:dep,/\1/'
mutate_and_expect_fail "panel-chat loses its ui-kit edge (tier left stale)" \
    's/^(panel-chat .*)ui-kit:peer$/\1-/'
mutate_and_expect_fail "abstractgateway claims the wrong tier" \
    's/^(abstractgateway +\|.*\| )5( +\|)/\14\2/'
mutate_and_expect_fail "flow gets the wrong npm name" \
    's#@abstractframework/flow #@abstractframework/flows#'
mutate_and_expect_fail "observer loses its panel-chat source alias" \
    's/^(observer .*)panel-chat:alias,/\1/'

# --- 3. bash loader == python helper ---------------------------------------------------
py_order="$(python3 "$SCRIPTS_DIR/lib/af_inventory.py" order | cut -f3 | sort)"
sh_order="$(ROOT_DIR="$ROOT_DIR" bash -c '
    source "$1/lib/repo_groups.sh"
    af_pkg_indices | while IFS= read -r i; do echo "${AF_PKG_ID[$i]}"; done' _ "$SCRIPTS_DIR" | sort)"
[[ -n "$py_order" && "$py_order" == "$sh_order" ]]
check "bash loader and af_inventory.py see the same $(echo "$py_order" | wc -l | tr -d ' ') packages" "$?"

sh_tiers="$(ROOT_DIR="$ROOT_DIR" bash -c '
    source "$1/lib/repo_groups.sh"
    af_pkg_indices | while IFS= read -r i; do echo "${AF_PKG_TIER[$i]}"; done' _ "$SCRIPTS_DIR" | tr '\n' ' ')"
sorted_tiers="$(echo "$sh_tiers" | tr ' ' '\n' | sed '/^$/d' | sort -n | tr '\n' ' ')"
[[ "$sh_tiers" == "$sorted_tiers" ]]
check "af_pkg_indices yields packages in non-decreasing tier order" "$?"

# --- 4. bootstrap installer pins vs install manifest, root pyproject, docs --------------
bash "$SCRIPTS_DIR/install.sh" --print-versions >"$WORK/install-versions.txt"
check "install.sh --print-versions runs" "$?"
python3 - "$WORK/install-versions.txt" "$ROOT_DIR" >"$WORK/pins.out" 2>&1 <<'PY'
import json, re, sys
from pathlib import Path

lines = [l.split() for l in Path(sys.argv[1]).read_text().splitlines() if l.strip()]
root = Path(sys.argv[2])
script = {(reg, name.lower()): ver for reg, name, ver in lines}
manifest = json.loads((root / "docs/installers/install-manifest.json").read_text())
problems = []
gw = manifest["bootstrap"]["gateway_version"]
pkg_gw = next(p["version"] for p in manifest["python_packages"] if p["id"] == "abstractgateway")
if gw != pkg_gw:
    problems.append(f"manifest bootstrap.gateway_version {gw} != python_packages abstractgateway {pkg_gw}")
expected = {("pypi", "abstractgateway"): gw}
for a in manifest["npm_apps"]:
    expected[("npm", a["package"].lower())] = a["version"]
for key, ver in expected.items():
    if script.get(key) != ver:
        problems.append(f"install.sh {key} = {script.get(key)}, install-manifest.json = {ver}")
for key in script:
    if key[0] != "crates" and key not in expected:
        problems.append(f"install.sh pins {key} which install-manifest.json does not list")
# root pyproject gateway pin
pyproject = (root / "pyproject.toml").read_text()
m = re.search(r'"abstractgateway==([^"]+)"', pyproject)
if not m or m.group(1) != gw:
    problems.append(f"pyproject abstractgateway pin {m and m.group(1)} != bootstrap {gw}")
# install.ps1 carries the same pins
ps1 = (root / "scripts/install.ps1").read_text()
m = re.search(r"^\$AfGatewayPinDefault = '([^']+)'", ps1, re.M)
if not m or m.group(1) != gw:
    problems.append(f"install.ps1 gateway pin {m and m.group(1)} != {gw}")
for (reg, name), ver in script.items():
    if reg in ("npm", "crates") and f"'{name}@{ver}'" not in ps1.lower():
        problems.append(f"install.ps1 does not pin {name}@{ver}")
# crates vs the docs/install.md table
install_md = (root / "docs/install.md").read_text()
for (reg, name), ver in script.items():
    if reg != "crates":
        continue
    row = next((l for l in install_md.splitlines() if f"cargo install {name}" in l and l.startswith("|")), None)
    if row is None or not row.rstrip().rstrip("|").strip().endswith(ver):
        problems.append(f"crate {name} {ver}: docs/install.md row is {row!r}")
print("\n".join(problems) if problems else "ok")
sys.exit(1 if problems else 0)
PY
status=$?
[[ "$status" == "0" ]] || sed 's/^/        /' "$WORK/pins.out"
check "install.sh/install.ps1 pins == install-manifest.json == pyproject gateway pin; crates == docs/install.md" "$status"

# --- 5. launchers reference real npm packages ---------------------------------------------
missing=""
for f in flow.sh observer.sh code.sh console.sh entity.sh; do
    spec="$(grep -oE 'NPM_SPEC:-@abstractframework/[a-z-]+' "$SCRIPTS_DIR/$f" | head -1 | sed 's/.*:-//')"
    if [[ -z "$spec" ]] || ! grep -qE "\| *${spec} +\|" "$SCRIPTS_DIR/lib/packages.txt"; then
        missing="$missing $f(${spec:-none})"
    fi
done
[[ -z "$missing" ]]
check "published launchers start npm packages listed in packages.txt${missing:+ (bad:$missing)}" "$?"

echo ""
echo "== results: $PASS passed, $FAIL failed =="
[[ "$FAIL" == "0" ]]
