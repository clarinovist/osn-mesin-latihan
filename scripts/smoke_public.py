#!/usr/bin/env python3
"""Smoke anonim situs kanonis; tanpa body, cookie, credential atau redirect."""

import time
import urllib.error
import urllib.parse
import urllib.request

URL_SITUS = "https://jagomat.id"
# User-Agent Python bawaan mendapat403 di edge saat inspeksi12 September2026.
# Identitas transport eksplisit, bukan melewati autentikasi aplikasi.
USER_AGENT = "curl/8.7.1"
PERMUKAAN = (("/", 200), ("/akun", 401), ("/murid/", 303))


class TanpaRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def lokasi_masuk_sah(lokasi):
    """Hanya lokasi relatif kanonis; query pesan boleh, host/fragment tidak."""
    if not isinstance(lokasi, str) or any(ord(c) <= 32 or ord(c) == 127 for c in lokasi):
        return False
    if "\\" in lokasi or "#" in lokasi:
        return False
    bagian = urllib.parse.urlsplit(lokasi)
    return (not bagian.scheme and not bagian.netloc and bagian.path == "/masuk"
            and (lokasi == "/masuk" or lokasi.startswith("/masuk?")))


def periksa(pembuka=None):
    """Periksa tiga permukaan tanpa mengikuti Location atau membaca isi akun."""
    if pembuka is None:
        pembuka = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), TanpaRedirect())
    for jalur, status in PERMUKAAN:
        permintaan = urllib.request.Request(
            URL_SITUS + jalur, headers={"User-Agent": USER_AGENT})
        try:
            try:
                hasil = pembuka.open(permintaan, timeout=10)
            except urllib.error.HTTPError as galat:
                hasil = galat
            with hasil:
                if hasil.code != status:
                    return False
                if jalur == "/murid/":
                    lokasi = hasil.headers.get_all("Location", [])
                    if len(lokasi) != 1 or not lokasi_masuk_sah(lokasi[0]):
                        return False
        except (OSError, ValueError, urllib.error.URLError):
            return False
    return True


def main(*, uji=periksa, tidur=time.sleep):
    for nomor in range(10):
        if uji():
            print("Smoke publik lulus: /200 /akun401 /murid/303 menuju /masuk.")
            return 0
        if nomor < 9:
            tidur(6)
    print("Smoke publik gagal; periksa origin/edge dan recovery, jangan restore DB otomatis.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
