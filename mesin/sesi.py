"""Sesi login: token acak -> (pengguna, peran, kedaluarsa), disimpan JSON.

Kenapa berkas, bukan tabel basis data: sesi adalah state AUTENTIKASI, bukan
data pendidikan — mencampurnya ke latihan.db membuat cadangan data anak ikut
membawa kuki sesi. Polanya mengikuti sandi.json: chmod 600, tulis atomik.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import tempfile
import threading
import time
from pathlib import Path

BERKAS_SESI = Path(
    os.environ.get("OSN_BERKAS_SESI", Path(__file__).resolve().parent / "sesi.json")
)
TTL_DETIK = 14 * 24 * 3600  # dua minggu; iPhone anak dipakai bergantian

_kunci_tulis = threading.Lock()
_jalur_dari_kunci_ip: dict[tuple[str, str], list[float]] = {}

# Umpan waktu-tetap untuk akun tak dikenal (B3): PBKDF2 satu kali ini agar
# jalur nama-salah memakan waktu serupa jalur nama-benar+sandi-salah.
_garam_dummy = hashlib.pbkdf2_hmac(
    "sha256", b"dummy", b"aaaaaaaaaaaaaaaa", 600_000, dklen=32
)  # dihitung saat import — tidak di hot path; nilai tidak dipakai selain untuk waktu

_BATAS_JENDELA = 15 * 60  # hitung gagal dalam 15 menit
_BATAS_GAGAL = 5  # gagal ke-5 menutup keran
_BATAS_TUNGGU = 15 * 60


# ── sesi token ──────────────────────────────────────────────────────────────

def muat(path: Path | None = None) -> dict:
    p = path or BERKAS_SESI
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _tulis(data: dict, path: Path | None = None) -> None:
    p = path or BERKAS_SESI
    with _kunci_tulis:
        # Tulis atomik: file sementara di direktori yang sama dengan tujuan
        # akhir, lalu os.replace. Direktori harus bisa ditulis (rw) — di
        # kontainer, sesi.json tinggal di /data (volume rw), bukan /app
        # (bind-mount read-only). Lihat ENV OSN_BERKAS_SESI di Dockerfile.
        fd, nama_sementara = tempfile.mkstemp(dir=p.parent, prefix=".sesi-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f)
            os.replace(nama_sementara, p)
            p.chmod(0o600)
        except Exception:
            try:
                os.unlink(nama_sementara)
            except FileNotFoundError:
                pass
            raise


def buat(pengguna: str, peran: str, path: Path | None = None,
         sekarang: float | None = None) -> str:
    token = secrets.token_urlsafe(32)
    data = muat(path)
    data[token] = {
        "pengguna": pengguna,
        "peran": peran,
        "kedaluarsa": (sekarang if sekarang is not None else time.time()) + TTL_DETIK,
    }
    _tulis(data, path)
    return token


def ambil(token: str | None, path: Path | None = None,
          sekarang: float | None = None) -> tuple[str, str] | None:
    if not token:
        return None
    kini = sekarang if sekarang is not None else time.time()
    entri = muat(path).get(token)
    if not entri or entri.get("kedaluarsa", 0) <= kini:
        return None
    return entri["pengguna"], entri["peran"]


def hapus(token: str, path: Path | None = None) -> bool:
    data = muat(path)
    if token not in data:
        return False
    del data[token]
    _tulis(data, path)
    return True


def bersihkan(path: Path | None = None) -> int:
    kini = time.time()
    data = muat(path)
    sisa = {t: e for t, e in data.items() if e.get("kedaluarsa", 0) > kini}
    dihapus = len(data) - len(sisa)
    if dihapus:
        _tulis(sisa, path)
    return dihapus


# ── rate limit percobaan masuk ──────────────────────────────────────────────
def _pangkas(kunci: tuple[str, str], kini: float) -> list[float]:
    lst = _jalur_dari_kunci_ip.get(kunci, [])
    lst = [t for t in lst if kini - t < _BATAS_JENDELA]
    _jalur_dari_kunci_ip[kunci] = lst
    return lst


def sedang_diblokir(nama: str, kunci_ip: str, sekarang: float | None = None) -> bool:
    kini = sekarang if sekarang is not None else time.time()
    kunci = (nama.strip().lower(), kunci_ip)
    lst = _pangkas(kunci, kini)
    return len(lst) >= _BATAS_GAGAL


def catat_gagal(nama: str, kunci_ip: str, sekarang: float | None = None) -> None:
    kini = sekarang if sekarang is not None else time.time()
    kunci = (nama.strip().lower(), kunci_ip)
    lst = _pangkas(kunci, kini)
    lst.append(kini)
    _jalur_dari_kunci_ip[kunci] = lst


def catat_berhasil(nama: str, kunci_ip: str) -> None:
    _jalur_dari_kunci_ip.pop((nama.strip().lower(), kunci_ip), None)


def _reset_rate_limit() -> None:  # khusus test
    _jalur_dari_kunci_ip.clear()
