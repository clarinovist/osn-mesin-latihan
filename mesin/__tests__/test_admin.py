"""Halaman /admin — panel khusus pengelola (role admin).

Admin = pemilik produk: melihat semua keluarga dan membuat akun orang tua.
Guru, murid, dan anonim tidak boleh masuk — tolakan 401, karena halaman
ini memuat daftar akun dan nama anak lintas keluarga.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import basis  # noqa: E402
import sandi  # noqa: E402
from uji_http import SANDI_GURU, SANDI_MURID, ServerUji  # noqa: E402

SANDI_A = "sandi-ortu-a-1234567"
SANDI_ADMIN = "sandi-pengelola-9999"


@pytest.fixture()
def server(tmp_path, monkeypatch):
    s = ServerUji(tmp_path, monkeypatch)
    with s.buka() as kon:
        a = basis.tambah_siswa(kon, "BimaA", "P3", pemilik="ortu-a")
        basis.buat_sesi(kon, a, seed=5)
    sandi.tambah_akun("ortu-a", SANDI_A, "guru", path=sandi.BERKAS_SANDI)
    sandi.tambah_akun("pengelola", SANDI_ADMIN, "admin", path=sandi.BERKAS_SANDI)
    yield s
    s.berhenti()


def test_bukan_admin_ditolak(server):
    assert server.minta("/admin")[0] == 401
    kode, isi, _ = server.minta("/admin", auth=("guru", SANDI_GURU))
    assert kode == 401
    assert "BimaA" not in isi, "daftar keluarga bocor ke guru"
    kode, _, _ = server.minta("/admin", auth=("feby", SANDI_MURID))
    assert kode == 401
    kode, _, _ = server.minta("/admin", method="POST", data={})
    assert kode == 401


def test_admin_melihat_daftar_keluarga(server):
    kode, isi, _ = server.minta("/admin", auth=("pengelola", SANDI_ADMIN))
    assert kode == 200
    assert "ortu-a" in isi
    assert "BimaA" in isi
    assert "guru" in isi  # akun "guru" bawaan ServerUji ikut terdaftar
    assert 'name="pengguna"' in isi  # form buat akun orang tua


def test_admin_membuat_akun_orang_tua(server):
    kode, isi, _ = server.minta(
        "/admin",
        auth=("pengelola", SANDI_ADMIN),
        data={
            "aksi": "guru_baru",
            "pengguna": "ortu-baru",
            "sandi": "sandi-ortu-baru-123",
        },
    )
    assert kode == 200
    assert "ortu-baru" in isi
    assert sandi.periksa_peran("ortu-baru", "sandi-ortu-baru-123", "guru")


def test_guru_baru_nama_ganda_ditolak_tanpa_mengubah_lama(server):
    server.minta(
        "/admin",
        auth=("pengelola", SANDI_ADMIN),
        data={
            "aksi": "guru_baru",
            "pengguna": "ortu-a",
            "sandi": "sandi-penyerang-999",
        },
    )
    assert sandi.periksa("ortu-a", SANDI_A), "sandi ortu-a ternyata berubah!"


def test_guru_baru_sandi_pendek_ditolak(server):
    kode, isi, _ = server.minta(
        "/admin",
        auth=("pengelola", SANDI_ADMIN),
        data={"aksi": "guru_baru", "pengguna": "pendek", "sandi": "pendek"},
    )
    assert kode == 200
    assert "12 karakter" in isi
    assert sandi.cari_akun("pendek") is None


def test_css_badge_peran_tersedia():
    """Badge peran harus bergaya — bukan span telanjang di topbar."""
    import gaya_guru

    assert ".badge-peran" in gaya_guru.GAYA_GURU
    assert ".badge-keluarga" in gaya_guru.GAYA_GURU
