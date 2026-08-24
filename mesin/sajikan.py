"""Jalankan halaman guru.

    ./.venv/bin/python sajikan.py            # hanya dari Mac ini
    ./.venv/bin/python sajikan.py --jaringan # bisa diakses dari HP di WiFi

Bawaannya localhost saja. Halaman ini memuat jawaban dan diagnosis anak,
jadi membukanya ke jaringan adalah keputusan sadar, bukan bawaan — dan
alamat WiFi berubah tiap ganti jaringan, sehingga dicetak saat dijalankan.
"""

from __future__ import annotations

import argparse
import socket
import sys
from http.server import ThreadingHTTPServer

import basis
from web import Penangan

PORT = 8724


def alamat_wifi() -> str:
    """IP di jaringan lokal, tanpa benar-benar mengirim paket."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def main() -> int:
    p = argparse.ArgumentParser(description="Sajikan halaman guru")
    p.add_argument("--jaringan", action="store_true",
                   help="izinkan akses dari perangkat lain di WiFi")
    p.add_argument("--port", type=int, default=PORT)
    arg = p.parse_args()

    basis.siapkan()
    inang = "0.0.0.0" if arg.jaringan else "127.0.0.1"

    with basis.buka() as kon:
        n_siswa = len(basis.daftar_siswa(kon))
        n_sesi = kon.execute("SELECT COUNT(*) AS n FROM sesi").fetchone()["n"]

    print(f"basis data : {basis.BAWAAN}")
    print(f"isi        : {n_siswa} siswa, {n_sesi} sesi")
    print()
    print(f"  http://127.0.0.1:{arg.port}")
    if arg.jaringan:
        print(f"  http://{alamat_wifi()}:{arg.port}   (dari HP di WiFi yang sama)")
        print()
        print("  Halaman ini memuat jawaban & diagnosis anak. Jangan dibuka")
        print("  di jaringan publik.")
    print()
    print("Ctrl-C untuk berhenti.")

    server = ThreadingHTTPServer((inang, arg.port), Penangan)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nberhenti.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
