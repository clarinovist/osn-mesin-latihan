"""Fase 5: kontrak paket topik ketujuh — geometri-ruang (P5/P6).

Tujuh template menutup cakupan geometri ruang OSN SD: unsur bangun ruang
& volume (bagian A), luas permukaan & jaring (B), kubus dicat & perbandingan
volume (C). P3/P4 tidak didukung.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import topik  # noqa: E402
from generator import buat_lembar, buat_soal  # noqa: E402


def _paket():
    return topik.ambil("geometri-ruang")


# ── Identitas & registrasi ─────────────────────────────────────────────


def test_geometri_ruang_terdaftar_dengan_identitas():
    paket = _paket()
    assert paket.id == "geometri-ruang"
    assert paket.nama == "Geometri Ruang"
    assert paket.judul_lembar == "Latihan Geometri Ruang"
    assert paket.judul_penilaian == "Penilaian — Geometri Ruang"


def test_geometri_ruang_memulai_dengan_template_awal():
    """Task 5.1 (kerangka): paket valid sejak template #1 #2 terisi."""
    paket = _paket()
    assert "unsur_bangun" in paket.templates
    assert "volume_kubus_balok" in paket.templates


# ── Komposisi per level (tabel plan Fase 5) ────────────────────────────


def test_komposisi_p5_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P5")
    assert komposisi == (
        "unsur_bangun",
        "volume_kubus_balok",
        "volume_prisma_tabung",
        "luas_permukaan",
        "unsur_bangun",
        "volume_kubus_balok",
        "volume_prisma_tabung",
        "luas_permukaan",
        "unsur_bangun",
        "volume_kubus_balok",
    )


def test_komposisi_p6_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P6")
    assert komposisi == (
        "unsur_bangun",
        "volume_kubus_balok",
        "volume_prisma_tabung",
        "luas_permukaan",
        "jaring_jaring",
        "kubus_dicat",
        "perbandingan_volume",
        "volume_kubus_balok",
        "volume_prisma_tabung",
        "luas_permukaan",
    )


def test_geometri_ruang_menolak_level_di_luar_scope():
    """Paket P5/P6 tidak boleh diam-diam membuat sesi untuk anak P3/P4."""
    for level in ("P3", "P4"):
        with pytest.raises(ValueError, match="geometri-ruang"):
            buat_lembar(7, level=level, topik="geometri-ruang")
        with pytest.raises(ValueError, match="geometri-ruang"):
            buat_soal("unsur_bangun", 7, level=level, topik="geometri-ruang")


def test_geometri_ruang_level_teks_aneh_jatuh_ke_p5():
    """Data tingkat lama yang aneh memakai level pertama paket (P5)."""
    aneh = buat_lembar(7, level="tingkat-lama", topik="geometri-ruang")
    p5 = buat_lembar(7, level="P5", topik="geometri-ruang")
    assert aneh.level == "P5"
    assert aneh.tanda_tangan == p5.tanda_tangan


def test_geometri_ruang_memuat_tujuh_template():
    """Task 5.4: seluruh 7 template sudah terimplementasi."""
    paket = _paket()
    assert len(paket.templates) == 7
    for nama in (
        "unsur_bangun",
        "volume_kubus_balok",
        "volume_prisma_tabung",
        "luas_permukaan",
        "jaring_jaring",
        "kubus_dicat",
        "perbandingan_volume",
    ):
        assert nama in paket.templates, nama


# ── Judul bagian ───────────────────────────────────────────────────────


def test_judul_bagian_geometri_ruang():
    paket = _paket()
    assert paket.judul_bagian == {
        "A": "Bagian A — Unsur & volume",
        "B": "Bagian B — Luas permukaan & jaring",
        "C": "Bagian C — Kubus dicat & perbandingan volume",
    }


# ── Template #1 unsur_bangun ───────────────────────────────────────────


def test_unsur_bangun_kunci():
    """#1: jumlah rusuk/sisi/titik untuk setiap bangun (dasar & ×n)."""
    for seed in range(1, 120):
        s = buat_soal("unsur_bangun", seed, level="P5", topik="geometri-ruang")
        p = s.parameter
        from topik_geometri_ruang import BANGUN, TANYA_INDEKS
        tanya_asli = p["tanya"].replace("_kali", "")
        nilai = BANGUN[p["bangun"]][TANYA_INDEKS[tanya_asli]]
        if p["tanya"].endswith("_kali"):
            expected = nilai * p["n"]
        else:
            expected = nilai
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


# ── Template #2 volume_kubus_balok ─────────────────────────────────────


def test_volume_kubus_balok_kunci():
    """#2: V=s³, V=p·l·t, dua arah."""
    for seed in range(1, 120):
        s = buat_soal("volume_kubus_balok", seed, level="P5", topik="geometri-ruang")
        p = s.parameter
        if p["varian"] == "kubus_cari_V":
            expected = p["s"] ** 3
        elif p["varian"] == "kubus_cari_s":
            expected = p["s"]
        elif p["varian"] == "balok_cari_V":
            expected = p["p"] * p["l"] * p["t"]
        else:
            expected = p["p"]
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


# ── Template #3 volume_prisma_tabung ───────────────────────────────────


