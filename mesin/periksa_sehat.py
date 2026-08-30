"""Pemeriksaan kesehatan container.

Sejak launch publik, / adalah landing publik (200). Rute yang membuktikan
palang sekaligus kehidupan proses kini /akun — rute data guru yang wajib
401 tanpa kredensial.

Yang dianggap SEHAT: server menjawab 401 tanpa kredensial di /akun. Itu
membuktikan dua hal sekaligus — prosesnya hidup, dan palang sandinya aktif.

Yang dianggap SAKIT:
  - tidak menjawab sama sekali (proses mati / menggantung)
  - menjawab 200 tanpa diminta sandi (palang tidak aktif)

Kasus kedua penting: kalau berkas sandi hilang dari volume, aplikasi akan
tetap jalan tapi rute data terbuka tanpa palang. Tanpa pemeriksaan ini,
container terlihat "sehat" sementara data anak bisa dibaca siapa saja.
"""

import sys
import urllib.error
import urllib.request

ALAMAT = "http://127.0.0.1:8724/akun"


def main() -> int:
    try:
        with urllib.request.urlopen(ALAMAT, timeout=6) as jawab:
            kode = jawab.status
    except urllib.error.HTTPError as e:
        kode = e.code
    except Exception as e:  # noqa: BLE001 — apa pun berarti tidak menjawab
        print(f"tidak menjawab: {e}", file=sys.stderr)
        return 1

    if kode == 401:
        return 0

    if kode == 200:
        print(
            "BAHAYA: server menjawab 200 tanpa sandi — palang tidak aktif. "
            "Periksa /data/sandi.json.",
            file=sys.stderr,
        )
        return 1

    print(f"kode tak terduga: {kode}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
