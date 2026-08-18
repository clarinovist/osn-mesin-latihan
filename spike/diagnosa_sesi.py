#!/usr/bin/env python3
"""Jalankan Tahap A atas seluruh soal dalam satu turunan.yaml.

Jalankan:
    python3 diagnosa_sesi.py                       # sesi terbaru di spike/turunan/
    python3 diagnosa_sesi.py <path/turunan.yaml>   # sesi tertentu

Kenapa ada: sampai 18 Agustus `tahap_a.py` hanya pernah dijalankan atas daftar
kasus hardcoded di dalam dirinya sendiri, dan `render.py` hanya menghasilkan
turunan.yaml. Keduanya tidak pernah bersambung — padahal "Selesai kalau" Hari 3
menuntut Tahap A menghasilkan kode atas jawaban sesi yang sesungguhnya.

Tidak ada panggilan API di sini. Soal yang tidak terjawab Tahap A sengaja
dibiarkan sebagai `tidak_pasti` — itu jatah Tahap B di Hari 4.
"""
import sys
from pathlib import Path

import yaml

import tahap_a

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
        baris.append({
            "soal_id": soal["soal_id"],
            "jawaban_diketik": soal["jawaban_diketik"],
            "kode": hasil["kode"],
            "alasan": hasil.get("alasan", ""),
            "malrule_id": hasil.get("malrule_id"),
        })
    return turunan.get("sesi_id", "?"), baris


def ringkas(baris):
    hitung = {}
    for b in baris:
        hitung[b["kode"]] = hitung.get(b["kode"], 0) + 1
    return hitung


def cetak(sesi_id, baris):
    print(f"Sesi: {sesi_id}")
    print(f"{len(baris)} soal, Tahap A deterministik (tanpa panggilan API)\n")
    print(f"{'soal':>5}  {'jawaban':<18} {'kode':<16} alasan")
    print("-" * 92)
    for b in baris:
        jawaban = (b["jawaban_diketik"] or "(kosong)")[:18]
        print(f"{b['soal_id']:>5}  {jawaban:<18} {b['kode']:<16} {b['alasan'][:44]}")

    hitung = ringkas(baris)
    print("\nRingkasan:", ", ".join(f"{k}={v}" for k, v in sorted(hitung.items())))

    terjawab = sum(v for k, v in hitung.items() if k not in ("tidak_pasti", "tidak_ada_template"))
    print(f"Terjawab Tahap A: {terjawab}/{len(baris)} — sisanya jatah Tahap B (Hari 4).")


def main():
    sumber = Path(sys.argv[1]) if len(sys.argv) > 1 else cari_turunan_terbaru()
    sesi_id, baris = diagnosa_sesi(sumber)
    cetak(sesi_id, baris)


if __name__ == "__main__":
    main()
