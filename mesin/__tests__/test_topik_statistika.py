"""Fase 6: kontrak paket topik kedelapan — statistika (P3-P6).

Lima template menutup cakupan statistika OSN SD: rata-rata (bagian A),
median & modus, diagram lingkaran dan batang/garis (B). P3 didukung
selaras band SASMO Primary 1-4 (statistics): hanya modus & diagram batang,
median menunggu P4.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import topik  # noqa: E402
from generator import buat_lembar, buat_soal  # noqa: E402


def _paket():
    return topik.ambil("statistika")


# ── Identitas & registrasi ─────────────────────────────────────────────


def test_statistika_terdaftar_dengan_identitas():
    paket = _paket()
    assert paket.id == "statistika"
    assert paket.nama == "Statistika"
    assert paket.judul_lembar == "Latihan Statistika"
    assert paket.judul_penilaian == "Penilaian — Statistika"


def test_statistika_memulai_dengan_template_awal():
    """Task 6.1 (kerangka): paket valid sejak template #1 #2 terisi."""
    paket = _paket()
    assert "rata_rata" in paket.templates
    assert "rata_rata_gabungan" in paket.templates


# ── Komposisi per level (tabel plan Fase 6) ────────────────────────────


def test_komposisi_p3_sepuluh_soal():
    """P3: hanya modus & diagram batang — median & rata-rata menunggu P4."""
    komposisi = _paket().komposisi_untuk("P3")
    assert komposisi == (
        "median_modus",
        "diagram_batang_garis",
        "median_modus",
        "diagram_batang_garis",
        "median_modus",
        "diagram_batang_garis",
        "median_modus",
        "diagram_batang_garis",
        "median_modus",
        "diagram_batang_garis",
    )


def test_komposisi_p4_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P4")
    assert komposisi == (
        "rata_rata",
        "median_modus",
        "diagram_batang_garis",
        "rata_rata",
        "median_modus",
        "diagram_batang_garis",
        "rata_rata",
        "median_modus",
        "diagram_batang_garis",
        "rata_rata",
    )


def test_komposisi_p5_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P5")
    assert komposisi == (
        "rata_rata",
        "rata_rata_gabungan",
        "median_modus",
        "diagram_lingkaran",
        "diagram_batang_garis",
        "rata_rata",
        "rata_rata_gabungan",
        "median_modus",
        "diagram_lingkaran",
        "diagram_batang_garis",
    )


def test_komposisi_p6_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P6")
    assert komposisi == (
        "rata_rata",
        "rata_rata_gabungan",
        "median_modus",
        "diagram_lingkaran",
        "diagram_batang_garis",
        "rata_rata_gabungan",
        "median_modus",
        "diagram_lingkaran",
        "diagram_batang_garis",
        "rata_rata",
    )


def test_statistika_p3_kini_didukung():
    """Dulu paket menolak P3; sejak P3 selaras band SASMO Primary 1-4,
    lembar P3 sah — pembukaan level tidak boleh melempar ValueError lagi."""
    lembar = buat_lembar(7, level="P3", topik="statistika")
    assert lembar.level == "P3"
    assert len(lembar.soal) == 10


def test_statistika_level_teks_aneh_jatuh_ke_p3():
    """Level teks aneh memakai level pertama paket.

    Dulu jatuh ke P4 — kunci pertama KOMPOSISI saat statistika belum
    mendukung P3. Kini "P3" kunci pertama KOMPOSISI, jadi teks aneh
    jatuh ke P3 (kontrak lama susun_lembar tetap dipertahankan).
    """
    aneh = buat_lembar(7, level="tingkat-lama", topik="statistika")
    p3 = buat_lembar(7, level="P3", topik="statistika")
    assert aneh.level == "P3"
    assert aneh.tanda_tangan == p3.tanda_tangan


def test_statistika_memuat_lima_template():
    """Task 6.3: seluruh 5 template sudah terimplementasi."""
    paket = _paket()
    assert len(paket.templates) == 5
    for nama in (
        "rata_rata",
        "rata_rata_gabungan",
        "median_modus",
        "diagram_lingkaran",
        "diagram_batang_garis",
    ):
        assert nama in paket.templates, nama


# ── Judul bagian ───────────────────────────────────────────────────────


def test_judul_bagian_statistika():
    paket = _paket()
    assert paket.judul_bagian == {
        "A": "Bagian A — Rata-rata",
        "B": "Bagian B — Median & modus, diagram",
    }


# ── Template #1 rata_rata ──────────────────────────────────────────────


def test_rata_rata_kunci():
    """#1: rata = jumlah/n; dua arah."""
    for seed in range(1, 120):
        s = buat_soal("rata_rata", seed, level="P4", topik="statistika")
        p = s.parameter
        if p["varian"] == "cari_rata":
            expected = sum(p["data"]) // len(p["data"])
        else:
            expected = p["rata"] * len(p["data"]) - sum(p["data"][:-1])
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


