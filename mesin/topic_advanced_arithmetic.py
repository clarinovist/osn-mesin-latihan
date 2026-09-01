"""Paket topik aritmatika-lanjut — Fase 4 plan 30 Aug 2026.

11 template menutup cakupan aritmatika terapan OSN SD: konversi satuan
& kecepatan (bagian A), perbandingan (B), kerja sama (C), persen (D).
Level P5/P6 (P3/P4 tidak didukung).
"""

from __future__ import annotations

import random

from templates import Malrule, Soal, saring_malrule
from topics import Topik, daftarkan


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
        pembahasan=(
            f"Langkah: jawaban benar = "
            + str(kunci)
            + ". Perhatikan malrule di halaman koreksi."
        ),
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
        pembahasan=(
            f"Langkah: jawaban benar = "
            + str(kunci)
            + ". Perhatikan malrule di halaman koreksi."
        ),
        bagian="A",
    )


def berpapasan(jarak: int, v1: int, v2: int) -> Soal:
    """Waktu bertemu dua kendaraan saling berhadapan = jarak/(v1+v2)."""
    kunci = jarak // (v1 + v2)
    mal = [
        Malrule("berpapasan.jumlah_kecepatan", str(v1 + v2), "K", "menjawab jumlah kecepatan, bukan waktu bertemu"),
        Malrule("berpapasan.dikali_kecepatan", str(jarak // (v1 * v2)) if jarak % (v1 * v2) == 0 else str(v1 * v2), "K", "mengalikan dua kecepatan padahal waktu = jarak/(v1+v2)"),
        Malrule("berpapasan.kurang_satu", str(kunci - 1), "H", "perhitungan benar, hasilnya meleset satu"),
    ]
    teks = (
        f"Jarak kota A dan B {jarak} km. Mobil dari A melaju {v1} km/jam "
        f"dan dari B melaju {v2} km/jam, saling berhadapan. Berapa jam "
        f"mereka akan berpapasan?"
    )
    return Soal(
        "berpapasan",
        {"jarak": jarak, "v1": v1, "v2": v2},
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        pembahasan=(
            f"Langkah: jawaban benar = "
            + str(kunci)
            + ". Perhatikan malrule di halaman koreksi."
        ),
        bagian="A",
    )


def menyusul(jarak: int, v1: int, v2: int) -> Soal:
    """Waktu menyusul = jarak_awal/(v2−v1), v2 > v1."""
    kunci = jarak // (v2 - v1)
    k1 = v2 - v1
    k2 = jarak // (v1 + v2)
    h = kunci - 1
    # jaga supaya K tidak menabrak kunci atau H (setelah saring)
    if k1 == kunci or k1 == h:
        k1 = kunci + 1
    if k2 == kunci or k2 == h or k2 == k1:
        k2 = kunci + 2
    mal = [
        Malrule("menyusul.kurang_satu", str(h), "H", "perhitungan benar, hasilnya meleset satu"),
        Malrule("menyusul.selisih_kecepatan", str(k1), "K", "menjawab selisih kecepatan, bukan waktu menyusul"),
        Malrule("menyusul.dikira_berpapasan", str(k2), "K", "memakai rumus berpapasan (v1+v2) padahal yang satu mengejar"),
    ]
    teks = (
        f"Sepeda motor dari A melaju {v2} km/jam mengejar mobil yang sudah "
        f"berjalan {v1} km/jam dan unggul {jarak} km. Berapa jam waktu "
        f"yang dibutuhkan untuk menyusul?"
    )
    return Soal(
        "menyusul",
        {"jarak": jarak, "v1": v1, "v2": v2},
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        pembahasan=(
            f"Langkah: jawaban benar = "
            + str(kunci)
            + ". Perhatikan malrule di halaman koreksi."
        ),
        bagian="A",
    )


def debit(varian: str, volume: int, waktu: int, d: int) -> Soal:
    """Debit = volume/waktu; dua arah (cari volume atau waktu)."""
    if varian == "cari_debit":
        kunci = volume // waktu
        teks = f"Volume {volume} liter mengalir dalam {waktu} menit. Berapa debitnya (liter/menit)?"
        salah = volume * waktu
    elif varian == "cari_volume":
        kunci = d * waktu
        teks = f"Debit {d} liter/menit selama {waktu} menit. Berapa volume yang mengalir (liter)?"
        salah = d + waktu
    else:
        kunci = volume // d
        teks = f"Volume {volume} liter dengan debit {d} liter/menit. Berapa waktu (menit)?"
        salah = volume * d
    if salah == kunci:
        salah = kunci + 1
    mal = [
        Malrule("debit.salah_rumus", str(salah), "K", "memakai rumus yang salah untuk besaran yang diminta"),
        Malrule("debit.lupa_bagi", str(volume // d if varian == "cari_volume" else d * waktu if varian == "cari_waktu" else volume), "K", "lupa membagi/mengalikan dengan waktu"),
        Malrule("debit.kurang_satu", str(kunci - 1), "H", "perhitungan benar, hasilnya meleset satu"),
    ]
    return Soal(
        "debit",
        {"varian": varian, "volume": volume, "waktu": waktu, "debit": d},
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        pembahasan=(
            f"Langkah: jawaban benar = "
            + str(kunci)
            + ". Perhatikan malrule di halaman koreksi."
        ),
        bagian="A",
    )


def perbandingan_senilai(p: int, q: int, n: int) -> Soal:
    """p:q = n:x → x = q·n/p. Senilai (searah)."""
    kunci = (q * n + p - 1) // p
    h = kunci - 1
    k = (p * n + q - 1) // q
    if k == kunci or k == h:
        k = kunci + 1
    mal = [
        Malrule("senilai.kurang_satu", str(h), "H", "perhitungan benar, hasilnya meleset satu"),
        Malrule("senilai.terbalik", str(k), "K", "perbandingan dibalik — senilai searah, bukan kebalikan"),
        Malrule("senilai.selisih", str(abs(q - p)), "B", "menjawab selisih pembanding, bukan nilai yang dicari"),
    ]
    teks = (
        f"Perbandingan {p} : {q}. Jika bagian pertama nilainya {n}, "
        f"berapa nilai bagian kedua?"
    )
    return Soal(
        "perbandingan_senilai",
        {"p": p, "q": q, "n": n},
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        pembahasan=(
            f"Langkah: jawaban benar = "
            + str(kunci)
            + ". Perhatikan malrule di halaman koreksi."
        ),
        bagian="B",
    )


def perbandingan_berbalik(a1: int, b1: int, a2: int) -> Soal:
    """a1·b1 = a2·b2 → b2 = a1·b1/a2. Berbalik (kebalikan)."""
    kunci = (a1 * b1 + a2 - 1) // a2
    h = kunci - 1
    k = (a2 * b1 + a1 - 1) // a1
    if k == kunci or k == h:
        k = kunci + 1
    mal = [
        Malrule("berbalik.kurang_satu", str(h), "H", "perhitungan benar, hasilnya meleset satu"),
        Malrule("berbalik.terbalik", str(k), "K", "memakai perbandingan senilai padahal ini berbalik nilai"),
        Malrule("berbalik.jumlah", str(a1 + b1), "B", "menjumlahkan dua besaran, padahal yang dicari hasil kali dibagi"),
    ]
    teks = (
        f"Jika {a1} pekerja dapat menyelesaikan pekerjaan dalam {b1} hari, "
        f"berapa hari waktu {a2} pekerja (semakin banyak semakin cepat)?"
    )
    return Soal(
        "perbandingan_berbalik",
        {"a1": a1, "b1": b1, "a2": a2},
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        pembahasan=(
            f"Langkah: jawaban benar = "
            + str(kunci)
            + ". Perhatikan malrule di halaman koreksi."
        ),
        bagian="B",
    )


def kerja_bersama(a: int, b: int) -> Soal:
    """Waktu bersama = a·b/(a+b)."""
    kunci = (a * b + a + b - 1) // (a + b)
    mal = [
        Malrule("kerja.jumlah_waktu", str(a + b), "K", "menjumlahkan dua waktu, padahal waktu bersama = a·b/(a+b)"),
        Malrule("kerja.kali_waktu", str(a * b), "K", "mengalikan dua waktu, padahal harus dibagi jumlahnya"),
        Malrule("kerja.kurang_satu", str(kunci - 1), "H", "perhitungan benar, hasilnya meleset satu"),
    ]
    teks = (
        f"Alif dapat menyelesaikan pekerjaan dalam {a} jam, Budi dalam {b} "
        f"jam. Jika bekerja bersama, berapa jam waktu yang dibutuhkan?"
    )
    return Soal(
        "kerja_bersama",
        {"a": a, "b": b},
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        pembahasan=(
            f"Langkah: jawaban benar = "
            + str(kunci)
            + ". Perhatikan malrule di halaman koreksi."
        ),
        bagian="C",
    )


def persen_diskon(harga: int, d: int) -> Soal:
    """Harga setelah diskon d% = harga·(100−d)/100."""
    kunci = harga * (100 - d) // 100
    diskon = harga * d // 100
    mal = [
        Malrule("diskon.jumlah_diskon", str(diskon), "K", f"menjawab besar diskon {diskon}, bukan harga setelah diskon"),
        Malrule("diskon.lupa_persen", str(harga * (100 - d)), "K", "lupa membagi 100 — menghitung (100−d)% dari harga"),
        Malrule("diskon.kurang_satu", str(kunci - 1), "H", "perhitungan benar, hasilnya meleset satu"),
    ]
    teks = (
        f"Harga sepatu {harga} rupiah mendapat diskon {d}%. "
        f"Berapa harga setelah diskon?"
    )
    return Soal(
        "persen_diskon",
        {"harga": harga, "d": d},
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        pembahasan=(
            f"Langkah: jawaban benar = "
            + str(kunci)
            + ". Perhatikan malrule di halaman koreksi."
        ),
        bagian="D",
    )


def persen_untung_rugi(jenis: str, modal: int, persen: int) -> Soal:
    """Harga jual = modal·(100±persen)/100 (untung/rugi)."""
    if jenis == "untung":
        kunci = modal * (100 + persen) // 100
        teks = f"Sebuah barang dibeli {modal} rupiah lalu dijual untung {persen}%. Berapa harga jualnya?"
    else:
        kunci = modal * (100 - persen) // 100
        teks = f"Sebuah barang dibeli {modal} rupiah lalu dijual rugi {persen}%. Berapa harga jualnya?"
    laba = modal * persen // 100
    mal = [
        Malrule("untung.laba_saja", str(laba), "K", f"menjawab besar untung/rugi {laba}, bukan harga jual"),
        Malrule("untung.lupa_persen", str(modal * (100 + persen) if jenis == "untung" else modal * (100 - persen)), "K", "lupa membagi 100"),
        Malrule("untung.kurang_satu", str(kunci - 1), "H", "perhitungan benar, hasilnya meleset satu"),
    ]
    return Soal(
        "persen_untung_rugi",
        {"jenis": jenis, "modal": modal, "persen": persen},
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        pembahasan=(
            f"Langkah: jawaban benar = "
            + str(kunci)
            + ". Perhatikan malrule di halaman koreksi."
        ),
        bagian="D",
    )


def persen_bertingkat(harga: int, d1: int, d2: int) -> Soal:
    """Diskon ganda: harga·(1−d1/100)·(1−d2/100)."""
    kunci = harga * (100 - d1) * (100 - d2) // 10000
    mal = [
        Malrule("bertingkat.jumlah_diskon", str(harga * (100 - d1 - d2) // 100), "K", "menjumlahkan dua diskon — diskon ganda tidak bisa dijumlah begitu saja"),
        Malrule("bertingkat.diskon_pertama", str(harga * (100 - d1) // 100), "K", "hanya menghitung diskon pertama, diskon kedua dilupakan"),
        Malrule("bertingkat.kurang_satu", str(kunci - 1), "H", "perhitungan benar, hasilnya meleset satu"),
    ]
    teks = (
        f"Harga baju {harga} rupiah didiskon {d1}%, lalu didiskon lagi "
        f"{d2}%. Berapa harga akhirnya?"
    )
    return Soal(
        "persen_bertingkat",
        {"harga": harga, "d1": d1, "d2": d2},
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        pembahasan=(
            f"Langkah: jawaban benar = "
            + str(kunci)
            + ". Perhatikan malrule di halaman koreksi."
        ),
        bagian="D",
    )


REGISTRI_TOPIK = {
    "satuan_konversi": satuan_konversi,
    "kecepatan_jarak_waktu": kecepatan_jarak_waktu,
    "berpapasan": berpapasan,
    "menyusul": menyusul,
    "debit": debit,
    "perbandingan_senilai": perbandingan_senilai,
    "perbandingan_berbalik": perbandingan_berbalik,
    "kerja_bersama": kerja_bersama,
    "persen_diskon": persen_diskon,
    "persen_untung_rugi": persen_untung_rugi,
    "persen_bertingkat": persen_bertingkat,
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
    if template_id == "berpapasan":
        # jarak kelipatan (v1+v2) supaya kunci bulat
        v1, v2 = rng.randint(20, 60), rng.randint(20, 60)
        jarak = (v1 + v2) * rng.randint(1, 4)
        return {"jarak": jarak, "v1": v1, "v2": v2}
    if template_id == "menyusul":
        # v2 > v1; jarak kelipatan selisih supaya kunci bulat
        v1, v2 = rng.randint(20, 50), rng.randint(40, 80)
        while v2 <= v1:
            v2 = rng.randint(40, 80)
        jarak = (v2 - v1) * rng.randint(1, 5)
        return {"jarak": jarak, "v1": v1, "v2": v2}
    if template_id == "debit":
        varian = rng.choice(("cari_debit", "cari_volume", "cari_waktu"))
        if varian == "cari_debit":
            volume = rng.randint(10, 500)
            waktu = rng.randint(1, 30)
            while volume % waktu != 0:
                volume = rng.randint(10, 500)
            return {"varian": varian, "volume": volume, "waktu": waktu, "d": volume // waktu}
        if varian == "cari_volume":
            d, waktu = rng.randint(2, 30), rng.randint(1, 30)
            return {"varian": varian, "volume": d * waktu, "waktu": waktu, "d": d}
        # cari_waktu
        volume = rng.randint(10, 500)
        d = rng.randint(2, 30)
        while volume % d != 0:
            volume = rng.randint(10, 500)
        return {"varian": varian, "volume": volume, "waktu": volume // d, "d": d}
    if template_id == "perbandingan_senilai":
        p, q = rng.randint(1, 10), rng.randint(1, 10)
        while p == q:
            q = rng.randint(1, 10)
        n = rng.randint(1, 20)
        return {"p": p, "q": q, "n": n}
    if template_id == "perbandingan_berbalik":
        a1, b1, a2 = rng.randint(2, 10), rng.randint(2, 10), rng.randint(2, 10)
        while a2 == a1:
            a2 = rng.randint(2, 10)
        return {"a1": a1, "b1": b1, "a2": a2}
    if template_id == "kerja_bersama":
        a, b = rng.randint(2, 24), rng.randint(2, 24)
        while a == b:
            b = rng.randint(2, 24)
        return {"a": a, "b": b}
    if template_id == "persen_diskon":
        # harga kelipatan 100 supaya hasil bulat
        harga = 100 * rng.randint(2, 5000)
        d = rng.randint(5, 50)
        return {"harga": harga, "d": d}
    if template_id == "persen_untung_rugi":
        jenis = rng.choice(("untung", "rugi"))
        modal = 100 * rng.randint(2, 5000)
        persen = rng.randint(5, 40)
        return {"jenis": jenis, "modal": modal, "persen": persen}
    if template_id == "persen_bertingkat":
        harga = 10000 * rng.randint(1, 500)
        d1, d2 = rng.randint(5, 40), rng.randint(5, 40)
        return {"harga": harga, "d1": d1, "d2": d2}
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