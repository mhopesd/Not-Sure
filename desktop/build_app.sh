#!/bin/bash
# ============================================================
# Build Personal Assistant as a macOS .app
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DESKTOP_DIR="$SCRIPT_DIR"
FRONTEND_DIR="$PROJECT_ROOT/figma-ui"

echo "🏗️  Building NotSure.app"
echo "   Project root: $PROJECT_ROOT"
echo ""

# ── Step 1: Build React frontend ──────────────────────────────
echo "📦 Step 1: Building React frontend..."
cd "$FRONTEND_DIR"
npm run build
echo "   ✓ Frontend built"

# ── Step 2: Copy frontend build into desktop/frontend ─────────
echo "📂 Step 2: Copying frontend to desktop/frontend..."
rm -rf "$DESKTOP_DIR/frontend"
cp -r "$FRONTEND_DIR/dist" "$DESKTOP_DIR/frontend"
echo "   ✓ Frontend copied"

# ── Step 3: Install Electron dependencies ─────────────────────
echo "📥 Step 3: Installing Electron dependencies..."
cd "$DESKTOP_DIR"
npm install
echo "   ✓ Dependencies installed"

# ── Step 4: Generate icon (if not present) ────────────────────
if [ ! -f "$DESKTOP_DIR/icons/icon.icns" ]; then
  echo "🎨 Step 4: Generating app icon..."
  mkdir -p "$DESKTOP_DIR/icons"

  # Create a simple icon using sips if we have a PNG
  if [ -f "$DESKTOP_DIR/icons/icon.png" ]; then
    # Ensure the source is real PNG format (may be JPEG saved as .png)
    REAL_SRC="/tmp/notsure_icon_src.png"
    sips -s format png "$DESKTOP_DIR/icons/icon.png" --out "$REAL_SRC" 2>/dev/null
    sips -z 1024 1024 "$REAL_SRC" --out "$REAL_SRC" 2>/dev/null

    # Create iconset from the validated PNG
    ICONSET="$DESKTOP_DIR/icons/icon.iconset"
    mkdir -p "$ICONSET"
    sips -z 16 16     "$REAL_SRC" --out "$ICONSET/icon_16x16.png"      2>/dev/null
    sips -z 32 32     "$REAL_SRC" --out "$ICONSET/icon_16x16@2x.png"   2>/dev/null
    sips -z 32 32     "$REAL_SRC" --out "$ICONSET/icon_32x32.png"      2>/dev/null
    sips -z 64 64     "$REAL_SRC" --out "$ICONSET/icon_32x32@2x.png"   2>/dev/null
    sips -z 128 128   "$REAL_SRC" --out "$ICONSET/icon_128x128.png"    2>/dev/null
    sips -z 256 256   "$REAL_SRC" --out "$ICONSET/icon_128x128@2x.png" 2>/dev/null
    sips -z 256 256   "$REAL_SRC" --out "$ICONSET/icon_256x256.png"    2>/dev/null
    sips -z 512 512   "$REAL_SRC" --out "$ICONSET/icon_256x256@2x.png" 2>/dev/null
    sips -z 512 512   "$REAL_SRC" --out "$ICONSET/icon_512x512.png"    2>/dev/null
    sips -z 1024 1024 "$REAL_SRC" --out "$ICONSET/icon_512x512@2x.png" 2>/dev/null
    iconutil -c icns "$ICONSET"
    rm -rf "$ICONSET" "$REAL_SRC"
    echo "   ✓ Icon generated from PNG"
  else
    echo "   ⚠ No icon.png found in desktop/icons/, using default Electron icon"
  fi
else
  echo "🎨 Step 4: Icon already exists, skipping"
fi

# ── Step 5: Build the .app with electron-builder ──────────────
echo "🔨 Step 5: Packaging as macOS .app..."
cd "$DESKTOP_DIR"
npx electron-builder --mac --dir
echo "   ✓ App packaged"

# ── Step 6: Copy to /Applications ─────────────────────────────
APP_OUTPUT="$PROJECT_ROOT/dist/electron/mac-arm64/NotSure.app"
if [ ! -d "$APP_OUTPUT" ]; then
  APP_OUTPUT="$PROJECT_ROOT/dist/electron/mac/NotSure.app"
fi

if [ -d "$APP_OUTPUT" ]; then
  echo "📲 Step 6: Installing to /Applications..."
  rm -rf "/Applications/NotSure.app"
  cp -a "$APP_OUTPUT" "/Applications/NotSure.app"
  echo "   ✓ Installed to /Applications/NotSure.app"
else
  echo "   ⚠ Could not find built .app at expected path"
  echo "   Check: $PROJECT_ROOT/dist/electron/"
  ls -la "$PROJECT_ROOT/dist/electron/" 2>/dev/null || true
fi

echo ""
echo "✅ Done! You can now launch NotSure from your Applications folder."
echo "   Or run: open '/Applications/NotSure.app'"
