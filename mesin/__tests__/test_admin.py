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

import database  # noqa: E402
import auth  # noqa: E402
from http_test_kit import SANDI_GURU, SANDI_MURID, ServerUji  # noqa: E402

SANDI_A = "sandi-ortu-a-1234567"
SANDI_ADMIN = "sandi-pengelola-9999"


@pytest.fixture()
def server(tmp_path, monkeypatch):
    s = ServerUji(tmp_path, monkeypatch)
    with s.buka() as kon:
        a = database.tambah_siswa(kon, "BimaA", "P3", pemilik="ortu-a")
        database.buat_sesi(kon, a, seed=5)
    auth.tambah_akun("ortu-a", SANDI_A, "guru", path=auth.BERKAS_SANDI)
    auth.tambah_akun("pengelola", SANDI_ADMIN, "admin", path=auth.BERKAS_SANDI)
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
    assert auth.periksa_peran("ortu-baru", "sandi-ortu-baru-123", "guru")


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
    assert auth.periksa("ortu-a", SANDI_A), "sandi ortu-a ternyata berubah!"


def test_guru_baru_sandi_pendek_ditolak(server):
    kode, isi, _ = server.minta(
        "/admin",
        auth=("pengelola", SANDI_ADMIN),
        data={"aksi": "guru_baru", "pengguna": "pendek", "sandi": "pendek"},
    )
    assert kode == 200
    assert "12 karakter" in isi
    assert auth.cari_akun("pendek") is None


def test_css_badge_peran_tersedia():
    """Badge peran harus bergaya — bukan span telanjang di topbar."""
    import teacher_style

    assert ".badge-peran" in teacher_style.GAYA_GURU
    assert ".badge-keluarga" in teacher_style.GAYA_GURU


# --- Kebijakan admin: dashboard khusus + baca-semua-tulis-tidak -----------


def _ids_siswa_dan_sesi(server):
    with server.buka() as kon:
        siswa = kon.execute(
            "SELECT id FROM siswa WHERE nama = 'BimaA'"
        ).fetchone()["id"]
        sesi_id = kon.execute("SELECT id FROM sesi LIMIT 1").fetchone()["id"]
    return siswa, sesi_id


