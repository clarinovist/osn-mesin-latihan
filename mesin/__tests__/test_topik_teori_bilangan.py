"""Fase 3: kontrak paket topik kelima — teori-bilangan (P4/P5/P6).

8 template menutup cakupan bilangan & teori bilangan OSN SD: keterbagian,
faktorisasi prima, KPK/FPB, sisa pembagian, paritas, digit satuan pangkat,
dan jumlah deret (Gauss). Level P4/P5/P6.
"""

from __future__ import annotations

import math  # noqa: E402
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import topik  # noqa: E402
from generator import buat_lembar, buat_soal  # noqa: E402


def _paket():
    return topik.ambil("teori-bilangan")


# ── Identitas & registrasi ─────────────────────────────────────────────


def test_teori_bilangan_terdaftar_dengan_identitas():
    paket = _paket()
    assert paket.id == "teori-bilangan"
    assert paket.nama == "Teori Bilangan"
    assert paket.judul_lembar == "Latihan Teori Bilangan"
    assert paket.judul_penilaian == "Penilaian — Teori Bilangan"


def test_teori_bilangan_memulai_dengan_template_awal():
    """Task 3.1 (kerangka): paket valid sejak template #1 #2 terisi."""
    paket = _paket()
    assert "keterbagian" in paket.templates
    assert "prima_faktorisasi" in paket.templates


# ── Komposisi per level (tabel plan Fase 3) ────────────────────────────


def test_komposisi_p4_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P4")
    assert komposisi == (
        "keterbagian", "sisa_pembagian", "paritas",
        "keterbagian", "sisa_pembagian", "paritas",
        "keterbagian", "sisa_pembagian", "paritas",
        "keterbagian",
    )


def test_komposisi_p5_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P5")
    assert komposisi == (
        "keterbagian", "prima_faktorisasi", "kpk_dua_bilangan",
        "sisa_pembagian", "paritas", "gauss_deret",
        "keterbagian", "prima_faktorisasi", "kpk_dua_bilangan",
        "gauss_deret",
    )


def test_komposisi_p6_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P6")
    assert komposisi == (
        "keterbagian", "prima_faktorisasi", "kpk_dua_bilangan",
        "fpb_kpk_hubungan", "sisa_pembagian", "angka_satuan_pangkat",
        "gauss_deret", "keterbagian", "fpb_kpk_hubungan",
        "angka_satuan_pangkat",
    )


def test_teori_bilangan_menolak_level_di_luar_scope():
    """Paket P4-P6 tidak boleh diam-diam membuat sesi untuk anak P3."""
    with pytest.raises(ValueError, match="teori-bilangan"):
        buat_lembar(7, level="P3", topik="teori-bilangan")
    with pytest.raises(ValueError, match="teori-bilangan"):
        buat_soal("keterbagian", 7, level="P3", topik="teori-bilangan")


# Level teks aneh -> P4 diuji di Task 3.5, saat seluruh template sudah ada.


# ── Judul bagian ───────────────────────────────────────────────────────


def test_judul_bagian_teori_bilangan():
    paket = _paket()
    assert paket.judul_bagian == {
        "A": "Bagian A — Keterbagian",
        "B": "Bagian B — KPK & FPB",
        "C": "Bagian C — Sisa & paritas",
        "D": "Bagian D — Pola bilangan",
    }
