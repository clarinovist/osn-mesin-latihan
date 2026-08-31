"""Renderer visual topik pola-bilangan (dipecah 31 Aug 2026).

SVG korek api & titik segitiga + _badan_khusus: HTML untuk soal yang butuh
perlakuan visual khusus, atau None untuk menyerahkan ke renderer teks
bawaan render.py. Leaf murni — tidak mengimpor modul topik mana pun.
"""

from __future__ import annotations

import html

from templates import Soal

def _svg_korek(n_tampil: int, awal: int, tambah: int) -> str:
    """Gambar tiga bangun pertama pola korek api sebagai SVG.

    Jumlah titik zig-zag untuk n segitiga berbagi sisi adalah n+2, bukan n+1.
    Nilai batang dihitung ulang di sini dan dipakai sebagai label — kalau
    rumus di template berubah, ketidakcocokannya langsung kelihatan.
    """
    potong = []
    x0 = 6
    for i in range(3):
        n = i + 1
        half, y0, y1 = 20, 44, 14
        P = [(x0 + j * half, y0 if j % 2 == 0 else y1) for j in range(n + 2)]
        zig = "M " + " L ".join(f"{x} {y}" for x, y in P)
        bawah, atas = P[0::2], P[1::2]
        seg = [zig]
        for arr in (bawah, atas):
            seg += [
                f"M {a[0]} {a[1]} L {b[0]} {b[1]}" for a, b in zip(arr, arr[1:])
            ]
        jml = awal + tambah * i
        potong.append(
            f'<path d="{" ".join(seg)}" stroke="#000" stroke-width="1.6" '
            f'fill="none" stroke-linejoin="round"/>'
            f'<text x="{x0 + (n * half) / 2}" y="58" font-size="8.5" '
            f'text-anchor="middle">Gbr {n} — {jml}</text>'
        )
        x0 += (n + 1) * half + 22
    return (
        f'<svg viewBox="0 0 {x0} 64" width="100%" height="64" '
        f'xmlns="http://www.w3.org/2000/svg">{"".join(potong)}</svg>'
    )


def _svg_titik(n_tampil: int = 4) -> str:
    """Susunan titik segitiga: 1, 3, 6, 10."""
    potong, x0 = [], 10
    for n in range(1, n_tampil + 1):
        lebar = n * 13
        for baris in range(n):
            for kolom in range(baris + 1):
                cx = x0 + lebar / 2 - (baris * 13) / 2 + kolom * 13
                cy = 10 + baris * 12
                potong.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="3.4" fill="#000"/>')
        jml = n * (n + 1) // 2
        potong.append(
            f'<text x="{x0 + lebar / 2:.1f}" y="{10 + n_tampil * 12 + 6}" '
            f'font-size="8.5" text-anchor="middle">Gbr {n} — {jml}</text>'
        )
        x0 += lebar + 26
    tinggi = 10 + n_tampil * 12 + 12
    return (
        f'<svg viewBox="0 0 {x0} {tinggi}" width="100%" height="{tinggi}" '
        f'xmlns="http://www.w3.org/2000/svg">{"".join(potong)}</svg>'
    )




# ── Renderer badan khusus topik ini ─────────────────────────────────────
#
# Mengembalikan HTML untuk bentuk soal yang butuh perlakuan khusus (deret
# ditebalkan, diagram SVG), atau None untuk menyerahkan ke renderer teks
# bawaan render.py. Dipanggil render.py SEBELUM renderer bawaannya.


def _badan_khusus(soal: Soal) -> str | None:
    t = soal.template_id

    if t in ("deret_aritmetika", "deret_aritmetika_turun", "deret_geometri",
             "deret_bertingkat"):
        deret = html.escape(soal.teks).replace(
            "___", '<span class="isian"></span>'
        )
        return f'<div class="teks deret">{deret}</div>'

    if t == "korek_api":
        p = soal.parameter
        svg = _svg_korek(3, p["awal"], p["tambah"])
        return (
            '<div class="teks">Segitiga dibuat dari batang korek api. '
            "Segitiga yang bersebelahan memakai batang bersama.</div>"
            f"{svg}"
            f'<div class="tanya">Gambar ke-<b>{p["gambar_ke"]}</b> '
            "butuh berapa batang?</div>"
        )

    if t == "titik_segitiga":
        return (
            '<div class="teks">Titik disusun jadi segitiga.</div>'
            f"{_svg_titik(4)}"
            f'<div class="tanya">Gambar ke-<b>{soal.parameter["gambar_ke"]}</b> '
            "punya berapa titik?</div>"
        )

    return None
