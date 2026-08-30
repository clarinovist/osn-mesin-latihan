"""Uji hapus sesi — Task perbaikan halaman guru.

Hapus sesi harus menghilangkan SEMUA jejaknya: baris sesi, sesi_soal,
jawaban, diagnosis, dan lampiran (semuanya lewat ON DELETE CASCADE di
skema), PLUS berkas foto lampiran di cakram yang tidak diurus basis data.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import basis  # noqa: E402
import lampiran  # noqa: E402
from diagnosa import diagnosa  # noqa: E402


@pytest.fixture()
def db(tmp_path, monkeypatch):
    p = tmp_path / "uji.db"
    basis.siapkan(p)
    monkeypatch.setattr(basis, "BAWAAN", p)
    monkeypatch.setenv("OSN_DIREKTORI_LAMPIRAN", str(tmp_path / "lampiran"))
    return p


def _sesi_dengan_hasil(kon) -> int:
    """Sesi 12 soal; dua soal pertama punya jawaban + diagnosis + foto."""
    sid = basis.tambah_siswa(kon, "Uji")
    sesi_id = basis.buat_sesi(kon, sid, seed=42)
    for baris in basis.isi_sesi(kon, sesi_id)[:2]:
        jid = basis.simpan_jawaban(
            kon, baris["sesi_soal_id"], jawaban="7", cara="aku hitung"
        )
        u = diagnosa(
            baris["kunci"], "7", "aku hitung", "", False,
            basis.malrule_soal(kon, baris["soal_id"]), False,
        )
        basis.simpan_diagnosis(
            kon, jid, u.benar, u.kode, u.kode, u.malrule_id, u.alasan
        )
    nama = lampiran.simpan_berkas(sesi_id, "foto-lembar.png", b"\x89PNG palsu")
    basis.simpan_lampiran(kon, sesi_id, nama, "image/png")
    return sesi_id


def test_hapus_sesi_kosong_menghilangkan_sesi_dan_soalnya(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Kosong")
        sesi_id = basis.buat_sesi(kon, sid, seed=7)
        assert basis.hapus_sesi(kon, sesi_id) is True
        sisa_sesi = kon.execute(
            "SELECT COUNT(*) FROM sesi WHERE id = ?", (sesi_id,)
        ).fetchone()[0]
        sisa_soal = kon.execute(
            "SELECT COUNT(*) FROM sesi_soal WHERE sesi_id = ?", (sesi_id,)
        ).fetchone()[0]
    assert sisa_sesi == 0
    assert sisa_soal == 0


def test_hapus_sesi_menghilangkan_jawaban_diagnosis_lampiran_dan_berkasnya(db):
    with basis.buka(db) as kon:
        sesi_id = _sesi_dengan_hasil(kon)
        folder = lampiran.direktori_lampiran() / str(sesi_id)
        assert folder.is_dir(), "prasyarat: foto sudah tersimpan di cakram"

        assert basis.hapus_sesi(kon, sesi_id) is True

        n_jawaban = kon.execute(
            """SELECT COUNT(*) FROM jawaban j
               JOIN sesi_soal ss ON ss.id = j.sesi_soal_id
               WHERE ss.sesi_id = ?""",
            (sesi_id,),
        ).fetchone()[0]
        n_diagnosis = kon.execute(
            """SELECT COUNT(*) FROM diagnosis d
               JOIN jawaban j ON j.id = d.jawaban_id
               JOIN sesi_soal ss ON ss.id = j.sesi_soal_id
               WHERE ss.sesi_id = ?""",
            (sesi_id,),
        ).fetchone()[0]
        n_lampiran = kon.execute(
            "SELECT COUNT(*) FROM lampiran WHERE sesi_id = ?", (sesi_id,)
        ).fetchone()[0]
    assert n_jawaban == 0
    assert n_diagnosis == 0
    assert n_lampiran == 0

    lampiran.bersihkan_berkas(sesi_id)
    assert not folder.exists(), "berkas foto lampiran harus ikut terhapus"


def test_hapus_sesi_tak_dikenal_mengembalikan_false_tanpa_meledak(db):
    with basis.buka(db) as kon:
        assert basis.hapus_sesi(kon, 99999) is False


def test_bersihkan_berkas_pada_folder_tidak_ada_tidak_meledak(db):
    # Idempoten: dipanggil dua kali (atau saat sesi tanpa foto) tetap aman.
    lampiran.bersihkan_berkas(424242)
    lampiran.bersihkan_berkas(424242)
