#!/usr/bin/env python3
"""Render sesi-<id>.json -> PNG per langkah + turunan.yaml (Rencana Spike Hari 3)."""
import json
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

SPIKE_DIR = Path(__file__).resolve().parent
DOWNLOADS = Path.home() / "Downloads"
OUTPUT_ROOT = SPIKE_DIR / "turunan"


def cari_sesi_terbaru():
    kandidat = sorted(DOWNLOADS.glob("sesi-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not kandidat:
        raise SystemExit("Tidak ada file sesi-*.json di ~/Downloads. Unduh dulu dari spike/index.html.")
    return kandidat[0]


def render_langkah(langkah, out_path):
    semua_titik = [t for goresan in langkah["goresan"] for t in goresan["titik"]]
    if not semua_titik:
        img = Image.new("RGB", (300, 140), "white")
        ImageDraw.Draw(img).text((10, 60), "(kosong — tidak ada goresan)", fill="gray")
        img.save(out_path)
        return

    xs = [t[0] for t in semua_titik]
    ys = [t[1] for t in semua_titik]
    margin = 15
    lebar = max(int(max(xs) + margin), 300)
    tinggi = max(int(max(ys) + margin), 140)

    img = Image.new("RGB", (lebar, tinggi), "white")
    draw = ImageDraw.Draw(img)
    for goresan in langkah["goresan"]:
        titik = [(p[0], p[1]) for p in goresan["titik"]]
        if len(titik) >= 2:
            draw.line(titik, fill="black", width=3, joint="curve")
        elif titik:
            x, y = titik[0]
            draw.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill="black")
    img.save(out_path)


def hitung_turunan(soal):
    langkah_list = soal["langkah"]

    goresan_pertama = next((l["goresan"][0] for l in langkah_list if l["goresan"]), None)
    jeda_awal_ms = goresan_pertama["mulai_ms"] if goresan_pertama else None

    durasi_per_langkah = []
    for l in langkah_list:
        akhir = l["segel_ms"] if l["segel_ms"] is not None else soal["selesai_ms"]
        durasi_per_langkah.append({"indeks": l["indeks"], "durasi_ms": round(akhir - l["buka_ms"], 1)})

    jumlah_hapus_per_langkah = [
        {"indeks": l["indeks"], "jumlah": l["jumlah_hapus"]} for l in langkah_list
    ]

    langkah_terakhir_selesai_ms = None
    if langkah_list:
        terakhir = langkah_list[-1]
        langkah_terakhir_selesai_ms = (
            terakhir["segel_ms"] if terakhir["segel_ms"] is not None else soal["selesai_ms"]
        )

    jawaban_duluan = None
    if soal["jawaban_ditulis_pada_ms"] is not None and langkah_terakhir_selesai_ms is not None:
        jawaban_duluan = soal["jawaban_ditulis_pada_ms"] < langkah_terakhir_selesai_ms

    return {
        "soal_id": soal["soal_id"],
        "jawaban_diketik": soal["jawaban_diketik"],
        "jeda_sebelum_goresan_pertama_ms": round(jeda_awal_ms, 1) if jeda_awal_ms is not None else None,
        "durasi_per_langkah_ms": durasi_per_langkah,
        "jumlah_hapus_per_langkah": jumlah_hapus_per_langkah,
        "jawaban_ditulis_pada_ms": (
            round(soal["jawaban_ditulis_pada_ms"], 1) if soal["jawaban_ditulis_pada_ms"] is not None else None
        ),
        "jawaban_ditulis_sebelum_langkah_selesai": jawaban_duluan,
        "selesai_ms": round(soal["selesai_ms"], 1),
    }


def main():
    sumber = Path(sys.argv[1]) if len(sys.argv) > 1 else cari_sesi_terbaru()
    data = json.loads(sumber.read_text())

    sesi_id_aman = data["sesi_id"].replace(":", "-").replace(".", "-")
    folder_sesi = OUTPUT_ROOT / sesi_id_aman
    folder_sesi.mkdir(parents=True, exist_ok=True)

    semua_turunan = []
    for soal in data["soal"]:
        folder_soal = folder_sesi / f"soal-{soal['soal_id']}"
        folder_soal.mkdir(parents=True, exist_ok=True)
        for langkah in soal["langkah"]:
            render_langkah(langkah, folder_soal / f"langkah-{langkah['indeks'] + 1}.png")
        semua_turunan.append(hitung_turunan(soal))

    turunan_path = folder_sesi / "turunan.yaml"
    turunan_path.write_text(
        yaml.dump({"sesi_id": data["sesi_id"], "soal": semua_turunan}, allow_unicode=True, sort_keys=False)
    )

    print(f"Selesai. Sumber: {sumber}")
    print(f"Output: {folder_sesi}")
    print(f"- {len(data['soal'])} soal diproses")
    print("- turunan.yaml ditulis")


if __name__ == "__main__":
    main()
