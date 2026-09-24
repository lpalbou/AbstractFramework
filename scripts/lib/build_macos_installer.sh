#!/bin/sh
# =============================================================================
# Build the double-click macOS installers (release engineering, not for users)
# =============================================================================
# Produces, in --out DIR (default: ./dist/macos-installer):
#
#   AbstractFramework-Installer-macOS.zip
#       "AbstractFramework Installer/" with Install AbstractFramework.command,
#       Uninstall AbstractFramework.command, install.sh, uninstall.sh. A zip
#       keeps the executable bit that a browser download of a bare .command
#       loses. Unsigned: a browser-downloaded copy is quarantined, and
#       Gatekeeper blocks it until the user allows it in System Settings >
#       Privacy & Security ("Open Anyway"). Fine for testers, not for the
#       non-technical path.
#
#   AbstractFramework-Installer.pkg
#       A payload-free installer package (nothing is copied to /Applications).
#       Its postinstall script copies the same folder to
#       ~/Library/Application Support/AbstractFramework/Installer and opens
#       "Install AbstractFramework.command" in Terminal as the logged-in user,
#       so the user watches every step there. "Install for me only" (the only
#       domain offered) needs no admin password.
#
# Signing, the one step this script cannot do without the operator's Apple
# Developer account (Developer Program membership, 99 USD/year):
#   AF_PKG_SIGN_IDENTITY  "Developer ID Installer: <Name> (<TEAMID>)" in the
#                         login keychain -> productbuild --sign
#   AF_NOTARY_PROFILE     a notarytool keychain profile, created once with
#                         `xcrun notarytool store-credentials <name> --apple-id
#                         <id> --team-id <TEAMID>` (app-specific password)
#                         -> notarytool submit --wait, then stapler staple
# With both set, the .pkg opens on any Mac with no Gatekeeper warning. Without
# them the script still builds everything and says plainly what is unsigned.
#
# Usage:  sh scripts/lib/build_macos_installer.sh [--out DIR] [--version X]
# =============================================================================

if [ -n "${ZSH_VERSION:-}" ]; then emulate sh; fi
set -eu

SCRIPTS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$SCRIPTS_DIR/.." && pwd)"
OUT="$ROOT/dist/macos-installer"
VERSION="$(sed -n 's/^version = "\(.*\)"/\1/p' "$ROOT/pyproject.toml" | head -n 1)"
PKG_ID="ai.abstractframework.installer"

while [ $# -gt 0 ]; do
    case "$1" in
        --out) OUT="$2"; shift ;;
        --version) VERSION="$2"; shift ;;
        -h|--help) sed -n '2,36p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "ERROR: unknown argument: $1" >&2; exit 2 ;;
    esac
    shift
done
[ "$(uname -s)" = Darwin ] || { echo "ERROR: pkgbuild/productbuild exist only on macOS" >&2; exit 1; }
[ -n "$VERSION" ] || { echo "ERROR: no version (root pyproject.toml or --version)" >&2; exit 1; }

say() { printf '  $ %s\n' "$*"; }
STAGE="$OUT/stage"
BUNDLE="$STAGE/AbstractFramework Installer"
mkdir -p "$OUT"
[ -d "$STAGE" ] && rm -r "$STAGE"
mkdir -p "$BUNDLE" "$STAGE/scripts" "$STAGE/resources"

# --- the folder users see -----------------------------------------------------
for f in "Install AbstractFramework.command" "Uninstall AbstractFramework.command" install.sh uninstall.sh; do
    cp "$SCRIPTS_DIR/$f" "$BUNDLE/$f"
    chmod 755 "$BUNDLE/$f"
done
ZIP="$OUT/AbstractFramework-Installer-macOS.zip"
rm -f "$ZIP"
say ditto -c -k --keepParent "$BUNDLE" "$ZIP"
ditto -c -k --keepParent "$BUNDLE" "$ZIP"

# --- the .pkg -------------------------------------------------------------------
cp -R "$BUNDLE" "$STAGE/scripts/"
cat >"$STAGE/scripts/postinstall" <<'POSTINSTALL'
#!/bin/sh
# AbstractFramework .pkg postinstall: hand the install to Terminal, as the
# logged-in user, so every step is visible (ADR-0038: the script is the install).
set -eu
SRC="$(cd "$(dirname "$0")" && pwd)/AbstractFramework Installer"
if [ "$(id -u)" = 0 ]; then
    USER_NAME="$(stat -f %Su /dev/console)"
    if [ -z "$USER_NAME" ] || [ "$USER_NAME" = root ] || [ "$USER_NAME" = loginwindow ]; then
        echo "AbstractFramework: nobody is logged in at the screen; open the installer from a user session." >&2
        exit 1
    fi
    USER_UID="$(id -u "$USER_NAME")"
    USER_HOME="$(dscl . -read "/Users/$USER_NAME" NFSHomeDirectory | awk '{print $2}')"
    as_user() { launchctl asuser "$USER_UID" sudo -u "$USER_NAME" -H "$@"; }
