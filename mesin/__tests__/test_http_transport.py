"""Regresi penutupan HTTP: POST ditolak tetap utuh tanpa menunggu body klien."""
from __future__ import annotations

import http.client
from pathlib import Path
import socket
import sys
import threading

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import web
from http_test_kit import ServerUji, SANDI_MURID, _basic


@pytest.mark.parametrize("identitas", ["anonim", "murid", "token_asing"])
def test_post_ditolak_menguras_body_terlambat_tanpa_mengubah_data(
    tmp_path, monkeypatch, identitas,
):
    """Body baru dikirim sesudah FIN server; tidak bergantung penjadwalan OS."""
    selesai = threading.Event()
    mulai_tutup = threading.Event()
    terkuras = bytearray()
    urutan = []
    asli = web.Penangan.setup

    class SoketTeramati:
        def __init__(self, soket):
            self.soket = soket

        def __getattr__(self, nama):
            return getattr(self.soket, nama)

        def shutdown(self, arah):
            hasil = self.soket.shutdown(arah)
            if arah == socket.SHUT_WR:
                urutan.append("tutup_tulis")
                mulai_tutup.set()
            return hasil

        def recv(self, ukuran):
            isi = self.soket.recv(ukuran)
            urutan.append("kuras")
            terkuras.extend(isi)
            return isi

    def siapkan(penangan):
        penangan.request = SoketTeramati(penangan.request)
        asli(penangan)

    monkeypatch.setattr(web.Penangan, "setup", siapkan)
    server = ServerUji(tmp_path, monkeypatch)
    tutup_asli = server.server.close_request

    def tutup(permintaan):
        try:
            tutup_asli(permintaan)
        finally:
            selesai.set()

    monkeypatch.setattr(server.server, "close_request", tutup)
    try:
        with server.buka() as kon:
            sebelum = tuple(kon.iterdump())
        header = ""
        if identitas == "murid":
            header = "Authorization: " + _basic("feby", SANDI_MURID) + "\r\n"
        elif identitas == "token_asing":
            header = "Cookie: osn_sesi=token-sintetis-bukan-login\r\n"
        tubuh = b"sesi_soal_id=1"
        with socket.create_connection(server.server.server_address, timeout=5) as klien:
            klien.sendall((
                "POST /sesi/1/latihan-serupa HTTP/1.0\r\nHost: localhost\r\n"
                + header + "Content-Length: " + str(len(tubuh)) + "\r\n\r\n"
            ).encode())
            with http.client.HTTPResponse(klien) as respons:
                respons.begin()
                isi = respons.read()
                assert respons.status == 401
                assert len(isi) == int(respons.getheader("Content-Length"))
                assert b"Perlu masuk" in isi
                # Server harus sudah mengirim respons TANPA meminta body dulu.
                assert mulai_tutup.wait(5), "Sisi tulis belum ditutup sebelum drain"
                klien.sendall(tubuh)
                klien.shutdown(socket.SHUT_WR)
                assert selesai.wait(5), "Cleanup koneksi belum selesai"
        assert bytes(terkuras) == tubuh
        assert urutan[0] == "tutup_tulis"
        with server.buka() as kon:
            assert tuple(kon.iterdump()) == sebelum
    finally:
        server.berhenti()


@pytest.mark.parametrize("panjang", ["0", "999999999999999999", "tidak-valid"])
def test_body_tidak_datang_tetap_401_dan_cleanup_selesai(tmp_path, monkeypatch, panjang):
    selesai = threading.Event()
    server = ServerUji(tmp_path, monkeypatch)
    tutup_asli = server.server.close_request

    def tutup(permintaan):
        try:
            tutup_asli(permintaan)
        finally:
            selesai.set()

    monkeypatch.setattr(server.server, "close_request", tutup)
    try:
        with socket.create_connection(server.server.server_address, timeout=5) as klien:
            klien.sendall((
                "POST /sesi/1/latihan-serupa HTTP/1.0\r\nHost: localhost\r\n"
                "Content-Length: " + panjang + "\r\n\r\n"
            ).encode())
            with http.client.HTTPResponse(klien) as respons:
                respons.begin()
                assert respons.status == 401
                assert len(respons.read()) == int(respons.getheader("Content-Length"))
                # Klien sengaja tetap terbuka tanpa mengirim body ataupun EOF.
                assert selesai.wait(5), "Server menunggu body tanpa batas"
    finally:
        server.berhenti()


@pytest.mark.parametrize("jalur", ["/", "/akun"])
def test_get_tetap_utuh_dan_socket_ditutup(tmp_path, monkeypatch, jalur):
    server = ServerUji(tmp_path, monkeypatch)
    try:
        kode, isi, header = server.minta(jalur)
        assert kode == (200 if jalur == "/" else 401)
        assert len(isi.encode()) == int(header["Content-Length"])
    finally:
        server.berhenti()


@pytest.mark.parametrize("mode", ["eof", "timeout", "reset", "shutdown_gagal", "banjir", "lambat"])
def test_finish_membatasi_waktu_dan_byte_drain(monkeypatch, mode):
    """Jam/socket terkontrol membuktikan batas tanpa sleep atau banjir jaringan."""
    urutan = []
    terbaca = []
    waktu = [10.0]
    timeout = []

    class Soket:
        def shutdown(self, arah):
            assert arah == socket.SHUT_WR
            urutan.append("fin")
            if mode == "shutdown_gagal":
                raise OSError("Koneksi sintetis sudah ditutup")

        def settimeout(self, nilai):
            assert 0 < nilai <= 0.2
            timeout.append(nilai)

        def recv(self, ukuran):
            assert 0 < ukuran <= 8192
            assert urutan == ["finish_stream", "fin"]
            terbaca.append(ukuran)
            assert len(terbaca) <= 8, "Drain tidak dibatasi"
            if mode == "timeout":
                raise socket.timeout()
            if mode == "reset":
                raise ConnectionResetError()
            if mode == "eof":
                return b""
            if mode == "lambat":
                waktu[0] += 0.125
                return b"x"
            return b"x" * ukuran

    def tutup_stream(penangan):
        urutan.append("finish_stream")

    monkeypatch.setattr(web.BaseHTTPRequestHandler, "finish", tutup_stream)
    monkeypatch.setattr(web.time, "monotonic", lambda: waktu[0])
    penangan = object.__new__(web.Penangan)
    penangan.connection = Soket()
    penangan.finish()
    assert urutan == ["finish_stream", "fin"]
    if mode == "banjir":
        assert sum(terbaca) == 64 * 1024
    elif mode == "lambat":
        assert len(terbaca) == 2
        assert timeout[1] < timeout[0]
    else:
        assert len(terbaca) == (0 if mode == "shutdown_gagal" else 1)
