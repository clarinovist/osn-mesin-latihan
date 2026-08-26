"""Kontrak image: setiap modul yang diimpor harus masuk Dockerfile.

Riwayat 25 Agustus 2026: render.py, gaya_*.py, murid.py, dan llm.py lahir
tanpa dimasukkan ke COPY Dockerfile. Semua 4282 test lolos di lokal (filenya
ada), build GitHub Actions juga hijau — lalu deploy gagal sehat karena import
error DI DALAM container, dan rollback otomatis menyembunyikan penyebabnya.

Test ini menutup celah itu: modul tingkat aplikasi yang di-COPY wajib mencakup
seluruh modul lokal yang diimpor oleh titik masuk. Kalau suatu hari ada modul
baru yang lupa didaftarkan, test ini merah sebelum push, bukan saat situs
hampir mati.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent

# Titik masuk & modul inti yang pasti dibutuhkan saat container jalan.
TITIK_MASUK = ("sajikan.py", "web.py", "periksa_sehat.py")


def _modul_di_dockerfile() -> set[str]:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    blok = re.search(r"COPY --chown=osn:osn(.*?)\n\n", dockerfile, flags=re.S)
    assert blok, "blok COPY tidak ditemukan di Dockerfile"
    nama = re.findall(r"([a-z_]+\.py)", blok.group(1))
    return set(nama)


def _impor_lokal(blok: str) -> set[str]:
    """Nama modul .py lokal yang diimpor dari sebuah berkas.

    Hanya impor level-atas bentuk `import x` / `from x import ...` yang
    cocok dengan berkas di root — impor stdlib/pytest otomatis tereliming
    karena tidak punya berkasnya.
    """
    hasil: set[str] = set()
    for m in re.finditer(
        r"^\s*(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_]*)", blok, flags=re.M
    ):
        nama = m.group(1)
        if (ROOT / f"{nama}.py").exists():
            hasil.add(f"{nama}.py")
    return hasil


def test_semua_modul_yang_diimpor_masuk_dockerfile():
    """Transitif dari titik masuk: satu modul lokal yang hilang dari COPY =
        container yang crash saat import = deploy gagal sehat."""
    daftar = _modul_di_dockerfile()

    # transisi tertutup: telusuri impor sampai habis
    diperiksa: set[str] = set()
    antre = list(TITIK_MASUK)
    while antre:
        berkas = antre.pop()
        if berkas in diperiksa:
            continue
        diperiksa.add(berkas)
        for modul in _impor_lokal((ROOT / berkas).read_text(encoding="utf-8")):
            if modul not in daftar:
                raise AssertionError(
                    f"{modul} diimpor {berkas} tapi TIDAK ada di COPY "
                    "Dockerfile — image akan gagal import saat jalan"
                )
            antre.append(modul)


def test_titik_masuk_memang_ada_di_daftar():
    """Titik masuk sendiri juga harus di-COPY — bukan cuma modulnya."""
    daftar = _modul_di_dockerfile()
    kurang = [t for t in TITIK_MASUK if t not in daftar]
    assert not kurang, f"titik masuk tidak di-COPY: {kurang}"
