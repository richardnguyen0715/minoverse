#!/usr/bin/env bash
# package.sh — Build the Minoverse desktop app and install to /Applications/
#
# Usage:
#   bash scripts/package.sh           # build + install to /Applications/
#   bash scripts/package.sh --no-install   # build only, skip install
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DESKTOP_DIR="$ROOT/apps/desktop"
SRC_TAURI="$DESKTOP_DIR/src-tauri"
BUNDLE_DIR="$SRC_TAURI/target/release/bundle/macos"
APP_NAME="Minoverse.app"
INSTALL_DIR="/Applications"

NO_INSTALL=false
for arg in "$@"; do
  [[ "$arg" == "--no-install" ]] && NO_INSTALL=true
done

# ── Preflight checks ─────────────────────────────────────────────────────────
export PATH="$HOME/.cargo/bin:$PATH"

if ! command -v cargo &> /dev/null; then
  echo ""
  echo "❌  Rust / Cargo not found."
  echo "    Run: make desktop-rust"
  echo "    Then: source ~/.cargo/env"
  echo ""
  exit 1
fi

if ! command -v node &> /dev/null; then
  echo "❌  Node.js not found. Install from https://nodejs.org"
  exit 1
fi

# ── Build ─────────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Packaging Minoverse Desktop"
echo "  Project root: $ROOT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📦 Installing npm dependencies..."
cd "$DESKTOP_DIR"
npm install --silent

echo "🦀 Building Tauri app (release)..."
npm run build

# ── Locate the .app bundle ─────────────────────────────────────────────────────
if [ ! -d "$BUNDLE_DIR/$APP_NAME" ]; then
  echo "❌  Build succeeded but $APP_NAME not found in:"
  echo "    $BUNDLE_DIR"
  echo "    Check: apps/desktop/src-tauri/target/release/bundle/"
  exit 1
fi

echo ""
echo "✅ Build complete!"
echo "   Bundle: $BUNDLE_DIR/$APP_NAME"

# ── Install ───────────────────────────────────────────────────────────────────
if [ "$NO_INSTALL" = true ]; then
  echo ""
  echo "   Skipped install (--no-install). To install manually:"
  echo "   cp -r \"$BUNDLE_DIR/$APP_NAME\" \"$INSTALL_DIR/\""
  echo ""
  exit 0
fi

echo ""
echo "📱 Installing to $INSTALL_DIR/$APP_NAME ..."

# Remove old version if present
if [ -d "$INSTALL_DIR/$APP_NAME" ]; then
  rm -rf "$INSTALL_DIR/$APP_NAME"
  echo "   Removed old version"
fi

cp -r "$BUNDLE_DIR/$APP_NAME" "$INSTALL_DIR/"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🎉 Minoverse.app installed!"
echo ""
echo "  You can now:"
echo "   • Double-click Minoverse in /Applications/"
echo "   • Add it to your Dock"
echo "   • Spotlight search → 'Minoverse'"
echo ""
echo "  The app will start all services automatically on launch."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Open Finder at /Applications so user can see the app
open "$INSTALL_DIR" 2>/dev/null || true
