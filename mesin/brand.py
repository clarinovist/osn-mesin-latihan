"""Aset brand: berkas statis (/aset/<nama>) + tag kepala HTML.

Aplikasi ini tidak punya penyaji berkas statis umum — satu-satunya yang ada
sebelum ini adalah /lampiran/berkas/<id> (foto lembar anak, ber-palang).
Modul ini menambah permukaan kedua yang sengaja dibuat sesempit mungkin:

  - **Allow-list**, bukan penggabungan path. Nama yang tidak terdaftar =
    404 sebelum menyentuh filesystem, jadi traversal `../` mustahil secara
    konstruksi, bukan karena sanitasi yang harus benar.
  - **Publik**: favicon dibutuhkan browser sebelum login. Rute ini
    didaftarkan sebelum palang guru — karena itu isinya hanya berkas brand
    statis. Tidak menyentuh basis data, tidak menyentuh data anak.
  - Cache satu tahun + immutable: berkasnya tidak pernah berubah tanpa
    ganti nama.

`manifest.json` sengaja TIDAK berupa berkas: ia di-generate dari
design_tokens supaya nama produk & warna tema tetap bersumber dari satu
tempat. Menyalin nama ke berkas JSON statis berarti brand punya dua sumber
kebenaran yang bisa berbeda diam-diam.
"""
from __future__ import annotations

import functools
import json
from pathlib import Path

import design_tokens as T

# Domain produksi saat ini. og:image dan og:url butuh URL ABSOLUT — crawler
# WhatsApp/Facebook menolak path relatif. Saat domain jagomat.id dibeli,
# ubah satu baris ini saja.
URL_SITUS = "https://osn.lesprivate.id"

FOLDER_ASET = Path(__file__).resolve().parent / "aset"

# Allow-list = kontrak rute. Menambah berkas ke mesin/aset/ tanpa
# mendaftarkannya di sini berarti berkas itu tidak terlayani (dan guard
# test_brand.py akan merah).
ASET: dict[str, str] = {
    "mark-sederhana.svg": "image/svg+xml",
    "mark-penuh.svg": "image/svg+xml",
    "mark-tinta.svg": "image/svg+xml",
    "lockup-horizontal.svg": "image/svg+xml",
    "lockup-cetak.svg": "image/svg+xml",
    "lockup-hero.svg": "image/svg+xml",
    "favicon.svg": "image/svg+xml",
    "favicon.ico": "image/x-icon",
    "apple-touch-180.png": "image/png",
    "pwa-192.png": "image/png",
    "pwa-512.png": "image/png",
    "og-image.png": "image/png",
}

NAMA_MANIFEST = "manifest.json"


@functools.lru_cache(maxsize=None)
def _isi(nama: str) -> bytes:
    """Isi berkas aset, di-cache di memori.

    Aset totalnya ~53 KB dan tidak pernah berubah selama proses hidup, jadi
    membacanya sekali lebih murah daripada I/O per permintaan favicon.
    """
    return (FOLDER_ASET / nama).read_bytes()


def manifest() -> bytes:
    """manifest.json PWA — di-generate, bukan berkas statis.

    Nama produk dan warna tema berasal dari design_tokens supaya tidak ada
    nilai brand yang terduplikasi di berkas JSON terpisah.
    """
    isi = {
        "name": T.NAMA_PRODUK,
        "short_name": T.NAMA_PRODUK,
        "description": T.TAGLINE,
        "start_url": "/",
        "display": "standalone",
        "background_color": T.LATAR_MURID,
        "theme_color": T.AKSEN_MURID_UTAMA,
        "icons": [
            {"src": "/aset/pwa-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/aset/pwa-512.png", "sizes": "512x512", "type": "image/png"},
            {
                "src": "/aset/pwa-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable",
            },
        ],
    }
    return json.dumps(isi, ensure_ascii=False, indent=2).encode("utf-8")


def berkas(nama: str) -> tuple[bytes, str] | None:
    """(isi, mime) untuk nama aset, atau None kalau tidak diizinkan.

    Nama diperiksa lewat allow-list SEBELUM menyentuh filesystem — jadi
    `../`, path absolut, dan nama berkas aplikasi tidak pernah sampai ke
    lapisan I/O sama sekali.
    """
    if nama == NAMA_MANIFEST:
        return manifest(), "application/json; charset=utf-8"
    mime = ASET.get(nama)
    if mime is None:
        return None
    try:
        return _isi(nama), mime
    except OSError:
        return None
