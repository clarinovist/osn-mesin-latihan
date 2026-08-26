"""Render lembar soal jadi HTML siap cetak.

Sejak Fase 3 berkas ini hanya fasade: struktur DOM pindah ke render.py,
CSS-nya pecah menjadi gaya_layar.py (browser/HP) dan gaya_cetak.py
(kertas A4). Pecahan ini yang membuat lembar yang sama punya dua tampilan
dari satu sumber — dan web.py bisa menyajikan versi layar tanpa menyalin
struktur apa pun.

Kontrak lama tetap dijaga lewat re-export:

  from cetak import lembar_soal, lembar_penilaian, tulis, CSS

Dua berkas per sesi, dan pemisahan ini tidak boleh dilanggar:

  <sesi>-SOAL.html      dipegang anak — TIDAK boleh memuat kunci
  <sesi>-PENILAIAN.html dipegang guru — kunci + tabel malrule

Alasan pemisahan: begitu kunci terlihat anak, dua kode yang paling berharga
(N menebak, K salah konsep) hilang selamanya dari data. Ada test yang
memastikan berkas anak tidak mengandung kunci.
"""

from render import (  # noqa: F401
    JUDUL_BAGIAN,
    CATATAN_BAGIAN,
    _badan_soal,
    _kartu_soal,
    _svg_korek,
    _svg_titik,
    lembar_penilaian,
    lembar_soal,
    tulis,
)

# Nama lama CSS dipertahankan untuk pemanggil yang sudah ada; isinya kini
# gaya cetak. Tampilan layar ada di gaya_layar.GAYA_LAYAR.
from gaya_cetak import GAYA_CETAK as CSS  # noqa: F401
