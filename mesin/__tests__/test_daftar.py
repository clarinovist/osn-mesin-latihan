"""Fase B launch publik: pendaftaran mandiri (pengelola + anak).

Kontrak:
1. GET /daftar tanpa sesi -> 200 form pendaftaran.
2. POST /daftar (nama+sandi+setuju) -> akun guru dibuat, auto-login
   (cookie sesi), 303 ke /.
3. Nama sudah dipakai -> galat jelas, TIDAK ada akun baru, TIDAK login.
4. Checkbox persetujuan tidak dicentang -> galat, tidak ada akun.
5. Sandi terlalu pendek -> galat, tidak ada akun.
6. Rate limit login (/masuk) tidak berubah; /daftar memakai jalur gagal
   yang sama bila ada.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sandi  # noqa: E402
from uji_http import ServerUji  # noqa: E402

SANDI_BARU = "sandi-panjang-ortu-123"


@pytest.fixture()
def server(tmp_path, monkeypatch):
    s = ServerUji(tmp_path, monkeypatch)
    yield s
    s.berhenti()


def test_get_daftar_publik(server):
    kode, isi, _ = s_minta(server, "/daftar")
    assert kode == 200
    assert "daftar" in isi.lower()
    assert 'name="nama"' in isi
    assert 'name="sandi"' in isi
    assert 'name="setuju"' in isi  # checkbox persetujuan


def s_minta(server, jalur, **kw):
    return server.minta(jalur, **kw)


def test_post_daftar_membuat_akun_guru_dan_login(server):
    # PITFALL (dari skill): ServerUji.minta memakai urllib yang MENGIKUTI 303,
    # jadi POST redirect diterima sebagai 200 halaman tujuan. Untuk memeriksa
    # 303 + Set-Cookie, pakai opener tanpa redirect.
    import urllib.error
    import urllib.parse
    import urllib.request

    class TanpaIkut(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(TanpaIkut)
    req = urllib.request.Request(
        server.alamat + "/daftar",
        data=urllib.parse.urlencode(
            {"nama": "orangtua-budi", "sandi": SANDI_BARU, "setuju": "1"}
        ).encode(),
        method="POST",
    )
    try:
        opener.open(req)
        kode, header = 200, {}
    except urllib.error.HTTPError as e:
        kode, header = e.code, dict(e.headers)
    assert kode == 303
    akun = sandi.cari_akun("orangtua-budi")
    assert akun is not None
    assert akun.get("peran") == "guru"
    assert sandi.periksa("orangtua-budi", SANDI_BARU)
    # auto-login: cookie sesi diberikan
    assert any("osn_sesi=" in v for k, v in header.items() if k.lower() == "set-cookie")


def test_post_daftar_nama_duplikat_ditolak(server):
    s_minta(
        server,
        "/daftar",
        data={"nama": "budi", "sandi": SANDI_BARU, "setuju": "1"},
    )
    kode, isi, header = s_minta(
        server,
        "/daftar",
        data={"nama": "BUDI", "sandi": "sandi-lain-panjang-999"},
    )
    assert kode == 200  # form kembali dengan galat, bukan 500
    assert sandi.cari_akun("budi") is not None
    # tidak ada akun kedua yang dibuat dengan sandi kedua
    assert not sandi.periksa("budi", "sandi-lain-panjang-999")
    # tidak di-login-kan
    assert not any(
        "osn_sesi=" in v and "Max-Age=0" not in v
        for k, v in header.items()
        if k.lower() == "set-cookie"
    )


def test_post_daftar_tanpa_persetujuan_ditolak(server):
    kode, isi, _ = s_minta(
        server, "/daftar", data={"nama": "tanpa-setuju", "sandi": SANDI_BARU}
    )
    assert kode == 200
    assert sandi.cari_akun("tanpa-setuju") is None
    assert "persetujuan" in isi.lower() or "setuju" in isi.lower()


def test_post_daftar_sandi_pendek_ditolak(server):
    kode, _, _ = s_minta(
        server,
        "/daftar",
        data={"nama": "sandipendek", "sandi": "pendek", "setuju": "1"},
    )
    assert kode == 200
    assert sandi.cari_akun("sandipendek") is None


def test_post_daftar_nama_kosong_ditolak(server):
    kode, _, _ = s_minta(
        server,
        "/daftar",
        data={"nama": "   ", "sandi": SANDI_BARU, "setuju": "1"},
    )
    assert kode == 200
    assert sandi.cari_akun("   ") is None and sandi.cari_akun("") is None
