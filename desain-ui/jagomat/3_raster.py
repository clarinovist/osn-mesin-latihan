"""Bikin pembungkus HTML untuk tiap target raster.

Chrome headless dipakai sebagai rasterizer (cairosvg/rsvg tidak terpasang).
Tiap berkas HTML berukuran persis sama dengan PNG yang dituju supaya
screenshot 1:1 tanpa penskalaan ulang.
"""
import pathlib

D = pathlib.Path(__file__).resolve().parent
(D / "raster").mkdir(exist_ok=True)

RESET = (
    "html,body{margin:0;padding:0;overflow:hidden}"
    "body{display:flex;align-items:center;justify-content:center}"
)


def tulis(nama, w, h, latar, isi):
    css = f"{RESET}body{{width:{w}px;height:{h}px;background:{latar};}}"
    html = (
        f'<!DOCTYPE html><html><head><meta charset="utf-8">'
        f"<style>{css}</style></head><body>{isi}</body></html>"
    )
    (D / "raster" / nama).write_text(html, encoding="utf-8")
    return nama


# ── favicon: latar transparan, mark sederhana ──────────────────────
for px in (16, 32, 48):
    tulis(
        f"favicon-{px}.html", px, px, "transparent",
        f'<img src="../mark-sederhana.svg" width="{px}" height="{px}">',
    )

# ── apple-touch-icon: iOS TIDAK mendukung transparan -> latar solid,
#    padding 12% tiap sisi supaya ikon tidak menempel tepi ──────────
tulis(
    "apple-touch-180.html", 180, 180, "#FFF8EE",
    '<img src="../mark-sederhana.svg" width="138" height="138">',
)

# ── PWA (opsional, kalau nanti mau Add to Home Screen) ─────────────
for px in (192, 512):
    tulis(
        f"pwa-{px}.html", px, px, "#FFF8EE",
        f'<img src="../mark-sederhana.svg" width="{int(px*0.76)}" '
        f'height="{int(px*0.76)}">',
    )

print("pembungkus HTML siap di raster/")

# ── og:image 1200x630 — share WhatsApp / Facebook ──────────────────
# Margin aman 60px tiap sisi; tidak ada elemen penting di luar itu.
OG = (
    '<div style="display:flex;flex-direction:column;align-items:center;'
    'justify-content:center;gap:26px;width:100%;height:100%">'
    '<img src="../lockup-hero.svg" height="132">'
    '<div style="font-family:-apple-system,Helvetica,sans-serif;'
    'font-size:40px;color:#16213e">Jago karena tahu caranya.</div>'
    "</div>"
)
tulis("og-image.html", 1200, 630, "#FFF8EE", OG)
print("og-image.html siap")
