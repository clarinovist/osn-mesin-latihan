#!/usr/bin/env python3
"""Tahap A — pencocokan malrule deterministik, tanpa LLM (Rencana Spike Hari 3, §2.3).

Ambiguitas (>=2 malrule berkode beda memprediksi jawaban sama) tidak pernah
diputuskan di sini — selalu diserahkan ke Tahap B (kode 'tidak_pasti').
"""
import re
import sys
from pathlib import Path

import yaml

SPIKE_DIR = Path(__file__).resolve().parent
MALRULE_PATH = SPIKE_DIR / "malrule.yaml"


def fpb(a, b):
    while b:
        a, b = b, a % b
    return a


def kpk(a, b):
    return a * b // fpb(a, b)


def format_pecahan(pembilang, penyebut):
    return f"{pembilang}/{penyebut}"


def format_angka(nilai, desimal):
    return f"{round(nilai, desimal):.{desimal}f}".replace(".", ",")


# Satu fungsi murni per malrule id: parameter template -> jawaban salah yang diprediksi.
PREDIKSI = {
    "urutan_operasi.kiri_ke_kanan_tanpa_prioritas": lambda p: str(
        int((p["a"] + p["b"]) / p["c"] * p["d"] - p["e"])
    ),
    "urutan_operasi.kali_sebelum_bagi_tanpa_kiri_ke_kanan": lambda p: str(
        int(p["a"] + p["b"] / (p["c"] * p["d"]) - p["e"])
    ),
    "pecahan.operasi_pembilang_penyebut_terpisah": lambda p: format_pecahan(
        sum(s["tanda"] * s["n"] for s in p["suku"]),
        sum(s["tanda"] * s["d"] for s in p["suku"]),
    ),
    "desimal.pecahan_dibaca_sebagai_persepuluh": lambda p: format_angka(p["desimal"] + p["n"] / 10, 2),
    "persen.koma_bergeser": lambda p: format_angka((p["persen"] / 100 * p["nilai"]) / 10, 1),
    "fpb.tertukar_dengan_kpk": lambda p: str(kpk(p["a"], p["b"])),
    "kpk.tertukar_dengan_fpb": lambda p: str(fpb(p["a"], p["b"])),
    "volume_kubus.luas_permukaan": lambda p: str(6 * p["rusuk"] ** 2),
    "volume_kubus.rusuk_kali_tiga": lambda p: str(p["rusuk"] * 3),
    "satuan_waktu.tidak_menyimpan_60": lambda p: f"{p['jam1'] + p['jam2']} jam {p['menit1'] + p['menit2']} menit",
}


def normalisasi(s):
    return re.sub(r"\s+", " ", str(s).strip().lower())


def sebagai_angka(s):
    try:
        return float(str(s).strip().replace(",", "."))
    except ValueError:
        return None


def cocok(prediksi, jawaban_diketik):
    if jawaban_diketik is None or jawaban_diketik == "":
        return False
    a_num, b_num = sebagai_angka(prediksi), sebagai_angka(jawaban_diketik)
    if a_num is not None and b_num is not None:
        return abs(a_num - b_num) < 1e-6
    return normalisasi(prediksi) == normalisasi(jawaban_diketik)


def muat_template():
    return yaml.safe_load(MALRULE_PATH.read_text())


def diagnosis(soal_id, jawaban_diketik, template_list=None):
    template_list = template_list or muat_template()
    entri = next((t for t in template_list if t["soal_id"] == soal_id), None)
    if entri is None:
        return {"kode": "tidak_ada_template", "alasan": f"tidak ada template untuk soal_id={soal_id}"}

    if cocok(entri["jawaban_benar"], jawaban_diketik):
        return {"kode": "benar", "alasan": "cocok dengan jawaban_benar"}

    cocok_dengan = [
        m for m in entri.get("malrule", []) if cocok(PREDIKSI[m["id"]](entri["parameter"]), jawaban_diketik)
    ]

    if not cocok_dengan:
        return {"kode": "tidak_pasti", "alasan": "tidak cocok jawaban_benar maupun malrule manapun — lanjut ke Tahap B"}

    kode_unik = {m["kode"] for m in cocok_dengan}
    if len(kode_unik) > 1:
        return {
            "kode": "tidak_pasti",
            "alasan": f"ambigu — malrule berkode beda cocok bersamaan ({sorted(kode_unik)}), diserahkan ke Tahap B",
        }

    return {
        "kode": cocok_dengan[0]["kode"],
        "alasan": cocok_dengan[0]["alasan_singkat"],
        "malrule_id": cocok_dengan[0]["id"],
    }


def cek_tanpa_tumbukan(template_list):
    """PRD §8.8 — tiap template, pastikan tidak ada 2 malrule berkode beda dgn prediksi sama."""
    masalah = []
    for entri in template_list:
        prediksi_ke_kode = {}
        for m in entri.get("malrule", []):
            nilai = PREDIKSI[m["id"]](entri["parameter"])
            if nilai in prediksi_ke_kode and prediksi_ke_kode[nilai] != m["kode"]:
                masalah.append((entri["template_id"], nilai, prediksi_ke_kode[nilai], m["kode"]))
            prediksi_ke_kode[nilai] = m["kode"]
    return masalah


def _tes_mandiri():
    template_list = muat_template()

    kasus = [
        (1, "35", "K"),
        (1, "17", "K"),
        (1, "41", "benar"),
        (2, "4/5", "K"),
        (2, "11/12", "benar"),
        (3, "0,55", "K"),
        (4, "10,8", "H"),
        (5, "144", "B"),
        (6, "6", "B"),
        (10, "384", "K"),
        (10, "24", "K"),
        (10, "512", "benar"),
        (13, "5 jam 85 menit", "H"),
        (8, "999", "tidak_pasti"),
    ]

    gagal = 0
    for soal_id, jawaban, kode_harap in kasus:
        hasil = diagnosis(soal_id, jawaban, template_list)
        status = "OK" if hasil["kode"] == kode_harap else "GAGAL"
        if status == "GAGAL":
            gagal += 1
        print(
            f"[{status}] soal_id={soal_id} jawaban='{jawaban}' -> kode={hasil['kode']} "
            f"(harap {kode_harap}) | {hasil.get('alasan', '')}"
        )

    tumbukan = cek_tanpa_tumbukan(template_list)
    print()
    if tumbukan:
        print("PERINGATAN TUMBUKAN MALRULE:")
        for t in tumbukan:
            print(" -", t)
        gagal += len(tumbukan)
    else:
        print("OK: tidak ada tumbukan prediksi antar-malrule berkode beda.")

    print()
    if gagal:
        print(f"{gagal} masalah ditemukan.")
        sys.exit(1)
    print(f"Semua {len(kasus)} kasus tes OK, tanpa panggilan API apa pun.")


if __name__ == "__main__":
    _tes_mandiri()
