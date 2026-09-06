"""Fase 1 Slice 3: adapter pembaca snapshot yang kompatibel."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
import question_views  # noqa: E402
import students  # noqa: E402
import teacher_pages  # noqa: E402
from visual_contract import buat_penyajian, serialisasi_kanonis, serialisasi_penyajian  # noqa: E402


KOLOM_SNAPSHOT = (
    "teks_soal", "bagian_soal", "tantangan_soal", "minta_restatement",
    "penyajian_json", "penyajian_versi", "renderer_versi", "asal_teks",
    "status_visual", "mode_representasi", "fingerprint_matematis",
    "fingerprint_penyajian",
)


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "reader.db"
    database.siapkan(path)
    monkeypatch.setattr(database, "BAWAAN", path)
    return path


def _baris_lama(**perubahan):
    baris = {
        "template_id": "deret_aritmetika",
        "parameter": json.dumps({"awal": 12, "beda": 3, "n_minta": 2, "n_tampil": 4}),
        "level": "P3",
        "bagian": "A",
        "tantangan": 0,
        "cerita": "",
    }
    baris.update({nama: None for nama in KOLOM_SNAPSHOT})
    baris.update(perubahan)
    return baris


def _snapshot(baris, *, teks="Teks yang dibekukan"):
    penyajian = buat_penyajian(
        template_id=baris["template_id"],
        level=baris["level"],
        parameter=json.loads(baris["parameter"]),
        teks_soal=teks,
        bagian_soal="B",
        tantangan_soal=True,
        minta_restatement=True,
        asal_teks="bawaan",
        status_visual="tanpa_visual",
        mode_representasi="teks-v1",
    )
    baris.update({
        "teks_soal": penyajian.teks_soal,
        "bagian_soal": penyajian.bagian_soal,
        "tantangan_soal": int(penyajian.tantangan_soal),
        "minta_restatement": int(penyajian.minta_restatement),
        "penyajian_json": serialisasi_penyajian(penyajian),
        "penyajian_versi": penyajian.penyajian_versi,
        "renderer_versi": penyajian.renderer_versi,
        "asal_teks": penyajian.asal_teks,
        "status_visual": penyajian.status_visual,
        "mode_representasi": penyajian.mode_representasi,
        "fingerprint_matematis": penyajian.fingerprint_matematis,
        "fingerprint_penyajian": penyajian.fingerprint_penyajian,
    })
    return penyajian


def _pasang_snapshot_db(kon, sesi_soal_id, baris):
    penugasan = ", ".join(f"{nama} = ?" for nama in KOLOM_SNAPSHOT)
    kon.execute(
        f"UPDATE sesi_soal SET {penugasan} WHERE id = ?",
        tuple(baris[nama] for nama in KOLOM_SNAPSHOT) + (sesi_soal_id,),
    )


def test_baris_warisan_direkonstruksi_dan_cerita_diutamakan():
    baris = _baris_lama(cerita="Cerita lama yang tersimpan")

    penyajian = question_views.penyajian_dari_baris(baris)

    assert penyajian.teks_soal == "Cerita lama yang tersimpan"
    assert penyajian.bagian_soal == "A"
    assert penyajian.status_visual == "warisan"
    assert penyajian.asal_teks == "cerita"


def test_snapshot_lengkap_diutamakan_meski_template_berubah(monkeypatch):
    baris = _baris_lama()
    _snapshot(baris)
    asli = question_views.REGISTRI[baris["template_id"]]
    monkeypatch.setitem(
        question_views.REGISTRI,
        baris["template_id"],
        lambda **parameter: replace(asli(**parameter), teks="TEKS TEMPLATE MUTASI"),
    )

    soal = teacher_pages._soal_dari_baris(baris)

    assert soal.teks == "Teks yang dibekukan"
    assert soal.bagian == "B"
    assert soal.tantangan is True
    assert soal.minta_restatement is True


def test_snapshot_parsial_ditolak_tanpa_fallback_template(monkeypatch):
    baris = _baris_lama(teks_soal="hanya satu kolom")
    monkeypatch.setitem(
        question_views.REGISTRI,
        baris["template_id"],
        lambda **parameter: pytest.fail("snapshot parsial tidak boleh fallback"),
    )

    with pytest.raises(ValueError, match="parsial"):
        question_views.penyajian_dari_baris(baris)


def test_snapshot_malformed_ditolak_tanpa_fallback_template(monkeypatch):
    baris = _baris_lama()
    _snapshot(baris)
    baris["penyajian_json"] = "{rusak"
    monkeypatch.setitem(
        question_views.REGISTRI,
        baris["template_id"],
        lambda **parameter: pytest.fail("snapshot rusak tidak boleh fallback"),
    )

    with pytest.raises(ValueError, match="snapshot"):
        question_views.penyajian_dari_baris(baris)


def test_snapshot_versi_asing_ditolak_tanpa_fallback():
    baris = _baris_lama()
    _snapshot(baris)
    muatan = json.loads(baris["penyajian_json"])
    muatan["penyajian_versi"] = 99
    baris["penyajian_json"] = serialisasi_kanonis(muatan)
    baris["penyajian_versi"] = 99

    with pytest.raises(ValueError, match="versi penyajian"):
        question_views.penyajian_dari_baris(baris)


def test_snapshot_dengan_kolom_denormalisasi_berbeda_ditolak():
    baris = _baris_lama()
    _snapshot(baris)
    baris["teks_soal"] = "teks yang tidak sama dengan JSON"

    with pytest.raises(ValueError, match="tidak cocok"):
        question_views.penyajian_dari_baris(baris)


def test_isi_sesi_menyediakan_snapshot_lengkap_untuk_sesi_baru(db):
    with database.buka(db) as kon:
        siswa_id = database.tambah_siswa(kon, "Reader")
        sesi_id = database.buat_sesi(kon, siswa_id, seed=42)
        baris = database.isi_sesi(kon, sesi_id)[0]

    assert set(KOLOM_SNAPSHOT) <= set(baris.keys())
    assert all(baris[nama] is not None for nama in KOLOM_SNAPSHOT)
    assert question_views.penyajian_dari_baris(baris).teks_soal == baris["teks_soal"]


def test_soal_murid_membaca_snapshot_tanpa_memanggil_template(db, monkeypatch):
    with database.buka(db) as kon:
        siswa_id = database.tambah_siswa(kon, "Anak Snapshot")
        sesi_id = database.buat_sesi(kon, siswa_id, seed=42)
        baris_db = database.isi_sesi(kon, sesi_id)[0]
        baris = dict(baris_db)
        _snapshot(baris, teks="Teks snapshot untuk anak")
        _pasang_snapshot_db(kon, baris_db["sesi_soal_id"], baris)
        monkeypatch.setitem(
            question_views.REGISTRI,
            baris["template_id"],
            lambda **parameter: pytest.fail("reader murid snapshot tidak perlu template"),
        )

        hasil = students.soal_murid(kon, sesi_id, siswa_id)

    assert hasil[0]["teks"] == "Teks snapshot untuk anak"
    assert hasil[0]["bagian"] == "B"
    assert hasil[0]["tantangan"] is True
    assert hasil[0]["minta_restatement"] is True
    assert not set(hasil[0]) & {"kunci", "malrule", "diagnosis"}
