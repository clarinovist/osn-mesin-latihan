"""Paket topik kombinatorik — Fase 2 plan 30 Aug 2026.

11 template menutup cakupan kombinatorik OSN SD: aturan mencacah (bagian A),
susunan angka (B), permutasi & kombinasi (C), penerapan (D). Level P5/P6
(P3/P4 tidak didukung). Soal berbentuk teks dulu (keputusan pengguna #2);
diagram pohon/petak/Venn adalah penyempurnaan `render_badan` belakangan.
"""

from __future__ import annotations

import math
import random

from templates import Malrule, Soal, saring_malrule
from topik import Topik, daftarkan


# ── Bagian A — Aturan mencacah ─────────────────────────────────────────


def aturan_tambah(m: int, n: int) -> Soal:
    """Aturan penjumlahan: m + n cara (mutually exclusive)."""
    kunci = m + n
    mal = [
        Malrule(
            "aturan_tambah.dikira_kali",
            str(m * n),
            "K",
            "mengalikan m dan n padahal aturan penjumlahan (pilihan saling lepas)",
        ),
        Malrule(
            "aturan_tambah.hanya_satu",
            str(m),
            "B",
            "hanya menghitung pilihan A, pilihan B tidak dijumlahkan",
        ),
        Malrule(
            "aturan_tambah.kurang_satu",
            str(kunci - 1),
            "H",
            "penjumlahan benar, hasilnya meleset satu",
        ),
    ]
    teks = (
        f"Di toko buku, ada {m} buku cerita dan {n} buku pelajaran. "
        f"Budi ingin membeli satu buku. Berapa banyak pilihan buku yang "
        f"dimiliki Budi?"
    )
    return Soal(
        "aturan_tambah",
        {"m": m, "n": n},
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        bagian="A",
    )


def aturan_kali(m: int, n: int) -> Soal:
    """Aturan perkalian: m × n cara (pilihan berurutan)."""
    kunci = m * n
    mal = [
        Malrule(
            "aturan_kali.dikira_tambah",
            str(m + n),
            "K",
            "menjumlahkan m dan n padahal aturan perkalian (pilihan berurutan)",
        ),
        Malrule(
            "aturan_kali.hanya_kedua",
            str(n),
            "B",
            "hanya menghitung pilihan kedua, pilihan pertama tidak diperhitungkan",
        ),
        Malrule(
            "aturan_kali.kurang_satu",
            str(kunci - 1),
            "H",
            "perkalian benar, hasilnya meleset satu",
        ),
    ]
    teks = (
        f"Di toko, ada {m} jenis roti dan {n} jenis selai. "
        f"Budi ingin memilih satu roti dan satu selai untuk sarapan. "
        f"Berapa banyak pilihan menu yang dimiliki Budi?"
    )
    return Soal(
        "aturan_kali",
        {"m": m, "n": n},
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        bagian="A",
    )


REGISTRI_TOPIK = {
    "aturan_tambah": aturan_tambah,
    "aturan_kali": aturan_kali,
}

KOMPOSISI = {
    # P5 (10 soal): 1, 2, 3, 4, 8, 11, 2, 3, 8, 11
    "P5": (
        "aturan_tambah",
        "aturan_kali",
        "susun_bilangan",
        "susun_bilangan_syarat",
        "jabat_tangan",
        "inklusi_eksklusi_2",
        "aturan_kali",
        "susun_bilangan",
        "jabat_tangan",
        "inklusi_eksklusi_2",
    ),
    # P6 (10 soal): 5, 6, 7, 9, 10, 4, 11, 5, 7, 9
    "P6": (
        "permutasi_urutan",
        "permutasi_blok",
        "kombinasi_pilih",
        "jalur_petak",
        "sarang_merpati",
        "susun_bilangan_syarat",
        "inklusi_eksklusi_2",
        "permutasi_urutan",
        "kombinasi_pilih",
        "jalur_petak",
    ),
}

JUDUL_BAGIAN = {
    "A": "Bagian A — Aturan mencacah",
    "B": "Bagian B — Susunan angka",
    "C": "Bagian C — Permutasi & kombinasi",
    "D": "Bagian D — Penerapan",
}

CATATAN_BAGIAN = {
    "A": "Baca dulu: pilihan saling lepas (tambah) atau berurutan (kali)?",
    "B": "0 tidak boleh di depan, kecuali di susunan khusus.",
    "C": "Urutan penting (permutasi) atau tidak (kombinasi)?",
    "D": "Rumusnya sering beda dari yang kelihatan.",
}


def _parameter(template_id: str, rng: random.Random, level: str) -> dict:
    if template_id == "aturan_tambah":
        m, n = rng.randint(2, 30), rng.randint(2, 30)
        while m == n:
            n = rng.randint(2, 30)
        return {"m": m, "n": n}
    if template_id == "aturan_kali":
        m, n = rng.randint(2, 20), rng.randint(2, 20)
        while m == n:
            n = rng.randint(2, 20)
        return {"m": m, "n": n}
    raise KeyError(f"template tidak dikenal: {template_id}")


TOPIK = Topik(
    id="kombinatorik",
    nama="Kombinatorik",
    judul_lembar="Latihan Kombinatorik",
    judul_penilaian="Penilaian — Kombinatorik",
    templates=REGISTRI_TOPIK,
    komposisi=KOMPOSISI,
    profil={"P5": {}, "P6": {}},
    judul_bagian=JUDUL_BAGIAN,
    catatan_bagian=CATATAN_BAGIAN,
    parameter_untuk=_parameter,
)

daftarkan(TOPIK)