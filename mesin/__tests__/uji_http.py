"""Server HTTP sungguhan untuk test palang web.

Lubang otorisasi ada di lapisan routing (Penangan.do_GET/do_POST), bukan di
fungsi halaman — jadi testnya harus lewat socket, bukan memanggil fungsi.
Helper ini menyalakan ThreadingHTTPServer di port acak 127.0.0.1 dengan
basis data dan berkas sandi sementara (tmp_path), lalu menyediakan minta()
yang mengembalikan (kode_status, isi_html).
"""
from __future__ import annotations

import base64
import threading
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from http.server import ThreadingHTTPServer

import basis  # noqa: E402
import sandi  # noqa: E402
import web  # noqa: E402

SANDI_GURU = "sandi-guru-panjang-123"
SANDI_MURID = "sandi-feby-12345"


def _basic(pengguna: str, sandi_txt: str) -> str:
    token = base64.b64encode(f"{pengguna}:{sandi_txt}".encode()).decode()
    return f"Basic {token}"


class ServerUji:
    """Server nyata di port acak; semua state di tmp_path."""

    def __init__(self, tmp_path, monkeypatch):
        db = tmp_path / "uji.db"
        basis.siapkan(db)
        monkeypatch.setattr(basis, "BAWAAN", db)
        # PENTING: buka() punya default arg terikat-saat-impor, jadi
        # monkeypatch BAWAAN tidak mengubah pemanggilan buka() tanpa argumen.
        # Test HARUS memakai server.buka(), bukan basis.buka().
        self.db = db

        berkas = tmp_path / "sandi.json"
        sandi.simpan_sandi(SANDI_GURU, "guru", path=berkas)
        if "akun" in (sandi.muat_sandi(berkas) or {}):
            # bentuk multi-aktif: simpan_sandi menulis {"akun": [...]} bila
            # berkas lama sudah multi-akun — tambahkan feby hanya sekali.
            if not sandi.cari_akun("feby", path=berkas):
                sandi.tambah_akun("feby", SANDI_MURID, "murid", path=berkas)
        else:
            sandi.tambah_akun("feby", SANDI_MURID, "murid", path=berkas)
        monkeypatch.setattr(sandi, "BERKAS_SANDI", berkas)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), web.Penangan)
        self.alamat = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.ulir = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.ulir.start()

    def berhenti(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    @contextmanager
    def buka(self):
        """Koneksi ke DB uji — selalu path eksplisit, tak tersentuh DB asli."""
        with basis.buka(self.db) as kon:
            yield kon

    def minta(
        self,
        jalur: str,
        auth: tuple[str, str] | None = None,
        data: dict | None = None,
        cookie: str | None = None,
        method: str | None = None,
        biner: bool = False,
    ) -> tuple[int, str | bytes, dict]:
        """Satu permintaan HTTP -> (kode, isi_str, header_respons).

        data dict -> form-encoded POST. auth -> Basic header. cookie -> nilai
        mentah untuk header Cookie (tanpa 'osn_sesi=' — itu ditambahkan di sini
        bila diberikan sebagai string token; boleh juga string penuh).
        biner=True -> isi dikembalikan sebagai bytes (untuk rute berkas).
        """
        isi = None
        metode = method
        if data is not None:
            isi = urllib.parse.urlencode(data).encode()
            if metode is None:
                metode = "POST"
        req = urllib.request.Request(self.alamat + jalur, data=isi, method=metode)
        if isi is not None:
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
        if auth:
            req.add_header("Authorization", _basic(*auth))
        if cookie:
            if "=" not in cookie:
                cookie = f"osn_sesi={cookie}"
            req.add_header("Cookie", cookie)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                mentah = r.read()
                return (
                    r.status,
                    mentah if biner else mentah.decode("utf-8"),
                    dict(r.headers),
                )
        except urllib.error.HTTPError as e:
            mentah = e.read()
            return (
                e.code,
                mentah if biner else mentah.decode("utf-8", "replace"),
                dict(e.headers),
            )
