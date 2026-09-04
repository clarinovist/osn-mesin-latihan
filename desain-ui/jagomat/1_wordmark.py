"""Unduh Plus Jakarta Sans 800 dan konversi kata 'Jagomat' jadi path SVG.

Wordmark WAJIB berupa path, bukan <text>: halaman cetak A4 dan preview
file:// tidak memuat font CDN (CLAUDE.md sec.10), jadi wordmark ber-font
akan berubah bentuk atau hilang di dua permukaan itu.
"""
import pathlib
import urllib.request

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

DIR = pathlib.Path(__file__).resolve().parent
TTF = DIR / "PlusJakartaSans-ExtraBold.ttf"
URL = (
    "https://github.com/tokotype/PlusJakartaSans/raw/master/fonts/ttf/"
    "PlusJakartaSans-ExtraBold.ttf"
)

if not TTF.exists():
    urllib.request.urlretrieve(URL, TTF)
    print("unduh:", TTF.name, TTF.stat().st_size, "byte")

font = TTFont(TTF)
upm = font["head"].unitsPerEm
gs = font.getGlyphSet()
cmap = font.getBestCmap()
kern = {}
if "kern" in font:
    for st in font["kern"].kernTables:
        kern.update(st.kernTable)

# Skala: tinggi kapital (cap height) jadi acuan, bukan em.
cap = font["OS/2"].sCapHeight if hasattr(font["OS/2"], "sCapHeight") else 700
print("upm:", upm, "cap height:", cap)

TRACKING = -0.02  # letter-spacing -0.02em sesuai design system

parts, x = [], 0.0
for i, ch in enumerate(" Jagomat".strip()):
    name = cmap[ord(ch)]
    pen = SVGPathPen(gs)
    gs[name].draw(pen)
    d = pen.getCommands()
    if d:
        parts.append(f'<path transform="translate({x:.1f} 0)" d="{d}"/>')
    x += gs[name].width + TRACKING * upm
    if i + 1 < len("Jagomat"):
        nxt = cmap[ord("Jagomat"[i + 1])]
        x += kern.get((name, nxt), 0)

lebar = x - TRACKING * upm  # buang tracking setelah huruf terakhir
(DIR / "_wordmark_raw.txt").write_text(
    f"{lebar:.1f}\n{cap}\n{upm}\n" + "\n".join(parts), encoding="utf-8"
)
print(f"wordmark: lebar={lebar:.0f} unit, {len(parts)} glyph -> _wordmark_raw.txt")
