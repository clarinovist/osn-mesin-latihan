"""Fase 4: kontrak paket topik keenam — aritmatika-lanjut (P5/P6).

11 template menutup cakupan aritmatika terapan OSN SD: konversi satuan,
kecepatan/jarak/waktu, berpapasan, menyusul, debit, perbandingan senilai
& berbalik, kerja bersama, dan persen (diskon/untung-rugi/bertingkat).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import topik  # noqa: E402
from generator import buat_lembar, buat_soal  # noqa: E402


def _paket():
    return topik.ambil("aritmatika-lanjut")


# ── Identitas & registrasi ─────────────────────────────────────────────


def test_aritmatika_lanjut_terdaftar_dengan_identitas():
    paket = _paket()
    assert paket.id == "aritmatika-lanjut"
    assert paket.nama == "Aritmatika Lanjut"
    assert paket.judul_lembar == "Latihan Aritmatika Lanjut"
    assert paket.judul_penilaian == "Penilaian — Aritmatika Lanjut"


def test_aritmatika_lanjut_memulai_dengan_template_awal():
    """Task 4.1 (kerangka): paket valid sejak template #1 #2 terisi."""
    paket = _paket()
    assert "satuan_konversi" in paket.templates
    assert "kecepatan_jarak_waktu" in paket.templates


# ── Komposisi per level (tabel plan Fase 4) ────────────────────────────


def test_komposisi_p5_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P5")
    assert komposisi == (
        "satuan_konversi", "kecepatan_jarak_waktu",
        "debit", "perbandingan_senilai", "perbandingan_berbalik",
        "kerja_bersama", "persen_diskon",
        "satuan_konversi", "kecepatan_jarak_waktu", "persen_diskon",
    )


def test_komposisi_p6_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P6")
    assert komposisi == (
        "berpapasan", "menyusul",
        "perbandingan_senilai", "perbandingan_berbalik",
        "kerja_bersama", "persen_untung_rugi", "persen_bertingkat",
        "satuan_konversi", "kecepatan_jarak_waktu", "debit",
    )


def test_aritmatika_lanjut_menolak_level_di_luar_scope():
    """Paket P5/P6 tidak boleh diam-diam membuat sesi untuk anak P3/P4."""
    for level in ("P3", "P4"):
        with pytest.raises(ValueError, match="aritmatika-lanjut"):
            buat_lembar(7, level=level, topik="aritmatika-lanjut")
        with pytest.raises(ValueError, match="aritmatika-lanjut"):
            buat_soal("satuan_konversi", 7, level=level, topik="aritmatika-lanjut")


# Level teks aneh -> P5 diuji di Task 4.5, saat seluruh template sudah ada.


# ── Judul bagian ───────────────────────────────────────────────────────


def test_judul_bagian_aritmatika_lanjut():
    paket = _paket()
    assert paket.judul_bagian == {
        "A": "Bagian A — Konversi & kecepatan",
        "B": "Bagian B — Perbandingan",
        "C": "Bagian C — Kerja sama",
        "D": "Bagian D — Persen",
    }
