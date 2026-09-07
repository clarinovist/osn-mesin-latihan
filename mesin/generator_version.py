"""Versi writer soal dipisahkan dari kemampuan reader saat rilis bertahap."""
import os

# Naikkan hanya setelah image reader jembatan terverifikasi di produksi.
VERSI_GENERATOR_BAWAAN = 2


def versi_generator_baru() -> int:
    """Pilih versi untuk soal baru; jangan dipanggil dari reader histori."""
    mentah = os.environ.get("OSN_MATEMATIKA_VERSI")
    if mentah is None:
        return VERSI_GENERATOR_BAWAAN
    nilai = mentah.strip()
    if nilai not in {"1", "2"}:
        raise ValueError("OSN_MATEMATIKA_VERSI hanya menerima 1 atau 2")
    return int(nilai)
