"""Paket topik aritmatika-lanjut — Fase 4 plan 30 Aug 2026.

11 template menutup cakupan aritmatika terapan OSN SD: konversi satuan
& kecepatan (bagian A), perbandingan (B), kerja sama (C), persen (D).
Level P5/P6 (P3/P4 tidak didukung).
"""

from __future__ import annotations

import random

from templates import Malrule, Soal, saring_malrule
from topik import Topik, daftarkan


# ── Bagian A — Konversi & kecepatan ────────────────────────────────────


def satuan_konversi(varian: str, nilai: int) -> Soal:
    """Konversi satuan: km↔m, jam↔menit, kg↔g, liter↔ml.

    Varian: "km_ke_m", "m_ke_km", "jam_ke_menit", "menit_ke_jam",
    "kg_ke_g", "g_ke_kg", "liter_ke_ml", "ml_ke_liter".
    """
    faktor = {
        "km_ke_m": 1000, "m_ke_km": 0.001,
        "jam_ke_menit": 60, "menit_ke_jam": 1/60,
        "kg_ke_g": 1000, "g_ke_kg": 0.001,
        "liter_ke_ml": 1000, "ml_ke_liter": 0.001,
    }
    tabel = {
        "km_ke_m": ("km", "m", "×", 1000),
        "m_ke_km": ("m", "km", "÷", 1000),
        "jam_ke_menit": ("jam", "menit", "×", 60),
        "menit_ke_jam": ("menit", "jam", "÷", 60),
        "kg_ke_g": ("kg", "g", "×", 1000),
        "g_ke_kg": ("g", "kg", "÷", 1000),
        "liter_ke_ml": ("liter", "ml", "×", 1000),
        "ml_ke_liter": ("ml", "liter", "÷", 1000),
    }
    src, dst, op, factor = tabel[varian]
    if op == "×":
        kunci = nilai * factor
        mal = [
            Malrule("konversi.salah_arah", str(nilai // factor), "K", f"membagi {nilai} dengan {factor} padahal {src}→{dst} dikali"),
            Malrule("konversi.lupa_faktor", str(nilai), "K", "tidak mengubah nilai — lupa faktor konversi"),
            Malrule("konversi.kurang_satu", str(kunci - 1), "H", "konversi benar, hasilnya meleset satu"),
        ]
    else:
        if nilai % factor != 0:
            kunci = nilai // factor  # integer division
        else:
            kunci = nilai // factor
        mal = [
            Malrule("konversi.salah_arah", str(nilai * factor), "K", f"mengali {nilai} dengan {factor} padahal {src}→{dst} dibagi"),
            Malrule("konversi.lupa_faktor", str(nilai), "K", "tidak mengubah nilai — lupa faktor konversi"),
            Malrule("konversi.kurang_satu", str(kunci - 1), "H", "konversi benar, hasilnya meleset satu"),
        ]
    teks = f"Konversikan {nilai} {src} ke {dst}."
    return Soal(
        "satuan_konversi",
        {"varian": varian, "nilai": nilai},
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        bagian="A",
    )


def kecepatan_jarak_waktu(varian: str, s: int, t: int, v: int) -> Soal:
    """v = s/t; dua arah: cari v, s, atau t. Semua bilangan bulat."""
    if varian == "cari_v":
        kunci = s // t
        teks = f"Jarak {s} km ditempuh dalam {t} jam. Berapa kecepatan rata-rata (km/jam)?"
        terbalik = t // s if s > 0 else t  # t/s salah arah
        salah_rumus = s * t
    elif varian == "cari_s":
        kunci = v * t
        teks = f"Kecepatan {v} km/jam selama {t} jam. Berapa jarak yang ditempuh (km)?"
        terbalik = v // t if t > 0 else v  # v/t salah arah
        salah_rumus = v + t
    else:
        kunci = s // v
        teks = f"Jarak {s} km ditempuh dengan kecepatan {v} km/jam. Berapa waktu tempuh (jam)?"
        terbalik = v // s if s > 0 else v  # v/s salah arah
        salah_rumus = s * v
    # jaga supaya malrule tidak menebak kunci
    if terbalik == kunci:
        terbalik = kunci + 1
    if salah_rumus == kunci:
        salah_rumus = kunci + 1
    mal = [
        Malrule("kec.t_terbalik", str(terbalik), "K", "rumus terbalik — membagi yang seharusnya dikali/dikali yang seharusnya dibagi"),
        Malrule("kec.salah_rumus", str(salah_rumus), "K", "memakai rumus yang salah untuk besaran yang diminta"),
        Malrule("kec.kurang_satu", str(kunci - 1), "H", "perhitungan benar, hasilnya meleset satu"),
    ]
    return Soal(
        "kecepatan_jarak_waktu",
        {"varian": varian, "s": s, "t": t, "v": v},
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        bagian="A",
    )


REGISTRI_TOPIK = {
    "satuan_konversi": satuan_konversi,
    "kecepatan_jarak_waktu": kecepatan_jarak_waktu,
}

KOMPOSISI = {
    "P5": (
        "satuan_konversi", "kecepatan_jarak_waktu",
        "debit", "perbandingan_senilai", "perbandingan_berbalik",
        "kerja_bersama", "persen_diskon",
        "satuan_konversi", "kecepatan_jarak_waktu", "persen_diskon",
    ),
    "P6": (
        "berpapasan", "menyusul",
        "perbandingan_senilai", "perbandingan_berbalik",
        "kerja_bersama", "persen_untung_rugi", "persen_bertingkat",
        "satuan_konversi", "kecepatan_jarak_waktu", "debit",
    ),
}

JUDUL_BAGIAN = {
    "A": "Bagian A — Konversi & kecepatan",
    "B": "Bagian B — Perbandingan",
    "C": "Bagian C — Kerja sama",
    "D": "Bagian D — Persen",
}

CATATAN_BAGIAN = {
    "A": "Baca dulu: km→m ×1000, jam→menit ×60, dst.",
    "B": "Senilai = searah, berbalik = kebalikan.",
    "C": "Waktu bersama = hasil kali dibagi jumlah: a×b/(a+b).",
    "D": "Diskon: harga×(100−d)%. Untung/rugi: dari modal.",
}


def _parameter(template_id: str, rng: random.Random, level: str) -> dict:
    if template_id == "satuan_konversi":
        varian = rng.choice((
            "km_ke_m", "m_ke_km", "jam_ke_menit", "menit_ke_jam",
            "kg_ke_g", "g_ke_kg", "liter_ke_ml", "ml_ke_liter",
        ))
        if varian in ("m_ke_km", "menit_ke_jam", "g_ke_kg", "ml_ke_liter"):
            # konversi bagi: pilih nilai kelipatan faktor
            faktor = {"m_ke_km": 1000, "menit_ke_jam": 60, "g_ke_kg": 1000, "ml_ke_liter": 1000}[varian]
            nilai = faktor * rng.randint(1, 500)
        else:
            nilai = rng.randint(1, 500)
        return {"varian": varian, "nilai": nilai}
    if template_id == "kecepatan_jarak_waktu":
        varian = rng.choice(("cari_v", "cari_s", "cari_t"))
        if varian == "cari_v":
            s = rng.randint(10, 500)
            t = rng.randint(1, 10)
            while s % t != 0:
                s = rng.randint(10, 500)
            return {"varian": varian, "s": s, "t": t, "v": s // t}
        if varian == "cari_s":
            v = rng.randint(2, 60)
            t = rng.randint(1, 10)
            return {"varian": varian, "s": v * t, "t": t, "v": v}
        # cari_t
        s = rng.randint(10, 500)
        v = rng.randint(2, 60)
        while s % v != 0:
            s = rng.randint(10, 500)
        return {"varian": varian, "s": s, "t": s // v, "v": v}
    raise KeyError(f"template tidak dikenal: {template_id}")


TOPIK = Topik(
    id="aritmatika-lanjut",
    nama="Aritmatika Lanjut",
    judul_lembar="Latihan Aritmatika Lanjut",
    judul_penilaian="Penilaian — Aritmatika Lanjut",
    templates=REGISTRI_TOPIK,
    komposisi=KOMPOSISI,
    profil={"P5": {}, "P6": {}},
    judul_bagian=JUDUL_BAGIAN,
    catatan_bagian=CATATAN_BAGIAN,
    parameter_untuk=_parameter,
)

daftarkan(TOPIK)