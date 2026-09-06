"""Renderer visual topik pola-bilangan (dipecah 31 Aug 2026).

SVG korek api & titik segitiga + _badan_khusus: HTML untuk soal yang butuh
perlakuan visual khusus, atau None untuk menyerahkan ke renderer teks
bawaan render.py. Leaf murni — tidak mengimpor modul topik mana pun.
"""

from __future__ import annotations

import html

import design_tokens as T
from templates import Soal


def _kunci_ruas(a: tuple[int, int], b: tuple[int, int]) -> tuple[tuple[int, int], tuple[int, int]]:
    return tuple(sorted((a, b)))  # type: ignore[return-value]


def _ruas_bertumbuh(jumlah: int) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Bangun graf garis tersambung; prefix mana pun tetap graf yang sama."""
    if jumlah < 3:
        raise ValueError("pola korek membutuhkan minimal 3 ruas")
    ruas = []
    terlihat = set()
    # Spiral kotak membuat tiap ruas baru menyambung ke ujung ruas sebelumnya.
    arah = ((1, 0), (0, -1), (-1, 0), (0, 1))
    panjang, langkah, x, y = 1, 0, 0, 0
    while len(ruas) < jumlah:
        dx, dy = arah[langkah % 4]
        for _ in range(2):
            for _ in range(panjang):
                if len(ruas) >= jumlah:
                    break
                baru = (x + dx, y + dy)
                kunci = _kunci_ruas((x, y), baru)
                if kunci not in terlihat:
                    ruas.append(((x, y), baru))
                    terlihat.add(kunci)
                x, y = baru
            langkah += 1
            dx, dy = arah[langkah % 4]
        panjang += 1
    return ruas


def _id_aksesibel(jenis: str, identitas: str) -> tuple[str, str]:
    """Buat ID aman dan deterministik; namespace membedakan SVG identik."""
    aman = "".join(c if c.isalnum() or c in "-_" else "-" for c in identitas)
    dasar = f"pola-{jenis}-{aman}"
    return f"{dasar}-title", f"{dasar}-desc"


def _svg_korek(n_tampil: int, awal: int, tambah: int,
               namespace: str | None = None) -> str:
    """Gambar pola pertumbuhan ruas yang nested untuk semua parameter lama."""
    identitas = namespace or f"{n_tampil}-{awal}-{tambah}"
    title_id, desc_id = _id_aksesibel("korek", identitas)
    maksimum = awal + tambah * (n_tampil - 1)
    dasar = _ruas_bertumbuh(maksimum)
    skala, jarak = 10, 18
    semua = [titik for ruas in dasar for titik in ruas]
    min_x = min(x for x, _ in semua)
    max_x = max(x for x, _ in semua)
    min_y = min(y for _, y in semua)
    max_y = max(y for _, y in semua)
    lebar_bentuk = (max_x - min_x) * skala + 12
    tinggi_bentuk = (max_y - min_y) * skala + 12
    potong = []
    for i in range(n_tampil):
        gambar_ke = i + 1
        jumlah = awal + tambah * i
        garis = "".join(
            f'<line x1="{(a[0] - min_x) * skala + 6}" y1="{(a[1] - min_y) * skala + 6}" '
            f'x2="{(b[0] - min_x) * skala + 6}" y2="{(b[1] - min_y) * skala + 6}"/>'
            for a, b in dasar[:jumlah]
        )
        x0 = i * (lebar_bentuk + jarak)
        potong.append(
            f'<g data-gambar="{gambar_ke}" data-ruas="{jumlah}" '
            f'transform="translate({x0} 0)" stroke="{T.TEKS_UTAMA}" '
            f'stroke-width="1.6" fill="none" stroke-linejoin="round">{garis}'
            f'<text x="{lebar_bentuk / 2}" y="{tinggi_bentuk + 10}" font-size="8.5" '
            f'stroke="none" fill="{T.TEKS_UTAMA}" text-anchor="middle">'
            f'Gbr {gambar_ke} — {jumlah}</text></g>'
        )
    lebar = n_tampil * lebar_bentuk + (n_tampil - 1) * jarak
    tinggi = tinggi_bentuk + 14
    return (
        f'<svg viewBox="0 0 {lebar} {tinggi}" width="100%" height="{tinggi}" '
        f'role="img" aria-labelledby="{title_id} {desc_id}" '
        'xmlns="http://www.w3.org/2000/svg">'
        f'<title id="{title_id}">{n_tampil} tahap pola pertumbuhan batang</title>'
        f'<desc id="{desc_id}">Setiap gambar mempertahankan semua batang sebelumnya '
        'lalu menambah batang baru.</desc>'
        f'{"".join(potong)}</svg>'
    )


def _svg_titik(n_tampil: int = 4, namespace: str | None = None) -> str:
    """Susunan titik segitiga: 1, 3, 6, 10."""
    identitas = namespace or str(n_tampil)
    title_id, desc_id = _id_aksesibel("titik", identitas)
    potong, x0 = [], 10
    for n in range(1, n_tampil + 1):
        lebar = n * 13
        titik = []
        for baris in range(n):
            for kolom in range(baris + 1):
                cx = x0 + lebar / 2 - (baris * 13) / 2 + kolom * 13
                cy = 10 + baris * 12
                titik.append(
                    f'<circle cx="{cx:.1f}" cy="{cy}" r="3.4" '
                    f'fill="{T.TEKS_UTAMA}"/>'
                )
        jml = n * (n + 1) // 2
        titik.append(
            f'<text x="{x0 + lebar / 2:.1f}" y="{10 + n_tampil * 12 + 6}" '
            f'font-size="8.5" text-anchor="middle">Gbr {n} — {jml}</text>'
        )
        potong.append(
            f'<g data-gambar="{n}" data-titik="{jml}">{"".join(titik)}</g>'
        )
        x0 += lebar + 26
    tinggi = 10 + n_tampil * 12 + 12
    return (
        f'<svg viewBox="0 0 {x0} {tinggi}" width="100%" height="{tinggi}" '
        f'role="img" aria-labelledby="{title_id} {desc_id}" '
        'xmlns="http://www.w3.org/2000/svg">'
        f'<title id="{title_id}">{n_tampil} tahap pola susunan titik segitiga</title>'
        f'<desc id="{desc_id}">{n_tampil} tahap pola menunjukkan titik yang bertambah '
        'satu baris pada setiap tahap.</desc>'
        f'{"".join(potong)}</svg>'
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
        namespace = (
            f"soal-{soal.template_id}-{p['awal']}-{p['tambah']}-{p['gambar_ke']}"
        )
        svg = _svg_korek(3, p["awal"], p["tambah"], namespace=namespace)
        return (
            '<div class="teks">Pola batang korek api bertumbuh. Setiap gambar '
            f'mempertahankan batang sebelumnya lalu menambah {p["tambah"]} batang.</div>'
            f"{svg}"
            f'<div class="tanya">Gambar ke-<b>{p["gambar_ke"]}</b> '
            "butuh berapa batang?</div>"
        )

    if t == "titik_segitiga":
        gambar_ke = soal.parameter["gambar_ke"]
        namespace = f"soal-{soal.template_id}-{gambar_ke}"
        return (
            '<div class="teks">Titik disusun jadi segitiga.</div>'
            f"{_svg_titik(4, namespace=namespace)}"
            f'<div class="tanya">Gambar ke-<b>{gambar_ke}</b> '
            "punya berapa titik?</div>"
        )

    return None
