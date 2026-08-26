"""Render lembar soal jadi HTML — struktur saja, tanpa CSS.

Dipecah dari cetak.py (Fase 3). Pemisahan tiga lapis:

  render.py       struktur DOM (fungsi di berkas ini)
  gaya_layar.py   tampilan browser/HP
  gaya_cetak.py   tampilan kertas A4

Struktur DOM-nya identik untuk kedua tampilan, sehingga test yang menjaga
kontrak — terutama "berkas anak tidak boleh memuat kunci" — cukup ditulis
sekali dan berlaku untuk keduanya.

Dua berkas per sesi, dan pemisahan ini tidak boleh dilanggar:

  <sesi>-SOAL.html      dipegang anak — TIDAK boleh memuat kunci
  <sesi>-PENILAIAN.html dipegang guru — kunci + tabel malrule

Alasan pemisahan: begitu kunci terlihat anak, dua kode yang paling berharga
(N menebak, K salah konsep) hilang selamanya dari data. Ada test yang
memastikan berkas anak tidak mengandung kunci.

Diagram digambar sebagai SVG, bukan ASCII: font monospace tidak dijamin ada
di headless Chrome, dan seni ASCII dari '/' dan '\\' berubah jadi coretan
tak beraturan saat font-nya proporsional.
"""

from __future__ import annotations

import html
import json

from gaya_cetak import GAYA_CETAK
from gaya_layar import GAYA_LAYAR
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


def _badan_soal(soal: Soal) -> str:
    """Teks soal + diagram. Deret ditebalkan supaya mudah dibaca sekilas."""
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

    # sisanya: teks biasa, baris pertama jadi badan, sisanya jadi pertanyaan
    baris = [b for b in soal.teks.split("\n") if b.strip()]
    if len(baris) == 1:
        return f'<div class="teks">{html.escape(baris[0])}</div>'
    isi = "".join(
        f'<div class="{"tanya" if i == len(baris) - 1 else "teks"}">'
        f"{html.escape(b.strip())}</div>"
        for i, b in enumerate(baris)
    )
    return isi


def _kartu_soal(nomor: int, soal: Soal) -> str:
    """Satu kartu soal dengan kotak-kotak diagnostik.

    Tinggi kotak 'Caraku' disesuaikan bagian: soal terbalik, tantangan, dan
    Bagian F butuh ruang lebih — soal terbalik dan Bagian F karena anak
    biasanya menulis deret panjang atau coretan rumus di situ.
    """
    tinggi = "besar" if soal.bagian in ("D", "E", "F") else (
        "sedang" if soal.bagian == "C" else "kecil"
    )

    restate = ""
    if soal.minta_restatement:
        restate = (
            '<div class="label">Soal ini mintanya apa? '
            "(tulis pakai kalimatmu sendiri)</div>"
            '<div class="restate"></div>'
        )

    lebar = "lebar" if soal.template_id in (
        "siklus_warna", "siklus_hari", "siklus_huruf"
    ) else ""
    n_isian = soal.parameter.get("n_minta", 1) if soal.template_id == "deret_aritmetika" else 1
    isian = " dan ".join(f'<span class="isian {lebar}"></span>' for _ in range(n_isian))

    awalan = "urutan ke-" if soal.template_id.startswith("deret_terbalik") else ""
    bintang = ' <span class="bintang">★</span>' if soal.tantangan else ""

    return (
        f'<div class="soal">'
        f'<span class="nomor">{nomor}</span>{bintang}'
        f"{_badan_soal(soal)}"
        f"{restate}"
        f'<div class="label">Caraku:</div>'
        f'<div class="cara {tinggi}"></div>'
        f'<div class="jawab">Jawabanku: {awalan}{isian}</div>'
        f'<div class="centang"><span class="kotak"></span>'
        f"belum pernah lihat soal seperti ini</div>"
        f"</div>"
    )


JUDUL_BAGIAN = {
    "A": "Bagian A — Lanjutkan polanya",
    "B": "Bagian B — Pola berulang",
    "C": "Bagian C — Pola gambar",
    "D": "Bagian D — Pola dibalik",
    "E": "Bagian E — Pola dalam cerita",
    "F": "Bagian F — Cari jalan pintasnya",
}

CATATAN_BAGIAN = {
    "D": "Baca pelan-pelan. Yang ditanya di bagian ini <b>berbeda</b> "
         "dari Bagian A.",
    # Anak P3-P4 terbiasa menulis deretnya satu per satu sampai ketemu, dan
    # itu memang cara yang sah di Bagian A-E. Di sini angkanya sengaja dibuat
    # terlalu jauh untuk itu. Tanpa kalimat ini sebagian anak akan mencoba
    # menulis 250 suku, kehabisan waktu, lalu mengosongkan sisa lembarnya —
    # dan yang tercatat jadi "tidak bisa", padahal masalahnya cuma belum
    # tahu boleh mencari jalan pintas.
    "F": "Angkanya terlalu besar untuk ditulis satu per satu. "
         "Coba cari <b>caranya</b>, bukan tulis semuanya.",
}


def _isi_lembar(soal: list[Soal]) -> list[str]:
    """Kartu-kartu soal + judul bagian, urut sesuai komposisi lembar."""
    isi, bagian_kini = [], None
    for i, s in enumerate(soal, start=1):
        if s.bagian != bagian_kini:
            bagian_kini = s.bagian
            judul = JUDUL_BAGIAN.get(bagian_kini, f"Bagian {bagian_kini}")
            isi.append(f'<div class="bagian">{judul}</div>')
            if bagian_kini in CATATAN_BAGIAN:
                isi.append(f'<div class="catatan-bagian">'
                           f"{CATATAN_BAGIAN[bagian_kini]}</div>")
        isi.append(_kartu_soal(i, s))
    return isi


