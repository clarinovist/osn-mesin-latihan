"""Paket topik geometri datar — Fase 1 plan 30 Aug 2026.

Dua belas template menutup cakupan geometri datar OSN SD: sudut (bagian A),
keliling & luas (B), lingkaran (C), arsiran & perubahan ukuran (D), dan
dasar P3 (E): luas dari kotak satuan serta simetri bangun dasar.
Level P3–P6; P3 dibuka selaras band SASMO Primary 1–4 (geometry &
mensuration). Soal berbentuk teks dulu; diagram SVG adalah penyempurnaan
`render_badan` belakangan.

Python tetap menghitung parameter, kunci, dan malrule; ini bukan soal
yang ditulis LLM. Malrule lulus `saring_malrule` dengan jalur K dan H
(setiap template diuji di __tests__/test_topik_geometri.py).
"""

from __future__ import annotations

import random

from templates import Malrule, Soal, saring_malrule
from topics import Topik, daftarkan


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


def sudut_luar_segitiga(a: int, b: int) -> Soal:
    """Sudut luar segitiga = a+b (dua sudut dalam tak bersisian).

    Hanya P5+ (komposisi P5/P6 memuatnya; P4 menolak lewat `_level_efektif`).
    Kunci a+b; malrule membedakan "dikira sudut dalam" (180−a−b) dari
    "selisih a−b" (keduanya K) dan salah hitung (H).
    """
    kunci = a + b
    mal = [
        Malrule(
            "sudut_luar.dikira_dalam",
            str(180 - a - b),
            "K",
            "menghitung sudut dalam yang tersisa padahal yang ditanya sudut luar",
        ),
        Malrule(
            "sudut_luar.selisih_a_b",
            str(a - b),
            "K",
            "mengurangkan dua sudut dalam padahal sudut luar = jumlah keduanya",
        ),
        Malrule(
            "sudut_luar.kurang_satu",
            str(kunci - 1),
            "H",
            "jumlah dua sudut dalam sudah benar, hasilnya meleset satu",
        ),
    ]
    return Soal(
        "sudut_luar_segitiga",
        {"a": a, "b": b},
        (
            f"Dua sudut dalam sebuah segitiga yang tidak bersisian dengan "
            f"sudut luar besarnya {a}° dan {b}°. "
            f"Berapa besar sudut luar tersebut?"
        ),
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        bagian="A",
    )


