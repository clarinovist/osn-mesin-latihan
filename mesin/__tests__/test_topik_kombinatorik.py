"""Fase 2: kontrak paket topik keempat — kombinatorik (P5/P6).

Keputusan pengguna #2: kombinatorik TEKS dulu — soal diekspos utuh dalam
teks; diagram pohon/petak/Venn jadi penyempurnaan render_badan belakangan.
11 template menutup cakupan: aturan mencacah, susun angka, permutasi &
kombinasi, dan penerapan (jabat tangan, jalur petak, sarang merpati,
inklusi-eksklusi).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import topik  # noqa: E402
from generator import buat_lembar, buat_soal  # noqa: E402


def _paket():
    return topik.ambil("kombinatorik")


# ── Identitas & registrasi ─────────────────────────────────────────────


def test_kombinatorik_terdaftar_dengan_identitas():
    paket = _paket()
    assert paket.id == "kombinatorik"
    assert paket.nama == "Kombinatorik"
    assert paket.judul_lembar == "Latihan Kombinatorik"
    assert paket.judul_penilaian == "Penilaian — Kombinatorik"


def test_kombinatorik_memulai_dengan_template_aturan():
    """Task 2.1 (kerangka): paket valid sejak template #1 #2 terisi."""
    paket = _paket()
    assert "aturan_tambah" in paket.templates
    assert "aturan_kali" in paket.templates


# ── Komposisi per level (tabel plan Fase 2) ────────────────────────────


def test_komposisi_p5_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P5")
    assert komposisi == (
        "aturan_tambah",
        "aturan_kali",
        "susun_bilangan",
        "susun_bilangan_syarat",
        "jabat_tangan",
        "inklusi_eksklusi_2",
        "aturan_kali",
        "susun_bilangan",
        "jabat_tangan",
        "inklusi_eksklusi_2",
    )


def test_komposisi_p6_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P6")
    assert komposisi == (
        "permutasi_urutan",
        "permutasi_blok",
        "kombinasi_pilih",
        "jalur_petak",
        "sarang_merpati",
        "susun_bilangan_syarat",
        "inklusi_eksklusi_2",
        "permutasi_urutan",
        "kombinasi_pilih",
        "jalur_petak",
    )


def test_kombinatorik_menolak_level_di_luar_scope():
    """Paket P5/P6 tidak boleh diam-diam membuat sesi untuk anak P3/P4."""
    for level in ("P3", "P4"):
        with pytest.raises(ValueError, match="kombinatorik"):
            buat_lembar(7, level=level, topik="kombinatorik")
        with pytest.raises(ValueError, match="kombinatorik"):
            buat_soal("aturan_tambah", 7, level=level, topik="kombinatorik")


# Level teks aneh -> P5 diuji di Task 2.5, saat seluruh 11 template sudah
# ada dan buat_lembar P5 bisa dibangun penuh.


# ── Judul bagian ───────────────────────────────────────────────────────


def test_judul_bagian_kombinatorik():
    paket = _paket()
    assert paket.judul_bagian == {
        "A": "Bagian A — Aturan mencacah",
        "B": "Bagian B — Susunan angka",
        "C": "Bagian C — Permutasi & kombinasi",
        "D": "Bagian D — Penerapan",
    }
