#!/usr/bin/env python3
"""Periksa kesehatan perekam dari satu berkas sesi — SEBELUM membaca hasil apa pun.

Jalankan:
    ./.venv/bin/python periksa_sesi.py                 # berkas terbaru di ~/Downloads
    ./.venv/bin/python periksa_sesi.py <sesi.json>

Kenapa ini didahulukan: gerbang di Rencana Spike menetapkan prasyarat yang
tidak bisa dilewati — "periksa titik_per_event_rata2 di JSON. Kalau angkanya
≈1,0, tabel di atas tidak berlaku". Alasannya, kalau perekamnya kehilangan
resolusi antar-frame, baik hasil "lulus" maupun "gagal" sama-sama tidak bisa
dipercaya: yang diuji bukan tesisnya, melainkan alat yang cacat.

Skrip ini hanya membaca dan melaporkan. Tidak mengubah apa pun, tidak
memanggil API apa pun.
"""
import json
import sys
from pathlib import Path

DOWNLOADS = Path.home() / "Downloads"

AMBANG_SEHAT = 1.5  # sama dengan verdictKoalisi() di toSamples.js


def cari_terbaru():
    kandidat = sorted(DOWNLOADS.glob("sesi-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not kandidat:
        raise SystemExit(
            f"Tidak ada berkas sesi-*.json di {DOWNLOADS}.\n"
            "Pindahkan dulu berkas sesi dari HP ke Mac (AirDrop paling mudah)."
        )
    return kandidat[0]


def periksa(path):
    data = json.loads(Path(path).read_text())
    cap = data.get("capture") or {}
    soal = data.get("soal") or []

    print(f"Berkas : {path}")
    print(f"Sesi   : {data.get('sesi_id', '?')}")
    print()

    # --- 1. Kesehatan alat (prasyarat gerbang) ---
    print("1. KESEHATAN PEREKAM")
    if not cap:
        print("   ⚠  Tidak ada blok `capture`. Berkas ini direkam oleh versi lama")
        print("      perekam, sebelum instrumentasi koalisi ada. Angka kesehatan")
        print("      alat tidak bisa dinilai — rekam ulang dengan versi sekarang.")
    else:
        rata = cap.get("titik_per_event_rata2")
        verdict = cap.get("verdict", "?")
        print(f"   titik per event : {rata}   (sehat kalau >= {AMBANG_SEHAT})")
        print(f"   titik terekam   : {cap.get('total_titik')}")
        print(f"   event pointermove: {cap.get('jumlah_event_pointermove')}")
        print(f"   getCoalescedEvents didukung: {cap.get('coalesced_didukung')}")
        if cap.get("layar"):
            print(f"   layar           : {cap['layar']} (dpr {cap.get('dpr')})")
        print(f"   VERDICT         : {verdict}")
        print()
        if verdict == "sehat":
            print("   ✅ Alatnya bekerja. Resolusi antar-frame tertangkap.")
            print("      Prasyarat gerbang terpenuhi — hasil sesi boleh dibaca.")
        elif verdict == "degradasi":
            print("   ⚠  Resolusi antar-frame nyaris hilang (≈1 titik per event).")
            print("      Tabel gerbang TIDAK berlaku atas data ini. Coba browser")
            print("      lain di device yang sama, lalu device lain, sebelum")
            print("      menyimpulkan apa pun tentang web sebagai platform.")
        elif verdict == "rusak":
            print("   ⛔ Event mengalir tapi NOL titik terekam. Data tidak terpakai.")
        elif verdict == "kosong":
            print("   ⚠  Belum ada goresan sama sekali di sesi ini.")

    # --- 2. Isi sesi ---
    print()
    print("2. ISI SESI")
    print(f"   soal terisi : {len(soal)} dari 10")
    total_goresan = 0
    total_dicoret = 0
    for s in soal:
        for lang in s.get("langkah", []):
            for g in lang.get("goresan", []):
                total_goresan += 1
                if g.get("dicoret"):
                    total_dicoret += 1
    print(f"   goresan     : {total_goresan} ({total_dicoret} dicoret, tetap tersimpan)")

    if soal:
        print()
        print(f"   {'soal':>5}  {'jawaban':<16} {'langkah':>7}  {'goresan':>7}")
        for s in soal:
            ng = sum(len(l.get("goresan", [])) for l in s.get("langkah", []))
            print(f"   {s['soal_id']:>5}  {(s.get('jawaban_diketik') or '(kosong)'):<16} "
                  f"{len(s.get('langkah', [])):>7}  {ng:>7}")

    # --- 3. Langkah berikutnya ---
    print()
    print("3. BERIKUTNYA")
    if not soal:
        print("   Sesi kosong — belum ada soal yang diselesaikan.")
    elif cap.get("verdict") == "sehat":
        print("   Jalankan render + diagnosis:")
        print(f"       ./.venv/bin/python render.py '{path}'")
        print("       ./.venv/bin/python diagnosa_sesi.py")
    else:
        print("   Perbaiki alatnya dulu sebelum membaca hasil (lihat butir 1).")


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else cari_terbaru()
    periksa(path)


if __name__ == "__main__":
    main()
