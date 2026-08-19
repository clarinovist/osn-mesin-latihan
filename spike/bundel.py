#!/usr/bin/env python3
"""Gabungkan index.html + toSamples.js jadi SATU berkas mandiri.

Jalankan:
    ./.venv/bin/python bundel.py              # -> latihan.html
    ./.venv/bin/python bundel.py keluaran.html

Kenapa ada: `index.html` memuat `toSamples.js` lewat `<script src>`. Di Mac
itu tidak masalah, tapi begitu berkasnya dikirim ke iPhone (AirDrop, Files,
iCloud), yang terkirim hanya satu berkas — halaman terbuka, kanvas mati
total, dan tidak ada pesan error yang menjelaskan kenapa.

Berkas hasil bundel tidak punya satu pun rujukan ke luar: nol `<script src>`,
nol `fetch`, nol `XMLHttpRequest`. Sifat itu diperiksa di akhir, bukan
diasumsikan — jaminan "tidak menyentuh internet" (Rencana Spike, Bagian
"Keputusan") harus bisa dibuktikan dengan membaca satu berkas.

Sumbernya tetap dua berkas terpisah supaya `toSamples.js` bisa diuji Node
tanpa DOM. Bundel ini artefak turunan, bukan sumber kebenaran.
"""
import json
import re
import sys
from pathlib import Path

SPIKE_DIR = Path(__file__).resolve().parent

# Pola yang menandakan halaman bisa menghubungi jaringan. Diperiksa atas
# hasil bundel, bukan atas sumbernya.
POLA_JARINGAN = [
    (r"<script[^>]+\bsrc\s*=", "masih ada <script src> — berkas tidak mandiri"),
    (r"<link[^>]+\bhref\s*=", "masih ada <link href> ke berkas luar"),
    (r"\bfetch\s*\(", "ada pemanggilan fetch()"),
    (r"\bXMLHttpRequest\b", "ada XMLHttpRequest"),
    (r"\bWebSocket\b", "ada WebSocket"),
    (r"\bnavigator\.sendBeacon\b", "ada navigator.sendBeacon"),
    (r"\bimport\s*\(", "ada dynamic import()"),
    (r"https?://(?!www\.w3\.org)", "ada URL http(s) ke domain luar"),
]


def bundel(sumber_html=None, sumber_js=None, soal_json=None):
    sumber_html = Path(sumber_html or SPIKE_DIR / "index.html")
    sumber_js = Path(sumber_js or SPIKE_DIR / "toSamples.js")

    html = sumber_html.read_text()
    js = sumber_js.read_text()

    pola = re.compile(r'<script\s+src=["\']' + re.escape(sumber_js.name) + r'["\']\s*>\s*</script>')
    if not pola.search(html):
        raise SystemExit(
            f"Tidak menemukan <script src=\"{sumber_js.name}\"> di {sumber_html.name}. "
            "Struktur berkas berubah — perbarui bundel.py."
        )

    catatan = (
        "<!-- Berkas mandiri hasil bundel.py — jangan diedit langsung.\n"
        f"     Sumber: {sumber_html.name} + {sumber_js.name}\n"
        "     Nol rujukan ke luar: tidak ada script src, fetch, atau URL domain lain. -->"
    )
    sisip = catatan + "\n<script>\n" + js.rstrip() + "\n</script>"

    # Set soal alternatif disuntikkan SEBELUM skrip utama, lewat window.SOAL_KUSTOM.
    # index.html memakainya kalau ada, jadi perekamnya tidak perlu digandakan.
    if soal_json:
        data = json.loads(Path(soal_json).read_text())
        daftar = [{"soal_id": s["soal_id"], "teks": s["teks"]} for s in data["soal"]]
        sisip += (
            "\n<script>\n"
            f"  // Set soal: {data.get('nama', '?')}\n"
            f"  // {data.get('tujuan', '')}\n"
            "  window.SOAL_KUSTOM = " + json.dumps(daftar, ensure_ascii=False, indent=2) + ";\n"
            "</script>"
        )

    return pola.sub(lambda _: sisip, html, count=1)


def periksa_mandiri(teks):
    """Kembalikan daftar pelanggaran. Kosong = benar-benar mandiri."""
    masalah = []
    for pola, pesan in POLA_JARINGAN:
        for m in re.finditer(pola, teks, re.IGNORECASE):
            baris = teks[: m.start()].count("\n") + 1
            masalah.append(f"baris {baris}: {pesan} -> {m.group(0)[:60]!r}")
    return masalah


def main():
    argumen = [a for a in sys.argv[1:] if not a.startswith("--")]
    soal_json = None
    for a in sys.argv[1:]:
        if a.startswith("--soal="):
            soal_json = a.split("=", 1)[1]

    if soal_json == "mudah":
        soal_json = SPIKE_DIR / "soal_mudah.json"

    bawaan = "latihan-mudah.html" if soal_json else "latihan.html"
    keluaran = Path(argumen[0]) if argumen else SPIKE_DIR / bawaan
    teks = bundel(soal_json=soal_json)

    masalah = periksa_mandiri(teks)
    if masalah:
        print("⛔ Hasil bundel TIDAK mandiri:")
        for m in masalah:
            print("  -", m)
        raise SystemExit(1)

    keluaran.write_text(teks)
    kb = keluaran.stat().st_size / 1024
    print(f"Selesai: {keluaran}  ({kb:.0f} KB, satu berkas, nol rujukan luar)")
    if soal_json:
        data = json.loads(Path(soal_json).read_text())
        print(f"Set soal: {data.get('nama')} — {len(data['soal'])} soal")
    print("\nSajikan lewat WiFi supaya bisa dibuka di HP:")
    print("    ./.venv/bin/python sajikan.py")


if __name__ == "__main__":
    main()
