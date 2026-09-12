"""Smoke publik diuji lewat transport sintetis, bukan akun/data keluarga."""

from email.message import Message
import importlib.util
import io
from pathlib import Path
import urllib.error

import pytest

AKAR = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("smoke_uji", AKAR / "scripts/smoke_public.py")
s = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s)


class Pembuka:
    def __init__(self, status=(200, 401, 303), lokasi=("/masuk?galat=pesan+sintetis",)):
        self.status = status
        self.lokasi = lokasi
        self.panggilan = []
        self.bodies = []

    def open(self, permintaan, timeout):
        self.panggilan.append(permintaan)
        assert timeout == 10
        assert permintaan.get_method() == "GET"
        assert permintaan.get_header("User-agent") == s.USER_AGENT
        assert not permintaan.has_header("Cookie")
        assert not permintaan.has_header("Authorization")
        nomor = len(self.panggilan) - 1
        h = Message()
        if nomor == 2:
            for lokasi in self.lokasi:
                h.add_header("Location", lokasi)
        tubuh = io.BytesIO(b"isi-sintetis-tidak-perlu-dibaca")
        self.bodies.append(tubuh)
        raise urllib.error.HTTPError(permintaan.full_url, self.status[nomor], "sintetis", h, tubuh)


def test_smoke_tiga_permukaan_dengan_query_dan_tutup_respons():
    pembuka = Pembuka()
    assert s.periksa(pembuka)
    assert [p.full_url for p in pembuka.panggilan] == [s.URL_SITUS + x for x in ("/", "/akun", "/murid/")]
    assert all(b.closed for b in pembuka.bodies)


@pytest.mark.parametrize("lokasi", ["/masuk", "/masuk?galat=pesan+sintetis"])
def test_redirect_relatif_dengan_query_sah(lokasi):
    assert s.periksa(Pembuka(lokasi=(lokasi,)))


@pytest.mark.parametrize("lokasi", [(), ("/masuk", "/masuk"), ("https://jahat.invalid/masuk",),
    ("https://jagomat.id/masuk",), ("//jahat.invalid/masuk",), ("/masuk#frag",),
    (" /masuk",), ("/masuk\n",), ("/masuk/lain",), ("/masuk\\lain",), ("/%6dasuk",), ("",)])
def test_redirect_tidak_aman_atau_ambigu_ditolak(lokasi):
    assert not s.periksa(Pembuka(lokasi=lokasi))


@pytest.mark.parametrize("status", [(403, 401, 303), (200, 200, 303), (200, 401, 200),
                                    (200, 401, 302), (503, 401, 303)])
def test_status_salah_tidak_disamarkan(status):
    assert not s.periksa(Pembuka(status=status))


def test_transport_tanpa_proxy_dan_redirect(monkeypatch):
    handlers = []
    pembuka = Pembuka()
    def buat(*args):
        handlers.extend(args)
        return pembuka
    monkeypatch.setattr(s.urllib.request, "build_opener", buat)
    assert s.periksa()
    assert handlers[0].proxies == {}
    assert isinstance(handlers[1], s.TanpaRedirect)
    assert handlers[1].redirect_request(None) is None


def test_body_tidak_dibaca():
    class Respons:
        code = 200
        headers = Message()
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, *args): pytest.fail("Jangan baca body")
    class TanpaBody:
        def open(self, *args, **kwargs): return Respons()
    assert not s.periksa(TanpaBody())  # /akun200 ditolak tanpa read()


@pytest.mark.parametrize("galat", [OSError, urllib.error.URLError, ValueError])
def test_transport_gagal_false(galat):
    class Gagal:
        def open(self, *args, **kwargs): raise galat("sintetis")
    assert not s.periksa(Gagal())


def test_retry_terbatas_dan_exit_nonzero():
    jeda = []
    assert s.main(uji=lambda: False, tidur=jeda.append) == 1
    assert jeda == [6] * 9
    hasil = iter([False, True])
    jeda.clear()
    assert s.main(uji=lambda: next(hasil), tidur=jeda.append) == 0
    assert jeda == [6]


def test_url_kanonis_dan_user_agent_terverifikasi():
    import ast
    pohon = ast.parse((AKAR / "mesin/brand.py").read_text())
    nilai = [n.value.value for n in pohon.body if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == "URL_SITUS" for t in n.targets)]
    assert nilai == [s.URL_SITUS]
    assert s.USER_AGENT == "curl/8.7.1"
