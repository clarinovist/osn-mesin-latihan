"""Regresi server test cepat dengan socket nyata dan cleanup ulir tuntas."""
from pathlib import Path
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import http_test_kit


def test_server_uji_memakai_polling_pendek_tanpa_mengganti_http(tmp_path, monkeypatch):
    interval = []
    masuk_loop = threading.Event()
    asli = http_test_kit.ThreadingHTTPServer.serve_forever

    def layani(server, poll_interval=0.5):
        interval.append(poll_interval)
        masuk_loop.set()
        return asli(server, poll_interval=poll_interval)

    monkeypatch.setattr(http_test_kit.ThreadingHTTPServer, "serve_forever", layani)
    server = http_test_kit.ServerUji(tmp_path, monkeypatch)
    try:
        assert masuk_loop.wait(5), "Ulir server uji tidak mulai"
        kode, isi, _ = server.minta("/")
        assert kode == 200
        assert "<html" in isi
        assert interval == [0.01]
    finally:
        server.berhenti()


def test_berhenti_menutup_socket_dan_join_ulir_sebelum_kembali(tmp_path, monkeypatch):
    """Akhir ulir ditahan agar test membuktikan join, bukan kebetulan timing."""
    keluar_loop = threading.Event()
    lepaskan_ulir = threading.Event()
    layani_asli = http_test_kit.ThreadingHTTPServer.serve_forever

    def layani(server, poll_interval=0.5):
        try:
            return layani_asli(server, poll_interval=poll_interval)
        finally:
            keluar_loop.set()
            # Timeout hanya pengaman deadlock test, bukan target performa.
            lepaskan_ulir.wait(10)

    monkeypatch.setattr(http_test_kit.ThreadingHTTPServer, "serve_forever", layani)
    server = http_test_kit.ServerUji(tmp_path, monkeypatch)
    urutan = []
    shutdown_asli = server.server.shutdown
    tutup_asli = server.server.server_close
    join_asli = server.ulir.join

    def shutdown():
        urutan.append("shutdown")
        shutdown_asli()

    def tutup():
        urutan.append("server_close")
        tutup_asli()

    def join(*args, **kwargs):
        urutan.append("join")
        assert keluar_loop.wait(5), "Loop belum berhenti sebelum join"
        assert server.ulir.is_alive(), "Ulir sintetis belum ditahan"
        lepaskan_ulir.set()
        join_asli(*args, **kwargs)

    monkeypatch.setattr(server.server, "shutdown", shutdown)
    monkeypatch.setattr(server.server, "server_close", tutup)
    monkeypatch.setattr(server.ulir, "join", join)
    try:
        assert server.minta("/")[0] == 200
        server.berhenti()
        assert urutan == ["shutdown", "server_close", "join"]
        assert server.server.socket.fileno() == -1
        assert not server.ulir.is_alive()
    finally:
        lepaskan_ulir.set()
        shutdown_asli()
        tutup_asli()
        join_asli(timeout=5)


def test_berhenti_berulang_tetap_menutup_server_uji(tmp_path, monkeypatch):
    server = http_test_kit.ServerUji(tmp_path, monkeypatch)
    try:
        assert server.minta("/")[0] == 200
    finally:
        server.berhenti()
        server.berhenti()
    assert not server.ulir.is_alive()
    assert server.server.socket.fileno() == -1
    assert server.db == tmp_path / "uji.db"
