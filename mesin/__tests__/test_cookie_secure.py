"""Kuki sesi: Secure hanya dipasang saat memang lewat HTTPS.

Bug lapangan (1 Sep 2026): Secure dipasang untuk SEMUA host non-localhost,
termasuk mode LAN HTTP (serve.py --jaringan, host 192.168.x.x lewat WiFi).
Peramban anak diam-diam membuang kuki Secure yang datang dari HTTP biasa —
muat-ulang tiba tanpa identitas, halaman murid jadi polos, dan anak harus
keluar-masuk lagi. Secure kini mengikuti bukti HTTPS yang sebenarnya
(X-Forwarded-Proto dari proxy / env OSN_HTTPS=1), bukan nama host.
"""
from __future__ import annotations

import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from http_test_kit import SANDI_GURU, ServerUji  # noqa: E402


@pytest.fixture()
def server(tmp_path, monkeypatch):
    s = ServerUji(tmp_path, monkeypatch)
    yield s
    s.berhenti()


def _kuki_setelah_masuk(server, headers=None):
    """POST /masuk tanpa mengikuti 303 -> nilai header Set-Cookie mentah."""

    class TanpaIkut(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(TanpaIkut)
    req = urllib.request.Request(
        server.alamat + "/masuk",
        data=urllib.parse.urlencode({"nama": "guru", "sandi": SANDI_GURU}).encode(),
        method="POST",
    )
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        opener.open(req)
        raise AssertionError("POST /masuk harusnya 303")
    except urllib.error.HTTPError as e:
        assert e.code == 303
        return dict(e.headers).get("Set-Cookie", "")


def test_kuki_lan_http_tanpa_secure(server):
    """Kondisi lapangan: host LAN (192.168.x.x) lewat HTTP biasa.

    Kuki HARUS datang tanpa atribut Secure — peramban membuang kuki Secure
    dari origin non-HTTPS, dan hilangnya kuki itulah yang membuat halaman
    murid polos saat muat-ulang. (Dengan aturan host lama, test ini gagal:
    Secure terpasang justru di kondisi yang paling sering dipakai anak.)
    """
    kuki = _kuki_setelah_masuk(server, headers={"Host": "192.168.1.5:8724"})
    assert "osn_sesi=" in kuki
    assert "secure" not in kuki.lower()


def test_kuki_lewat_proxy_https_punya_secure(server):
    """Di VPS di balik Caddy, proxy meneruskan X-Forwarded-Proto: https."""
    kuki = _kuki_setelah_masuk(server, headers={"X-Forwarded-Proto": "https"})
    assert "secure" in kuki.lower()


def test_kuki_env_https_punya_secure(server, monkeypatch):
    """Penyiapan manual: env OSN_HTTPS=1 menandakan semua request lewat HTTPS."""
    monkeypatch.setenv("OSN_HTTPS", "1")
    kuki = _kuki_setelah_masuk(server)
    assert "secure" in kuki.lower()