def keliling_luas_datar(
    varian: str, p: int, l: int | None = None, K: int | None = None
) -> Soal:
    """Keliling 2(p+l) maju, atau balik arah: dari K cari luas p·(K/2−p).

    Balik arah adalah sumber kesalahan utama (anak membaca soal ulang),
    jadi varian itu wajib `minta_restatement`. Malrule membedakan tukar
    rumus (K) dari lupa bagi dua (K/H) dan salah hitung (H).
    """
    if varian == "keliling":
        kunci = 2 * (p + l)
        mal = [
            Malrule(
                "datar.tukar_luas",
                str(p * l),
                "K",
                "menghitung luas padahal yang diminta keliling (rumus tertukar)",
            ),
            Malrule(
                "datar.lupa_kali_dua",
                str(p + l),
                "K",
                "hanya menjumlahkan dua sisi, keliling = 2×(panjang+lebar)",
            ),
            Malrule(
                "datar.kurang_satu",
                str(kunci - 1),
                "H",
                "kelilingnya benar, penjumlahannya meleset satu",
            ),
        ]
        teks = (
            f"Persegi panjang panjangnya {p} cm dan lebarnya {l} cm. "
            f"Berapa kelilingnya?"
        )
        param = {"varian": varian, "p": p, "l": l}
    else:
        kunci = p * (K // 2 - p)
        mal = [
            Malrule(
                "datar.balik_lupa_bagi_dua",
                str(p * (K - p)),
                "K",
                "keliling dibagi dua dilupakan — panjang+lebar dianggap sama dengan keliling",
            ),
            Malrule(
                "datar.balik_jawab_panjang",
                str(K // 2 - p),
                "B",
                "sudah mencari lebar, tapi luasnya tidak dihitung",
            ),
            Malrule(
                "datar.balik_kurang_satu",
                str(kunci - 1),
                "H",
                "langkahnya benar, perkalian luasnya meleset satu",
            ),
        ]
        teks = (
            f"Keliling persegi panjang {K} cm dan panjangnya {p} cm. "
            f"Berapa luas persegi panjang itu?"
        )
        param = {"varian": varian, "p": p, "K": K}
    return Soal(
        "keliling_luas_datar",
        param,
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        bagian="B",
    )


def luas_segitiga_jajargenjang(varian: str, a: int, t: int, s: int) -> Soal:
    """½·a·t (segitiga) atau a·t (jajargenjang); tinggi TEGAK, bukan sisi miring.

    Sisi miring `s` sengaja ada di teks: malrule "pakai sisi miring sebagai
    tinggi" membedakan anak yang paham tinggi tegak dari yang tidak.
    """
    if varian == "segitiga":
        kunci = a * t // 2
        mal = [
            Malrule(
                "segitiga.lupa_setengah",
                str(a * t),
                "K",
                "alas dikali tinggi tanpa dibagi dua",
            ),
            Malrule(
                "segitiga.pakai_sisi_miring",
                str(a * s // 2),
                "K",
                "memakai sisi miring sebagai tinggi padahal tinggi harus tegak",
            ),
            Malrule(
                "segitiga.kurang_satu",
                str(kunci - 1),
                "H",
                "rumus ½·a·t benar, perkaliannya meleset satu",
            ),
        ]
        teks = (
            f"Segitiga alasnya {a} cm, tingginya {t} cm, dan sisi miringnya "
            f"{s} cm. Berapa luas segitiga itu?"
        )
        param = {"varian": varian, "a": a, "t": t, "s": s}
    else:
        kunci = a * t
        mal = [
            Malrule(
                "jajargenjang.pakai_sisi_miring",
                str(a * s),
                "K",
                "memakai sisi miring sebagai tinggi padahal tinggi harus tegak lurus",
            ),
            Malrule(
                "jajargenjang.pakai_setengah",
                str(a * t // 2),
                "K",
                "memakai rumus segitiga ½·a·t padahal jajargenjang tanpa ½",
            ),
            Malrule(
                "jajargenjang.kurang_satu",
                str(kunci - 1),
                "H",
                "rumus a·t benar, perkaliannya meleset satu",
            ),
        ]
        teks = (
            f"Jajargenjang alasnya {a} cm, tingginya {t} cm, dan sisi "
            f"miringnya {s} cm. Berapa luas jajargenjang itu?"
        )
        param = {"varian": varian, "a": a, "t": t, "s": s}
    return Soal(
        "luas_segitiga_jajargenjang",
        param,
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        bagian="B",
    )


def luas_segiempat_lain(varian: str, **nilai: int) -> Soal:
    """Trapesium ½(a+b)t, ketupat/layang ½·d1·d2, atau balik arah cari diagonal.

    Plan #6: (a+b)t lupa ½ (K), jumlah diagonal d1+d2 (K), lupa bagi 2 saat
    balik arah (H). Semua kunci bilangan bulat (jumlah sisi/diagonal genap).
    """
    if varian == "trapesium":
        a, b, t = nilai["a"], nilai["b"], nilai["t"]
        kunci = (a + b) * t // 2
        mal = [
            Malrule(
                "segiempat.trapesium_lupa_setengah",
                str((a + b) * t),
                "K",
                "(jumlah sisi sejajar) × tinggi tanpa dibagi dua",
            ),
            Malrule(
                "segiempat.trapesium_jawab_sisi",
                str(a + b),
                "B",
                "menjawab jumlah dua sisi sejajar, bukan luas trapesium",
            ),
            Malrule(
                "segiempat.trapesium_kurang_satu",
                str(kunci - 1),
                "H",
                "rumus ½(a+b)t benar, perkaliannya meleset satu",
            ),
        ]
        teks = (
            f"Trapesium sisi sejajarnya {a} cm dan {b} cm, tingginya {t} cm. "
            f"Berapa luas trapesium itu?"
        )
        param = {"varian": varian, "a": a, "b": b, "t": t}
    elif varian == "ketupat_layang":
        d1, d2 = nilai["d1"], nilai["d2"]
        kunci = d1 * d2 // 2
        mal = [
            Malrule(
                "segiempat.jumlah_diagonal",
                str(d1 + d2),
                "K",
                "menjumlahkan dua diagonal padahal luas = ½ × d1 × d2",
            ),
            Malrule(
                "segiempat.lupa_setengah",
                str(d1 * d2),
                "K",
                "dua diagonal dikalikan tanpa dibagi dua",
            ),
            Malrule(
                "segiempat.kurang_satu",
                str(kunci - 1),
                "H",
                "rumus ½·d1·d2 benar, perkaliannya meleset satu",
            ),
        ]
        teks = (
            f"Belah ketupat diagonalnya {d1} cm dan {d2} cm. "
            f"Berapa luasnya?"
        )
        param = {"varian": varian, "d1": d1, "d2": d2}
    else:
        luas, d1 = nilai["L"], nilai["d1"]
        kunci = 2 * luas // d1
        mal = [
            Malrule(
                "segiempat.balik_lupa_bagi_dua",
                str(luas // d1),
                "K",
                "membalik rumus tanpa mengalikan dua — lupa luas = ½ × d1 × d2",
            ),
            Malrule(
                "segiempat.balik_jawab_d1",
                str(d1),
                "B",
                "menjawab diagonal yang sudah diketahui, bukan yang dicari",
            ),
            Malrule(
                "segiempat.balik_kurang_satu",
                str(kunci - 1),
                "H",
                "rumus balik benar, pembagiannya meleset satu",
            ),
        ]
        teks = (
            f"Luas belah ketupat {luas} cm² dan salah satu diagonalnya "
            f"{d1} cm. Berapa panjang diagonal yang lain?"
        )
        param = {"varian": varian, "L": luas, "d1": d1}
    return Soal(
        "luas_segiempat_lain",
        param,
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        bagian="B",
    )


def lingkaran_keliling_luas(varian: str, r: int) -> Soal:
    """K=2πr, L=πr²; π=22/7 bila r kelipatan 7, selain itu π=3,14.

    Kunci desimal memakai koma ("153,86") — normalisasi di diagnosis.py
    mengubah koma ke titik. Semua nilai malrule diformat sama dengan kunci
    supaya jawaban anak yang salah benar-benar cocok dengan diagnosis.
    """

    def fmt(val: float) -> str:
        if val % 1 == 0:
            return str(int(val))
        return f"{val:.1f}".replace(".", ",")

    if r % 7 == 0:
        pi_val = 22 / 7
    else:
        pi_val = 3.14

    if varian == "keliling":
        kunci = fmt(2 * pi_val * r)
        mal = [
            Malrule(
                "lingkaran.tukar_luas",
                fmt(pi_val * r * r),
                "K",
                "menghitung luas πr² padahal yang diminta keliling 2πr",
            ),
            Malrule(
                "lingkaran.pakai_diameter",
                fmt(2 * pi_val * (2 * r)),
                "K",
                "memakai diameter sebagai jari-jari — keliling 2π·(2r) bukan 2πr",
            ),
            Malrule(
                "lingkaran.kurang_satu",
                fmt(2 * pi_val * r - 1),
                "H",
                "langkah benar, hitungan meleset satu",
            ),
        ]
        teks = (
            f"Lingkaran berjari-jari {r} cm. "
            f"{'(π = 22/7)' if r % 7 == 0 else '(π = 3,14)'} "
            f"Berapa kelilingnya?"
        )
    else:
        kunci = fmt(pi_val * r * r)
        mal = [
            Malrule(
                "lingkaran.pakai_diameter",
                fmt(pi_val * (2 * r) ** 2),
                "K",
                "memakai diameter sebagai jari-jari — luas π·(2r)² bukan πr²",
            ),
            Malrule(
                "lingkaran.tukar_keliling",
                fmt(2 * pi_val * r),
                "K",
                "menghitung keliling 2πr padahal yang diminta luas πr²",
            ),
            Malrule(
                "lingkaran.kurang_satu",
                fmt(pi_val * r * r - 1),
                "H",
                "langkah benar, hitungan meleset satu",
            ),
        ]
        teks = (
            f"Lingkaran berjari-jari {r} cm. "
            f"{'(π = 22/7)' if r % 7 == 0 else '(π = 3,14)'} "
            f"Berapa luasnya?"
        )
    return Soal(
        "lingkaran_keliling_luas",
        {"varian": varian, "r": r},
        teks,
        kunci,
        saring_malrule(kunci, mal),
        minta_restatement=True,
        bagian="C",
    )


def juring(varian: str, s: int, r: int) -> Soal:
    """Luas juring = (s/360)πr²; keliling juring = busur + 2r.

    π=22/7 bila r kelipatan 7, selain itu π=3,14. Hanya level P6
    (komposisi memuatnya di P6). s derajat sudut pusat dari himpunan
    {30,45,60,90,120,180,270}.
    """

    def fmt(val: float) -> str:
        if val % 1 == 0:
            return str(int(val))
        return f"{val:.1f}".replace(".", ",")

    pi_val = 22 / 7 if r % 7 == 0 else 3.14

    if varian == "luas_juring":
        kunci = fmt(s / 360 * pi_val * r * r)
        mal = [
            Malrule(
                "juring.lupa_setengah_busur",
                fmt(pi_val * r * r),
                "K",
                "menghitung luas lingkaran penuh, bukan luas juring",
            ),
            Malrule(
                "juring.pakai_s_180",
                fmt(s / 180 * pi_val * r * r),
                "K",
                "menggunakan s/180 bukan s/360 — dua kali luas juring sebenarnya",
            ),
            Malrule(
                "juring.kurang_satu",
                fmt(s / 360 * pi_val * r * r - 1),
                "H",
                "langkah benar, hitungan meleset satu",
            ),
        ]
        teks = (
            f"Juring lingkaran berjari-jari {r} cm dengan sudut pusat {s}°. "
            f"{'(π = 22/7)' if r % 7 == 0 else '(π = 3,14)'} "
            f"Berapa luas juring itu?"
        )
    else:
        kunci = fmt(s / 360 * 2 * pi_val * r + 2 * r)
        busur = s / 360 * 2 * pi_val * r
        mal = [
            Malrule(
                "juring.lupa_tambah_2r",
                fmt(busur),
                "K",
                "hanya menghitung panjang busur, lupa menambah dua kali jari-jari",
            ),
            Malrule(
                "juring.pakai_diameter",
                fmt(s / 360 * 2 * pi_val * (2 * r)),
                "K",
                "memakai diameter sebagai jari-jari pada rumus busur",
            ),
            Malrule(
                "juring.kurang_satu",
                fmt(s / 360 * 2 * pi_val * r + 2 * r - 1),
                "H",
                "langkah benar, hitungan meleset satu",
            ),
        ]
        teks = (
            f"Juring lingkaran berjari-jari {r} cm dengan sudut pusat {s}°. "
            f"{'(π = 22/7)' if r % 7 == 0 else '(π = 3,14)'} "
            f"Berapa keliling juring itu?"
        )
    return Soal(
        "juring",
        {"varian": varian, "s": s, "r": r},
        teks,
        kunci,
        saring_malrule(kunci, mal),
        minta_restatement=True,
        bagian="C",
    )


def luas_arsiran(varian: str, **nilai: int) -> Soal:
    """Luas arsiran = bangun pembungkus − bagian dibuang.

    Dua varian dalam SATU template (plan #9):
      - persegi_titik_tengah: persegi sisi 2r memuat 4 × ¼ lingkaran
        (jari-jari r, berimpit di titik tengah sisi) → (2r)² − πr².
        r kelipatan 7 → π=22/7 (kunci bulat).
      - jalan_pinggir: persegi luar − persegi dalam (jalan mengelilingi);
        lebar jalan = (luar−dalam)/2, dipakai dua kali.
    """
    if varian == "persegi_titik_tengah":
        r = nilai["r"]
        val = (2 * r) ** 2 - 22 / 7 * r * r
        kunci = str(int(val))
        # pakai diameter sebagai jari-jari → bagian dibuang jadi π·(2r)²
        diam = (2 * r) ** 2 - 22 / 7 * (2 * r) ** 2
        mal = [
            Malrule(
                "arsiran.pakai_diameter",
                str(int(diam)),
                "K",
                "memakai diameter lingkaran sebagai jari-jari — bagian dibuang jadi π·(2r)²",
            ),
            Malrule(
                "arsiran.pakai_pi_314",
                f"{((2 * r) ** 2 - 3.14 * r * r):.1f}".replace(".", ","),
                "H",
                "memakai π=3,14 padahal r kelipatan 7 harus pakai 22/7",
            ),
            Malrule(
                "arsiran.kurang_satu",
                str(int(val) - 1),
                "H",
                "pengurangan luas benar, hasilnya meleset satu",
            ),
        ]
        teks = (
            f"Persegi bersisi {2 * r} cm memuat empat seperempat lingkaran "
            f"berjari-jari {r} cm di tiap pojok (π = 22/7). "
            f"Berapa luas daerah yang diarsir?"
        )
        param = {"varian": varian, "r": r}
    else:
        luar, dalam = nilai["luar"], nilai["dalam"]
        kunci = str(luar * luar - dalam * dalam)
        # jalan dihitung sekali (hanya satu sisi) → luas = luar² − (dalam+lebar)²
        lebar = (luar - dalam) // 2
        sekali = luar * luar - (dalam + lebar) ** 2
        mal = [
            Malrule(
                "arsiran.lebar_hanya_sekali",
                str(sekali),
                "K",
                "jalan dihitung sekali padahal mengelilingi — lebar jalan harus dipakai di dua sisi",
            ),
            Malrule(
                "arsiran.jawab_selisih_sisi",
                str(luar - dalam),
                "B",
                "menjawab selisih sisi luar dan dalam, bukan luas jalan",
            ),
            Malrule(
                "arsiran.kurang_satu",
                str(luar * luar - dalam * dalam - 1),
                "H",
                "pengurangan luas benar, hasilnya meleset satu",
            ),
        ]
        teks = (
            f"Sebuah jalan mengelilingi taman berbentuk persegi. Bagian luar "
            f"jalan bersisi {luar} m dan bagian dalam bersisi {dalam} m. "
            f"Berapa luas jalan itu?"
        )
        param = {"varian": varian, "luar": luar, "dalam": dalam}
    return Soal(
        "luas_arsiran",
        param,
        teks,
        kunci,
        saring_malrule(kunci, mal),
        minta_restatement=True,
        bagian="D",
    )


def perbandingan_ukuran(varian: str, k: int, ukuran: int) -> Soal:
    """Sisi ×k → keliling ×k, luas ×k², volume ×k³ (angka kecil).

    Hanya P6. Volume hanya sebagai kontras angka — konten volume penuh ada
    di paket geometri-ruang (Fase 5). Plan #10: luas ikut ×k (K), tukar
    k²/k³ (K), kurang-1 (H).
    """
    if varian == "keliling":
        kunci = k * ukuran
        mal = [
            Malrule(
                "perbandingan.skala_salah",
                str(ukuran),
                "K",
                "menjawab ukuran mula-mula, tidak dikalikan skala",
            ),
            Malrule(
                "perbandingan.tukar_pangkat",
                str(k * k * ukuran),
                "K",
                "mengalikan keliling dengan k² padahal keliling hanya ×k",
            ),
            Malrule(
                "perbandingan.kurang_satu",
                str(kunci - 1),
                "H",
                "perkalian skala benar, hasilnya meleset satu",
            ),
        ]
        teks = (
            f"Persegi sisinya diperbesar {k} kali lipat. Keliling semula "
            f"{ukuran} cm. Berapa kelilingnya sekarang?"
        )
    elif varian == "luas":
        kunci = k * k * ukuran
        mal = [
            Malrule(
                "perbandingan.skala_salah",
                str(k * ukuran),
                "K",
                "luas ikut ×k padahal luas mengikuti k²",
            ),
            Malrule(
                "perbandingan.tukar_k_pangkat",
                str(k * k * k * ukuran),
                "K",
                "memakai k³ untuk luas padahal luas hanya k²",
            ),
            Malrule(
                "perbandingan.kurang_satu",
                str(kunci - 1),
                "H",
                "perkalian skala benar, hasilnya meleset satu",
            ),
        ]
        teks = (
            f"Persegi sisinya diperbesar {k} kali lipat. Luas semula "
            f"{ukuran} cm². Berapa luasnya sekarang?"
        )
    else:
        kunci = k * k * k * ukuran
        mal = [
            Malrule(
                "perbandingan.skala_salah",
                str(k * k * ukuran),
                "K",
                "volume ikut k² padahal volume mengikuti k³",
            ),
            Malrule(
                "perbandingan.tukar_k_pangkat",
                str(k * ukuran),
                "K",
                "memakai k untuk volume padahal volume mengikuti k³",
            ),
            Malrule(
                "perbandingan.kurang_satu",
                str(kunci - 1),
                "H",
                "perkalian skala benar, hasilnya meleset satu",
            ),
        ]
        teks = (
            f"Kubus rusuknya diperbesar {k} kali lipat. Volume semula "
            f"{ukuran} cm³. Berapa volumenya sekarang?"
        )
    return Soal(
        "perbandingan_ukuran",
        {"varian": varian, "k": k, "ukuran": ukuran},
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        bagian="D",
    )


# ── Bagian E — dasar P3 (pembukaan level P3) ────────────────────────────
#
# Band SASMO Primary 1–4 (geometry & mensuration): luas dibaca langsung
# dari kotak-kotak satuan, sumbu simetri bangun dasar, keliling maju.

# Hiasan teks NON-jawaban untuk template dasar P3 — melebarkan variasi
# parameter (target >= 200 kombinasi unik) tanpa menyentuh kunci.
KONTEKS_KOTAK = (
    "ubin",
    "keramik",
    "kotak kue",
    "potongan cokelat",
    "stiker",
    "kancing",
)
WARNA_KERTAS = ("merah", "biru", "hijau", "kuning", "oranye", "ungu")


def luas_kotak_satuan(p: int, l: int, satuan: str = "cm", konteks: str = "kotak") -> Soal:
    """Luas persegi panjang dibaca dari kotak-kotak satuan: grid p × l.

    Template pembuka geometri di P3: luas = banyak kotak yang mengisi
    bangun, kunci p·l (belum ada rumus). Malrule khasnya: menghitung kotak
    di tepi saja (keliling, H), menghitung satu baris/kolom saja (K), dan
    meleset satu (H). p·l == 2(p+l) — (3,6), (4,4), (6,3) — dieksklusi di
    `_parameter` seperti pada `keliling_luas_datar` supaya hitung_keliling
    tidak bertabrakan dengan kunci; p·l == 2(p+l)+1 — (3,7), (7,3) — juga
    dieksklusi supaya kurang_satu (jalur H) tidak ikut tersaring.
    """
    kunci = p * l
    mal = [
        Malrule(
            "datar.hitung_keliling",
            str(2 * (p + l)),
            "H",
            "menghitung kotak-kotak di tepi (keliling) padahal yang ditanya isi seluruh bangun",
        ),
        Malrule(
            "datar.hanya_satu_baris",
            str(p),
            "K",
            "hanya menghitung kotak pada satu baris, belum dikalikan banyak barisnya",
        ),
        Malrule(
            "datar.hanya_satu_kolom",
            str(l),
            "K",
            "hanya menghitung kotak pada satu kolom, belum dikalikan banyak kolomnya",
        ),
        Malrule(
            "datar.kurang_satu",
            str(kunci - 1),
            "H",
            "penghitungan kotaknya benar, hasil akhirnya meleset satu",
        ),
    ]
    teks = (
        f"Persegi panjang tersusun rapi dari {konteks} berbentuk persegi: "
        f"{p} {konteks} ke samping dan {l} {konteks} ke bawah. "
        f"Setiap {konteks} bersisi 1 {satuan}. Berapa luas persegi panjang itu?"
    )
    return Soal(
        "luas_kotak_satuan",
        {"p": p, "l": l, "satuan": satuan, "konteks": konteks},
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        bagian="E",
    )


def simetri_bangun(
    bangun: str,
    ukuran: int,
    satuan: str = "cm",
    warna: str | None = None,
    lebar: int | None = None,
) -> Soal:
    """Banyak sumbu simetri bangun dasar: persegi 4, persegi-panjang 2,
    segitiga sama sisi 3, belah ketupat 2.

    Jebalan malrule: untuk persegi dan segitiga sama sisi, "menghitung
    sisi/sudut" memberi angka yang SAMA dengan sumbu simetrinya (4=4,
    3=3) — keduanya tersaring `saring_malrule`. Jalur K diselamatkan
    miskonsepsi lain (persegi: "hanya lipatan tegak-mendatar" = 2; sama
    sisi: "hanya sumbu tegak dari puncak" = 1), dan jalur H datang dari
    jawaban salah khas (menemukan satu garis saja = 1, salah hitung satu).
    Ukuran, satuan, warna, dan lebar adalah parameter NON-jawaban —
    melebarkan variasi tanpa menyentuh kunci.
    """
    warna_txt = f" berwarna {warna}" if warna else ""
    if bangun == "persegi":
        kunci = 4
        teks = (
            f"Persegi{warna_txt} bersisi {ukuran} {satuan}. "
            f"Berapa banyak sumbu simetrinya?"
        )
        # hitung_sisi/hitung_sudut = 4 == kunci → tersaring (jebalan).
        mal = [
            Malrule(
                "simetri.hitung_sisi",
                "4",
                "K",
                "menghitung banyak sisi bangun, bukan banyak garis lipatnya",
            ),
            Malrule(
                "simetri.hitung_sudut",
                "4",
                "K",
                "menghitung banyak sudut bangun, bukan banyak garis lipatnya",
            ),
            Malrule(
                "simetri.hanya_dua_arah",
                "2",
                "K",
                "hanya menghitung lipatan tegak dan mendatar — garis diagonalnya tidak dianggap sumbu simetri",
            ),
        ]
    elif bangun == "persegi_panjang":
        if lebar is None:
            lebar = max(2, ukuran // 2)
        kunci = 2
        teks = (
            f"Persegi panjang{warna_txt} panjangnya {ukuran} {satuan} dan "
            f"lebarnya {lebar} {satuan}. Berapa banyak sumbu simetrinya?"
        )
        # 4 sisi ≠ 2 sumbu → hitung_sisi selamat sebagai jalur K.
        mal = [
            Malrule(
                "simetri.hitung_sisi",
                "4",
                "K",
                "menghitung banyak sisi bangun, bukan banyak garis lipatnya",
            ),
            Malrule(
                "simetri.hitung_sudut",
                "4",
                "K",
                "menghitung banyak sudut bangun, bukan banyak garis lipatnya",
            ),
        ]
    elif bangun == "segitiga_sama_sisi":
        kunci = 3
        teks = (
            f"Segitiga sama sisi{warna_txt} sisinya {ukuran} {satuan}. "
            f"Berapa banyak sumbu simetrinya?"
        )
        # Jebalan yang sama dengan persegi: 3 sisi = 3 sumbu, 3 sudut = 3
        # sumbu → keduanya tersaring; jalur K dari "hanya sumbu tegak".
        mal = [
            Malrule(
                "simetri.hitung_sisi",
                "3",
                "K",
                "menghitung banyak sisi bangun, bukan banyak garis lipatnya",
            ),
            Malrule(
                "simetri.hitung_sudut",
                "3",
                "K",
                "menghitung banyak sudut bangun, bukan banyak garis lipatnya",
            ),
            Malrule(
                "simetri.hanya_sumbu_tegak",
                "1",
                "K",
                "hanya menghitung garis lipat yang tegak dari sudut puncak — dua sumbu miringnya tidak terlihat",
            ),
        ]
    else:  # belah_ketupat
        kunci = 2
        teks = (
            f"Belah ketupat{warna_txt} sisinya {ukuran} {satuan}. "
            f"Berapa banyak sumbu simetrinya?"
        )
        mal = [
            Malrule(
                "simetri.hitung_sisi",
                "4",
                "K",
                "menghitung banyak sisi bangun, bukan banyak garis lipatnya",
            ),
            Malrule(
                "simetri.hitung_sudut",
                "4",
                "K",
                "menghitung banyak sudut bangun, bukan banyak garis lipatnya",
            ),
        ]
    # Jalur H yang selamat dari jebalan di SEMUA bangun: jawaban salah khas
    # (garis lipatnya ditemukan semua tapi salah menghitung jumlahnya, atau
    # hanya satu garis yang ditemukan).
    mal.append(
        Malrule(
            "simetri.kurang_satu",
            str(kunci - 1),
            "H",
            "garis lipatnya ditemukan semua, penghitungan jumlahnya meleset satu",
        )
    )
    mal.append(
        Malrule(
            "simetri.hanya_satu_sumbu",
            "1",
            "H",
            "hanya menemukan satu garis lipat, sumbu yang lain tidak terlihat",
        )
    )
    return Soal(
        "simetri_bangun",
        {"bangun": bangun, "ukuran": ukuran, "satuan": satuan, "warna": warna, "lebar": lebar},
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        bagian="E",
    )


REGISTRI_TOPIK = {
    "sudut_pelurus_berpenyiku": sudut_pelurus_berpenyiku,
    "jumlah_sudut_segitiga": jumlah_sudut_segitiga,
    "sudut_luar_segitiga": sudut_luar_segitiga,
    "keliling_luas_datar": keliling_luas_datar,
    "luas_segitiga_jajargenjang": luas_segitiga_jajargenjang,
    "luas_segiempat_lain": luas_segiempat_lain,
    "lingkaran_keliling_luas": lingkaran_keliling_luas,
    "juring": juring,
    "luas_arsiran": luas_arsiran,
    "perbandingan_ukuran": perbandingan_ukuran,
    # Bagian E — dasar P3 (pembukaan level P3)
    "luas_kotak_satuan": luas_kotak_satuan,
    "simetri_bangun": simetri_bangun,
}

KOMPOSISI = {
    # P3 (8 soal): 11, 11, 12, 11, 12, 4, 4, 4
    # Dasar dulu (kotak satuan & simetri, bagian E menyatu di depan),
    # keliling varian "keliling" p, l ∈ 2..10 di akhir sebagai yang tersulit.
    "P3": (
        "luas_kotak_satuan",
        "luas_kotak_satuan",
        "simetri_bangun",
        "luas_kotak_satuan",
        "simetri_bangun",
        "keliling_luas_datar",
        "keliling_luas_datar",
        "keliling_luas_datar",
    ),
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
    "E": "Bagian E — Kotak satuan & simetri",
}

CATATAN_BAGIAN = {
    "A": "Jumlah sudut segitiga 180°, sudut pelurus 180°, penyiku 90°.",
    "B": "Keliling adalah jumlah semua sisi; luas adalah isi bangun.",
    "C": "π = 22/7 hanya saat jari-jari kelipatan 7, selain itu π = 3,14.",
    "E": "Luas adalah banyak kotak yang mengisi bangun; sumbu simetri "
    "adalah garis lipat yang membagi bangun jadi dua bagian sama persis.",
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
    if template_id == "sudut_luar_segitiga":
        # a > b supaya selisih positif; a != 90 supaya dikira_dalam (180-a-b)
        # != selisih_a_b (a-b); a+b != 90 supaya dikira_dalam != kunci (a+b).
        a = rng.randint(30, 89)
        b = rng.randint(20, a - 1)
        while a + b == 90:
            a = rng.randint(30, 89)
            b = rng.randint(20, a - 1)
        return {"a": a, "b": b}
    if template_id == "keliling_luas_datar":
        if level == "P3":
            # P3 (SASMO Primary 1-4): hanya keliling maju dengan angka kecil
            # (2..16). balik_luas (dari K cari luas) disisakan P4+.
            # Ambang variasi pasangan level baru butuh >=200 kombinasi —
            # 2..10 cuma 81 pasang, 2..16 memberi 15x15-6 eksklusi = 219.
            # Eksklusi: p*l == 2(p+l) — (3,6), (4,4), (6,3) — menjatuhkan
            # malrule tukar_luas; p*l == 2(p+l)-1 — (3,5), (5,3) — menjatuhkan
            # kurang_satu, satu-satunya jalur H varian ini; (2,2) membuat
            # tukar_luas dan lupa_kali_dua sama-sama 4.
            p, l = rng.randint(2, 16), rng.randint(2, 16)
            while p * l in (2 * (p + l), 2 * (p + l) - 1) or p == l == 2:
                p, l = rng.randint(2, 16), rng.randint(2, 16)
            return {"varian": "keliling", "p": p, "l": l}
        if rng.random() < 0.5:
            # maju: keliling 2(p+l). Hindari p*l == 2(p+l) (3x6, 4x4, 6x3)
            # supaya malrule tukar_luas tidak bertabrakan dengan kunci.
            p, l = rng.randint(3, 40), rng.randint(3, 40)
            while p * l == 2 * (p + l) or p == l == 2:
                p, l = rng.randint(3, 40), rng.randint(3, 40)
            return {"varian": "keliling", "p": p, "l": l}
        # balik arah: dari K cari luas. l = K/2 - p >= 2, jadi K >= 2(p+2).
        p = rng.randint(3, 30)
        l = rng.randint(2, 25)
        K = 2 * (p + l)
        return {"varian": "balik_luas", "p": p, "K": K}
    if template_id == "luas_segitiga_jajargenjang":
        # a genap supaya a*t/2 dan a*s/2 bilangan bulat. s > t (sisi miring
        # lebih panjang dari tinggi) dan s != 2t supaya lupa_setengah (a*t)
        # != pakai_sisi_miring (a*s/2) untuk varian segitiga.
        a = rng.choice([x for x in range(4, 41, 2)])
        t = rng.randint(3, 20)
        s = rng.randint(t + 1, 2 * t - 1)
        return {"varian": rng.choice(("segitiga", "jajargenjang")), "a": a, "t": t, "s": s}
    if template_id == "luas_segiempat_lain":
        varian = rng.choice(("trapesium", "ketupat_layang", "balik_diagonal"))
        if varian == "trapesium":
            # (a+b) genap supaya (a+b)*t/2 bulat; t >= 3 supaya malrule
            # jawab_sisi (a+b) != kunci; a != b supaya sisi sejajar beda.
            a, b = rng.randint(4, 30), rng.randint(4, 30)
            while (a + b) % 2 or a == b:
                a, b = rng.randint(4, 30), rng.randint(4, 30)
            return {"varian": varian, "a": a, "b": b, "t": rng.randint(3, 15)}
        if varian == "ketupat_layang":
            # d1,d2 genap supaya d1*d2/2 bulat; d1 != d2 supaya jumlah_diagonal
            # != lupa_setengah... cek: d1+d2 != d1*d2/2 untuk d1,d2 >= 4.
            d1 = rng.choice([x for x in range(4, 41, 2)])
            d2 = rng.choice([x for x in range(4, 41, 2)])
            while d1 == d2:
                d2 = rng.choice([x for x in range(4, 41, 2)])
            return {"varian": varian, "d1": d1, "d2": d2}
        # balik arah: cari d2 = 2L/d1. L = d1*d2/2 dengan d1,d2 genap; L//d1
        # harus != kunci (kunci = 2L//d1 = d2) dan != d1 (malrule jawab_d1).
        d1 = rng.choice([x for x in range(4, 41, 2)])
        d2 = rng.choice([x for x in range(4, 41, 2)])
        while d1 == d2:
            d2 = rng.choice([x for x in range(4, 41, 2)])
        L = d1 * d2 // 2
        return {"varian": varian, "L": L, "d1": d1}
    if template_id == "lingkaran_keliling_luas":
        # r lebar (5..130) supaya guard variasi >= 200 kombinasi unik
        # terpenuhi dari 500 seed (r ~126 nilai x 2 varian). r kelipatan 7
        # otomatis memilih π=22/7 di template; sisanya π=3,14.
        r = rng.randint(5, 130)
        return {"varian": rng.choice(("keliling", "luas")), "r": r}
    if template_id == "juring":
        # s dari himpunan OSN (7 nilai) x r (5..40) x 2 varian = 504 combo.
        r = rng.randint(5, 40)
        return {"varian": rng.choice(("luas_juring", "keliling_juring")), "s": rng.choice((30, 45, 60, 90, 120, 180, 270)), "r": r}
    if template_id == "luas_arsiran":
        if rng.random() < 0.3:
            # persegi_titik_tengah: r kelipatan 7 supaya 22/7 (kunci bulat)
            r = rng.choice((7, 14, 21, 28, 35))
            return {"varian": "persegi_titik_tengah", "r": r}
        # jalan_pinggir: dalam lebar (10..100) x lebar (2,4,...,20) = 910 combo
        dalam = rng.randint(10, 100)
        luar = dalam + rng.choice((2, 4, 6, 8, 10, 12, 14, 16, 18, 20))
        return {"varian": "jalan_pinggir", "luar": luar, "dalam": dalam}
    if template_id == "perbandingan_ukuran":
        # k kecil (2,3,4,5) x ukuran lebar (1..30) x 3 varian = 360 combo
        k = rng.choice((2, 3, 4, 5))
        return {"varian": rng.choice(("keliling", "luas", "volume")), "k": k, "ukuran": rng.randint(1, 30)}
    if template_id == "luas_kotak_satuan":
        # P3: grid p × l kecil (2..8) supaya kotaknya masih bisa digambar dan
        # dihitung anak. Eksklusi: p*l == 2(p+l) — (3,6), (4,4), (6,3) —
        # menjatuhkan malrule hitung_keliling; p*l == 2(p+l)+1 — (3,7), (7,3)
        # — menjatuhkan kurang_satu (pola yang sama dengan keliling_luas_datar).
        p, l = rng.randint(2, 8), rng.randint(2, 8)
        while p * l in (2 * (p + l), 2 * (p + l) + 1):
            p, l = rng.randint(2, 8), rng.randint(2, 8)
        # satuan & konteks hanya menghias teks (NON-jawaban) dan menjaga
        # variasi >= 200 kombinasi unik: 44 grid x 2 satuan x 6 konteks.
        return {
            "p": p,
            "l": l,
            "satuan": rng.choice(("cm", "m")),
            "konteks": rng.choice(KONTEKS_KOTAK),
        }
    if template_id == "simetri_bangun":
        # Empat bangun dasar; kunci (jumlah sumbu) ditentukan di template.
        # ukuran/satuan/warna (+lebar untuk persegi-panjang) NON-jawaban —
        # 4 bangun x 14 ukuran x 2 satuan x 6 warna melebihi 200 kombinasi.
        bangun = rng.choice(
            ("persegi", "persegi_panjang", "segitiga_sama_sisi", "belah_ketupat")
        )
        ukuran = rng.randint(3, 16)
        param: dict = {
            "bangun": bangun,
            "ukuran": ukuran,
            "satuan": rng.choice(("cm", "m")),
            "warna": rng.choice(WARNA_KERTAS),
        }
        if bangun == "persegi_panjang":
            # lebar < panjang supaya teksnya masuk akal
            param["lebar"] = rng.randint(2, ukuran - 1)
        return param
    raise KeyError(f"template tidak dikenal: {template_id}")


TOPIK = Topik(
    id="geometri-datar",
    nama="Geometri Datar",
    judul_lembar="Latihan Geometri Datar",
    judul_penilaian="Penilaian — Geometri Datar",
    templates=REGISTRI_TOPIK,
    komposisi=KOMPOSISI,
    profil={"P3": {}, "P4": {}, "P5": {}, "P6": {}},
    judul_bagian=JUDUL_BAGIAN,
    catatan_bagian=CATATAN_BAGIAN,
    parameter_untuk=_parameter,
)

daftarkan(TOPIK)
