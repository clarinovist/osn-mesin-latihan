"""Setelan pytest bersama untuk seluruh __tests__/.

Dimuat pytest sebelum modul test apa pun (termasuk http_test_kit) diimpor,
jadi env var yang disetel di sini pasti terbaca auth.py dan sessions.py saat
impor.

PBKDF2 600.000 iterasi (~0,2 detik per hash) adalah pilihan keamanan yang
tepat untuk produksi, tetapi mubazir bila diulang pada tiap setup test —
yang diverifikasi di sini adalah logika palang, bukan kecepatan hash.
Iterasinya diturunkan lewat OSN_PBKDF2_ITERASI; angkanya ikut tersimpan di
berkas sandi uji dan diverifikasi dengan nilai yang sama, sehingga jalur
kodenya identik dengan produksi.
"""

import os

os.environ.setdefault("OSN_PBKDF2_ITERASI", "1000")