def _opener_tanpa_ikut():
    import urllib.error
    import urllib.request

    class TanpaIkut(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    return urllib.request.build_opener(TanpaIkut)


def test_admin_setelah_masuk_diarahkan_ke_panel(server):
    import urllib.error
    import urllib.parse
    import urllib.request

    req = urllib.request.Request(
        server.alamat + "/masuk",
        data=urllib.parse.urlencode(
            {"nama": "pengelola", "sandi": SANDI_ADMIN}
        ).encode(),
        method="POST",
    )
    try:
        _opener_tanpa_ikut().open(req)
        kode, header = 200, {}
    except urllib.error.HTTPError as e:
        kode, header = e.code, dict(e.headers)
    assert kode == 303
    lokasi = [v for k, v in header.items() if k.lower() == "location"]
    assert lokasi == ["/admin"], "admin harus darat di dashboard admin"


def test_admin_buka_root_diarahkan_ke_panel(server):
    # urllib mengikuti 303 -> halaman /admin, BUKAN dashboard guru.
    kode, isi, _ = server.minta("/", auth=("pengelola", SANDI_ADMIN))
    assert kode == 200
    assert "Panel Pengelola" in isi
    assert "Buat sesi baru" not in isi, "admin masih pegang murid lewat /"


def test_admin_dilarang_membuat_sesi(server):
    siswa_a, _ = _ids_siswa_dan_sesi(server)
    with server.buka() as kon:
        n0 = kon.execute("SELECT COUNT(*) AS n FROM sesi").fetchone()["n"]
    kode, _, _ = server.minta(
        f"/sesi-baru/{siswa_a}",
        auth=("pengelola", SANDI_ADMIN),
        data={"topik": "pola-bilangan", "mode": "diagnostik"},
    )
    assert kode == 404
    with server.buka() as kon:
        assert kon.execute("SELECT COUNT(*) AS n FROM sesi").fetchone()["n"] == n0


def test_admin_dilarang_hapus_sesi(server):
    _, sesi_a = _ids_siswa_dan_sesi(server)
    kode, _, _ = server.minta(
        f"/sesi/{sesi_a}/hapus",
        auth=("pengelola", SANDI_ADMIN),
        data={"konfirmasi": "1"},
    )
    assert kode == 404
    with server.buka() as kon:
        n = kon.execute(
            "SELECT COUNT(*) AS n FROM sesi WHERE id = ?", (sesi_a,)
        ).fetchone()["n"]
    assert n == 1, "sesi ternyata terhapus oleh admin"


def test_admin_dilarang_simpan_jawaban(server):
    _, sesi_a = _ids_siswa_dan_sesi(server)
    kode, _, _ = server.minta(
        f"/sesi/{sesi_a}",
        auth=("pengelola", SANDI_ADMIN),
        data={"jawaban_1": "diusap admin"},
    )
    assert kode == 404
    with server.buka() as kon:
        n = kon.execute(
            """SELECT COUNT(*) AS n FROM jawaban j
               JOIN sesi_soal ss ON ss.id = j.sesi_soal_id
               WHERE ss.sesi_id = ?""",
            (sesi_a,),
        ).fetchone()["n"]
    assert n == 0, "jawaban ternyata tersentuh admin"


def test_admin_dilarang_variasi_cerita(server):
    _, sesi_a = _ids_siswa_dan_sesi(server)
    kode, _, _ = server.minta(
        f"/cerita/{sesi_a}", auth=("pengelola", SANDI_ADMIN), data={}
    )
    assert kode == 404


def test_admin_dilarang_upload_lampiran(server):
    _, sesi_a = _ids_siswa_dan_sesi(server)
    kode, _, _ = server.minta(
        f"/lampiran/{sesi_a}", auth=("pengelola", SANDI_ADMIN), data={"x": "1"}
    )
    assert kode == 404


def test_admin_hanya_ganti_sandi_sendiri_di_akun(server):
    siswa_a, _ = _ids_siswa_dan_sesi(server)
    kode, _, _ = server.minta(
        "/akun",
        auth=("pengelola", SANDI_ADMIN),
        data={"aksi": "tingkat", "siswa_id": siswa_a, "tingkat": "P4"},
    )
    assert kode == 404, "aksi tulis di /akun harus tertutup untuk admin"
    with server.buka() as kon:
        tingkat = kon.execute(
            "SELECT tingkat FROM siswa WHERE id = ?", (siswa_a,)
        ).fetchone()["tingkat"]
    assert tingkat == "P3", "tingkat anak ternyata diubah admin"

    kode, isi, _ = server.minta(
        "/akun",
        auth=("pengelola", SANDI_ADMIN),
        data={
            "aksi": "sandi",
            "lama": SANDI_ADMIN,
            "baru": "sandi-pengelola-baru-1",
            "ulang": "sandi-pengelola-baru-1",
        },
    )
    assert kode == 200
    assert "Sandi diganti" in isi


def test_halaman_sesi_admin_hanya_baca(server):
    _, sesi_a = _ids_siswa_dan_sesi(server)
    kode, isi, _ = server.minta(
        f"/sesi/{sesi_a}", auth=("pengelola", SANDI_ADMIN)
    )
    assert kode == 200
    assert "Simpan &amp; diagnosis" not in isi, "form tulis bocor ke admin"
    assert "Hapus sesi" not in isi
    assert "Upload foto" not in isi
    assert "laporan siswa ini" in isi, "jalur baca harus tetap ada"


def test_admin_laporan_tetap_terbuka(server):
    siswa_a, _ = _ids_siswa_dan_sesi(server)
    kode, _, _ = server.minta(
        f"/laporan/{siswa_a}", auth=("pengelola", SANDI_ADMIN)
    )
    assert kode == 200, "admin masih boleh MEMBACA laporan"


def test_admin_panel_anak_ditautkan_ke_laporan(server):
    siswa_a, _ = _ids_siswa_dan_sesi(server)
    kode, isi, _ = server.minta("/admin", auth=("pengelola", SANDI_ADMIN))
    assert kode == 200
    assert f'href="/laporan/{siswa_a}"' in isi, "nama anak harus jadi tautan"
