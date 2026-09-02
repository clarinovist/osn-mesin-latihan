"""Paket topik aritmetika dasar — Fase B, terbatas untuk P5/P6.

Tiga template awal diambil dari malrule yang sudah diprototipekan di
spike/malrule.yaml. Python tetap menghitung parameter, kunci, dan malrule;
ini bukan soal yang ditulis LLM.
"""

from __future__ import annotations

import math
import random
from fractions import Fraction

from templates import Malrule, Soal, saring_malrule
from topics import Topik, daftarkan


def _teks_pecahan(nilai: Fraction) -> str:
    return f"{nilai.numerator}/{nilai.denominator}"


def _kandidat_pecahan(penyebut: tuple[int, ...]) -> list[dict[str, int]]:
    """Semua (n,d) yang menghasilkan soal pecahan dengan diagnosis sehat.

    Syarat yang disaring di sini — hasil positif, hasil tidak bilangan
    bulat, dan keempat jawaban (kunci + 3 malrule) saling berbeda —
    menjaga `saring_malrule` tidak membuang satu jalur pun. Kalau sebuah
    kombinasi parameter membuat K atau H bertabrakan dengan kunci, soal
    yang dihasilkan kehilangan jalur diagnosis tanpa terlihat dari kode.

    Konteks plan 30 Aug 2026 (Fase 0 Task 0.2): versi lama memilih dari 2
    kombinasi hardcoded per level sehingga dua anak beda seed bisa dapat
    soal identik. Sekarang rentangnya lebar dan divalidasi otomatis.
    """
    kandidat: list[dict[str, int]] = []
    for d1 in penyebut:
        for d2 in penyebut:
            for d3 in penyebut:
                if d1 + d2 == d3:
                    continue  # penyebut malrule "terpisah" jadi nol
                for n1 in range(1, d1):
                    for n2 in range(1, d2):
                        for n3 in range(1, d3):
                            pertama = Fraction(n1, d1)
                            kedua = Fraction(n2, d2)
                            ketiga = Fraction(n3, d3)
                            hasil = pertama + kedua - ketiga
                            if hasil <= 0 or hasil.denominator == 1:
                                continue  # hasil harus positif dan pecahan
                            terpisah = Fraction(n1 + n2 - n3, d1 + d2 - d3)
                            satu_unit = Fraction(1, math.lcm(d1, d2, d3))
                            salah_hitung = hasil - satu_unit
                            pertama_kedua = pertama + kedua
                            jawaban = {
                                _teks_pecahan(hasil),
                                _teks_pecahan(terpisah),
                                _teks_pecahan(salah_hitung),
                                _teks_pecahan(pertama_kedua),
                            }
                            if len(jawaban) < 4:
                                continue  # tabrakan — saring_malrule akan buang
                            if (
                                terpisah.denominator == 1
                                or salah_hitung.denominator == 1
                            ):
                                continue  # anak menulis bilangan bulat, bukan pecahan
                            kandidat.append(
                                {
                                    "n1": n1,
                                    "d1": d1,
                                    "n2": n2,
                                    "d2": d2,
                                    "n3": n3,
                                    "d3": d3,
                                }
                            )
    return kandidat


# Dibangun sekali saat impor, lalu dipilih rng per soal. List tetap
# deterministik (bukan hasil rng), jadi seed yang sama tetap menghasilkan
# parameter yang sama persis.
_KANDIDAT_PECAHAN_P5 = _kandidat_pecahan((2, 3, 4, 6))
_KANDIDAT_PECAHAN_P6 = _kandidat_pecahan((3, 4, 5, 6, 8))


