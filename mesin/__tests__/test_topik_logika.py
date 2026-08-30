"""Fase 7: kontrak paket topik kesembilan — logika (P5/P6).

Enam template menutup cakupan penalaran & logika OSN SD: penalaran
(bagian A), besaran & umur (B). P3/P4 tidak didukung.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import topik  # noqa: E402
from generator import buat_lembar, buat_soal  # noqa: E402


def _paket():
    return topik.ambil("logika")


# ── Identitas & registrasi ─────────────────────────────────────────────


def test_logika_terdaftar_dengan_identitas():
    paket = _paket()
    assert paket.id == "logika"
    assert paket.nama == "Logika & Penalaran"
    assert paket.judul_lembar == "Latihan Logika & Penalaran"
    assert paket.judul_penilaian == "Penilaian — Logika & Penalaran"


def test_logika_memulai_dengan_template_awal():
    """Task 7.1 (kerangka): paket valid sejak template #1 #2 terisi."""
    paket = _paket()
    assert "benar_salah_pengandaian" in paket.templates
    assert "tabel_penalaran" in paket.templates


# ── Komposisi per level (tabel plan Fase 7) ────────────────────────────


def test_komposisi_p5_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P5")
    assert komposisi == (
        "benar_salah_pengandaian",
        "tabel_penalaran",
        "jumlah_selisih",
        "soal_uang",
        "benar_salah_pengandaian",
        "tabel_penalaran",
        "jumlah_selisih",
        "soal_uang",
        "benar_salah_pengandaian",
        "tabel_penalaran",
    )


def test_komposisi_p6_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P6")
    assert komposisi == (
        "benar_salah_pengandaian",
        "tabel_penalaran",
        "jumlah_selisih",
        "soal_umur",
        "soal_uang",
        "dua_besaran_selisih",
        "jumlah_selisih",
        "soal_umur",
        "soal_uang",
        "dua_besaran_selisih",
    )


def test_logika_menolak_level_di_luar_scope():
    """Paket P5/P6 tidak boleh diam-diam membuat sesi untuk anak P3/P4."""
    for level in ("P3", "P4"):
        with pytest.raises(ValueError, match="logika"):
            buat_lembar(7, level=level, topik="logika")
        with pytest.raises(ValueError, match="logika"):
            buat_soal("jumlah_selisih", 7, level=level, topik="logika")


def test_logika_level_teks_aneh_jatuh_ke_p5():
    """Data tingkat lama yang aneh memakai level pertama paket (P5)."""
    aneh = buat_lembar(7, level="tingkat-lama", topik="logika")
    p5 = buat_lembar(7, level="P5", topik="logika")
    assert aneh.level == "P5"
    assert aneh.tanda_tangan == p5.tanda_tangan


def test_logika_memuat_enam_template():
    """Task 7.3: seluruh 6 template sudah terimplementasi."""
    paket = _paket()
    assert len(paket.templates) == 6
    for nama in (
        "benar_salah_pengandaian",
        "tabel_penalaran",
        "jumlah_selisih",
        "soal_umur",
        "soal_uang",
        "dua_besaran_selisih",
    ):
        assert nama in paket.templates, nama


# ── Judul bagian ───────────────────────────────────────────────────────


def test_judul_bagian_logika():
    paket = _paket()
    assert paket.judul_bagian == {
        "A": "Bagian A — Penalaran",
        "B": "Bagian B — Besaran & umur",
    }


# ── Template #1-#2 penalaran ───────────────────────────────────────────


def test_benar_salah_pengandaian_kunci():
    """#1: kunci = huruf A-E (posisi pernyataan benar)."""
    for seed in range(1, 60):
        s = buat_soal("benar_salah_pengandaian", seed, level="P5", topik="logika")
        p = s.parameter
        assert s.kunci in ("A", "B", "C", "D", "E"), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        # harus ada B, K, H (4 malrule: B, K, K, H)
        assert {"B", "K", "H"} <= {m.kode for m in s.malrule}, p


def test_tabel_penalaran_kunci():
    """#2: kunci = nama orang (tertinggi/terendah/posisi)."""
    for seed in range(1, 60):
        s = buat_soal("tabel_penalaran", seed, level="P5", topik="logika")
        p = s.parameter
        assert s.kunci in p["urutan"], f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


# ── Template #3-#6 besaran & umur ──────────────────────────────────────


def test_jumlah_selisih_kunci():
    """#3: (j+s)/2 dan (j-s)/2."""
    for seed in range(1, 120):
        s = buat_soal("jumlah_selisih", seed, level="P5", topik="logika")
        p = s.parameter
        if p["tanya"] == "besar":
            expected = (p["jumlah"] + p["selisih"]) // 2
        else:
            expected = (p["jumlah"] - p["selisih"]) // 2
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


def test_soal_umur_kunci():
    """#4: n = (a−kb)/(k−1) bulat."""
    for seed in range(1, 120):
        s = buat_soal("soal_umur", seed, level="P6", topik="logika")
        p = s.parameter
        if p["tanya"] == "n_tahun":
            expected = (p["a"] - p["k"] * p["b"]) // (p["k"] - 1)
        else:
            expected = p["k"] * p["b"]
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


def test_soal_uang_kunci():
    """#5: B = total/(k+1), A = k·B."""
    for seed in range(1, 120):
        s = buat_soal("soal_uang", seed, level="P5", topik="logika")
        p = s.parameter
        kecil = p["total"] // (p["k"] + 1)
        if p["tanya"] == "uang_kecil":
            expected = kecil
        else:
            expected = p["k"] * kecil
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


def test_dua_besaran_selisih_kunci():
    """#6: b = s/(k−1), a = k·b."""
    for seed in range(1, 120):
        s = buat_soal("dua_besaran_selisih", seed, level="P6", topik="logika")
        p = s.parameter
        kecil = p["selisih"] // (p["k"] - 1)
        if p["tanya"] == "besar":
            expected = p["k"] * kecil
        else:
            expected = kecil
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


# ── Sweep per kelompok template ────────────────────────────────────────

KELOMPOK_A = ("benar_salah_pengandaian", "tabel_penalaran")
KELOMPOK_B = ("jumlah_selisih", "soal_umur", "soal_uang", "dua_besaran_selisih")


@pytest.mark.parametrize("template_id", KELOMPOK_A)
@pytest.mark.parametrize("level", ("P5", "P6"))
def test_kelompok_a_sweep(template_id, level):
    for seed in range(1, 60):
        s = buat_soal(template_id, seed, level=level, topik="logika")
        assert s.malrule, f"{template_id}@{level}/{seed} kosong"
        # benar_salah_pengandaian punya B/K/H; tabel_penalaran punya K/H
        if template_id == "benar_salah_pengandaian":
            assert {"B", "K", "H"} <= {m.kode for m in s.malrule}, f"{template_id}@{level}/{seed}"
        else:
            assert {"K", "H"} <= {m.kode for m in s.malrule}, f"{template_id}@{level}/{seed}"


@pytest.mark.parametrize("template_id", KELOMPOK_B)
@pytest.mark.parametrize("level", ("P5", "P6"))
def test_kelompok_b_sweep(template_id, level):
    if template_id in ("soal_umur", "dua_besaran_selisih") and level == "P5":
        return  # #4 #6 hanya P6
    for seed in range(1, 120):
        s = buat_soal(template_id, seed, level=level, topik="logika")
        assert s.malrule, f"{template_id}@{level}/{seed} kosong"
        assert {"K", "H"} <= {m.kode for m in s.malrule}, f"{template_id}@{level}/{seed}"