"""Fase 1 Slice 4: satu writer snapshot atomik untuk semua pembuat sesi."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
import question_views  # noqa: E402
from generator import buat_lembar  # noqa: E402
from learning_cycle import PutaranFokus, RencanaBelajar  # noqa: E402
from visual_contract import deserialisasi_penyajian  # noqa: E402


KOLOM_SNAPSHOT = (
    "teks_soal", "bagian_soal", "tantangan_soal", "minta_restatement",
    "penyajian_json", "penyajian_versi", "renderer_versi", "asal_teks",
    "status_visual", "mode_representasi", "fingerprint_matematis",
    "fingerprint_penyajian",
)


@pytest.fixture()
def db(tmp_path):
    path = tmp_path / "snapshot-writer.db"
    database.siapkan(path)
    return path


def _assert_snapshot_lengkap(baris):
    assert all(baris[nama] is not None for nama in KOLOM_SNAPSHOT)
    penyajian = deserialisasi_penyajian(baris["penyajian_json"])
    assert penyajian.teks_soal == baris["teks_soal"]
    assert penyajian.bagian_soal == baris["bagian_soal"]
    assert penyajian.tantangan_soal is bool(baris["tantangan_soal"])
    assert penyajian.minta_restatement is bool(baris["minta_restatement"])
    assert penyajian.asal_teks == "bawaan"
    assert penyajian.status_visual == "tanpa_visual"
    assert penyajian.mode_representasi == "teks-v1"
    assert penyajian.descriptor is None
    assert penyajian.fingerprint_matematis == baris["fingerprint_matematis"]
    assert penyajian.fingerprint_penyajian == baris["fingerprint_penyajian"]


def test_projector_soal_bawaan_membuat_snapshot_teks_tanpa_mengubah_identitas():
    soal = buat_lembar(42, jumlah_soal=1).soal[0]
    tanda_tangan = soal.tanda_tangan

    penyajian = question_views.penyajian_dari_soal(soal)

    assert penyajian.teks_soal == soal.teks
    assert penyajian.bagian_soal == soal.bagian
    assert penyajian.tantangan_soal is soal.tantangan
    assert penyajian.minta_restatement is soal.minta_restatement
    assert penyajian.asal_teks == "bawaan"
    assert penyajian.status_visual == "tanpa_visual"
    assert penyajian.mode_representasi == "teks-v1"
    assert penyajian.descriptor is None
    assert soal.tanda_tangan == tanda_tangan


def test_buat_sesi_normal_menyimpan_snapshot_lengkap(db):
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Normal")
        sesi = database.buat_sesi(kon, siswa, seed=42, jumlah_soal=3)
        baris = database.isi_sesi(kon, sesi)

    assert len(baris) == 3
    for butir in baris:
        _assert_snapshot_lengkap(butir)


def test_buat_sesi_urutan_remedial_menyimpan_snapshot_lengkap(db):
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Urutan")
        sesi = database.buat_sesi_dari_urutan(
            kon,
            siswa,
            seed=43,
            urutan=("deret_aritmetika", "deret_aritmetika"),
            jenis="remedial",
        )
        baris = database.isi_sesi(kon, sesi)

    assert len(baris) == 2
    assert all(b["template_id"] == "deret_aritmetika" for b in baris)
    for butir in baris:
        _assert_snapshot_lengkap(butir)


def test_buat_sesi_gabungan_menyimpan_snapshot_lengkap(db):
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Gabungan", tingkat="P5")
        sesi = database.buat_sesi_gabungan(
            kon,
            siswa,
            seed=44,
            topik_ids=["geometri-datar", "logika"],
            level="P5",
            jumlah_soal=4,
        )
        baris = database.isi_sesi(kon, sesi)

    assert len(baris) == 4
    for butir in baris:
        _assert_snapshot_lengkap(butir)


def test_buat_sesi_remedial_tidak_langsung_memakai_writer_snapshot(db, monkeypatch):
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Remedial")
        monkeypatch.setattr(
            database,
            "sasaran_remedial_anak",
            lambda _kon, _siswa: [{"template_id": "deret_aritmetika"}],
        )
        sesi = database.buat_sesi_remedial(
            kon, siswa, seed=45, jumlah_soal=2
        )
        baris = database.isi_sesi(kon, sesi)

    assert len(baris) == 2
    for butir in baris:
        _assert_snapshot_lengkap(butir)


def test_buat_sesi_siklus_tidak_langsung_memakai_writer_snapshot(db):
    rencana = RencanaBelajar(
        "pemetaan",
        "uji writer",
        putaran=PutaranFokus(1, "P3", ()),
    )
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Siklus", tingkat="P3")
        putaran = database.buat_putaran_fokus(kon, siswa, "P3")
        sesi = database.buat_sesi_dari_rencana(
            kon, siswa, rencana, putaran_id=putaran, seed=46
        )
        baris = database.isi_sesi(kon, sesi)

    assert len(baris) == 15
    for butir in baris:
        _assert_snapshot_lengkap(butir)


def test_bank_soal_bersama_tetap_punya_snapshot_per_sesi(db):
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Bank bersama")
        sesi_a = database.buat_sesi(kon, siswa, seed=47, jumlah_soal=2)
        sesi_b = database.buat_sesi(kon, siswa, seed=47, jumlah_soal=2)
        baris_a = database.isi_sesi(kon, sesi_a)
        baris_b = database.isi_sesi(kon, sesi_b)

    assert [b["soal_id"] for b in baris_a] == [b["soal_id"] for b in baris_b]
    assert [b["sesi_soal_id"] for b in baris_a] != [
        b["sesi_soal_id"] for b in baris_b
    ]
    assert [b["penyajian_json"] for b in baris_a] == [
        b["penyajian_json"] for b in baris_b
    ]
    for butir in baris_a + baris_b:
        _assert_snapshot_lengkap(butir)


def _pembuat_normal(kon, siswa):
    return database.buat_sesi(kon, siswa, seed=51, jumlah_soal=3)


def _pembuat_urutan(kon, siswa):
    return database.buat_sesi_dari_urutan(
        kon,
        siswa,
        seed=52,
        urutan=("deret_aritmetika",) * 3,
    )


def _pembuat_gabungan(kon, siswa):
    return database.buat_sesi_gabungan(
        kon,
        siswa,
        seed=53,
        topik_ids=["geometri-datar", "logika"],
        level="P5",
        jumlah_soal=3,
    )


@pytest.mark.parametrize(
    "pembuat", [_pembuat_normal, _pembuat_urutan, _pembuat_gabungan]
)
def test_kegagalan_proyeksi_butir_kedua_menggulung_seluruh_sesi(
    db, monkeypatch, pembuat
):
    asli = question_views.penyajian_dari_soal
    panggilan = 0

    def gagal_kedua(soal):
        nonlocal panggilan
        panggilan += 1
        if panggilan == 2:
            raise RuntimeError("proyeksi sengaja gagal")
        return asli(soal)

    monkeypatch.setattr(question_views, "penyajian_dari_soal", gagal_kedua)
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Atomik")
        kon.execute("SAVEPOINT transaksi_pemanggil")
        sebelum_soal = kon.execute("SELECT COUNT(*) FROM soal").fetchone()[0]

        with pytest.raises(RuntimeError, match="sengaja gagal"):
            pembuat(kon, siswa)

        assert kon.execute("SELECT COUNT(*) FROM sesi").fetchone()[0] == 0
        assert kon.execute("SELECT COUNT(*) FROM sesi_soal").fetchone()[0] == 0
        assert kon.execute("SELECT COUNT(*) FROM soal").fetchone()[0] == sebelum_soal
        assert kon.execute(
            "SELECT COUNT(*) FROM siswa WHERE id = ?", (siswa,)
        ).fetchone()[0] == 1
        kon.execute("RELEASE SAVEPOINT transaksi_pemanggil")