def lembar_soal(
    soal: list[Soal],
    nama: str = "",
    tanggal: str = "",
    gaya: str | None = None,
) -> str:
    """HTML lembar anak. Tidak memuat kunci — dijaga oleh test.

    gaya: CSS mentah. Default GAYA_CETAK supaya pemanggil lama (cetak CLI,
    PDF via browser) tetap menghasilkan kertas yang sama persis; web
    (web.py) memanggil dengan GAYA_LAYAR.
    """
    css = GAYA_CETAK if gaya is None else gaya
    return f"""<!DOCTYPE html>
<html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Latihan Pola Bilangan</title><style>{css}</style></head><body>
<div class="wrap">
<h1>Latihan Pola Bilangan</h1>
<div class="identitas">
  <span>Nama: <span class="garis">{html.escape(nama)}</span></span>
  <span>Tanggal: <span class="garis pendek">{html.escape(tanggal)}</span></span>
  <span>Mulai: <span class="garis pendek"></span></span>
  <span>Selesai: <span class="garis pendek"></span></span>
</div>
<div class="petunjuk">
  <p><b>Cara mengerjakan — baca dulu:</b></p>
  <p>Tiap soal ada kotak <b>Caraku</b>. Tulis di situ bagaimana kamu dapat
  jawabannya. Boleh berantakan, boleh dicoret-coret. Yang penting kelihatan
  caramu.</p>
  <p>Kalau ada soal yang belum pernah kamu lihat, centang kotaknya. Itu
  <b>bukan</b> salah — itu menandakan soalnya memang baru, dan itu berguna.</p>
  <p>Tidak apa-apa ada yang kosong. Jangan menebak asal.</p>
</div>
{"".join(_isi_lembar(soal))}
<div class="akhir"><b>Sudah selesai?</b> Cek sekali lagi: apakah setiap kotak
"Caraku" ada isinya? Kalau ada jawaban yang kamu tulis tanpa cara, tulis dulu
caranya sekarang.</div>
</div>
</body></html>"""


def lembar_penilaian(
    soal: list[Soal],
    nama: str = "",
    tanggal: str = "",
    seed: int | None = None,
    gaya: str | None = None,
) -> str:
    """HTML lembar guru: kunci + tabel malrule + rekap."""
    baris = []
    for i, s in enumerate(soal, start=1):
        mal = "".join(
            f"<tr><td><span class=\"kode\">{m.kode}</span></td>"
            f"<td><b>{html.escape(m.jawaban)}</b></td>"
            f"<td>{html.escape(m.alasan)}</td></tr>"
            for m in s.malrule
        )
        tabel = (
            '<table class="kunci-tabel">'
            "<tr><th>Kode</th><th>Kalau dijawab</th><th>Artinya</th></tr>"
            f"{mal}</table>"
            if mal else '<div class="catatan-guru">'
                        "(tidak ada pola kesalahan terdaftar — baca kotak Caraku)</div>"
        )
        param = html.escape(json.dumps(s.parameter, ensure_ascii=False))
        baris.append(
            f'<div class="soal"><span class="nomor">{i}</span>'
            f'<span class="meta-template">{s.template_id} '
            f"<code>{param}</code></span>"
            f'<div class="kunci-nilai">'
            f"Kunci: {html.escape(s.kunci)}</div>{tabel}</div>"
        )

    rekap = "".join(
        f"<tr><td>{i}{' ★' if s.tantangan else ''}</td>"
        f"<td>{'&nbsp;' if s.minta_restatement else '—'}</td>"
        f"<td></td><td></td><td></td></tr>"
        for i, s in enumerate(soal, start=1)
    )

    css = GAYA_CETAK if gaya is None else gaya
    return f"""<!DOCTYPE html>
<html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Penilaian — Pola Bilangan</title><style>{css}</style></head><body>
<div class="wrap">
<h1>Lembar Penilaian — Pola Bilangan</h1>
<div class="identitas">
  <span>Nama: <b>{html.escape(nama) or "______"}</b></span>
  <span>Tanggal: <b>{html.escape(tanggal) or "______"}</b></span>
  {f"<span>seed: <code>{seed}</code></span>" if seed is not None else ""}
</div>
<div class="petunjuk">
  <p><b>Jangan diperlihatkan ke anak.</b></p>
  <p><b>Metrik utama = jumlah K, bukan skor.</b> Anak dengan 9 H skor 3 lebih
  siap daripada anak dengan 3 K skor 9.</p>
  <p>Alur baca, berhenti di yang pertama cocok:
  centang "belum pernah lihat" → <b>T</b>;
  jawaban tanpa Caraku → <b>N</b>;
  "mintanya apa" salah → <b>B</b>;
  cara/aturannya keliru → <b>K</b>;
  jawaban ≠ hasil di Caraku → <b>E</b>; selain itu salah hitung → <b>H</b>.</p>
</div>
{"".join(baris)}
<div class="bagian">Rekap</div>
<table class="rekap">
<tr><th>No</th><th>"Mintanya apa"</th><th>Jawaban</th><th>Kode</th>
<th>Catatan</th></tr>
{rekap}
</table>
<div class="akhir">
<p><b>Jumlah K: ______</b> ← angka yang dipantau</p>
<p><b>Jumlah T: ______</b> ← bukan kegagalan, ini peta materi yang belum diajarkan</p>
<p>Miskonsepsi yang muncul (tulis gagasannya, bukan nomor soalnya):</p>
<p>1. ______________________________________________</p>
<p>2. ______________________________________________</p>
<p>3. ______________________________________________</p>
</div>
</div>
</body></html>"""


def tulis(path, isi: str):
    from pathlib import Path

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(isi, encoding="utf-8")
    return path
