"""Buat lembar latihan siap cetak untuk satu atau semua siswa.

    ./.venv/bin/python buat_lembar.py                  # semua siswa
    ./.venv/bin/python buat_lembar.py --siswa Andi  # satu siswa
    ./.venv/bin/python buat_lembar.py --pdf            # sekalian render PDF

Tiap siswa mendapat seed berbeda supaya lembarnya tidak sama — kalau seed-nya
sama, satu anak bisa menyalin jawaban yang lain.

Sesi tercatat di basis data sebelum lembarnya dicetak, jadi nomor sesi dan
seed-nya bisa ditelusuri kalau kertasnya tertukar.
"""

from __future__ import annotations

import argparse
import datetime as dt
import random
import subprocess
import sys
from pathlib import Path

import basis
import cetak
from generator import buat_lembar

KELUARAN = Path(__file__).resolve().parent / "lembar"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def seed_baru(kon, siswa_id: int) -> int:
    """Seed acak yang belum pernah dipakai siswa ini.

    Mengulang seed berarti mengulang soal yang persis sama — anak bisa
    mengingat jawabannya, dan diagnosisnya jadi menilai hafalan, bukan
    pemahaman.
    """
    dipakai = {
        r["seed"]
        for r in kon.execute(
            "SELECT seed FROM sesi WHERE siswa_id = ?", (siswa_id,)
        ).fetchall()
    }
    for _ in range(500):
        s = random.randint(1, 9_999_999)
        if s not in dipakai:
            return s
    raise RuntimeError("gagal menemukan seed baru")


def ke_pdf(html_path: Path) -> Path | None:
    """Render lewat headless Chrome. Chrome mencetak peringatan yang tidak
    berbahaya di macOS, jadi keberhasilan diukur dari berkasnya ada."""
    if not Path(CHROME).exists():
        print(f"  (Chrome tidak ditemukan — lewati PDF untuk {html_path.name})")
        return None
    pdf = html_path.with_suffix(".pdf")
    subprocess.run(
        [CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
         f"--print-to-pdf={pdf}", str(html_path)],
        capture_output=True, timeout=120,
    )
    return pdf if pdf.exists() else None


def main() -> int:
    p = argparse.ArgumentParser(description="Buat lembar latihan pola bilangan")
    p.add_argument("--siswa", help="nama siswa; kosong berarti semua")
    p.add_argument("--pdf", action="store_true", help="render PDF juga")
    p.add_argument("--seed", type=int, help="pakai seed tertentu (cetak ulang)")
    arg = p.parse_args()

    basis.siapkan()
    KELUARAN.mkdir(exist_ok=True)
    hari_ini = dt.datetime.now().strftime("%Y-%m-%d")

    with basis.buka() as kon:
        siswa = basis.daftar_siswa(kon)
        if arg.siswa:
            siswa = [s for s in siswa if s["nama"].lower() == arg.siswa.lower()]
            if not siswa:
                print(f"siswa '{arg.siswa}' tidak ada di basis data", file=sys.stderr)
                return 1

        for s in siswa:
            seed = arg.seed if arg.seed else seed_baru(kon, s["id"])
            sesi_id = basis.buat_sesi(kon, s["id"], seed)
            lembar = buat_lembar(seed)

            dasar = f"{hari_ini}-{s['nama'].lower()}-sesi{sesi_id}"
            f_soal = cetak.tulis(
                KELUARAN / f"{dasar}-SOAL.html",
                cetak.lembar_soal(list(lembar.soal), s["nama"], hari_ini),
            )
            f_nilai = cetak.tulis(
                KELUARAN / f"{dasar}-PENILAIAN.html",
                cetak.lembar_penilaian(
                    list(lembar.soal), s["nama"], hari_ini, seed
                ),
            )

            print(f"{s['nama']}  sesi #{sesi_id}  seed {seed}")
            print(f"  {f_soal}")
            print(f"  {f_nilai}")

            if arg.pdf:
                for f in (f_soal, f_nilai):
                    hasil = ke_pdf(f)
                    if hasil:
                        kb = hasil.stat().st_size / 1024
                        print(f"  -> {hasil.name}  ({kb:.0f} KB)")

    print()
    print("Cetak pada skala 100%, JANGAN 'fit to page' — kotak Caraku")
    print("mengecil kalau diskalakan, padahal itu inti lembarnya.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
