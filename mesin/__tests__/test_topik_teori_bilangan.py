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


# ── Template #1 keterbagian — Task 3.2 ─────────────────────────────────


def test_keterbagian_kunci_adalah_bilangan_yang_habis():
    """#1: tepat satu dari tiga bilangan habis dibagi d."""
    for seed in range(1, 120):
        s = buat_soal("keterbagian", seed, level="P4", topik="teori-bilangan")
        p = s.parameter
        pilihan = (p["a"], p["b"], p["c"])
        habis = [x for x in pilihan if x % p["d"] == 0]
        assert len(habis) == 1, f"{p=} tidak punya tepat satu kelipatan"
        assert s.kunci == str(habis[0]), f"{p=}, kunci={s.kunci}"
        # malrule tak boleh menebak kunci
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p


def test_keterbagian_trap_divisor():
    """#1: K = bilangan yang habis dibagi trap tapi tidak habis dibagi d."""
    from topik_teori_bilangan import _TRAP

    for seed in range(1, 120):
        s = buat_soal("keterbagian", seed, level="P5", topik="teori-bilangan")
        p = s.parameter
        trap = _TRAP[p["d"]]
        jawaban = {m.id: m.jawaban for m in s.malrule}
        if "keterbagian.trap_divisor" in jawaban:
            num = int(jawaban["keterbagian.trap_divisor"])
            assert num % trap == 0, f"{p=}: {num} tidak habis dibagi {trap}"
            assert num % p["d"] != 0, f"{p=}: {num} habis dibagi {p['d']}"


def test_keterbagian_level_membedakan_pool_divisor():
    """d pool P4 tanpa 8/9/11; P5 ada 8,9; P6 ada 11."""
    terlihat = {"P4": set(), "P5": set(), "P6": set()}
    for level in ("P4", "P5", "P6"):
        for seed in range(1, 200):
            s = buat_soal("keterbagian", seed, level=level, topik="teori-bilangan")
            terlihat[level].add(s.parameter["d"])
    assert terlihat["P4"] <= {2, 3, 4, 5, 6}
    assert 8 in terlihat["P5"] and 9 in terlihat["P5"]
    assert 11 in terlihat["P6"]


def test_keterbagian_sweep_tanpa_malrule_kosong():
    for level in ("P4", "P5", "P6"):
        for seed in range(1, 120):
            s = buat_soal("keterbagian", seed, level=level, topik="teori-bilangan")
            assert s.malrule, f"keterbagian@{level}/{seed} kosong"
            assert {"K", "H"} <= {m.kode for m in s.malrule}
