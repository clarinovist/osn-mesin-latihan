"""Verifikasi palang sandi — penjaga data anak.

Yang diuji bukan "apakah sandi benar diterima" saja, tapi terutama apakah
yang SALAH benar-benar ditolak, dan apakah tidak ada jalur yang lolos tanpa
sandi. Palang yang bocor di satu rute membuat seluruh sisanya sia-sia.
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import auth  # noqa: E402


@pytest.fixture()
def berkas(tmp_path, monkeypatch):
    p = tmp_path / "sandi.json"
    monkeypatch.setattr(auth, "BERKAS_SANDI", p)
    return p


def test_sandi_benar_diterima(berkas):
    auth.simpan_sandi("rahasia-kuat-123", "guru", berkas)
    assert auth.periksa("guru", "rahasia-kuat-123", auth.muat_sandi(berkas))


def test_sandi_salah_ditolak(berkas):
    auth.simpan_sandi("rahasia-kuat-123", "guru", berkas)
    d = auth.muat_sandi(berkas)
    assert not auth.periksa("guru", "rahasia-kuat-124", d)
    assert not auth.periksa("guru", "", d)
    assert not auth.periksa("guru", "rahasia-kuat-1234", d)


def test_nama_pengguna_salah_ditolak(berkas):
    auth.simpan_sandi("rahasia", "guru", berkas)
    d = auth.muat_sandi(berkas)
    assert not auth.periksa("admin", "rahasia", d)
    assert not auth.periksa("", "rahasia", d)


def test_sandi_tidak_disimpan_sebagai_teks(berkas):
    """Kalau berkasnya terbaca orang, sandinya tidak boleh langsung terpakai."""
    auth.simpan_sandi("sandi-sangat-rahasia", "guru", berkas)
    isi = berkas.read_text()
    assert "sandi-sangat-rahasia" not in isi
    assert "kunci" in isi and "garam" in isi


def test_berkas_sandi_hanya_bisa_dibaca_pemilik(berkas):
    """Di VPS bersama, berkas world-readable sama saja dengan tanpa sandi."""
    auth.simpan_sandi("x", "guru", berkas)
    assert oct(berkas.stat().st_mode)[-3:] == "600"


def test_garam_berbeda_tiap_kali(berkas):
    """Dua orang dengan sandi sama tidak boleh punya hash sama."""
    a = auth.buat_hash("sandi-sama")
    b = auth.buat_hash("sandi-sama")
    assert a["garam"] != b["garam"]
    assert a["kunci"] != b["kunci"]


def test_tanpa_berkas_sandi_palang_tidak_aktif(berkas):
    """Mode lokal: tanpa berkas sandi, tidak ada palang — dan itu disengaja
    supaya pemakaian di localhost tidak terhambat."""
    assert not auth.wajib_sandi()
    assert not auth.periksa("guru", "apa saja", None)


def test_berkas_rusak_tidak_membuka_palang(berkas):
    """Berkas rusak harus GAGAL TERTUTUP, bukan gagal terbuka."""
    berkas.write_text("{ini bukan json")
    assert auth.muat_sandi(berkas) is None
    assert not auth.periksa("guru", "apa pun", auth.muat_sandi(berkas))


def test_hash_rusak_tidak_membuka_palang(berkas):
    berkas.write_text('{"pengguna":"guru","garam":"bukanhex","kunci":"zz"}')
    assert not auth.periksa("guru", "apa pun", auth.muat_sandi(berkas))


# ── Penguraian header ───────────────────────────────────────────────────


def test_header_basic_diuraikan():
    sandi_b64 = base64.b64encode(b"guru:rahasia").decode()
    assert auth.dari_header(f"Basic {sandi_b64}") == ("guru", "rahasia")


def test_header_tidak_sah_ditolak():
    for h in (None, "", "Bearer abc", "Basic ???", "Basic " + base64.b64encode(b"tanpatitikdua").decode()):
        assert auth.dari_header(h) is None


def test_sandi_boleh_mengandung_titik_dua():
    """Hanya titik dua PERTAMA yang memisahkan; sisanya bagian dari sandi."""
    b = base64.b64encode(b"guru:sandi:dengan:titik").decode()
    assert auth.dari_header(f"Basic {b}") == ("guru", "sandi:dengan:titik")


# ── Role admin & tautan siswa akun murid (multi-keluarga) ───────────────


def test_peran_meliputi_admin():
    assert auth.PERAN == ("admin", "guru", "murid")


def test_tambah_akun_murid_membawa_siswa_id(berkas):
    auth.tambah_akun("feby", "sandi-anak-123", "murid", berkas, siswa_id=7)
    a = auth.cari_akun("feby", berkas)
    assert a["siswa_id"] == 7


def test_tambah_akun_tanpa_siswa_id_tak_membawa_kunci(berkas):
    auth.tambah_akun("guru", "sandi-guru-1234", "guru", berkas)
    a = auth.cari_akun("guru", berkas)
    assert "siswa_id" not in a


def test_tambah_akun_admin_sah(berkas):
    auth.tambah_akun("pengelola", "sandi-guru-1234", "admin", berkas)
    assert auth.cari_akun("pengelola", berkas)["peran"] == "admin"
    assert auth.periksa_peran("pengelola", "sandi-guru-1234", "admin", berkas)


def test_pastikan_admin_mempromosikan_guru_pertama(berkas):
    auth.tambah_akun("ortu-a", "sandi-guru-1234", "guru", berkas)
    auth.tambah_akun("feby", "sandi-anak-123", "murid", berkas)
    nama = auth.pastikan_admin(berkas)
    assert nama == "ortu-a"
    akun = auth.muat_akun(berkas)
    assert [a["peran"] for a in akun] == ["admin", "murid"]


def test_pastikan_admin_idempoten(berkas):
    auth.tambah_akun("ortu-a", "sandi-guru-1234", "guru", berkas)
    auth.tambah_akun("ortu-b", "sandi-guru-1234", "guru", berkas)
    assert auth.pastikan_admin(berkas) == "ortu-a"
    assert auth.pastikan_admin(berkas) == "ortu-a"
    n = sum(1 for a in auth.muat_akun(berkas) if a.get("peran") == "admin")
    assert n == 1


def test_pastikan_admin_tanpa_guru_mengembalikan_none(berkas):
    auth.tambah_akun("feby", "sandi-anak-123", "murid", berkas)
    assert auth.pastikan_admin(berkas) is None
    # berkas tak berubah
    assert auth.cari_akun("feby", berkas)["peran"] == "murid"


def test_pastikan_admin_bila_sudah_ada(berkas):
    auth.tambah_akun("pengelola", "sandi-guru-1234", "admin", berkas)
    auth.tambah_akun("ortu-a", "sandi-guru-1234", "guru", berkas)
    assert auth.pastikan_admin(berkas) == "pengelola"
