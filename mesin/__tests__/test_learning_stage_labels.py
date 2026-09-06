"""Label tahap netral tanpa membaca bukti internal orang tua."""
import sqlite3

import pytest

import database
import student_pages


TAHAP = (
    ("pemetaan", "Latihan campuran"),
    ("latihan_terbimbing", "Pelajari bersama"),
    ("penguatan", "Coba mandiri"),
    ("evaluasi", "Coba kembali"),
    ("checkpoint", "Latihan berkala"),
    ("pengenalan", "Kenali hal baru"),
    ("maintenance", "Latihan campuran"),
)


@pytest.fixture()
def db(tmp_path, monkeypatch):
    jalur = tmp_path / "label.db"
    database.siapkan(jalur)
    monkeypatch.setattr(database, "BAWAAN", jalur)
    return jalur


@pytest.fixture()
def db_terjaga(db, monkeypatch):
    class BarisTerjaga(sqlite3.Row):
        def __getitem__(self, nama):
            assert nama not in {"kunci", "kode_final", "kode_usulan", "malrule_id", "alasan"}
            return super().__getitem__(nama)

    monkeypatch.setattr(sqlite3, "Row", BarisTerjaga)
    return db


@pytest.mark.parametrize("tujuan,label", TAHAP)
@pytest.mark.parametrize("permukaan", ["daftar", "daftar_baru", "kerja", "kerja_baru", "tautan"])
def test_label_tahap_netral_di_semua_permukaan(db_terjaga, tujuan, label, permukaan):
    with database.buka(db_terjaga) as kon:
        siswa = database.tambah_siswa(kon, "Anak Uji", pemilik="guru")
        sesi = database.buat_sesi(kon, siswa, seed=83, jumlah_soal=1)
        kon.execute("UPDATE sesi SET tujuan = ?, jenis = 'remedial' WHERE id = ?", (tujuan, sesi))
        if permukaan == "daftar":
            isi = student_pages.halaman_daftar_sesi(kon, siswa, "Anak Uji")
        elif permukaan == "daftar_baru":
            isi = student_pages.halaman_daftar_sesi_baru(kon, siswa, "Anak Uji")
        elif permukaan == "kerja":
            isi = student_pages.halaman_kerja(kon, siswa, sesi)
        else:
            isi = student_pages.halaman_kerja_baru(kon, siswa, sesi, akses_tautan=permukaan == "tautan")
    assert isi is not None
    teks = isi.decode()
    assert label in teks
    assert "Remedial" not in teks
    assert "<span>Fokus " not in teks
    for rahasia in ("malrule", "kode_final", "Rencana belajar hari ini", "kelemahan"):
        assert rahasia not in teks


def test_sesi_bebas_tetap_memakai_label_lama(db):
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Anak Uji", pemilik="guru")
        database.buat_sesi(kon, siswa, seed=83, mode="drill", jumlah_soal=1)
        teks = student_pages.halaman_daftar_sesi_baru(kon, siswa, "Anak Uji").decode()
    assert "Latihan Cepat" in teks
    assert 'class="label-tahap-murid"' not in teks


def test_label_keluar_lewat_router_murid(tmp_path, monkeypatch):
    from http_test_kit import SANDI_MURID, ServerUji

    server = ServerUji(tmp_path, monkeypatch)
    try:
        with server.buka() as kon:
            siswa = database.tambah_siswa(kon, "feby", pemilik="guru")
            sesi = database.buat_sesi(kon, siswa, seed=83, jumlah_soal=1)
            kon.execute("UPDATE sesi SET tujuan = 'penguatan' WHERE id = ?", (sesi,))
        for jalur in ("/murid/", f"/murid/kerjakan/{sesi}"):
            status, isi, _ = server.minta(jalur, auth=("feby", SANDI_MURID))
            assert status == 200
            assert isinstance(isi, str)
            assert '<span class="label-tahap-murid">Coba mandiri</span>' in isi
            assert "Rencana belajar hari ini" not in isi
    finally:
        server.berhenti()
