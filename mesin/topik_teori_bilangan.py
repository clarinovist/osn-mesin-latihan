"""Paket topik teori-bilangan — Fase 3 plan 30 Aug 2026.

8 template menutup cakupan bilangan & teori bilangan OSN SD: keterbagian
(bagian A), KPK & FPB (B), sisa & paritas (C), pola bilangan (D).
Level P4/P5/P6 (P3 tidak didukung).
"""

from __future__ import annotations

import math
import random

from templates import Malrule, Soal, saring_malrule
from topik import Topik, daftarkan


# ── Bagian A — Keterbagian ─────────────────────────────────────────────

# Trap map: d → divisor yang aturannya sering tertukar.
_TRAP: dict[int, int] = {
    2: 3, 3: 2, 4: 2, 5: 3, 6: 2, 8: 4, 9: 3, 11: 9,
}


def _habis(n: int, d: int) -> bool:
    return n % d == 0


def keterbagian(d: int, a: int, b: int, c: int, jawab: int) -> Soal:
    """Dari tiga bilangan, manakah yang habis dibagi d?

    Tepat satu dari a,b,c habis dibagi d (dijamin _parameter). Kunci =
    bilangan itu. Malrule: jawab bilangan tak habis (B), jawab bilangan
    yang habis dibagi trap divisor (K), kurang-1 (H). Kandidat trap
    dicari eksplisit — posisinya setelah shuffle tidak bisa diasumsikan.
    """
    pilihan = (a, b, c)
    kunci = str(pilihan[jawab])
    trap = _TRAP.get(d, d)
    kandidat_trap = [
        x for x in pilihan
        if x != pilihan[jawab] and _habis(x, trap) and not _habis(x, d)
    ]
    trap_num = kandidat_trap[0] if kandidat_trap else pilihan[(jawab + 1) % 3]
    mal = [
        Malrule(
            "keterbagian.pilih_tak_habis",
            str(pilihan[(jawab + 1) % 3]),
            "B",
            f"memilih bilangan yang tidak habis dibagi {d}",
        ),
        Malrule(
            "keterbagian.trap_divisor",
            str(trap_num),
            "K",
            f"memilih bilangan yang hanya habis dibagi {trap} — "
            f"aturan pembagian {d} tidak dipakai dengan benar",
        ),
        Malrule(
            "keterbagian.kurang_satu",
            str(int(kunci) - 1),
            "H",
            "menentukan bilangan yang benar, lalu menguranginya satu",
        ),
    ]
    teks = (
        f"Manakah dari bilangan {a}, {b}, dan {c} yang habis dibagi {d}?"
    )
    return Soal(
        "keterbagian",
        {"d": d, "a": a, "b": b, "c": c, "jawab": jawab},
        teks,
        kunci,
        saring_malrule(kunci, mal),
        minta_restatement=True,
        bagian="A",
    )


def _faktor_prima(n: int) -> dict[int, int]:
    """Faktorisasi prima n -> {prima: eksponen}."""
    hasil: dict[int, int] = {}
    sisa = n
    p = 2
    while p * p <= sisa:
        while sisa % p == 0:
            hasil[p] = hasil.get(p, 0) + 1
            sisa //= p
        p += 1 if p == 2 else 2
    if sisa > 1:
        hasil[sisa] = hasil.get(sisa, 0) + 1
    return hasil


# ── Bagian B — KPK & FPB ───────────────────────────────────────────────


def prima_faktorisasi(n: int) -> Soal:
    """Banyak faktor positif dari n = ∏(eᵢ+1)."""
    faktor = _faktor_prima(n)
    kunci = 1
    for e in faktor.values():
        kunci *= e + 1
    mal = [
        Malrule(
            "prima.jumlah_eksponen",
            str(sum(faktor.values())),
            "K",
            f"menjumlahkan eksponen {sum(faktor.values())} padahal banyak "
            "faktor = hasil kali (eᵢ+1)",
        ),
        Malrule(
            "prima.banyak_prima_beda",
            str(len(faktor)),
            "K",
            f"menghitung banyak faktor prima berbeda ({len(faktor)}) "
            "padahal yang diminta banyak faktor positif",
        ),
        Malrule(
            "prima.kurang_satu",
            str(kunci - 1),
            "H",
            "perhitungan banyak faktor benar, hasilnya meleset satu",
        ),
    ]
    teks = f"Berapa banyak faktor positif dari bilangan {n}?"
    return Soal(
        "prima_faktorisasi",
        {"n": n},
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        bagian="B",
    )


