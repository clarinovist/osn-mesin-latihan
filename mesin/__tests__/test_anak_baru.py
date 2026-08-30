"""Fase B.2: aksi gabungan "anak_baru" — siswa + akun murid sekaligus.

Kontrak proses_akun aksi=anak_baru:
1. Data lengkap -> siswa dibuat + akun murid dibuat (nama sama) -> pesan sukses.
2. Nama siswa sudah ada -> galat, TIDAK ada apa pun yang dibuat.
3. Nama akun sudah dipakai (tapi siswa belum) -> galat, siswa TIDAK dibuat.
4. Tingkat tak valid -> galat (kontrak sama dengan aksi "siswa").
5. Sandi anak < 8 -> galat, siswa TIDAK dibuat (atomic, tanpa setengah jadi).
6. Persetujuan anak: kolom opsional "persetujuan_ortu" dicatat di pesan bila
   dicentang — bukti alur orang tua, bukan pengganti audit.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import basis  # noqa: E402
import sandi  # noqa: E402
import web  # noqa: E402


@pytest.fixture()
def db(tmp_path, monkeypatch):
    berkas = tmp_path / "sandi.json"
    sandi.simpan_sandi("sandi-guru-panjang-123", "guru", path=berkas)
    monkeypatch.setattr(sandi, "BERKAS_SANDI", berkas)
    db_path = tmp_path / "uji.db"
    basis.siapkan(db_path)
    monkeypatch.setattr(basis, "BAWAAN", db_path)
    with basis.buka(db_path) as kon:
        yield kon


DATA_LENGKAP = {
    "aksi": "anak_baru",
    "nama": "Aisha",
    "tingkat": "P4",
    "sandi_anak": "sandi-aisha-12345",
    "persetujuan_ortu": "1",
}


def test_anak_baru_membuat_siswa_dan_akun(db):
    pesan, galat = web.proses_akun(db, dict(DATA_LENGKAP), "guru")
    assert galat == ""
    assert "Aisha" in pesan
    # siswa ada dengan tingkat yang diminta
    baris = db.execute("SELECT * FROM siswa WHERE nama='Aisha'").fetchone()
    assert baris is not None and baris["tingkat"] == "P4"
    # akun murid ada dan bisa diautentikasi
    akun = sandi.cari_akun("Aisha")
    assert akun is not None and akun["peran"] == "murid"
    assert sandi.periksa("Aisha", "sandi-aisha-12345")


def test_anak_baru_nama_siswa_sudah_ada(db):
    web.proses_akun(db, dict(DATA_LENGKAP), "guru")
    pesan, galat = web.proses_akun(db, dict(DATA_LENGKAP), "guru")
    assert galat != ""
    jumlah = db.execute("SELECT COUNT(*) c FROM siswa WHERE nama='Aisha'").fetchone()["c"]
    assert jumlah == 1


def test_anak_baru_siswa_tidak_dibuat_bila_akun_gagal(db, tmp_path):
    # nama akun sudah terpakai oleh akun lain -> tambah_akun gagal ->
    # siswa TIDAK boleh tertinggal setengah jadi
    sandi.tambah_akun("Aisha", "akun-lain-123456", "guru")
    pesan, galat = web.proses_akun(db, dict(DATA_LENGKAP), "guru")
    assert galat != ""
    assert db.execute("SELECT COUNT(*) c FROM siswa WHERE nama='Aisha'").fetchone()["c"] == 0


def test_anak_baru_tingkat_tak_valid_ditolak(db):
    data = dict(DATA_LENGKAP, tingkat="kelas-4")
    _, galat = web.proses_akun(db, data, "guru")
    assert galat != ""
    assert db.execute("SELECT COUNT(*) c FROM siswa").fetchone()["c"] == 0


def test_anak_baru_sandi_pendek_ditolak_tanpa_siswa_yatim(db):
    data = dict(DATA_LENGKAP, sandi_anak="pendek")
    _, galat = web.proses_akun(db, data, "guru")
    assert galat != ""
    assert db.execute("SELECT COUNT(*) c FROM siswa").fetchone()["c"] == 0
    assert sandi.cari_akun("Aisha") is None
