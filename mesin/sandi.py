"""Autentikasi halaman guru.

Wajib aktif begitu aplikasi ini bisa dijangkau dari luar mesin sendiri:
halamannya memuat jawaban dan diagnosis anak, dan tanpa palang ini siapa
pun yang tahu alamatnya bisa membacanya.

Bentuknya HTTP Basic. Cukup untuk satu pengguna di balik HTTPS, tidak
menambah dependensi, dan tidak perlu tabel sesi. Yang TIDAK boleh:
menjalankannya tanpa HTTPS, karena Basic mengirim sandi sebagai teks
ter-base64 yang bisa dibaca siapa saja di jaringan.

Sandi disimpan sebagai hash PBKDF2 di berkas, bukan di kode dan bukan
sebagai teks biasa. Dibandingkan dengan compare_digest supaya lama
pembandingan tidak membocorkan berapa karakter yang sudah cocok.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path

BERKAS_SANDI = Path(
    os.environ.get("OSN_BERKAS_SANDI", Path(__file__).resolve().parent / "sandi.json")
)

# PBKDF2-HMAC-SHA256, bukan scrypt.
#
# scrypt lebih tahan serangan perangkat keras, TAPI hashlib.scrypt hanya ada
# kalau Python dibangun dengan OpenSSL yang mendukungnya — ada di VPS
# (Python 3.12) dan TIDAK ADA di Mac ini (Python 3.9.6 bawaan sistem).
# Memakainya berarti sandi yang disetel di satu mesin tidak bisa diverifikasi
# di mesin lain, dan kegagalannya baru muncul saat login, bukan saat menyetel.
#
# pbkdf2_hmac tersedia di keduanya. 600.000 iterasi mengikuti anjuran OWASP
# 2023 untuk SHA-256, dan diukur ~0,2 detik di mesin ini — tidak terasa saat
# login, tapi mahal bila dicoba jutaan kali.
_ITERASI = 600_000


def buat_hash(sandi: str) -> dict:
    garam = secrets.token_bytes(16)
    kunci = hashlib.pbkdf2_hmac("sha256", sandi.encode(), garam, _ITERASI, dklen=32)
    return {
        "garam": binascii.hexlify(garam).decode(),
        "kunci": binascii.hexlify(kunci).decode(),
        "iterasi": _ITERASI,
    }


def simpan_sandi(sandi: str, pengguna: str = "guru", path: Path | None = None) -> Path:
    p = path or BERKAS_SANDI
    p.write_text(
        json.dumps({"pengguna": pengguna, **buat_hash(sandi)}, indent=2),
        encoding="utf-8",
    )
    p.chmod(0o600)  # hanya pemilik yang boleh membaca
    return p


def muat_sandi(path: Path | None = None) -> dict | None:
    p = path or BERKAS_SANDI
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def periksa(pengguna: str, sandi: str, data: dict | None = None) -> bool:
    """Bandingkan dengan waktu tetap.

    Nama pengguna ikut dibandingkan dengan compare_digest, bukan '==', supaya
    tidak ada jalur yang lebih cepat gagal untuk nama yang salah.
    """
    d = data if data is not None else muat_sandi()
    if not d:
        return False

    nama_cocok = hmac.compare_digest(pengguna.encode(), d["pengguna"].encode())

    try:
        garam = binascii.unhexlify(d["garam"])
        harap = binascii.unhexlify(d["kunci"])
        coba = hashlib.pbkdf2_hmac(
            "sha256",
            sandi.encode(),
            garam,
            int(d.get("iterasi", _ITERASI)),
            dklen=len(harap),
        )
    except (binascii.Error, ValueError):
        return False

    sandi_cocok = hmac.compare_digest(coba, harap)
    return nama_cocok and sandi_cocok


def dari_header(header: str | None) -> tuple[str, str] | None:
    """Uraikan header Authorization: Basic <base64>."""
    if not header or not header.startswith("Basic "):
        return None
    try:
        mentah = base64.b64decode(header[6:]).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return None
    if ":" not in mentah:
        return None
    pengguna, _, sandi = mentah.partition(":")
    return pengguna, sandi


def wajib_sandi() -> bool:
    """Apakah palang ini aktif.

    Aktif kalau berkas sandi ada. Dengan begitu pemakaian di localhost tetap
    tanpa hambatan, sementara deploy WAJIB membuat berkas sandinya — dan
    kalau lupa, ada palang kedua di sajikan.py yang menolak berjalan terbuka
    ke jaringan tanpa sandi.
    """
    return BERKAS_SANDI.exists()
