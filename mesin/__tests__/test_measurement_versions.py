"""Matematika pengukuran eksak untuk soal baru; warisan tetap stabil."""
from __future__ import annotations

import json
import random
import sys
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database
import question_views
import topic_measurement as pengukuran
import topics


def test_regresi_matematika_generator_tanpa_mengandalkan_versi():
    paket = topics.ambil("pengukuran")
    p = paket.parameter_untuk("skala_peta", random.Random(26), "P5")
    assert p["peta"] * p["skala"] == p["sebenarnya"] * 100000


def test_regresi_konversi_generator_tanpa_mengandalkan_versi():
    paket = topics.ambil("pengukuran")
    for seed in range(100):
        p = paket.parameter_untuk("jam_menit_detik", random.Random(seed), "P4")
        if p["varian"] == "detik_ke_menit":
            s = pengukuran.jam_menit_detik(**p)
            assert Fraction(s.kunci) == Fraction(p["detik"], 60)


@pytest.mark.parametrize("level", ("P4", "P5", "P6"))
def test_generator_konversi_tidak_memotong_sisa(level):
    pembagi = {"menit_ke_jam": ("menit", 60),
               "detik_ke_menit": ("detik", 60), "detik_ke_jam": ("detik", 3600)}
    paket = topics.ambil("pengukuran")
    for seed in range(500):
        p = paket.parameter_untuk("jam_menit_detik", random.Random(seed), level)
        s = pengukuran.jam_menit_detik(**p)
        if p["varian"] in pembagi:
            nama, faktor = pembagi[p["varian"]]
            assert Fraction(s.kunci) == Fraction(p[nama], faktor), (seed, p)
        assert s.parameter.get("versi") == 2
        assert {"K", "H"} <= {m.kode for m in s.malrule}


@pytest.mark.parametrize("level", ("P5", "P6"))
def test_generator_skala_relasi_eksak_dan_satuan(level):
    paket = topics.ambil("pengukuran")
    for seed in range(500):
        p = paket.parameter_untuk("skala_peta", random.Random(seed), level)
        s = pengukuran.skala_peta(**p)
        assert Fraction(p["peta"] * p["skala"], 100000) == p["sebenarnya"], p
        assert f"jarak sebenarnya {p['sebenarnya']} km" in s.pembahasan
        assert s.parameter.get("versi") == 2
        assert {"K", "H"} <= {m.kode for m in s.malrule}


@pytest.mark.parametrize("varian", ("cari_skala", "cari_peta", "cari_sebenarnya"))
def test_skala_v2_menolak_fakta_tidak_konsisten(varian):
    with pytest.raises(ValueError, match="skala"):
        pengukuran.skala_peta(varian, 107, 43, 250000, versi=2)


@pytest.mark.parametrize("varian,jam,menit,detik", (
    ("menit_ke_jam", 1, 61, 0), ("detik_ke_menit", 1, 0, 2533),
    ("detik_ke_jam", 1, 0, 3599),
))
def test_konversi_v2_tidak_menerima_pemotongan(varian, jam, menit, detik):
    with pytest.raises(ValueError, match="habis"):
        pengukuran.jam_menit_detik(varian, jam, menit, detik, versi=2)


@pytest.mark.parametrize("versi", (0, 3, True, "2", None))
def test_versi_asing_ditolak(versi):
    with pytest.raises(ValueError, match="versi"):
        pengukuran.skala_peta("cari_peta", 10, 10, 100000, versi=versi)


@pytest.mark.parametrize("parameter", (
    {"varian": "asing", "jam": 1, "menit": 2, "detik": 3},
    {"varian": "jam_ke_menit", "jam": True, "menit": 2, "detik": 3},
    {"varian": "jam_ke_menit", "jam": -1, "menit": 2, "detik": 3},
    {"varian": [], "jam": 1, "menit": 2, "detik": 3},
))
def test_parameter_konversi_invalid_ditolak(parameter):
    with pytest.raises(ValueError):
        pengukuran.jam_menit_detik(**parameter, versi=2)


def test_skala_batas_satu_tetap_memiliki_h_tanpa_mengubah_warisan():
    baru = pengukuran.skala_peta("cari_sebenarnya", 1, 1, 100000, versi=2)
    assert {"H", "K"} <= {m.kode for m in baru.malrule}
    assert len({baru.kunci, *(m.jawaban for m in baru.malrule)}) == len(baru.malrule) + 1
    lama = pengukuran.skala_peta("cari_sebenarnya", 1, 1, 100000)
    assert not any(m.kode == "H" for m in lama.malrule)


def test_warisan_tanpa_versi_tidak_diubah():
    s = pengukuran.skala_peta("cari_sebenarnya", 107, 43, 250000)
    assert s.kunci == "107"
    assert "jarak sebenarnya 107 cm" in s.pembahasan
    assert "versi" not in s.parameter
    s = pengukuran.jam_menit_detik("detik_ke_menit", 1, 0, 2533)
    assert s.kunci == "42"
    assert "versi" not in s.parameter


def test_bank_dan_snapshot_v1_v2_terpisah(tmp_path, monkeypatch):
    monkeypatch.delenv("OSN_VISUAL_KELUARGA", raising=False)
    jalur = tmp_path / "pengukuran.db"
    database.siapkan(jalur)
    lama = replace(pengukuran.skala_peta("cari_peta", 10, 10, 100000), level="P5")
    baru = replace(pengukuran.skala_peta("cari_peta", 10, 10, 100000, versi=2), level="P5")
    with database.buka(jalur) as kon:
        siswa = database.tambah_siswa(kon, "Fixture", pemilik="guru")
        def simpan(s):
            return database.buat_sesi_dari_urutan(
                kon, siswa, seed=1, urutan=(s.template_id,), topik="pengukuran",
                level="P5", soal_terpilih=(s,))
        sesi_lama = simpan(lama)
        sebelum = tuple(dict(b) for b in database.isi_sesi(kon, sesi_lama))
        sesi_baru = simpan(baru)
        assert tuple(dict(b) for b in database.isi_sesi(kon, sesi_lama)) == sebelum
        assert kon.execute("SELECT COUNT(*) FROM soal").fetchone()[0] == 2
        baris = database.isi_sesi(kon, sesi_baru)[0]
        pulih = question_views.soal_dari_baris(baris)
        assert pulih.parameter == baru.parameter
        assert pulih.pembahasan == baru.pembahasan
        assert pulih.tanda_tangan == baru.tanda_tangan != lama.tanda_tangan
        assert json.loads(baris["parameter"])["versi"] == 2
