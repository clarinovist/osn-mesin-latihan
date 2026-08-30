"""Fase 1: kontrak paket topik ketiga — geometri datar (P4/P5/P6).

Paket ketiga adalah bukti kedua bahwa registry benar-benar menjadi seam
(plan 30 Aug 2026): paket baru terdaftar, komposisinya dipakai generator,
dan ia tidak mengubah paket pola-bilangan maupun aritmetika-dasar.
Keputusan pengguna: geometri-datar mulai di P4 (P3 ditunda), 10 template,
soal berbentuk teks (SVG belakangan).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import topik  # noqa: E402
from generator import buat_lembar, buat_soal  # noqa: E402


def _paket():
    return topik.ambil("geometri-datar")


# ── Identitas & registrasi ─────────────────────────────────────────────


def test_geometri_datar_terdaftar_dengan_identitas():
    paket = _paket()
    assert paket.id == "geometri-datar"
    assert paket.nama == "Geometri Datar"
    assert paket.judul_lembar == "Latihan Geometri Datar"
    assert paket.judul_penilaian == "Penilaian — Geometri Datar"


def test_geometri_datar_memulai_dengan_template_sudut():
    """Task 1.1 (kerangka): paket valid sejak template #1 #2 terisi.
    Daftar 10 template penuh diuji di Task 1.5 saat semua masuk."""
    paket = _paket()
    assert "sudut_pelurus_berpenyiku" in paket.templates
    assert "jumlah_sudut_segitiga" in paket.templates


# ── Komposisi per level (tabel plan 30 Aug 2026) ───────────────────────


def test_komposisi_p4_delapan_soal():
    komposisi = _paket().komposisi_untuk("P4")
    assert komposisi == (
        "sudut_pelurus_berpenyiku",
        "jumlah_sudut_segitiga",
        "keliling_luas_datar",
        "luas_segitiga_jajargenjang",
        "sudut_pelurus_berpenyiku",
        "jumlah_sudut_segitiga",
        "keliling_luas_datar",
        "luas_segitiga_jajargenjang",
    )


def test_komposisi_p5_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P5")
    assert komposisi == (
        "sudut_pelurus_berpenyiku",
        "jumlah_sudut_segitiga",
        "sudut_luar_segitiga",
        "keliling_luas_datar",
        "luas_segitiga_jajargenjang",
        "luas_segiempat_lain",
        "lingkaran_keliling_luas",
        "luas_arsiran",
        "jumlah_sudut_segitiga",
        "luas_segitiga_jajargenjang",
    )


def test_komposisi_p6_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P6")
    assert komposisi == (
        "sudut_luar_segitiga",
        "keliling_luas_datar",
        "luas_segitiga_jajargenjang",
        "luas_segiempat_lain",
        "lingkaran_keliling_luas",
        "juring",
        "luas_arsiran",
        "perbandingan_ukuran",
        "lingkaran_keliling_luas",
        "luas_arsiran",
    )


def test_geometri_menolak_level_di_luar_scope():
    """Paket P4/P5/P6 tidak boleh diam-diam membuat sesi untuk anak P3."""
    with pytest.raises(ValueError, match="geometri-datar"):
        buat_lembar(7, level="P3", topik="geometri-datar")
    with pytest.raises(ValueError, match="geometri-datar"):
        buat_soal("sudut_pelurus_berpenyiku", 7, level="P3", topik="geometri-datar")


# Level teks aneh -> P4 diuji di Task 1.5, saat seluruh template sudah
# ada dan buat_lembar P4 bisa dibangun penuh.


# ── Judul bagian ───────────────────────────────────────────────────────


def test_judul_bagian_geometri():
    paket = _paket()
    assert paket.judul_bagian == {
        "A": "Bagian A — Sudut",
        "B": "Bagian B — Keliling & luas",
        "C": "Bagian C — Lingkaran",
        "D": "Bagian D — Arsiran & perubahan ukuran",
    }