# ── Template #2 rata_rata_gabungan ─────────────────────────────────────


def test_rata_rata_gabungan_kunci():
    """#2: (n₁·x̄₁ + n₂·x̄₂)/(n₁+n₂)."""
    for seed in range(1, 120):
        s = buat_soal("rata_rata_gabungan", seed, level="P5", topik="statistika")
        p = s.parameter
        expected = (p["n1"] * p["x1"] + p["n2"] * p["x2"]) // (p["n1"] + p["n2"])
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


# ── Template #3 median_modus ───────────────────────────────────────────


def test_median_modus_kunci():
    """#3: median (urut) & modus (paling sering)."""
    for seed in range(1, 120):
        s = buat_soal("median_modus", seed, level="P4", topik="statistika")
        p = s.parameter
        data = p["data"]
        if p["varian"] == "median":
            urut = sorted(data)
            n = len(data)
            if n % 2 == 1:
                expected = urut[n // 2]
            else:
                expected = (urut[n // 2 - 1] + urut[n // 2]) // 2
        else:
            from collections import Counter
            hitung = Counter(data)
            expected = max(hitung.items(), key=lambda kv: kv[1])[0]
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


def test_median_modus_p3_modus_saja():
    """P3: median tidak boleh lolos — selalu varian modus, data kecil.

    Median di atas kelas 3; band SASMO Primary 1-4 (statistics) memuat
    modus. P3: n 3-5, nilai 1-12, konstruksi jamin-modus data[0]=data[1].
    """
    from collections import Counter

    for seed in range(1, 120):
        s = buat_soal("median_modus", seed, level="P3", topik="statistika")
        p = s.parameter
        assert p["varian"] == "modus", p
        data = p["data"]
        assert 3 <= len(data) <= 5, p
        assert all(1 <= x <= 12 for x in data), p
        hitung = Counter(data)
        expected = max(hitung.items(), key=lambda kv: kv[1])[0]
        assert data[0] == data[1], p  # jamin-modus: nilai ganda di depan
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


# ── Template #4 diagram_lingkaran ──────────────────────────────────────


def test_diagram_lingkaran_kunci():
    """#4: nilai = s/360×total; balik arah cari sudut."""
    for seed in range(1, 120):
        s = buat_soal("diagram_lingkaran", seed, level="P5", topik="statistika")
        p = s.parameter
        if p["varian"] == "cari_nilai":
            expected = p["total"] * p["s"] // 360
        else:
            expected = p["nilai"] * 360 // p["total"]
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


# ── Template #5 diagram_batang_garis ───────────────────────────────────


def test_diagram_batang_garis_kunci():
    """#5: baca/jumlah/selisih dari diagram batang."""
    for seed in range(1, 120):
        s = buat_soal("diagram_batang_garis", seed, level="P4", topik="statistika")
        p = s.parameter
        data = p["data"]
        if p["varian"] == "baca":
            expected = data[p["i"]]
        elif p["varian"] == "jumlah":
            expected = sum(data)
        else:
            a, b = data[p["i"]], data[(p["i"] + 1) % len(data)]
            expected = abs(a - b)
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


def test_diagram_batang_garis_p3_batas():
    """P3: empat batang, nilai 1-20; ketiga varian tetap boleh."""
    for seed in range(1, 120):
        s = buat_soal("diagram_batang_garis", seed, level="P3", topik="statistika")
        p = s.parameter
        assert p["varian"] in ("baca", "jumlah", "selisih"), p
        data = p["data"]
        assert len(data) == 4, p
        assert all(1 <= x <= 20 for x in data), p
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


# ── Sweep per kelompok template ────────────────────────────────────────

KELOMPOK_A = ("rata_rata", "rata_rata_gabungan")
KELOMPOK_B = ("median_modus", "diagram_lingkaran", "diagram_batang_garis")


@pytest.mark.parametrize("template_id", KELOMPOK_A)
@pytest.mark.parametrize("level", ("P4", "P5", "P6"))
def test_kelompok_a_sweep(template_id, level):
    if template_id == "rata_rata_gabungan" and level == "P4":
        return  # #2 hanya P5+
    for seed in range(1, 120):
        s = buat_soal(template_id, seed, level=level, topik="statistika")
        assert s.malrule, f"{template_id}@{level}/{seed} kosong"
        assert {"K", "H"} <= {m.kode for m in s.malrule}, f"{template_id}@{level}/{seed}"


@pytest.mark.parametrize("template_id", KELOMPOK_B)
@pytest.mark.parametrize("level", ("P4", "P5", "P6"))
def test_kelompok_b_sweep(template_id, level):
    if template_id == "diagram_lingkaran" and level == "P4":
        return  # #4 hanya P5+
    for seed in range(1, 120):
        s = buat_soal(template_id, seed, level=level, topik="statistika")
        assert s.malrule, f"{template_id}@{level}/{seed} kosong"
        assert {"K", "H"} <= {m.kode for m in s.malrule}, f"{template_id}@{level}/{seed}"