def test_volume_prisma_tabung_kunci():
    """#3: V=(½·a·t)·t atau V=πr²t."""
    for seed in range(1, 120):
        s = buat_soal("volume_prisma_tabung", seed, level="P5", topik="geometri-ruang")
        p = s.parameter
        if p["varian"] == "prisma_V":
            expected = (p["a"] * p["t_segitiga"] // 2) * p["t_prisma"]
        elif p["varian"] == "tabung_V":
            pi = 22 / 7 if p["r"] % 7 == 0 else 3.14
            expected = int(pi * p["r"] * p["r"] * p["t"])
        elif p["varian"] == "prisma_balik":
            expected = p["t_prisma"]
        else:
            expected = p["t"]
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


# ── Template #4 luas_permukaan ─────────────────────────────────────────


def test_luas_permukaan_kunci():
    """#4: LP=6s², 2(pl+pt+lt), 2πr²+2πrt."""
    for seed in range(1, 120):
        s = buat_soal("luas_permukaan", seed, level="P5", topik="geometri-ruang")
        p = s.parameter
        if p["varian"] == "kubus_LP":
            expected = 6 * p["s"] * p["s"]
        elif p["varian"] == "kubus_cari_s":
            expected = p["s"]
        elif p["varian"] == "balok_LP":
            expected = 2 * (p["p"] * p["l"] + p["p"] * p["t"] + p["l"] * p["t"])
        elif p["varian"] == "balok_cari_p":
            expected = p["p"]
        elif p["varian"] == "tabung_LP":
            pi = 22 / 7 if p["r"] % 7 == 0 else 3.14
            expected = int(2 * pi * p["r"] * p["r"] + 2 * pi * p["r"] * p["t"])
        else:
            expected = p["t"]
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


# ── Template #5 jaring_jaring ──────────────────────────────────────────


def test_jaring_jaring_kunci():
    """#5: 5 pilihan, 1 benar, kunci = huruf A-E."""
    s = buat_soal("jaring_jaring", 7, level="P6", topik="geometri-ruang")
    p = s.parameter
    opsi = ["A", "B", "C", "D", "E"]
    assert s.kunci in opsi, f"{p=}, kunci={s.kunci}"
    assert s.kunci not in [m.jawaban for m in s.malrule]
    assert {"B", "K", "H"} <= {m.kode for m in s.malrule}, p


# ── Template #6 kubus_dicat ────────────────────────────────────────────


def test_kubus_dicat_kunci():
    """#6: n×n×n dicat, jumlah cat 0/1/2/3 sisi (dasar & ×n_kubus)."""
    for seed in range(1, 120):
        s = buat_soal("kubus_dicat", seed, level="P6", topik="geometri-ruang")
        p = s.parameter
        n = p["n"]
        tanya_asli = p["tanya"].replace("_kali", "")
        if tanya_asli == "tiga_sisi":
            dasar = 8
        elif tanya_asli == "dua_sisi":
            dasar = 12 * (n - 2)
        elif tanya_asli == "satu_sisi":
            dasar = 6 * (n - 2) ** 2
        else:
            dasar = (n - 2) ** 3
        expected = dasar * p.get("n_kubus", 1)
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


# ── Template #7 perbandingan_volume ────────────────────────────────────


def test_perbandingan_volume_kunci():
    """#7: V baru = k³ × V lama."""
    for seed in range(1, 120):
        s = buat_soal("perbandingan_volume", seed, level="P6", topik="geometri-ruang")
        p = s.parameter
        if p["varian"] == "cari_k":
            expected = p["k"]
        else:
            expected = p["k"] ** 3 * p["s"]
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


# ── Sweep per kelompok template ────────────────────────────────────────

KELOMPOK_A = ("unsur_bangun", "volume_kubus_balok", "volume_prisma_tabung")
KELOMPOK_B = ("luas_permukaan", "jaring_jaring")
KELOMPOK_C = ("kubus_dicat", "perbandingan_volume")


@pytest.mark.parametrize("template_id", KELOMPOK_A)
@pytest.mark.parametrize("level", ("P5", "P6"))
def test_kelompok_a_sweep(template_id, level):
    for seed in range(1, 120):
        if template_id == "volume_prisma_tabung" and level == "P5":
            # tabung_V with 3.14 may produce 0 for small r
            s = buat_soal(template_id, seed, level=level, topik="geometri-ruang")
        else:
            s = buat_soal(template_id, seed, level=level, topik="geometri-ruang")
        # jaring_jaring only P6
        if template_id == "jaring_jaring" and level == "P5":
            continue
        assert s.malrule, f"{template_id}@{level}/{seed} kosong"
        assert {"K", "H"} <= {m.kode for m in s.malrule}, f"{template_id}@{level}/{seed}"


@pytest.mark.parametrize("template_id", KELOMPOK_B)
@pytest.mark.parametrize("level", ("P5", "P6"))
def test_kelompok_b_sweep(template_id, level):
    if template_id == "jaring_jaring" and level == "P5":
        return  # #5 hanya P6
    for seed in range(1, 120):
        s = buat_soal(template_id, seed, level=level, topik="geometri-ruang")
        assert s.malrule, f"{template_id}@{level}/{seed} kosong"
        assert {"K", "H"} <= {m.kode for m in s.malrule}, f"{template_id}@{level}/{seed}"


@pytest.mark.parametrize("template_id", KELOMPOK_C)
@pytest.mark.parametrize("level", ("P5", "P6"))
def test_kelompok_c_sweep(template_id, level):
    if level == "P5":
        return  # #6 #7 hanya P6
    for seed in range(1, 120):
        s = buat_soal(template_id, seed, level=level, topik="geometri-ruang")
        assert s.malrule, f"{template_id}@{level}/{seed} kosong"
        assert {"K", "H"} <= {m.kode for m in s.malrule}, f"{template_id}@{level}/{seed}"