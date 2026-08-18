#!/usr/bin/env python3
"""Jalankan Tahap A (+ Tahap B heuristik) atas seluruh soal dalam satu turunan.yaml.

Jalankan:
    python3 diagnosa_sesi.py                       # sesi terbaru di spike/turunan/
    python3 diagnosa_sesi.py <path/turunan.yaml>   # sesi tertentu

Kenapa ada: sampai 18 Agustus `tahap_a.py` hanya pernah dijalankan atas daftar
kasus hardcoded di dalam dirinya sendiri, dan `render.py` hanya menghasilkan
turunan.yaml. Keduanya tidak pernah bersambung — padahal "Selesai kalau" Hari 3
menuntut Tahap A menghasilkan kode atas jawaban sesi yang sesungguhnya.

Sejak Hari 4: Tahap B heuristik ikut dijalankan untuk soal yang tidak
terjawab Tahap A. Tetap nol panggilan API — `tinta_llm` terpisah, dijalankan
sendiri supaya biayanya selalu disengaja.
"""
import sys
from pathlib import Path

import yaml

import tahap_a
import tinta_heuristik

SPIKE_DIR = Path(__file__).resolve().parent
TURUNAN_ROOT = SPIKE_DIR / "turunan"


def cari_turunan_terbaru():
    kandidat = sorted(
        TURUNAN_ROOT.glob("*/turunan.yaml"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not kandidat:
        raise SystemExit(
            f"Tidak ada turunan.yaml di {TURUNAN_ROOT}. Jalankan render.py dulu."
        )
    return kandidat[0]


def diagnosa_sesi(turunan_path):
    turunan = yaml.safe_load(Path(turunan_path).read_text())
    template_list = tahap_a.muat_template()

    baris = []
    for soal in turunan["soal"]:
        hasil = tahap_a.diagnosis(soal["soal_id"], soal["jawaban_diketik"], template_list)
        kode_a = hasil["kode"]

        # Tahap B heuristik hanya untuk yang Tahap A serahkan.
        heur = tinta_heuristik.diagnosa(soal, kode_a)
        diserahkan = kode_a in ("tidak_pasti", "tidak_ada_template")

        baris.append({
            "soal_id": soal["soal_id"],
            "jawaban_diketik": soal["jawaban_diketik"],
            "kode": kode_a,
            "alasan": hasil.get("alasan", ""),
            "malrule_id": hasil.get("malrule_id"),
            "kode_heuristik": heur["kode"] if diserahkan else None,
            "alasan_heuristik": heur["alasan"] if diserahkan else None,
            "kode_gabungan": heur["kode"],
        })
    return turunan.get("sesi_id", "?"), baris


def ringkas(baris, kunci="kode"):
    hitung = {}
    for b in baris:
        hitung[b[kunci]] = hitung.get(b[kunci], 0) + 1
    return hitung


def cetak(sesi_id, baris):
    print(f"Sesi: {sesi_id}")
    print(f"{len(baris)} soal — Tahap A (malrule) + Tahap B heuristik, nol panggilan API\n")
    print(f"{'soal':>5}  {'jawaban':<18} {'Tahap A':<16} {'heuristik':<12} alasan")
    print("-" * 100)
    for b in baris:
        jawaban = (b["jawaban_diketik"] or "(kosong)")[:18]
        heur = b["kode_heuristik"] or "—"
        alasan = (b["alasan_heuristik"] or b["alasan"])[:38]
        print(f"{b['soal_id']:>5}  {jawaban:<18} {b['kode']:<16} {heur:<12} {alasan}")

    hitung_a = ringkas(baris, "kode")
    hitung_gab = ringkas(baris, "kode_gabungan")
    print("\nTahap A saja :", ", ".join(f"{k}={v}" for k, v in sorted(hitung_a.items())))
    print("A + heuristik:", ", ".join(f"{k}={v}" for k, v in sorted(hitung_gab.items())))

    def terjawab(h):
        return sum(v for k, v in h.items() if k not in ("tidak_pasti", "tidak_ada_template"))

    n = len(baris)
    print(f"\nTerjawab Tahap A       : {terjawab(hitung_a)}/{n}")
    print(f"Terjawab A + heuristik : {terjawab(hitung_gab)}/{n}  (lantai tanpa AI sama sekali)")


def main():
    sumber = Path(sys.argv[1]) if len(sys.argv) > 1 else cari_turunan_terbaru()
    sesi_id, baris = diagnosa_sesi(sumber)
    cetak(sesi_id, baris)


if __name__ == "__main__":
    main()
