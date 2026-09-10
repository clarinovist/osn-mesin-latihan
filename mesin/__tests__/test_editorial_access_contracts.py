"""Palang lintas halaman editorial: penolakan identik tanpa efek samping."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import auth
import database
from http_test_kit import ServerUji, SANDI_GURU, SANDI_MURID


@pytest.fixture()
def server(tmp_path, monkeypatch):
    server = ServerUji(tmp_path, monkeypatch)
    auth.tambah_akun("pendamping-lain", "sandi-sintetis-lain-123", "guru")
    with server.buka() as kon:
        anak = database.tambah_siswa(kon, "Anak Rahasia Sintetis", "P3", pemilik="pendamping-lain")
        sesi = database.buat_sesi(kon, anak, seed=173, level="P3", jumlah_soal=2)
        database.tandai_selesai(kon, sesi)
        lampiran = database.simpan_lampiran(kon, sesi, "foto-sintetis.png")
    yield server, {"anak": anak, "sesi": sesi, "lampiran": lampiran}
    server.berhenti()


@pytest.mark.parametrize("pola,kunci", [
    ("/anak/{}", "anak"),
    ("/laporan/{}", "anak"),
    ("/sesi/{}", "sesi"),
    ("/sesi/{}/cetak", "sesi"),
    ("/sesi/{}/lampiran", "sesi"),
    ("/sesi/{}/hapus", "sesi"),
    ("/lampiran/{}", "lampiran"),
    ("/lembar/{}", "sesi"),
    ("/lembar/{}/penilaian", "sesi"),
])
def test_halaman_asing_dan_tidak_ada_identik_tanpa_efek_samping(server, pola, kunci):
    s, ids = server
    with s.buka() as kon:
        sebelum = tuple(kon.iterdump())
    asing = s.minta(pola.format(ids[kunci]), auth=("guru", SANDI_GURU))
    hilang = s.minta(pola.format(999999), auth=("guru", SANDI_GURU))
    assert asing[0] == hilang[0] == 404
    assert asing[1] == hilang[1]
    assert "Anak Rahasia Sintetis" not in asing[1]
    with s.buka() as kon:
        assert tuple(kon.iterdump()) == sebelum


@pytest.mark.parametrize("jalur", [
    "/guru", "/ortu", "/akun?section=akun", "/akun?section=siswa",
    "/akun?section=akun-murid", "/sesi/1", "/sesi/1/cetak",
    "/sesi/1/lampiran", "/sesi/1/hapus", "/lampiran/1", "/laporan/1",
    "/anak/1", "/lembar/1", "/lembar/1/penilaian",
])
def test_murid_tidak_mendapat_permukaan_pendamping(server, jalur):
    s, _ = server
    with s.buka() as kon:
        sebelum = tuple(kon.iterdump())
    kode, isi, _ = s.minta(jalur, auth=("feby", SANDI_MURID))
    assert kode == 401
    assert "Anak Rahasia Sintetis" not in isi
    assert 'name="kode_' not in isi
    assert 'name="cek_pemahaman_' not in isi
    with s.buka() as kon:
        assert tuple(kon.iterdump()) == sebelum
