"""Rakit favicon.ico multi-size + favicon.svg, lalu rapikan berkas final.

favicon.ico berisi 16/32/48 supaya browser & OS memilih sendiri ukuran
yang paling pas — bukan menskalakan satu ukuran (yang bikin buram).
"""
import pathlib
import shutil

from PIL import Image

D = pathlib.Path(__file__).resolve().parent
R = D / "raster"
OUT = D / "final"
OUT.mkdir(exist_ok=True)

# ── favicon.ico multi-size ─────────────────────────────────────────
img48 = Image.open(R / "favicon-48.png").convert("RGBA")
img48.save(OUT / "favicon.ico", format="ICO",
           sizes=[(16, 16), (32, 32), (48, 48)])

# ── salin aset final ke satu folder ────────────────────────────────
salin = {
    "mark-sederhana.svg": "mark-sederhana.svg",
    "mark-penuh.svg": "mark-penuh.svg",
    "mark-sederhana-tinta.svg": "mark-tinta.svg",
    "lockup-horizontal.svg": "lockup-horizontal.svg",
    "lockup-horizontal-cetak.svg": "lockup-cetak.svg",
    "lockup-hero.svg": "lockup-hero.svg",
}
for src, dst in salin.items():
    shutil.copy(D / src, OUT / dst)
shutil.copy(D / "mark-sederhana.svg", OUT / "favicon.svg")

for png in ("apple-touch-180", "pwa-192", "pwa-512", "og-image"):
    shutil.copy(R / f"{png}.png", OUT / f"{png}.png")

# ── verifikasi ─────────────────────────────────────────────────────
ico = Image.open(OUT / "favicon.ico")
print("favicon.ico ukuran:", sorted(ico.info.get("sizes", [])))
print("\nfinal/")
for f in sorted(OUT.iterdir()):
    print(f"  {f.name:26} {f.stat().st_size:>8,} byte")