def urutan_operasi_1(a: int, b: int, c: int, d: int, e: int) -> Soal:
    """Penjumlahan dan pengurangan dengan kali/bagi di tengah."""
    jawab = a + b // c * d - e
    kiri_ke_kanan = ((a + b) // c) * d - e
    kali_dulu = a + b // (c * d) - e
    mal = [
        Malrule(
            "urutan_operasi.kiri_ke_kanan_tanpa_prioritas",
            str(kiri_ke_kanan),
            "K",
            "mengerjakan lurus dari kiri ke kanan, tidak mendahulukan kali dan bagi",
        ),
        Malrule(
            "urutan_operasi.kali_sebelum_bagi_tanpa_kiri_ke_kanan",
            str(kali_dulu),
            "K",
            "mendahulukan kali atas bagi, padahal kali dan bagi dikerjakan dari kiri ke kanan",
        ),
        Malrule(
            "urutan_operasi.hasil_akhir_kurang_satu",
            str(jawab - 1),
            "H",
            "urutan caranya benar, tetapi pengurangan akhir kurang satu",
        ),
    ]
    return Soal(
        "urutan_operasi_1",
        {"a": a, "b": b, "c": c, "d": d, "e": e},
        f"Hitung: {a} + {b} ÷ {c} × {d} − {e}",
        str(jawab),
        saring_malrule(str(jawab), mal),
        minta_restatement=True,
        pembahasan=(
            f"Langkah: jawaban benar = "
            + str(jawab)
            + ". Cocokkan dengan caramu sendiri, ya."
        ),
        bagian="A",
    )


def fpb_dua_bilangan(a: int, b: int) -> Soal:
    """FPB dua bilangan dengan pembeda eksplisit terhadap KPK."""
    jawab = math.gcd(a, b)
    kpk = math.lcm(a, b)
    mal = [
        Malrule(
            "fpb.tertukar_dengan_kpk",
            str(kpk),
            "B",
            "menjawab KPK padahal yang diminta FPB",
        ),
        Malrule(
            "fpb.faktor_terbesar_kurang_satu",
            str(jawab - 1),
            "H",
            "faktor bersama sudah dicari, tetapi memilih satu angka terlalu kecil",
        ),
        Malrule(
            "fpb.salah_pilih_faktor_bersama",
            str(max(1, jawab // 2)),
            "K",
            "berhenti pada faktor bersama kecil, belum mencari faktor persekutuan terbesar",
        ),
    ]
    return Soal(
        "fpb_dua_bilangan",
        {"a": a, "b": b},
        f"Tentukan FPB dari {a} dan {b}.",
        str(jawab),
        saring_malrule(str(jawab), mal),
        minta_restatement=True,
        pembahasan=(
            f"Langkah: jawaban benar = "
            + str(jawab)
            + ". Cocokkan dengan caramu sendiri, ya."
        ),
        bagian="B",
    )


def pecahan_operasi_campuran(
    n1: int, d1: int, n2: int, d2: int, n3: int, d3: int
) -> Soal:
    """Penjumlahan dan pengurangan tiga pecahan berbeda penyebut."""
    pertama = Fraction(n1, d1)
    kedua = Fraction(n2, d2)
    ketiga = Fraction(n3, d3)
    hasil = pertama + kedua - ketiga
    terpisah = Fraction(n1 + n2 - n3, d1 + d2 - d3)
    satu_unit = Fraction(1, math.lcm(d1, d2, d3))
    salah_hitung = hasil - satu_unit
    mal = [
        Malrule(
            "pecahan.operasi_pembilang_penyebut_terpisah",
            _teks_pecahan(terpisah),
            "K",
            "menjumlahkan pembilang dan penyebut secara terpisah",
        ),
        Malrule(
            "pecahan.pengurangan_pembilang_meleset",
            _teks_pecahan(salah_hitung),
            "H",
            "penyebut sudah disamakan, tetapi pengurangan pembilang kurang satu",
        ),
        Malrule(
            "pecahan.mengabaikan_pengurangan_terakhir",
            _teks_pecahan(pertama + kedua),
            "B",
            "menjawab penjumlahan dua pecahan pertama dan tidak mengurangi pecahan terakhir",
        ),
    ]
    return Soal(
        "pecahan_operasi_campuran",
        {"n1": n1, "d1": d1, "n2": n2, "d2": d2, "n3": n3, "d3": d3},
        f"Hitung: {n1}/{d1} + {n2}/{d2} − {n3}/{d3}",
        _teks_pecahan(hasil),
        saring_malrule(_teks_pecahan(hasil), mal),
        minta_restatement=True,
        pembahasan=(
            f"Langkah: jawaban benar = "
            + str(hasil)
            + ". Cocokkan dengan caramu sendiri, ya."
        ),
        bagian="C",
        tantangan=True,
    )


REGISTRI_TOPIK = {
    "urutan_operasi_1": urutan_operasi_1,
    "fpb_dua_bilangan": fpb_dua_bilangan,
    "pecahan_operasi_campuran": pecahan_operasi_campuran,
}

KOMPOSISI = {
    "P5": (
        "urutan_operasi_1", "fpb_dua_bilangan", "pecahan_operasi_campuran",
        "urutan_operasi_1", "fpb_dua_bilangan", "pecahan_operasi_campuran",
    ),
    "P6": (
        "urutan_operasi_1", "fpb_dua_bilangan", "pecahan_operasi_campuran",
        "urutan_operasi_1", "fpb_dua_bilangan", "pecahan_operasi_campuran",
    ),
}


def _parameter(template_id: str, rng: random.Random, level: str) -> dict[str, int]:
    if template_id == "urutan_operasi_1":
        c, d = rng.choice(((3, 2), (4, 3), (5, 2)))
        pengali = (6, 14) if level == "P5" else (12, 22)
        batas_a = (4, 12) if level == "P5" else (8, 18)
        batas_e = (5, 18) if level == "P5" else (15, 32)
        kandidat = [
            (a_unit, b_unit)
            for a_unit in range(batas_a[0], batas_a[1] + 1)
            for b_unit in range(pengali[0], pengali[1] + 1)
            if (a_unit * d + b_unit * d * d)
            != (a_unit * d + b_unit)
            and (a_unit * d + b_unit * d * d)
            != (a_unit * c + b_unit)
            and (a_unit * d + b_unit * d)
            != (a_unit * c + b_unit)
        ]
        a_unit, b_unit = rng.choice(kandidat)
        return {
            "a": c * a_unit,
            "b": c * d * b_unit,
            "c": c,
            "d": d,
            "e": rng.randint(*batas_e),
        }
    if template_id == "fpb_dua_bilangan":
        faktor = rng.choice(
            (4, 6, 8, 9, 12, 15, 18) if level == "P5" else (12, 15, 18, 20, 24, 30, 36)
        )
        x, y = rng.sample(range(2, 12), 2)
        return {"a": faktor * x, "b": faktor * y}
    if template_id == "pecahan_operasi_campuran":
        kandidat = _KANDIDAT_PECAHAN_P5 if level == "P5" else _KANDIDAT_PECAHAN_P6
        return dict(rng.choice(kandidat))
    raise KeyError(f"template tidak dikenal: {template_id}")


TOPIK = Topik(
    id="aritmetika-dasar",
    nama="Aritmetika Dasar",
    judul_lembar="Latihan Aritmetika Dasar",
    judul_penilaian="Penilaian — Aritmetika Dasar",
    templates=REGISTRI_TOPIK,
    komposisi=KOMPOSISI,
    profil={"P5": {}, "P6": {}},
    judul_bagian={
        "A": "Bagian A — Urutan operasi",
        "B": "Bagian B — Faktor persekutuan",
        "C": "Bagian C — Operasi pecahan",
    },
    catatan_bagian={
        "A": "Kerjakan kali dan bagi lebih dulu. Kalau sama tingkatnya, baca dari kiri ke kanan.",
        "C": "Samakan penyebut sebelum menjumlahkan atau mengurangi pecahan.",
    },
    parameter_untuk=_parameter,
)

daftarkan(TOPIK)