else
    # Installer.app may run a user-domain script without HOME: ask Directory Services.
    USER_HOME="${HOME:-$(dscl . -read "/Users/$(id -un)" NFSHomeDirectory | awk '{print $2}')}"
    as_user() { "$@"; }
fi
DEST="$USER_HOME/Library/Application Support/AbstractFramework/Installer"
as_user mkdir -p "$DEST"
as_user cp -R "$SRC/." "$DEST/"
echo "AbstractFramework: installer copied to $DEST; opening it in Terminal"
as_user open -a Terminal "$DEST/Install AbstractFramework.command"
exit 0
POSTINSTALL
chmod 755 "$STAGE/scripts/postinstall"

cat >"$STAGE/resources/welcome.html" <<'HTML'
<html><body style="font-family:-apple-system,sans-serif">
<h2>AbstractFramework</h2>
<p>This installs AbstractFramework for you (not for other users of this Mac). No admin password is needed.</p>
<p>When you click <b>Install</b>, a Terminal window opens and shows each step as it downloads and sets
things up (about 5 to 15 minutes). It asks one question: whether AbstractFramework should start when you
log in. When it is done, your web browser opens AbstractFramework.</p>
</body></html>
HTML
cat >"$STAGE/resources/conclusion.html" <<'HTML'
<html><body style="font-family:-apple-system,sans-serif">
<h2>Almost there</h2>
<p>The installation continues in the <b>Terminal</b> window that just opened. Leave it open; your web
browser opens AbstractFramework when it is ready.</p>
<p>If something goes wrong, the Terminal window says what to do. To remove AbstractFramework later, open
<code>~/Library/Application Support/AbstractFramework/Installer</code> and double-click
<b>Uninstall AbstractFramework.command</b>.</p>
</body></html>
HTML
cat >"$STAGE/distribution.xml" <<XML
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="2">
    <title>AbstractFramework</title>
    <welcome file="welcome.html" mime-type="text/html"/>
    <conclusion file="conclusion.html" mime-type="text/html"/>
    <options customize="never" require-scripts="false" hostArchitectures="arm64,x86_64"/>
    <domains enable_anywhere="false" enable_currentUserHome="true" enable_localSystem="false"/>
    <choices-outline>
        <line choice="$PKG_ID"/>
    </choices-outline>
    <choice id="$PKG_ID" visible="false" title="AbstractFramework">
        <pkg-ref id="$PKG_ID"/>
    </choice>
    <pkg-ref id="$PKG_ID" version="$VERSION" onConclusion="none">component.pkg</pkg-ref>
</installer-gui-script>
XML

say pkgbuild --nopayload --scripts "$STAGE/scripts" --identifier "$PKG_ID" --version "$VERSION" "$STAGE/component.pkg"
pkgbuild --nopayload --scripts "$STAGE/scripts" --identifier "$PKG_ID" --version "$VERSION" "$STAGE/component.pkg" >/dev/null

PKG="$OUT/AbstractFramework-Installer.pkg"
rm -f "$PKG"
set -- productbuild --distribution "$STAGE/distribution.xml" --resources "$STAGE/resources" --package-path "$STAGE"
if [ -n "${AF_PKG_SIGN_IDENTITY:-}" ]; then set -- "$@" --sign "$AF_PKG_SIGN_IDENTITY"; fi
say "$@" "$PKG"
"$@" "$PKG" >/dev/null

SIGNED=0; NOTARIZED=0
if [ -n "${AF_PKG_SIGN_IDENTITY:-}" ]; then
    say pkgutil --check-signature "$PKG"
    pkgutil --check-signature "$PKG"
    SIGNED=1
    if [ -n "${AF_NOTARY_PROFILE:-}" ]; then
        say xcrun notarytool submit "$PKG" --keychain-profile "$AF_NOTARY_PROFILE" --wait
        xcrun notarytool submit "$PKG" --keychain-profile "$AF_NOTARY_PROFILE" --wait
        say xcrun stapler staple "$PKG"
        xcrun stapler staple "$PKG"
        NOTARIZED=1
    fi
fi

echo ""
echo "Built (version $VERSION):"
echo "  $ZIP"
echo "  $PKG"
if [ "$NOTARIZED" = 1 ]; then
    echo "  signed and notarized: opens on any Mac without a Gatekeeper warning"
elif [ "$SIGNED" = 1 ]; then
    echo "  SIGNED BUT NOT NOTARIZED: set AF_NOTARY_PROFILE; macOS still warns on other Macs"
else
    echo "  UNSIGNED: on other Macs Gatekeeper blocks both until the user clicks 'Open Anyway' in"
    echo "  System Settings > Privacy & Security. Set AF_PKG_SIGN_IDENTITY and AF_NOTARY_PROFILE to fix."
fi
