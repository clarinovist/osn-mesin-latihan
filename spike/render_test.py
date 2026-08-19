#!/usr/bin/env python3
"""Test render.py — hitung_turunan() + render 10 soal.

Jalankan: python3 render_test.py   (butuh .venv: pyyaml + pillow)

Kenapa ada: sampai 18 Agustus render.py hanya pernah dijalankan atas satu
sesi berisi SATU soal, jadi tidak ada bukti pipeline-nya benar untuk sesi
10 soal — padahal itu bentuk data Hari 5 yang sesungguhnya. Test ini memakai
fixture sintetis (bukan data anak) supaya bisa dijalankan ulang kapan saja
tanpa sesi manual.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

import render

SOAL_UJI = [1, 2, 3, 4, 5, 6, 8, 10, 13, 15]


def buat_langkah(indeks, buka_ms, segel_ms, n_goresan=2, n_titik=12, jumlah_hapus=0):
    goresan = []
    for g in range(n_goresan):
        mulai = buka_ms + 100 + g * 300
        titik = [
            [20 + g * 40 + i * 3, 30 + (i % 5) * 4, mulai + i * 8]
            for i in range(n_titik)
        ]
        goresan.append({"mulai_ms": mulai, "titik": titik})
    return {
        "indeks": indeks,
        "buka_ms": buka_ms,
        "segel_ms": segel_ms,
        "goresan": goresan,
        "jumlah_hapus": jumlah_hapus,
    }


def buat_sesi_10_soal():
    soal = []
    for n, soal_id in enumerate(SOAL_UJI):
        langkah = [
            buat_langkah(0, 0, 5000, jumlah_hapus=1 if n % 3 == 0 else 0),
            buat_langkah(1, 5000, 11000, jumlah_hapus=2 if n % 4 == 0 else 0),
        ]
        soal.append({
            "soal_id": soal_id,
            "langkah": langkah,
            "jawaban_diketik": "42",
            "jawaban_ditulis_pada_ms": 10500,
            "selesai_ms": 12000,
        })
    return {
        "sesi_id": "2026-08-18T99:99:99.999Z",
        "soal": soal,
        "capture": {
            "coalesced_didukung": True,
            "titik_per_event_rata2": 3.2,
            "titik_per_event_maks": 7,
            "jumlah_event_pointermove": 500,
            "total_titik": 1600,
            "verdict": "sehat",
        },
    }


def tes_hitung_turunan_dasar():
    soal = {
        "soal_id": 2,
        "langkah": [
            buat_langkah(0, 0, 4000, jumlah_hapus=1),
            buat_langkah(1, 4000, 9000, jumlah_hapus=3),
        ],
        "jawaban_diketik": "4/5",
        "jawaban_ditulis_pada_ms": 8000,
        "selesai_ms": 9500,
    }
    t = render.hitung_turunan(soal)

    assert t["soal_id"] == 2, t
    assert t["jawaban_diketik"] == "4/5", t
    # Goresan pertama mulai di buka_ms(0) + 100.
    assert t["jeda_sebelum_goresan_pertama_ms"] == 100, t
    assert [d["durasi_ms"] for d in t["durasi_per_langkah_ms"]] == [4000, 5000], t
    assert [h["jumlah"] for h in t["jumlah_hapus_per_langkah"]] == [1, 3], t
    # Jawaban ditulis 8000 < langkah terakhir tersegel 9000 -> True.
    assert t["jawaban_ditulis_sebelum_langkah_selesai"] is True, t
    print("hitung_turunan dasar: PASS")


def tes_langkah_belum_tersegel():
    """segel_ms None harus jatuh ke selesai_ms, bukan bikin TypeError."""
    soal = {
        "soal_id": 8,
        "langkah": [buat_langkah(0, 0, None)],
        "jawaban_diketik": "126",
        "jawaban_ditulis_pada_ms": None,
        "selesai_ms": 7000,
    }
    t = render.hitung_turunan(soal)
    assert t["durasi_per_langkah_ms"][0]["durasi_ms"] == 7000, t
    # Tanpa timestamp jawaban, pertanyaan "duluan mana" tidak terjawab -> None.
    assert t["jawaban_ditulis_sebelum_langkah_selesai"] is None, t
    assert t["jawaban_ditulis_pada_ms"] is None, t
    print("langkah belum tersegel: PASS")


def tes_langkah_tanpa_goresan():
    """Langkah kosong tidak boleh bikin crash saat cari goresan pertama."""
    soal = {
        "soal_id": 15,
        "langkah": [
            {"indeks": 0, "buka_ms": 0, "segel_ms": 2000, "goresan": [], "jumlah_hapus": 0},
            buat_langkah(1, 2000, 6000),
        ],
        "jawaban_diketik": "10",
        "jawaban_ditulis_pada_ms": 5000,
        "selesai_ms": 6500,
    }
    t = render.hitung_turunan(soal)
    # Goresan pertama ada di langkah kedua: buka 2000 + 100.
    assert t["jeda_sebelum_goresan_pertama_ms"] == 2100, t
    print("langkah tanpa goresan: PASS")


def tes_sesi_tanpa_goresan_sama_sekali():
    soal = {
        "soal_id": 5,
        "langkah": [
            {"indeks": 0, "buka_ms": 0, "segel_ms": 1000, "goresan": [], "jumlah_hapus": 0},
        ],
        "jawaban_diketik": "",
        "jawaban_ditulis_pada_ms": None,
        "selesai_ms": 1000,
    }
    t = render.hitung_turunan(soal)
    assert t["jeda_sebelum_goresan_pertama_ms"] is None, t
    print("sesi tanpa goresan: PASS")


def tes_render_10_soal(tmp):
    """Bukti pipeline jalan untuk 10 soal, bukan cuma 1."""
    data = buat_sesi_10_soal()
    sumber = tmp / "sesi-uji-10-soal.json"
    sumber.write_text(json.dumps(data))

    asli = render.OUTPUT_ROOT
    render.OUTPUT_ROOT = tmp / "turunan"
    try:
        sys.argv = ["render.py", str(sumber)]
        render.main()
    finally:
        render.OUTPUT_ROOT = asli

    folder = tmp / "turunan" / "2026-08-18T99-99-99-999Z"
    assert folder.is_dir(), f"folder sesi tidak dibuat: {folder}"

    for soal_id in SOAL_UJI:
        fsoal = folder / f"soal-{soal_id}"
        assert fsoal.is_dir(), f"folder soal-{soal_id} tidak ada"
        png = sorted(fsoal.glob("langkah-*.png"))
        assert len(png) == 2, f"soal-{soal_id}: harap 2 PNG, dapat {len(png)}"
        for p in png:
            assert p.stat().st_size > 0, f"{p} kosong"

    turunan = yaml.safe_load((folder / "turunan.yaml").read_text())
    assert len(turunan["soal"]) == 10, f"harap 10 soal, dapat {len(turunan['soal'])}"
    assert [s["soal_id"] for s in turunan["soal"]] == SOAL_UJI, turunan["soal"]

    for s in turunan["soal"]:
        assert s["jeda_sebelum_goresan_pertama_ms"] is not None, s
        assert len(s["durasi_per_langkah_ms"]) == 2, s
        assert len(s["jumlah_hapus_per_langkah"]) == 2, s

    total_png = len(list(folder.glob("soal-*/langkah-*.png")))
    print(f"render 10 soal: PASS ({total_png} PNG, {len(turunan['soal'])} soal di turunan.yaml)")


def tes_goresan_dicoret_tetap_dirender(tmp):
    """Goresan yang dicoret anak TIDAK boleh hilang dari PNG.

    Panduan Orang Tua: "Larang menghapus coretan; kalau keliru cukup dicoret."
    Versi lama index.html melakukan `langkah.goresan = []` — membuang bukti
    paling berharga, yaitu apa yang sempat dipikirkan anak sebelum berubah
    pikiran. Test ini mengunci perilaku barunya.
    """
    langkah = buat_langkah(0, 0, 5000, n_goresan=2)
    langkah["goresan"][0]["dicoret"] = True
    langkah["goresan"][0]["dicoret_pada_ms"] = 1200

    out = tmp / "dicoret.png"
    render.render_langkah(langkah, out)
    assert out.stat().st_size > 0, "PNG kosong"

    from PIL import Image
    daftar = Image.open(out).convert("RGB").getcolors(maxcolors=100000)
    assert daftar is not None, "gambar terlalu banyak warna — tidak terduga untuk goresan"
    warna = [w for _, w in daftar]
    # Hitam = goresan asli, abu-abu = yang dicoret. Keduanya harus ada.
    assert any(sum(w) < 200 for w in warna), f"goresan asli hilang: {warna}"
    assert any(150 < sum(w) < 700 for w in warna), f"goresan dicoret tidak dirender: {warna}"
    print("goresan dicoret tetap dirender: PASS")


def tes_goresan_tanpa_flag_dicoret(tmp):
    """Sesi lama (sebelum flag `dicoret` ada) harus tetap bisa dirender."""
    langkah = buat_langkah(0, 0, 5000, n_goresan=1)
    assert "dicoret" not in langkah["goresan"][0]
    out = tmp / "lama.png"
    render.render_langkah(langkah, out)
    assert out.stat().st_size > 0
    print("kompatibel dengan sesi lama: PASS")


def main():
    tes_hitung_turunan_dasar()
    tes_langkah_belum_tersegel()
    tes_langkah_tanpa_goresan()
    tes_sesi_tanpa_goresan_sama_sekali()

    tmp = Path(tempfile.mkdtemp(prefix="spike-render-test-"))
    try:
        tes_goresan_dicoret_tetap_dirender(tmp)
        tes_goresan_tanpa_flag_dicoret(tmp)
        tes_render_10_soal(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\nSemua test render.py OK.")


if __name__ == "__main__":
    main()
