#!/bin/bash
# Rasterisasi SVG -> PNG lewat Chrome headless.
#
# CATATAN: Chrome headless di mesin ini MENULIS screenshot lalu menggantung
# (tidak exit sendiri). Jadi: timeout pendek, exit code SENGAJA diabaikan,
# keberhasilan diverifikasi dari berkas PNG-nya — bukan dari exit code.
# Karena itu tidak boleh pakai `set -e`.
cd "$(dirname "$0")"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

shot() {  # nama lebar tinggi transparan(y/n)
  local n=$1 w=$2 h=$3 tr=$4 bg=""
  [ "$tr" = "y" ] && bg="--default-background-color=00000000"
  rm -f "raster/$n.png"
  rm -rf "/tmp/chr-$n"
  timeout 20 "$CHROME" --headless --disable-gpu --no-sandbox \
    --user-data-dir="/tmp/chr-$n" --hide-scrollbars $bg \
    --force-device-scale-factor=1 --window-size=$w,$h \
    --screenshot="raster/$n.png" \
    "file://$PWD/raster/$n.html" >/dev/null 2>&1
  pkill -f "chr-$n" 2>/dev/null
  rm -rf "/tmp/chr-$n"
  if [ -f "raster/$n.png" ]; then
    python3 - "$n" <<'PY'
import sys
from PIL import Image
n = sys.argv[1]
im = Image.open(f"raster/{n}.png")
alpha = "alpha" if im.mode in ("RGBA", "LA") else "opaque"
print(f"  OK  {n}.png  {im.size[0]}x{im.size[1]}  {im.mode} ({alpha})")
PY
  else
    echo "  GAGAL $n.png"
  fi
}

echo "Rasterisasi:"
shot favicon-16       16   16 y
shot favicon-32       32   32 y
shot favicon-48       48   48 y
shot apple-touch-180 180  180 n
shot pwa-192         192  192 n
shot pwa-512         512  512 n
shot og-image       1200  630 n
