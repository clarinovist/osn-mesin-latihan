"""Fase 8: kontrak paket topik kesepuluh — pengukuran (P4/P5/P6).

Tiga template menutup cakupan pengukuran OSN SD yang belum tercakup Fase 4/6:
skala peta, satuan waktu lama, jam/menit/detik. P3 tidak didukung.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import topics  # noqa: E402
from generator import buat_lembar, buat_soal  # noqa: E402


def _paket():
    return topics.ambil("pengukuran")


# ── Identitas & registrasi ─────────────────────────────────────────────


def test_pengukuran_terdaftar_dengan_identitas():
    paket = _paket()
    assert paket.id == "pengukuran"
    assert paket.nama == "Pengukuran"
    assert paket.judul_lembar == "Latihan Pengukuran"
    assert paket.judul_penilaian == "Penilaian — Pengukuran"


def test_pengukuran_memulai_dengan_template_awal():
    """Task 8.1 (kerangka): paket valid sejak template #1 #2 terisi."""
    paket = _paket()
    assert "skala_peta" in paket.templates
    assert "satuan_waktu_lama" in paket.templates


# ── Komposisi per level (tabel plan Fase 8) ────────────────────────────


def test_komposisi_p4_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P4")
    assert komposisi == (
        "satuan_waktu_lama", "jam_menit_detik",
        "satuan_waktu_lama", "jam_menit_detik",
        "satuan_waktu_lama", "jam_menit_detik",
        "satuan_waktu_lama", "jam_menit_detik",
        "satuan_waktu_lama", "jam_menit_detik",
    )


def test_komposisi_p5_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P5")
    assert komposisi == (
        "skala_peta", "satuan_waktu_lama", "jam_menit_detik",
        "skala_peta", "satuan_waktu_lama", "jam_menit_detik",
        "skala_peta", "satuan_waktu_lama", "jam_menit_detik",
        "skala_peta",
    )


def test_komposisi_p6_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P6")
    assert komposisi == (
        "skala_peta", "satuan_waktu_lama", "jam_menit_detik",
        "skala_peta", "satuan_waktu_lama", "jam_menit_detik",
        "skala_peta", "satuan_waktu_lama", "jam_menit_detik",
        "skala_peta",
    )


def test_pengukuran_menolak_level_di_luar_scope():
    """Paket P4-P6 tidak boleh diam-diam membuat sesi untuk anak P3."""
    with pytest.raises(ValueError, match="pengukuran"):
        buat_lembar(7, level="P3", topik="pengukuran")
    with pytest.raises(ValueError, match="pengukuran"):
        buat_soal("skala_peta", 7, level="P3", topik="pengukuran")


def test_pengukuran_level_teks_aneh_jatuh_ke_p4():
    """Data tingkat lama yang aneh memakai level pertama paket (P4)."""
    aneh = buat_lembar(7, level="tingkat-lama", topik="pengukuran")
    p4 = buat_lembar(7, level="P4", topik="pengukuran")
    assert aneh.level == "P4"
    assert aneh.tanda_tangan == p4.tanda_tangan


def test_pengukuran_memuat_tiga_template():
    """Task 8.2: seluruh 3 template sudah terimplementasi."""
    paket = _paket()
    assert len(paket.templates) == 3
    for nama in ("skala_peta", "satuan_waktu_lama", "jam_menit_detik"):
        assert nama in paket.templates, nama


# ── Judul bagian ───────────────────────────────────────────────────────


def test_judul_bagian_pengukuran():
    paket = _paket()
    assert paket.judul_bagian == {
        "A": "Bagian A — Skala peta",
        "B": "Bagian B — Waktu & konversi",
    }


# ── Template #1 skala_peta ─────────────────────────────────────────────


def test_skala_peta_kunci():
    """#1: skala = peta:sebenarnya (cm:cm); tiga arah."""
    for seed in range(1, 120):
        s = buat_soal("skala_peta", seed, level="P5", topik="pengukuran")
        p = s.parameter
        if p["varian"] == "cari_skala":
            expected = f"1:{p['skala']}"
        elif p["varian"] == "cari_peta":
            expected = str(p["peta"])
        else:
            expected = str(p["sebenarnya"])
        assert s.kunci == expected, f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


# ── Template #2 satuan_waktu_lama ──────────────────────────────────────


def test_satuan_waktu_lama_kunci():
    """#2: konversi abad/windu/lustrum/dasawarsa."""
    SATUAN = {
        "abad_ke_tahun": ("tahun", 100), "tahun_ke_abad": ("abad", 1/100),
        "windu_ke_tahun": ("tahun", 8), "tahun_ke_windu": ("windu", 1/8),
        "lustrum_ke_tahun": ("tahun", 5), "tahun_ke_lustrum": ("lustrum", 1/5),
        "dasawarsa_ke_tahun": ("tahun", 10), "tahun_ke_dasawarsa": ("dasawarsa", 1/10),
        "windu_ke_lustrum": ("lustrum", 8/5), "abad_ke_dasawarsa": ("dasawarsa", 10),
    }
    for seed in range(1, 120):
        s = buat_soal("satuan_waktu_lama", seed, level="P4", topik="pengukuran")
        p = s.parameter
        dst, faktor = SATUAN[p["varian"]]
        expected = int(p["nilai"] * faktor)
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


# ── Template #3 jam_menit_detik ────────────────────────────────────────


def test_jam_menit_detik_kunci():
    """#3: konversi jam/menit/detik; dua arah."""
    for seed in range(1, 120):
        s = buat_soal("jam_menit_detik", seed, level="P4", topik="pengukuran")
        p = s.parameter
        varian = p["varian"]
        if varian == "jam_ke_menit":
            expected = p["jam"] * 60
        elif varian == "menit_ke_jam":
            expected = p["menit"] // 60
        elif varian == "menit_ke_detik":
            expected = p["menit"] * 60
        elif varian == "detik_ke_menit":
            expected = p["detik"] // 60
        elif varian == "jam_ke_detik":
            expected = p["jam"] * 3600
        elif varian == "detik_ke_jam":
            expected = p["detik"] // 3600
        elif varian == "durasi_ke_menit":
            expected = p["jam"] * 60 + p["menit"]
        else:
            expected = p["jam"] * 3600 + p["menit"] * 60 + p["detik"]
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


# ── Sweep per template ─────────────────────────────────────────────────

TEMPLATE_ALL = ("skala_peta", "satuan_waktu_lama", "jam_menit_detik")


@pytest.mark.parametrize("template_id", TEMPLATE_ALL)
@pytest.mark.parametrize("level", ("P4", "P5", "P6"))
def test_sweep(template_id, level):
    if template_id == "skala_peta" and level == "P4":
        return  # #1 hanya P5+
    for seed in range(1, 120):
        s = buat_soal(template_id, seed, level=level, topik="pengukuran")
        assert s.malrule, f"{template_id}@{level}/{seed} kosong"
        assert {"K", "H"} <= {m.kode for m in s.malrule}, f"{template_id}@{level}/{seed}"