"""Paket topik geometri datar — Fase 1 plan 30 Aug 2026.

Sepuluh template menutup cakupan geometri datar OSN SD: sudut (bagian A),
keliling & luas (B), lingkaran (C), arsiran & perubahan ukuran (D).
Level P4/P5/P6 (P3 ditunda — keputusan pengguna). Soal berbentuk teks
dulu; diagram SVG adalah penyempurnaan `render_badan` belakangan.

Python tetap menghitung parameter, kunci, dan malrule; ini bukan soal
yang ditulis LLM. Malrule lulus `saring_malrule` dengan jalur K dan H
(setiap template diuji di __tests__/test_topik_geometri.py).
"""

from __future__ import annotations

import random

from templates import Malrule, Soal, saring_malrule
from topik import Topik, daftarkan


# ── Bagian A — Sudut ───────────────────────────────────────────────────


def sudut_pelurus_berpenyiku(varian: str, x: int | None = None, kali: int | None = None) -> Soal:
    """Pelurus 180−x, penyiku 90−x, balik arah, atau varian perbandingan.

    Lima bentuk di SATU template (satu template_id, satu paket — aturan
    plan: satu template hidup di satu paket):
      - pelurus:      x diketahui → cari 180−x
      - penyiku:      x diketahui → cari 90−x
      - balik_pelurus: pelurus y diketahui → cari x = 180−y
      - balik_penyiku: penyiku y diketahui → cari x = 90−y
      - tiga_kali:    dua sudut berpelurus, satu kali yang lain → 180/(k+1)

    Bentuk balik selain memperkaya soal, membuat ruang parameter lebar
    (guard variasi >= 200 kombinasi). Kali di {3,4,5,8,9,11} supaya kunci,
    K (360/(k+1)) dan B (k·kunci) selalu saling berbeda.
    """
    if varian == "pelurus":
        kunci = 180 - x
        mal = [
            Malrule(
                "sudut.tukar_penyiku",
                str(90 - x),
                "K",
                "menggunakan sudut penyiku padahal yang diminta pelurus",
            ),
            Malrule(
                "sudut.pelurus_kurang_satu",
                str(kunci - 1),
                "H",
                "pelurusnya benar, pengurangannya meleset satu",
            ),
            Malrule(
                "sudut.jawab_x",
                str(x),
                "B",
                "menjawab besar sudut yang diberikan, bukan pelurusnya",
            ),
        ]
        teks = f"Sudut x besarnya {x}°. Berapa besar sudut pelurusnya?"
        param = {"varian": varian, "x": x}
    elif varian == "penyiku":
        kunci = 90 - x
        mal = [
            Malrule(
                "sudut.tukar_pelurus",
                str(180 - x),
                "K",
                "menggunakan sudut pelurus padahal yang diminta penyiku",
            ),
            Malrule(
                "sudut.penyiku_kurang_satu",
                str(kunci - 1),
                "H",
                "penyikunya benar, pengurangannya meleset satu",
            ),
            Malrule(
                "sudut.jawab_x",
                str(x),
                "B",
                "menjawab besar sudut yang diberikan, bukan penyikunya",
            ),
        ]
        teks = f"Sudut x besarnya {x}°. Berapa besar sudut penyikunya?"
        param = {"varian": varian, "x": x}
    elif varian == "balik_pelurus":
        kunci = 180 - x  # x di sini = pelurus yang diketahui
        mal = [
            Malrule(
                "sudut.balik_tukar_penyiku",
                str(90 - x),
                "K",
                "menggunakan penyiku padahal yang diketahui pelurus",
            ),
            Malrule(
                "sudut.balik_pelurus_kurang_satu",
                str(kunci - 1),
                "H",
                "pengurangannya benar, hasilnya meleset satu",
            ),
            Malrule(
                "sudut.balik_jawab_y",
                str(x),
                "B",
                "menjawab besar pelurus yang diberikan, bukan sudut x",
            ),
        ]
        teks = (
            f"Sudut pelurus dari x adalah {x}°. "
            f"Berapa besar sudut x itu sendiri?"
        )
        param = {"varian": varian, "x": x}
    elif varian == "balik_penyiku":
        kunci = 90 - x  # x di sini = penyiku yang diketahui
        mal = [
            Malrule(
                "sudut.balik_tukar_pelurus",
                str(180 - x),
                "K",
                "menggunakan pelurus padahal yang diketahui penyiku",
            ),
            Malrule(
                "sudut.balik_penyiku_kurang_satu",
                str(kunci - 1),
                "H",
                "pengurangannya benar, hasilnya meleset satu",
            ),
            Malrule(
                "sudut.balik_jawab_y",
                str(x),
                "B",
                "menjawab besar penyiku yang diberikan, bukan sudut x",
            ),
        ]
        teks = (
            f"Sudut penyiku dari x adalah {x}°. "
            f"Berapa besar sudut x itu sendiri?"
        )
        param = {"varian": varian, "x": x}
    else:
        kunci = 180 // (kali + 1)
        besar = kali * kunci
        mal = [
            Malrule(
                "sudut.tiga_kali_jawab_besar",
                str(besar),
                "B",
                "menjawab sudut yang besar padahal yang ditanya yang kecil",
            ),
            Malrule(
                "sudut.tiga_kali_total_360",
                str(360 // (kali + 1)),
                "K",
                "jumlah kedua sudut dikira 360° padahal berpelurus = 180°",
            ),
            Malrule(
                "sudut.tiga_kali_kurang_satu",
                str(kunci - 1),
                "H",
                "pembagiannya benar, hasilnya meleset satu",
            ),
        ]
        teks = (
            f"Dua sudut saling berpelurus dan yang satu {kali} kali yang "
            f"lain. Berapa besar sudut yang kecil?"
        )
        param = {"varian": varian, "kali": kali}
    return Soal(
        "sudut_pelurus_berpenyiku",
        param,
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        bagian="A",
    )


def jumlah_sudut_segitiga(
    varian: str,
    a: int | None = None,
    b: int | None = None,
    p: int | None = None,
    q: int | None = None,
    r: int | None = None,
) -> Soal:
    """Sudut ketiga segitiga = 180−a−b, atau varian perbandingan.

    Varian "perbandingan": sudut berbanding p:q:r, ditanya yang terkecil.
    Total bagian wajib membagi 180 supaya tiap sudut bilangan bulat.
    """
    if varian == "dua_sudut":
        kunci = 180 - a - b
        mal = [
            Malrule(
                "segitiga.pakai_360",
                str(360 - a - b),
                "K",
                "jumlah sudut segitiga dikira 360° padahal 180°",
            ),
            Malrule(
                "segitiga.salah_tanda",
                str(180 - a + b),
                "H",
                "tanda pada sudut kedua terbalik (ditambah, padahal dikurang)",
            ),
            Malrule(
                "segitiga.hanya_kurang_satu",
                str(180 - a),
                "B",
                "hanya mengurangi satu sudut, sudut kedua tidak dihitung",
            ),
        ]
        teks = f"Dalam sebuah segitiga, dua sudutnya {a}° dan {b}°. Berapa besar sudut yang ketiga?"
        param = {"varian": varian, "a": a, "b": b}
    else:
        total = p + q + r
        kunci = 180 * p // total
        mal = [
            Malrule(
                "segitiga.perbandingan_total_360",
                str(360 * p // total),
                "K",
                "jumlah perbandingan dikali 360° padahal 180°",
            ),
            Malrule(
                "segitiga.perbandingan_kurang_satu",
                str(kunci - 1),
                "H",
                "perbandingannya benar, hasil kalinya meleset satu",
            ),
            Malrule(
                "segitiga.perbandingan_jawab_angka",
                str(p),
                "B",
                "menjawab angka perbandingannya, bukan besar sudut",
            ),
        ]
        teks = (
            f"Sudut-sudut sebuah segitiga berbanding {p} : {q} : {r}. "
            f"Berapa besar sudut yang terkecil?"
        )
        param = {"varian": varian, "p": p, "q": q, "r": r}
    return Soal(
        "jumlah_sudut_segitiga",
        param,
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        bagian="A",
    )


REGISTRI_TOPIK = {
    "sudut_pelurus_berpenyiku": sudut_pelurus_berpenyiku,
    "jumlah_sudut_segitiga": jumlah_sudut_segitiga,
}

KOMPOSISI = {
    # P4 (8 soal): 1, 2, 4, 5, 1, 2, 4, 5
    "P4": (
        "sudut_pelurus_berpenyiku",
        "jumlah_sudut_segitiga",
        "keliling_luas_datar",
        "luas_segitiga_jajargenjang",
        "sudut_pelurus_berpenyiku",
        "jumlah_sudut_segitiga",
        "keliling_luas_datar",
        "luas_segitiga_jajargenjang",
    ),
    # P5 (10 soal): 1, 2, 3, 4, 5, 6, 7, 9, 2, 5
    "P5": (
        "sudut_pelurus_berpenyiku",
        "jumlah_sudut_segitiga",
        "sudut_luar_segitiga",
        "keliling_luas_datar",
        "luas_segitiga_jajargenjang",
        "luas_segiempat_lain",
        "lingkaran_keliling_luas",
        "luas_arsiran",
        "jumlah_sudut_segitiga",
        "luas_segitiga_jajargenjang",
    ),
    # P6 (10 soal): 3, 4, 5, 6, 7, 8, 9, 10, 7, 9
    "P6": (
        "sudut_luar_segitiga",
        "keliling_luas_datar",
        "luas_segitiga_jajargenjang",
        "luas_segiempat_lain",
        "lingkaran_keliling_luas",
        "juring",
        "luas_arsiran",
        "perbandingan_ukuran",
        "lingkaran_keliling_luas",
        "luas_arsiran",
    ),
}

JUDUL_BAGIAN = {
    "A": "Bagian A — Sudut",
    "B": "Bagian B — Keliling & luas",
    "C": "Bagian C — Lingkaran",
    "D": "Bagian D — Arsiran & perubahan ukuran",
}

CATATAN_BAGIAN = {
    "A": "Jumlah sudut segitiga 180°, sudut pelurus 180°, penyiku 90°.",
    "B": "Keliling adalah jumlah semua sisi; luas adalah isi bangun.",
    "C": "π = 22/7 hanya saat jari-jari kelipatan 7, selain itu π = 3,14.",
}


def _parameter(template_id: str, rng: random.Random, level: str) -> dict:
    if template_id == "sudut_pelurus_berpenyiku":
        varian = rng.choice(("pelurus", "penyiku", "balik_pelurus", "balik_penyiku", "tiga_kali"))
        if varian in ("pelurus", "balik_pelurus"):
            # x bebas 15..165. Untuk pelurus: x=90 membuat kunci == x (B
            # bertabrakan); untuk balik_pelurus: x=90 membuat kunci == 0
            # (tidak sah). Keduanya dieksklusi di sini.
            x = rng.randint(15, 165)
            while x == 90:
                x = rng.randint(15, 165)
            return {"varian": varian, "x": x}
        if varian in ("penyiku", "balik_penyiku"):
            return {"varian": varian, "x": rng.randint(15, 85)}
        # tiga_kali: kali di {3,4,5,8,9,11} — 360/(k+1) ≠ k·180/(k+1)
        # untuk k≠2, jadi malrule K dan B tidak bertabrakan.
        return {"varian": varian, "kali": rng.choice((3, 4, 5, 8, 9, 11))}
    if template_id == "jumlah_sudut_segitiga":
        varian = rng.choice(("dua_sudut", "perbandingan"))
        if varian == "dua_sudut":
            # a+b <= 160 supaya sudut ketiga >= 20; b != 90 supaya malrule
            # salah_tanda tidak bertabrakan dengan pakai_360.
            a = rng.randint(20, 100)
            b = rng.randint(20, min(140 - a, 100))
            while b == 90:
                b = rng.randint(20, min(140 - a, 100))
            return {"varian": varian, "a": a, "b": b}
        # perbandingan: total bagian membagi 180 dan <= 12, p < q < r,
        # p sudut terkecil. Kunci selalu bilangan bulat.
        pilihan = (
            (1, 2, 3),
            (1, 2, 6),
            (1, 3, 5),
            (2, 3, 4),
            (1, 2, 7),
            (1, 3, 6),
            (1, 4, 5),
            (2, 3, 5),
            (1, 2, 9),
            (1, 3, 8),
            (1, 4, 7),
            (1, 5, 6),
            (2, 3, 7),
            (2, 4, 6),
            (3, 4, 5),
        )
        p, q, r = rng.choice(pilihan)
        return {"varian": varian, "p": p, "q": q, "r": r}
    raise KeyError(f"template tidak dikenal: {template_id}")


TOPIK = Topik(
    id="geometri-datar",
    nama="Geometri Datar",
    judul_lembar="Latihan Geometri Datar",
    judul_penilaian="Penilaian — Geometri Datar",
    templates=REGISTRI_TOPIK,
    komposisi=KOMPOSISI,
    profil={"P4": {}, "P5": {}, "P6": {}},
    judul_bagian=JUDUL_BAGIAN,
    catatan_bagian=CATATAN_BAGIAN,
    parameter_untuk=_parameter,
)

daftarkan(TOPIK)