REGISTRI_TOPIK = {
    "keterbagian": keterbagian,
    "prima_faktorisasi": prima_faktorisasi,
}

KOMPOSISI = {
    # P4 (10): 1,5,6 x3 + 1
    "P4": (
        "keterbagian", "sisa_pembagian", "paritas",
        "keterbagian", "sisa_pembagian", "paritas",
        "keterbagian", "sisa_pembagian", "paritas",
        "keterbagian",
    ),
    # P5 (10): 1,2,3,5,6,8,1,2,3,8
    "P5": (
        "keterbagian", "prima_faktorisasi", "kpk_dua_bilangan",
        "sisa_pembagian", "paritas", "gauss_deret",
        "keterbagian", "prima_faktorisasi", "kpk_dua_bilangan",
        "gauss_deret",
    ),
    # P6 (10): 1,2,3,4,5,7,8,1,4,7
    "P6": (
        "keterbagian", "prima_faktorisasi", "kpk_dua_bilangan",
        "fpb_kpk_hubungan", "sisa_pembagian", "angka_satuan_pangkat",
        "gauss_deret", "keterbagian", "fpb_kpk_hubungan",
        "angka_satuan_pangkat",
    ),
}

JUDUL_BAGIAN = {
    "A": "Bagian A — Keterbagian",
    "B": "Bagian B — KPK & FPB",
    "C": "Bagian C — Sisa & paritas",
    "D": "Bagian D — Pola bilangan",
}

CATATAN_BAGIAN = {
    "A": "Pelajari aturan habis dibagi 2, 3, 4, 5, 6, 8, 9, dan 11.",
    "B": "Faktorisasi prima adalah kunci KPK dan FPB.",
    "D": "Jumlah deret punya jalan pintas (rumus Gauss).",
}


def _parameter(template_id: str, rng: random.Random, level: str) -> dict:
    if template_id == "keterbagian":
        # d pool per level; pilih tiga bilangan, tepat satu habis dibagi d.
        if level == "P4":
            pool = (2, 3, 4, 5, 6)
        elif level == "P5":
            pool = (2, 3, 4, 5, 6, 8, 9)
        else:
            pool = (2, 3, 4, 5, 6, 8, 9, 11)
        d = rng.choice(pool)
        trap = _TRAP[d]
        # bilangan benar: kelipatan d (2 digit)
        benar = d * rng.randint(4, 50)
        # bilangan trap: kelipatan trap, tidak habis dibagi d
        trap_num = trap * rng.randint(5, 60)
        while _habis(trap_num, d) or trap_num == benar:
            trap_num = trap * rng.randint(5, 60)
        # bilangan salah: tak habis dibagi d maupun trap (supaya malrule
        # pilih_tak_habis dan trap_divisor tidak menebak bilangan sama)
        salah = benar + 1
        while _habis(salah, d) or _habis(salah, trap) or salah == benar:
            salah += 1
        return {"d": d, "a": benar, "b": salah, "c": trap_num, "jawab": 0}
    if template_id == "prima_faktorisasi":
        # n acak rentang lebar: berapa pun n, faktorisasinya dihitung di
        # template (banyak faktor positif = ∏(eᵢ+1)). P5 lebih kecil.
        if level == "P5":
            return {"n": rng.randint(12, 2000)}
        return {"n": rng.randint(12, 5000)}
    raise KeyError(f"template tidak dikenal: {template_id}")


TOPIK = Topik(
    id="teori-bilangan",
    nama="Teori Bilangan",
    judul_lembar="Latihan Teori Bilangan",
    judul_penilaian="Penilaian — Teori Bilangan",
    templates=REGISTRI_TOPIK,
    komposisi=KOMPOSISI,
    profil={"P4": {}, "P5": {}, "P6": {}},
    judul_bagian=JUDUL_BAGIAN,
    catatan_bagian=CATATAN_BAGIAN,
    parameter_untuk=_parameter,
)

daftarkan(TOPIK)