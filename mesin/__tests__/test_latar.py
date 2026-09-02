"""Kontrak `templates.putar` — latar cerita turunan parameter.

Fungsi ini dulu privat di topic_combinatorics (`_putar`, 2 Sep 2026).
Diangkat ke templates.py karena dipakai banyak modul topik: gelombang 2
mengukur 43 dari 85 template hanya punya <= 2 bentuk kalimat, dan obatnya
memberi latar berputar pada template yang sudah ada.

Kontraknya tiga, dan ketiganya ada karena kerusakan nyata:

  1. deterministik atas PARAMETER, bukan rng — mencetak ulang lembar lama
     dari bank soal harus menghasilkan kalimat yang sama persis;
  2. bukan `hash()` bawaan — hash() diacak per proses lewat PYTHONHASHSEED;
  3. tidak menambah parameter — parameter ikut Soal.tanda_tangan.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import templates  # noqa: E402
from templates import putar  # noqa: E402


def test_putar_memilih_menurut_jumlah_angka():
    """Indeks = jumlah angka mod panjang pilihan. Ditulis eksplisit supaya
    perubahan rumus pemilihan tidak lolos diam-diam: mengubahnya mengubah
    kalimat SELURUH soal yang sudah tersimpan di bank."""
    pilihan = ("a", "b", "c")
    assert putar(pilihan, 0) == "a"
    assert putar(pilihan, 1) == "b"
    assert putar(pilihan, 4, 1) == "c"
    assert putar(pilihan, 3) == "a"


def test_putar_menerima_tuple_bersarang():
    """Pemakaian terbanyak: satu latar membawa beberapa kata sekaligus
    (tempat, benda, tokoh) yang dibongkar di sisi pemanggil."""
    tempat, tokoh = putar((("kantin", "Sinta"), ("toko", "Budi")), 1)
    assert (tempat, tokoh) == ("toko", "Budi")


def test_putar_deterministik_antar_proses():
    """Bukan hash() bawaan: hash() diacak per proses lewat PYTHONHASHSEED,
    jadi lembar yang sama akan berganti kalimat tiap server restart —
    guru menilai soal yang tidak dikerjakan anak."""
    kode = (
        "import sys; sys.path.insert(0, %r);"
        "from templates import putar;"
        "print(putar(('satu','dua','tiga','empat','lima'), 7, 13))"
    ) % str(Path(__file__).resolve().parent.parent)
    hasil = set()
    for benih in ("0", "1", "12345"):
        keluar = subprocess.run(
            [sys.executable, "-c", kode],
            capture_output=True,
            text=True,
            env={"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": benih},
        )
        hasil.add(keluar.stdout.strip())
    assert len(hasil) == 1, f"latar berubah antar PYTHONHASHSEED: {hasil}"
    assert hasil == {putar(("satu", "dua", "tiga", "empat", "lima"), 7, 13)}


def test_putar_tanpa_angka_tetap_sah():
    """Template berparameter tunggal-nol (kalau kelak ada) tidak boleh
    meledak — sum(()) = 0, jadi latar pertama."""
    assert putar(("x", "y"), ) == "x"


def test_topic_combinatorics_memakai_helper_bersama():
    """Pengunci Langkah 1: salinan lokal `_putar` tidak boleh hidup lagi.

    Dua salinan berarti dua definisi 'latar', dan perbaikan di satu
    tempat diam-diam tidak berlaku di tempat lain.
    """
    import topic_combinatorics

    assert not hasattr(topic_combinatorics, "_putar"), (
        "salinan lokal _putar masih ada — pakai templates.putar"
    )
    assert topic_combinatorics.putar is templates.putar
