"""Paket sintetis harus mewarisi renderer visual pemilik templatenya.

Topik "campuran" dan paket ad-hoc `gabungan()` merangkai templates dari
beberapa topik, tapi keduanya lahir dengan `render_badan=None`. Akibatnya
soal yang PUNYA bentuk visual khusus (SVG korek api, susunan titik
segitiga, dan deret dengan kotak isian) turun jadi teks polos begitu ia
muncul di sesi campuran/gabungan — termasuk sesi remedial, yang sekarang
memang dibangun dari paket gabungan.

Anak melihat soal yang berbeda untuk template yang sama, tergantung sesi
itu dibuat lewat jalur mana. Itu bukan variasi yang disengaja.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import render  # noqa: E402
import topics  # noqa: E402
from generator import buat_soal  # noqa: E402

# Template yang renderer teksnya JELAS berbeda dari renderer khususnya.
VISUAL = ("korek_api", "titik_segitiga")


def _badan(soal, paket):
    return render._badan_soal(soal, paket)


def test_campuran_mempertahankan_svg_pola_bilangan():
    """Soal korek api di sesi campuran harus tetap bergambar."""
    asli = topics.ambil("pola-bilangan")
    campuran = topics.ambil("campuran")
    for tid in VISUAL:
        soal = buat_soal(tid, 3, level="P4", topik="pola-bilangan")
        assert "<svg" in _badan(soal, asli), f"prasyarat: {tid} bergambar"
        assert "<svg" in _badan(soal, campuran), (
            f"{tid} kehilangan diagram di paket campuran"
        )


def test_campuran_mempertahankan_kotak_isian_deret():
    """Deret memakai kotak isian, bukan garis bawah mentah."""
    asli = topics.ambil("pola-bilangan")
    campuran = topics.ambil("campuran")
    soal = buat_soal("deret_aritmetika", 3, level="P4", topik="pola-bilangan")
    assert 'class="isian"' in _badan(soal, asli)
    assert 'class="isian"' in _badan(soal, campuran), (
        "deret kehilangan kotak isian di paket campuran"
    )


def test_gabungan_mempertahankan_renderer_pemiliknya():
    paket = topics.gabungan(["pola-bilangan", "logika"])
    soal = buat_soal("korek_api", 5, level="P3", topik="pola-bilangan")
    assert "<svg" in _badan(soal, paket), (
        "paket gabungan kehilangan diagram milik pola-bilangan"
    )


def test_renderer_tidak_dipakai_untuk_template_topik_lain():
    """Renderer pemilik hanya berlaku untuk templatenya sendiri.

    Kalau renderer pola-bilangan diterapkan membabi buta ke semua soal,
    template topik lain bisa ikut tersentuh. `_badan_khusus` mengembalikan
    None untuk yang bukan miliknya, dan itu harus dihormati.
    """
    paket = topics.gabungan(["pola-bilangan", "logika"])
    soal = buat_soal("soal_umur", 5, level="P5", topik="logika")
    hasil = _badan(soal, paket)
    assert "<svg" not in hasil
    assert soal.teks.split("\n")[0][:20] in hasil


def test_dispatch_renderer_per_pemilik_bukan_dirantai():
    """Tiap template dirender oleh renderer TOPIKNYA SENDIRI.

    Diuji dengan renderer palsu, bukan data nyata: saat ini hanya
    pola-bilangan yang punya render_badan, jadi versi "rantai semua
    renderer sampai ada yang menjawab" tidak bisa dibedakan dari versi
    "petakan per pemilik" — mutation test membuktikan mutasi itu LOLOS
    tanpa test ini.

    Bedanya baru terasa saat topik kedua punya renderer: renderer yang
    lapar (mengembalikan HTML untuk soal apa pun) akan membajak template
    milik topik lain, dan urutan paket diam-diam menentukan tampilan soal.
    """
    from dataclasses import replace as _replace

    asli = topics.ambil("pola-bilangan")
    logika = topics.ambil("logika")

    def renderer_lapar(soal):
        return "<div>DIBAJAK</div>"

    palsu = _replace(logika, render_badan=renderer_lapar)
    fungsi = topics._render_gabungan([palsu, asli])
    assert fungsi is not None

    soal_pola = buat_soal("korek_api", 3, level="P3", topik="pola-bilangan")
    assert "DIBAJAK" not in (fungsi(soal_pola) or ""), (
        "renderer topik lain membajak template pola-bilangan — "
        "renderer dirantai, bukan dipetakan per pemilik"
    )
    assert "<svg" in (fungsi(soal_pola) or "")

    soal_logika = buat_soal("soal_umur", 3, level="P5", topik="logika")
    assert fungsi(soal_logika) == "<div>DIBAJAK</div>", (
        "template logika tidak dirender oleh renderer topiknya sendiri"
    )


def test_remedial_lintas_topik_tetap_bergambar():
    """Jalur nyata: sesi remedial dibangun dari paket gabungan."""
    paket = topics.paket_untuk_template(["korek_api", "soal_umur"])
    soal = buat_soal("korek_api", 9, level="P3", topik="pola-bilangan")
    assert "<svg" in _badan(soal, paket), (
        "sesi remedial kehilangan diagram korek api"
    )
