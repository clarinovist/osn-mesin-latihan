"""Paket topik statistika — Fase 6 plan 30 Aug 2026.

Lima template menutup cakupan statistika & pengukuran OSN SD: rata-rata
(bagian A), median & modus, diagram lingkaran dan batang/garis (B).
Level P3-P6; P3 selaras band SASMO Primary 1-4 (statistics) — cukup modus
dan pembacaan diagram batang, median & rata-rata menunggu P4+. Soal
berbentuk teks; diagram dirender sebagai deskripsi data (SVG adalah
penyempurnaan render_badan belakangan).
"""

from __future__ import annotations

import random

from templates import Malrule, Soal, saring_malrule
from topics import Topik, daftarkan


# ── Bagian A — Rata-rata ────────────────────────────────────────────────


def rata_rata(varian: str, data: list[int], rata: int = 0) -> Soal:
    """Rata-rata = jumlah/n; dua arah (cari rata atau cari data ke-n)."""
    n = len(data)
    jumlah = sum(data)
    if varian == "cari_rata":
        kunci = str(jumlah // n)
        teks = f"Data: {', '.join(str(x) for x in data)}. Berapa rata-ratanya?"
        k_jumlah = str(jumlah)  # lupa bagi n
        k_salah_n = str(jumlah // (n + 1))  # salah n
        mal = [
            Malrule("rata.jumlah_saja", k_jumlah, "K", "menjumlahkan data tanpa membagi banyak data"),
            Malrule("rata.salah_n", k_salah_n, "K", "membagi dengan banyak data yang salah"),
            Malrule("rata.kurang_satu", str(int(kunci) - 1), "H", "perhitungan benar, hasilnya meleset satu"),
        ]
        param = {"varian": varian, "data": data}
    else:
        # cari_data_ke_n: data terakhir sudah dihitung di _parameter
        kunci = str(data[-1])
        teks = (
            f"Rata-rata {n} data adalah {rata}. Jika {n-1} data pertama adalah "
            f"{', '.join(str(x) for x in data[:-1])}, berapa data terakhirnya?"
        )
        k_total = str(rata * n)  # lupa kurangi jumlah
        k_salah = str(data[-1] + 1)
        mal = [
            Malrule("rata.total_saja", k_total, "K", "menghitung total semua data tanpa mencari data terakhir"),
            Malrule("rata.kurang_satu_data", k_salah, "K", "melakukan perhitungan yang salah pada data terakhir"),
            Malrule("rata.kurang_satu", str(int(kunci) - 1), "H", "perhitungan benar, hasilnya meleset satu"),
        ]
        param = {"varian": varian, "data": data, "rata": rata}
    return Soal(
        "rata_rata",
        param,
        teks,
        kunci,
        saring_malrule(kunci, mal),
        minta_restatement=True,
        bagian="A",
    )


def rata_rata_gabungan(n1: int, n2: int, x1: int, x2: int) -> Soal:
    """Rata gabung = (n₁·x̄₁ + n₂·x̄₂)/(n₁+n₂)."""
    total1 = n1 * x1
    total2 = n2 * x2
    kunci = (total1 + total2) // (n1 + n2)
    h = kunci - 1
    k1 = total1 + total2  # lupa bagi total
    k2 = (x1 + x2) // 2  # rata dua rata-rata
    if k1 == kunci or k1 == h:
        k1 = kunci + 1
    if k2 == kunci or k2 == h or k2 == k1:
        k2 = kunci + 2
    mal = [
        Malrule("gabung.total_saja", str(k1), "K", "menjumlahkan total kedua kelompok tanpa membagi"),
        Malrule("gabung.rata_rata_rata", str(k2), "K", "merata-ratakan dua rata-rata tanpa memperhitungkan jumlah data"),
        Malrule("gabung.kurang_satu", str(h), "H", "perhitungan benar, hasilnya meleset satu"),
    ]
    teks = (
        f"Kelompok A: {n1} anak dengan rata-rata {x1}. Kelompok B: {n2} anak "
        f"dengan rata-rata {x2}. Berapa rata-rata gabungan keduanya?"
    )
    return Soal(
        "rata_rata_gabungan",
        {"n1": n1, "n2": n2, "x1": x1, "x2": x2},
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        minta_restatement=True,
        bagian="A",
    )


# ── Bagian B — Median & modus, diagram ─────────────────────────────────


def median_modus(varian: str, data: list[int]) -> Soal:
    """Median = nilai tengah data urut; modus = nilai paling sering."""
    n = len(data)
    urut = sorted(data)
    if varian == "median":
        if n % 2 == 1:
            kunci = urut[n // 2]
            k_tengah = data[n // 2]  # tengah tanpa urut
        else:
            kunci = (urut[n // 2 - 1] + urut[n // 2]) // 2
            k_tengah = (data[n // 2 - 1] + data[n // 2]) // 2  # tanpa urut
        k_terkecil = urut[0]
        h = kunci - 1
        if k_tengah == kunci or k_tengah == h:
            k_tengah = kunci + 1
        if k_terkecil == kunci or k_terkecil == h or k_terkecil == k_tengah:
            k_terkecil = kunci + 2
        if h == k_tengah or h == k_terkecil:
            h = kunci + 1
        mal = [
            Malrule("median.tanpa_urut", str(k_tengah), "K", "mengambil nilai tengah tanpa mengurutkan data"),
            Malrule("median.terkecil", str(k_terkecil), "K", "menjawab data terkecil, bukan median"),
            Malrule("median.kurang_satu", str(h), "H", "perhitungan benar, hasilnya meleset satu"),
        ]
        teks = f"Data: {', '.join(str(x) for x in data)}. Berapa mediannya?"
        param = {"varian": varian, "data": data}
    else:
        # modus: nilai paling sering muncul
        from collections import Counter
        hitung = Counter(data)
        modus = max(hitung.items(), key=lambda kv: kv[1])[0]
        kunci = str(modus)
        # malrule: nilai pertama, nilai terbanyak kedua (bila ada)
        k_pertama = str(data[0])
        if k_pertama == kunci:
            k_pertama = str(int(kunci) + 1)
        urut_modus = sorted(hitung, key=lambda x: -hitung[x])
        kedua = urut_modus[1] if len(urut_modus) > 1 and hitung[urut_modus[1]] != hitung[urut_modus[0]] else int(kunci) + 2
        h = int(kunci) - 1
        # jaga H tidak bertabrakan dengan K (saring_malrule membuang duplikat)
        while str(h) in (kunci, k_pertama, str(kedua)):
            h += 1
        mal = [
            Malrule("modus.pertama", k_pertama, "K", "menjawab data pertama, bukan yang paling sering muncul"),
            Malrule("modus.kedua", str(kedua), "K", "menjawab nilai yang bukan paling sering muncul"),
            Malrule("modus.kurang_satu", str(h), "H", "perhitungan benar, hasilnya meleset satu"),
        ]
        teks = f"Data: {', '.join(str(x) for x in data)}. Berapa modusnya (nilai yang paling sering muncul)?"
        param = {"varian": varian, "data": data}
    return Soal(
        "median_modus",
        param,
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        bagian="B",
    )


def diagram_lingkaran(varian: str, s: int, total: int, nilai: int = 0) -> Soal:
    """Dari diagram lingkaran (derajat): nilai = s/360×total, atau cari sudut."""
    if varian == "cari_nilai":
        kunci = str(total * s // 360)
        teks = (
            f"Diagram lingkaran menunjukkan data {total} siswa. Bagian yang "
            f"memilih olahraga menempati sudut {s}°. Berapa siswa yang memilih "
            f"olahraga?"
        )
        k_lupa_total = str(s // 360 * total if s >= 360 else s)  # baca sudut saja
        k_dobel = str(total * s // 180)  # s/180 bukan s/360
        mal = [
            Malrule("lingkaran.sudut_saja", k_lupa_total, "K", "menjawab sudut, bukan banyak siswa"),
            Malrule("lingkaran.salah_360", k_dobel, "K", "memakai sudut/180 bukan sudut/360"),
            Malrule("lingkaran.kurang_satu", str(int(kunci) - 1), "H", "perhitungan benar, hasilnya meleset satu"),
        ]
        param = {"varian": varian, "s": s, "total": total}
    else:
        # cari_sudut: sudut = nilai/total×360
        kunci = str(nilai * 360 // total)
        teks = (
            f"Diagram lingkaran menunjukkan data {total} siswa. Sebanyak {nilai} "
            f"siswa memilih membaca. Berapa sudut bagian membaca pada diagram "
            f"lingkaran (derajat)?"
        )
        k_nilai_saja = str(nilai)  # baca nilai saja
        k_balik = str((total - nilai) * 360 // total)  # sudut bagian lain
        mal = [
            Malrule("lingkaran.nilai_saja", k_nilai_saja, "K", "menjawab banyak siswa, bukan sudut"),
            Malrule("lingkaran.bagian_lain", k_balik, "K", "menghitung sudut bagian yang lain"),
            Malrule("lingkaran.kurang_satu", str(int(kunci) - 1), "H", "perhitungan benar, hasilnya meleset satu"),
        ]
        param = {"varian": varian, "s": nilai * 360 // total, "total": total, "nilai": nilai}
    return Soal(
        "diagram_lingkaran",
        param,
        teks,
        kunci,
        saring_malrule(kunci, mal),
        bagian="B",
    )


def diagram_batang_garis(varian: str, data: list[int], i: int = 0) -> Soal:
    """Dari diagram batang: baca nilai, jumlah, selisih, atau total."""
    n = len(data)
    nama = [f"B{i+1}" for i in range(n)]
    teks_data = ", ".join(f"{nama[k]}: {data[k]}" for k in range(n))
    if varian == "baca":
        kunci = data[i]
        k1 = data[(i + 1) % n]
        k2 = data[(i + 2) % n]
        h = kunci - 1
        if k1 == kunci or k1 == h:
            k1 = kunci + 1
        if k2 == kunci or k2 == h or k2 == k1:
            k2 = kunci + 2
        mal = [
            Malrule("batang.baca_tetangga", str(k1), "K", f"membaca batang yang berdekatan, bukan {nama[i]}"),
            Malrule("batang.baca_lain", str(k2), "K", "membaca batang yang salah"),
            Malrule("batang.kurang_satu", str(h), "H", "membaca benar, nilainya meleset satu"),
        ]
        teks = f"Diagram batang: {teks_data}. Berapa nilai {nama[i]}?"
        param = {"varian": varian, "data": data, "i": i}
    elif varian == "jumlah":
        kunci = sum(data)
        k1 = max(data)  # menjawab batang terbesar
        k2 = sum(data) - data[0]  # lupa menjumlahkan batang pertama
        h = kunci - 1
        if k1 == kunci or k1 == h:
            k1 = kunci + 1
        if k2 == kunci or k2 == h or k2 == k1:
            k2 = kunci + 2
        mal = [
            Malrule("batang.terbesar", str(k1), "K", "menjawab batang terbesar, bukan jumlah"),
            Malrule("batang.lupa_pertama", str(k2), "K", "menjumlahkan dengan melupakan satu batang"),
            Malrule("batang.kurang_satu", str(h), "H", "perhitungan benar, hasilnya meleset satu"),
        ]
        teks = f"Diagram batang: {teks_data}. Berapa jumlah seluruh nilai?"
        param = {"varian": varian, "data": data}
    elif varian == "selisih":
        a, b = data[i], data[(i + 1) % n]
        kunci = abs(a - b)
        k1 = a + b  # menjumlahkan dua batang
        k2 = abs(a - data[(i + 2) % n])  # selisih batang yang berbeda
        h = kunci - 1
        if k1 == kunci or k1 == h:
            k1 = kunci + 1
        if k2 == kunci or k2 == h or k2 == k1:
            k2 = kunci + 2
        mal = [
            Malrule("batang.jumlah_dua", str(k1), "K", "menjumlahkan dua batang padahal yang diminta selisih"),
            Malrule("batang.selisih_lain", str(k2), "K", "menghitung selisih batang yang berbeda"),
            Malrule("batang.kurang_satu", str(h), "H", "perhitungan benar, hasilnya meleset satu"),
        ]
        teks = f"Diagram batang: {teks_data}. Berapa selisih {nama[i]} dan {nama[(i+1)%n]}?"
        param = {"varian": varian, "data": data, "i": i}
    else:  # total == jumlah, alias untuk komposisi
        kunci = sum(data)
        k1 = max(data)
        k2 = sum(data) - data[-1]  # lupa menjumlahkan batang terakhir
        h = kunci - 1
        if k1 == kunci or k1 == h:
            k1 = kunci + 1
        if k2 == kunci or k2 == h or k2 == k1:
            k2 = kunci + 2
        mal = [
            Malrule("batang.terbesar_total", str(k1), "K", "menjawab batang terbesar, bukan total"),
            Malrule("batang.lupa_terakhir", str(k2), "K", "menjumlahkan dengan melupakan satu batang"),
            Malrule("batang.kurang_satu", str(h), "H", "perhitungan benar, hasilnya meleset satu"),
        ]
        teks = f"Diagram batang: {teks_data}. Berapa total seluruh nilai?"
        param = {"varian": varian, "data": data}
    return Soal(
        "diagram_batang_garis",
        param,
        teks,
        str(kunci),
        saring_malrule(str(kunci), mal),
        bagian="B",
    )


# ── Registry ─────────────────────────────────────────────────────────────

REGISTRI_TOPIK = {
    "rata_rata": rata_rata,
    "rata_rata_gabungan": rata_rata_gabungan,
    "median_modus": median_modus,
    "diagram_lingkaran": diagram_lingkaran,
    "diagram_batang_garis": diagram_batang_garis,
}

KOMPOSISI = {
    # P3 (10 soal): 3, 5, 3, 5, 3, 5, 3, 5, 3, 5 — modus dulu (mudah),
    # diagram batang menyusul; median & rata-rata menunggu P4.
    "P3": (
        "median_modus",
        "diagram_batang_garis",
        "median_modus",
        "diagram_batang_garis",
        "median_modus",
        "diagram_batang_garis",
        "median_modus",
        "diagram_batang_garis",
        "median_modus",
        "diagram_batang_garis",
    ),
    # P4 (10 soal): 1, 3, 5, 1, 3, 5, 1, 3, 5, 1
    "P4": (
        "rata_rata",
        "median_modus",
        "diagram_batang_garis",
        "rata_rata",
        "median_modus",
        "diagram_batang_garis",
        "rata_rata",
        "median_modus",
        "diagram_batang_garis",
        "rata_rata",
    ),
    # P5 (10 soal): 1, 2, 3, 4, 5, 1, 2, 3, 4, 5
    "P5": (
        "rata_rata",
        "rata_rata_gabungan",
        "median_modus",
        "diagram_lingkaran",
        "diagram_batang_garis",
        "rata_rata",
        "rata_rata_gabungan",
        "median_modus",
        "diagram_lingkaran",
        "diagram_batang_garis",
    ),
    # P6 (10 soal): 1, 2, 3, 4, 5, 2, 3, 4, 5, 1
    "P6": (
        "rata_rata",
        "rata_rata_gabungan",
        "median_modus",
        "diagram_lingkaran",
        "diagram_batang_garis",
        "rata_rata_gabungan",
        "median_modus",
        "diagram_lingkaran",
        "diagram_batang_garis",
        "rata_rata",
    ),
}

JUDUL_BAGIAN = {
    "A": "Bagian A — Rata-rata",
    "B": "Bagian B — Median & modus, diagram",
}

CATATAN_BAGIAN = {
    "A": "Rata-rata = jumlah data ÷ banyak data.",
    "B": "Median = nilai tengah (urutkan dulu). Modus = nilai paling sering muncul.",
}


def _parameter(template_id: str, rng: random.Random, level: str) -> dict:
    if template_id == "rata_rata":
        varian = rng.choice(("cari_rata", "cari_data_ke_n"))
        n = rng.randint(3, 8)
        if varian == "cari_rata":
            # jumlah harus habis dibagi n supaya rata-rata bulat
            data = [rng.randint(1, 100) for _ in range(n)]
            while sum(data) % n != 0:
                data = [rng.randint(1, 100) for _ in range(n)]
            return {"varian": varian, "data": data}
        # cari_data_ke_n: pilih rata bulat, lalu data pertama; data terakhir = rata×n−jumlah
        rata = rng.randint(15, 50)
        data = [rng.randint(1, 100) for _ in range(n - 1)]
        data.append(rata * n - sum(data))
        # jaga data terakhir tetap positif & masuk akal (1..200)
        while data[-1] < 1 or data[-1] > 200:
            data = [rng.randint(1, 100) for _ in range(n - 1)]
            data.append(rata * n - sum(data))
        return {"varian": varian, "data": data, "rata": rata}
    if template_id == "rata_rata_gabungan":
        n1, n2 = rng.randint(2, 10), rng.randint(2, 10)
        x1, x2 = rng.randint(5, 90), rng.randint(5, 90)
        # total gabungan habis dibagi (n1+n2)
        while (n1 * x1 + n2 * x2) % (n1 + n2) != 0:
            x2 = rng.randint(5, 90)
        return {"n1": n1, "n2": n2, "x1": x1, "x2": x2}
    if template_id == "median_modus":
        # P3: median di atas kelas 3 — selalu varian modus; band SASMO
        # Primary 1-4 (statistics) memuat modus, bukan median.
        if level == "P3":
            varian = "modus"
        else:
            varian = rng.choice(("median", "modus"))
        if varian == "median":
            n = rng.randint(3, 9)
            data = [rng.randint(1, 30) for _ in range(n)]
            return {"varian": varian, "data": data}
        # modus: 3-7 data (P3: 3-5, nilai 1-12), minimal satu nilai muncul ≥2 kali
        if level == "P3":
            n = rng.randint(3, 5)
            data = [rng.randint(1, 12) for _ in range(n)]
            modus = rng.randint(1, 12)
        else:
            n = rng.randint(3, 7)
            data = [rng.randint(1, 20) for _ in range(n)]
            modus = rng.randint(1, 20)
        data[0] = modus
        if n > 1:
            data[1] = modus
        return {"varian": varian, "data": data}
    if template_id == "diagram_lingkaran":
        varian = rng.choice(("cari_nilai", "cari_sudut"))
        s_pilihan = (30, 45, 60, 90, 120, 180)
        if varian == "cari_nilai":
            s = rng.choice(s_pilihan)
            kunci = rng.randint(2, 50)
            total = kunci * 360 // s
            return {"varian": varian, "s": s, "total": total}
        # cari_sudut: pilih sudut kunci, nilai = kunci_sudut/360×total
        sudut = rng.choice(s_pilihan)
        total = rng.randint(36, 3600)
        while total * sudut // 360 == 0 or total * sudut % 360 != 0:
            total = rng.randint(36, 3600)
        nilai = total * sudut // 360
        return {"varian": varian, "s": sudut, "total": total, "nilai": nilai}
    if template_id == "diagram_batang_garis":
        varian = rng.choice(("baca", "jumlah", "selisih"))
        if level == "P3":
            # P3: empat batang, nilai 1-20 — ketiga varian tetap boleh.
            n, atas = 4, 20
        else:
            n, atas = rng.randint(4, 6), 50
        data = [rng.randint(1, atas) for _ in range(n)]
        i = rng.randint(0, n - 1)
        if varian == "baca":
            return {"varian": varian, "data": data, "i": i}
        if varian == "jumlah":
            return {"varian": varian, "data": data}
        # selisih: pastikan dua batang yang dibandingkan berbeda
        a, b = data[i], data[(i + 1) % n]
        while a == b:
            data[(i + 1) % n] = rng.randint(1, atas)
            b = data[(i + 1) % n]
        return {"varian": varian, "data": data, "i": i}
    raise KeyError(f"template tidak dikenal: {template_id}")


TOPIK = Topik(
    id="statistika",
    nama="Statistika",
    judul_lembar="Latihan Statistika",
    judul_penilaian="Penilaian — Statistika",
    templates=REGISTRI_TOPIK,
    komposisi=KOMPOSISI,
    profil={"P3": {}, "P4": {}, "P5": {}, "P6": {}},
    judul_bagian=JUDUL_BAGIAN,
    catatan_bagian=CATATAN_BAGIAN,
    parameter_untuk=_parameter,
)

daftarkan(TOPIK)