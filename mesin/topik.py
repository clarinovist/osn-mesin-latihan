"""Kontrak paket topik + registry — dimensi yang hilang dari mesin.

Sebelum Fase A, mesin mengandaikan satu topik: komposisi lembar, profil
angka, judul bagian, dan renderer semuanya mengandaikan pola bilangan.
Fase A memasukkan dimensi itu sebagai PAKET: satu topik membawa seluruh
kontennya sendiri, dan menambah topik baru tidak menyentuh paket lain.

Isi satu paket (dataclass Topik):

  templates       template_id -> fungsi parameter -> Soal
  komposisi       level -> urutan template_id untuk satu lembar
  profil          level -> batas angka per parameter
  judul_bagian    huruf bagian -> judul yang tampil di lembar
  catatan_bagian  huruf bagian -> catatan khusus di bawah judul
  render_badan    soal -> HTML/SVG khusus, atau None untuk renderer teks

Konvensi penting yang diwarisi dari kode lama:

  - Level TAK DIKENAL tidak boleh meledak. `siswa.tingkat` adalah kolom
    teks bebas yang sudah terisi di basis data produksi; satu nilai aneh
    jatuh ke level bawaan (P3), bukan exception. Topik berbeda: salah
    ketik id topik adalah bug pemanggil, jadi dicari dengan jelas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from templates import LEVEL, Soal

TOPIK_BAWAAN = "pola-bilangan"


@dataclass(frozen=True)
class Topik:
    """Seluruh konten satu topik — lihat docstring modul."""

    id: str
    nama: str
    judul_lembar: str
    judul_penilaian: str
    templates: dict[str, Callable[..., Soal]]
    komposisi: dict[str, tuple[str, ...]]
    profil: dict[str, dict[str, Any]] = field(default_factory=dict)
    judul_bagian: dict[str, str] = field(default_factory=dict)
    catatan_bagian: dict[str, str] = field(default_factory=dict)
    render_badan: Callable[[Soal], str | None] | None = None

    def komposisi_untuk(self, level: str) -> tuple[str, ...]:
        """Urutan template untuk satu lembar di level itu.

        Level tak dikenal jatuh ke level bawaan (P3) — kontrak lama
        `susun_lembar`, dipertahankan demi data produksi.
        """
        return self.komposisi.get(level, self.komposisi[LEVEL[0]])

    def profil_untuk(self, level: str) -> dict[str, Any]:
        """Batas angka untuk level itu; tak dikenal jatuh ke P3 —
        kontrak lama `generator.profil`, dengan alasan yang sama."""
        return dict(self.profil.get(level, self.profil[LEVEL[0]]))

    def susun_lembar(self, level: str) -> tuple[str, ...]:
        return self.komposisi_untuk(level)


# ── Registry ────────────────────────────────────────────────────────────
#
# PAKET sengaja TIDAK diisi saat modul ini diimpor. Modul paket mengimpor
# templates.py, dan templates.py mengekspor simbol kompatibilitas yang
# mengimpor topik — daftar isi yang lengkap saat impor akan membentuk
# lingkaran yang hasilnya bergantung urutan impor. Jadi paket dimuat
# MALAS: panggilan fungsi di bawah yang memuatnya, dan setelah itu
# registry terisi penuh apa pun urutan impor pertama.

PAKET: dict[str, Topik] = {}


def daftarkan(topik: Topik) -> None:
    if topik.id in PAKET:
        raise ValueError(f"topik duplikat: {topik.id}")
    PAKET[topik.id] = topik


def _pastikan_dimuat() -> None:
    """Muat modul paket. Paket mendaftarkan dirinya sendiri saat impor
    (satu mekanisme, bukan dua), jadi di sini cukup impor dan pastikan
    registry tidak kosong."""
    if PAKET:
        return
    import topik_pola_bilangan  # noqa: F401  (mendaftarkan diri saat impor)

    if not PAKET:
        raise RuntimeError("paket topik dimuat tapi tidak mendaftarkan diri")


def paket_bawaan() -> Topik:
    _pastikan_dimuat()
    return PAKET[TOPIK_BAWAAN]


def ambil(topik_id: str) -> Topik:
    """Ambil paket berdasar id. Topik tak dikenal = bug pemanggil:
    dilempar, bukan disamarkan (beda dengan level, lihat docstring modul)."""
    _pastikan_dimuat()
    try:
        return PAKET[topik_id]
    except KeyError:
        raise KeyError(
            f"topik tidak dikenal: {topik_id!r}. "
            f"Yang terdaftar: {daftar_topik()}"
        ) from None


def daftar_topik() -> list[str]:
    _pastikan_dimuat()
    return sorted(PAKET)


def registri() -> dict[str, Callable[..., Soal]]:
    """Gabungan template semua paket. Pemanggil lama yang masih mengimpor
    REGISTRI dari templates.py mendapat dict ini lewat jalur kompatibilitas."""
    _pastikan_dimuat()
    gabungan: dict[str, Callable[..., Soal]] = {}
    for t in PAKET.values():
        for tid, fungsi in t.templates.items():
            if tid in gabungan:
                raise ValueError(f"template_id duplikat lintas topik: {tid}")
            gabungan[tid] = fungsi
    return gabungan
