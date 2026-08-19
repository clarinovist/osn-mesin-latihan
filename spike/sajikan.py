#!/usr/bin/env python3
"""Sajikan perekam goresan lewat WiFi lokal, supaya bisa dibuka di HP.

Jalankan:
    ./.venv/bin/python sajikan.py

Lalu buka alamat yang tercetak di Safari HP. Hentikan dengan Ctrl-C.

Kenapa ada: berkas HTML yang dibuka lewat app Files di iOS dijalankan di
WebView terbatas, bukan Safari penuh — beberapa hal berperilaku lain di
sana, dan gejalanya membingungkan (halaman tampil, tapi interaksinya tidak
jalan). Menyajikannya lewat `http://` menghilangkan seluruh kelas masalah
itu sekaligus: HP membukanya sebagai halaman web biasa, persis seperti di
Mac tempat semuanya sudah terbukti bekerja.

Soal jaminan "tidak menyentuh internet" (Rencana Spike, Bagian "Keputusan"):
server ini hanya mendengar di jaringan lokal dan hanya MENGIRIM berkas ke
HP. Halamannya sendiri tetap nol rujukan keluar — tidak ada data anak yang
dikirim ke mana pun, dan hasil sesi tetap turun sebagai unduhan di HP.
Server ini juga hanya hidup selama Bapak menjalankannya.
"""
import http.server
import socket
import socketserver
import sys
from pathlib import Path

SPIKE_DIR = Path(__file__).resolve().parent
PORT = 8000


def alamat_lokal():
    """IP Mac di jaringan WiFi, dilihat dari sudut pandang perangkat lain."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Tidak benar-benar mengirim paket — hanya memaksa OS memilih interface.
        s.connect(("192.0.2.1", 1))
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(SPIKE_DIR), **kw)

    def end_headers(self):
        # Jangan sampai HP menyajikan versi lama dari cache setelah diperbaiki.
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def log_message(self, format, *args):
        # Ringkas: cukup terlihat kalau HP benar-benar mengambil berkasnya.
        sys.stderr.write("  %s\n" % (format % args))


def main():
    bundel = SPIKE_DIR / "latihan.html"
    if not bundel.is_file():
        print("latihan.html belum ada — membuatnya dulu...")
        import bundel as modul_bundel

        teks = modul_bundel.bundel()
        masalah = modul_bundel.periksa_mandiri(teks)
        if masalah:
            raise SystemExit("Bundel tidak mandiri: " + "; ".join(masalah))
        bundel.write_text(teks)
        print("latihan.html dibuat.\n")

    ip = alamat_lokal()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print("=" * 58)
        if ip:
            print("  Buka alamat ini di Safari HP:\n")
            print(f"      http://{ip}:{PORT}/latihan.html\n")
        else:
            print("  Tidak menemukan alamat WiFi. Pastikan Mac terhubung WiFi.\n")
        print("  Syarat: HP dan Mac di jaringan WiFi yang SAMA.")
        print("  Hentikan dengan Ctrl-C kalau sudah selesai.")
        print("=" * 58)
        print("\nPermintaan yang masuk:")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer dihentikan.")


if __name__ == "__main__":
    main()
