"""Siapkan basis data: buat tabel, daftarkan siswa, siapkan sesi pertama.

Jalankan sekali per mesin:
    ./.venv/bin/python siapkan_db.py

Aman dijalankan ulang — siswa tidak terduplikasi, dan bank soal memakai
tanda_tangan sebagai penjaga. Yang TIDAK aman diulang: pembuatan sesi,
karena tiap panggilan membuat sesi baru. Karena itu sesi hanya dibuat
kalau siswa belum punya satu pun.
"""

from __future__ import annotations

import sys

import basis

SISWA = ["Andi", "Bila"]


def main() -> int:
    basis.siapkan()
    print(f"basis data siap: {basis.BAWAAN}")

    with basis.buka() as kon:
        for nama in SISWA:
            sid = basis.tambah_siswa(kon, nama)
            print(f"  siswa: {nama} (id={sid})")

        print()
        for baris in basis.daftar_siswa(kon):
            sudah = kon.execute(
                "SELECT COUNT(*) AS n FROM sesi WHERE siswa_id = ?", (baris["id"],)
            ).fetchone()["n"]
            if sudah:
                print(f"  {baris['nama']}: sudah punya {sudah} sesi — dilewati")
                continue
            # Seed diambil dari id siswa + tanggal supaya dua anak dapat
            # lembar BERBEDA di hari yang sama. Kalau seed-nya sama, satu
            # anak bisa menyalin jawaban yang lain.
            seed = 1000 + baris["id"]
            sesi_id = basis.buat_sesi(kon, baris["id"], seed)
            print(f"  {baris['nama']}: sesi #{sesi_id} dibuat (seed {seed})")

        print()
        print("bank soal terisi:")
        total = 0
        for s in basis.statistik_bank(kon):
            print(f"  {s['template_id']:30s} {s['jumlah']:3d}")
            total += s["jumlah"]
        print(f"  {'TOTAL':30s} {total:3d}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
