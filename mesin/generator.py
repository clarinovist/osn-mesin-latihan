"""Generator lembar latihan — seed menentukan parameter, parameter menentukan soal.

Dipisahkan dari templates.py supaya batas kesulitan (yang perlu sering
disetel setelah melihat hasil anak) tidak bercampur dengan definisi soal
(yang jarang berubah).

Jaminan yang diuji di __tests__/test_generator.py:
  - seed sama -> lembar identik (bisa dicetak ulang persis)
  - seed beda -> parameter beda (bank soal benar-benar tumbuh)
  - tiap malrule menghasilkan jawaban != kunci (kalau sama, malrule itu bug)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace

from templates import HARI, LEVEL, REGISTRI, URUTAN_LEMBAR, Soal, susun_lembar

WARNA = ("merah", "kuning", "hijau", "biru", "putih", "ungu")
HURUF = ("A", "B", "C", "D")

# Alfabet lebih panjang untuk soal siklus level atas, yang butuh cukup huruf
# unik agar malrule-nya tidak saling bertabrakan (lihat sisa_bagi_siklus).
HURUF_PANJANG = ("A", "B", "C", "D", "E", "F")

LEVEL_BAWAAN = "P3"

# Pengali batas angka per level.
#
# HANYA menggeser besar angka, TIDAK menaikkan level yang sebenarnya.
# Lembar penilaian 20 Agustus sudah menuliskannya: "di P4 angkanya jadi
# ke-100 dan cara manual berhenti bekerja". Menaikkan posisi dari 20 ke 100
# pada template yang sama membuat anak menulis lebih lama, bukan berpikir
# lebih dalam.
#
# Kenaikan level yang sesungguhnya datang dari template yang menuntut rumus
# suku ke-n (lihat URUTAN_PER_LEVEL) — tabel ini hanya memastikan angkanya
# tidak terasa kekanak-kanakan di level atas.
PROFIL_LEVEL: dict[str, dict] = {
    "P3": {
        "posisi_suku_n": (25, 30, 40),
        "posisi_sisa_bagi": (40, 70),
        "penyebut_pecahan": (4, 5, 6),
        "n_jumlah_deret": (8, 10),
        "n_tampil_geometri": (3, 4),
        "posisi_terbalik_geometri": (4, 6, 3, 4),
        "beda_aritmetika": (3, 4, 5, 6, 7),
        "n_minta": 2,
        "rasio_geometri": (2, 2, 2, 3, 3, 4),
        "kenaikan_bertingkat": (1, 2, 3),
        "posisi_siklus": (15, 40),
        "posisi_warna": (20, 45),
        "gambar_korek": (8, 20),
        "gambar_titik": (6, 12),
        "posisi_terbalik": (10, 16),
        "tambah_hari": (16, 20, 23, 30, 40, 50, 100),
        "n_angka_kelipatan": (5, 12),
    },
    "P4": {
        "posisi_suku_n": (50, 60, 75, 100),
        "posisi_sisa_bagi": (80, 150),
        "penyebut_pecahan": (5, 6, 7, 8),
        "n_jumlah_deret": (10, 12, 15),
        "n_tampil_geometri": (4, 5),
        "posisi_terbalik_geometri": (6, 8, 4, 5),
        "beda_aritmetika": (6, 7, 8, 9, 11, 12),
        "n_minta": 2,
        "rasio_geometri": (2, 2, 3, 3, 4),
        "kenaikan_bertingkat": (2, 3, 4),
        "posisi_siklus": (30, 80),
        "posisi_warna": (40, 90),
        "gambar_korek": (15, 40),
        "gambar_titik": (8, 16),
        "posisi_terbalik": (12, 22),
        "tambah_hari": (45, 60, 75, 90, 100, 120, 150),
        "n_angka_kelipatan": (8, 20),
    },
    "P5": {
        "posisi_suku_n": (100, 120, 150, 200),
        "posisi_sisa_bagi": (150, 300),
        "penyebut_pecahan": (7, 8, 9, 10, 12),
        "n_jumlah_deret": (15, 20, 25),
        "n_tampil_geometri": (5, 6),
        "posisi_terbalik_geometri": (8, 10, 5, 6),
        "beda_aritmetika": (9, 11, 12, 13, 14, 15, 16),
        "n_minta": 3,
        "rasio_geometri": (2, 3, 3, 4, 5),
        "kenaikan_bertingkat": (3, 4, 5),
        "posisi_siklus": (60, 150),
        "posisi_warna": (75, 180),
        "gambar_korek": (25, 60),
        "gambar_titik": (10, 20),
        "posisi_terbalik": (15, 30),
        "tambah_hari": (100, 150, 200, 250, 300, 365),
        "n_angka_kelipatan": (12, 30),
    },
    "P6": {
        "posisi_suku_n": (150, 200, 250, 300, 500),
        "posisi_sisa_bagi": (300, 700),
        "penyebut_pecahan": (9, 10, 11, 12, 15),
        "n_jumlah_deret": (20, 25, 30, 40),
        "n_tampil_geometri": (6, 7),
        "posisi_terbalik_geometri": (10, 12, 6, 7),
        "beda_aritmetika": (12, 13, 14, 15, 16, 17, 18, 19, 21),
        "n_minta": 3,
        "rasio_geometri": (3, 4, 5, 6),
        "kenaikan_bertingkat": (4, 5, 6, 7),
        "posisi_siklus": (100, 300),
        "posisi_warna": (120, 350),
        "gambar_korek": (40, 100),
        "gambar_titik": (12, 25),
        "posisi_terbalik": (20, 40),
        "tambah_hari": (200, 300, 365, 500, 730, 1000),
        "n_angka_kelipatan": (20, 50),
    },
}


def profil(level: str) -> dict:
    """Batas angka untuk satu level. Level tak dikenal jatuh ke bawaan.

    Sengaja tidak melempar: `siswa.tingkat` adalah kolom teks bebas yang
    sudah terisi di basis data produksi, dan satu nilai aneh di situ tidak
    boleh membuat guru gagal membuat sesi. Yang salah levelnya lebih baik
    daripada yang tidak ada lembarnya.
    """
    return PROFIL_LEVEL.get(level, PROFIL_LEVEL[LEVEL_BAWAAN])


@dataclass(frozen=True)
class Lembar:
    seed: int
    soal: tuple[Soal, ...]
    level: str = LEVEL_BAWAAN

    @property
    def tanda_tangan(self) -> str:
        return "|".join(s.tanda_tangan for s in self.soal)


def _pola_huruf(rng: random.Random) -> tuple[str, ...]:
    """Pola dengan tepat satu huruf berulang, mis. A B B C.

    Huruf yang muncul dua kali membuat anak tidak bisa menebak dari posisi
    saja; ia harus benar-benar menghitung siklusnya.

    Dua bentuk yang sengaja dihindari:
      - semua huruf sama (AAA) — semua posisi berjawab sama, tidak
        mendiagnosis apa pun
      - semua huruf beda (ABCD) — anak bisa memetakan posisi ke huruf tanpa
        memahami siklus

    Minimal 3 huruf UNIK, karena itu panjangnya mulai dari 4 dan bukan 3.
    Dengan hanya 2 huruf unik cuma ada satu jawaban salah yang mungkin,
    sehingga semua malrule menyusut jadi satu setelah `saring_malrule` dan
    jalur H tidak pernah selamat — soalnya tetap sah, tapi berhenti bisa
    memisahkan salah konsep dari salah hitung. Terukur: pola 3-huruf membuat
    78% soal siklus_huruf bermalrule tunggal.
    """
    panjang = rng.choice([4, 5])
    dasar = list(HURUF_PANJANG[:panjang])
    sumber, tujuan = rng.sample(range(panjang), 2)
    dasar[tujuan] = dasar[sumber]
    # Ujung kembar merusak diagnosis: kalau pola[0] == pola[-1] (DBCD,
    # ABCA), malrule "ambil unsur pertama" dan "ambil unsur terakhir" jadi
    # JAWABAN YANG SAMA, dan pada posisi ber-sisa 0 atau ber-sisa 1 salah
    # satunya bahkan = kunci. Semua kandidat K yang menebak satu huruf
    # lalu habis tersaring bersamaan — terukur ~3% soal kehilangan seluruh
    # jalur K. Ujung harus beda.
    if dasar[0] == dasar[-1]:
        pengganti = next(h for h in HURUF_PANJANG if h not in dasar)
        dasar[-1] = pengganti
    return tuple(dasar)


def _parameter(template_id: str, rng: random.Random, level: str = LEVEL_BAWAAN) -> dict:
    """Batas parameter dijaga supaya soal tetap pada levelnya.

    Aturan yang ditegakkan di sini:
      - hasil akhir tidak negatif
      - angka hasil masih terbayang anak pada level itu
      - posisi target selalu jatuh TEPAT pada suku deret (bukan di antaranya)
    """
    pf = profil(level)
    if template_id == "deret_aritmetika":
        return {
            "awal": rng.randint(2, 12),
            "beda": rng.choice(pf["beda_aritmetika"]),
            "n_tampil": 4,
            "n_minta": pf["n_minta"],
        }

    if template_id == "deret_aritmetika_turun":
        beda = rng.choice(pf["beda_aritmetika"])
        n_tampil = rng.choice([4, 5])
        # awal harus cukup besar supaya suku terakhir tetap positif
        awal = beda * rng.randint(n_tampil + 2, n_tampil + 8)
        return {"awal": awal, "beda": beda, "n_tampil": n_tampil}

    if template_id == "deret_geometri":
        # Rasio 2 diberi porsi lebih besar di level bawah: pola x2 adalah
        # prasyarat Bagian D (soal terbalik). Rasio lain tetap ada supaya anak
        # tidak menghafal "pola kali berarti dikali dua". Di level atas rasio 2
        # ditinggalkan — yang menantang bukan lagi mengenali pola kali,
        # melainkan besarnya perkalian.
        rasio = rng.choice(pf["rasio_geometri"])
        lo_tampil, hi_tampil = pf["n_tampil_geometri"]
        if rasio == 2:
            awal = rng.choice([1, 2, 3, 4, 5, 6])
        elif rasio == 3:
            awal = rng.choice([1, 2, 3])
        else:
            awal = rng.choice([1, 2, 3])
        # n_tampil ikut level, bukan dipatok per rasio. Versi sebelumnya
        # memakai angka tetap untuk rasio 3 dan 4, sehingga P3 dan P6 bisa
        # menghasilkan soal yang identik persis — perbedaan level hilang
        # tanpa ada yang memberi tahu.
        n_tampil = rng.randint(lo_tampil, hi_tampil)
        # Jaga supaya suku terakhir tetap terbayang anak.
        while awal * rasio**n_tampil > 6000 and n_tampil > 3:
            n_tampil -= 1
        return {"awal": awal, "rasio": rasio, "n_tampil": n_tampil}

    if template_id == "deret_bertingkat":
        return {
            "awal": rng.randint(1, 9),
            "beda_awal": rng.choice([1, 2, 3, 4]),
            "kenaikan": rng.choice(pf["kenaikan_bertingkat"]),
            "n_tampil": rng.choice([5, 6]),
        }

    if template_id == "siklus_huruf":
        pola = _pola_huruf(rng)
        # Sisa 0 adalah jebakan off-by-one — pastikan sering muncul.
        lo, hi = pf["posisi_siklus"]
        posisi = rng.choice(
            [
                len(pola) * rng.randint(lo // len(pola) + 1, hi // len(pola)),  # sisa 0
                rng.randint(lo, hi),
            ]
        )
        return {"pola": pola, "posisi": posisi}

    if template_id == "siklus_warna":
        # Sama alasannya dengan _pola_huruf: minimal 3 warna UNIK.
        # Bentuk lama `rng.sample(WARNA, n-1)` lalu menduplikasi unsur
        # pertama menghasilkan hanya 2 warna unik saat n=3, dan 89% soal
        # siklus_warna berakhir bermalrule tunggal — tidak bisa memisahkan
        # salah konsep dari salah hitung.
        n = rng.choice([4, 5])
        pilih = list(rng.sample(WARNA, n - 1))  # n-1 warna unik
        ulang = rng.randrange(len(pilih))
        sisip = rng.randrange(len(pilih) + 1)
        pola = pilih[:sisip] + [pilih[ulang]] + pilih[sisip:]
        return {"pola": tuple(pola), "posisi": rng.randint(*pf["posisi_warna"])}

    if template_id == "korek_api":
        return {
            "awal": rng.choice([3, 4, 5, 6, 7]),
            "tambah": rng.choice([2, 3, 4]),
            "gambar_ke": rng.randint(*pf["gambar_korek"]),
        }

    if template_id == "titik_segitiga":
        # T(12)=78 di P3 — masih terbayang anak, dan menjaga varian tetap
        # cukup banyak untuk drill mingguan. Level atas memperlebar rentang
        # ini, yang sekaligus menambal keluhan "titik_segitiga cuma 7 varian"
        # di README §Batas yang diketahui.
        return {"gambar_ke": rng.randint(*pf["gambar_titik"])}

    if template_id == "deret_terbalik_aritmetika":
        return {
            "awal": rng.randint(2, 8),
            "beda": rng.choice([3, 4, 5, 6]),
            "posisi_target": rng.randint(*pf["posisi_terbalik"]),
        }

    if template_id == "deret_terbalik_geometri":
        # Batas atas dijaga ketat: nilai target tumbuh eksponensial, dan
        # bilangan yang tidak lagi terbayang anak berhenti mendiagnosis
        # apa pun. Posisi diambil dari profil, lalu dipangkas supaya
        # target tetap di bawah ~5000 bahkan di P6.
        # Rasio dibatasi 2 atau 3 (bukan diambil dari rasio_geometri): nilai
        # target tumbuh eksponensial, dan rasio 4+ pada posisi belasan
        # menghasilkan bilangan yang tidak lagi terbayang anak — soal berhenti
        # mendiagnosis dan berubah jadi uji ketelitian mengalikan.
        #
        # Rentang posisi ditulis eksplisit per level, TIDAK diturunkan dari
        # posisi_terbalik lewat min(). Pemangkasan seperti itu membuat P3 dan
        # P6 sama-sama jatuh ke batas yang sama, dan perbedaan levelnya hilang
        # diam-diam — persis bug yang tertangkap test
        # `test_setiap_template_berubah_antara_p3_dan_p6`.
        rasio = rng.choice([2, 2, 3])
        lo2, hi2, lo3, hi3 = pf["posisi_terbalik_geometri"]
        if rasio == 2:
            posisi = rng.randint(lo2, hi2)
            # awal dipilih setelah posisi diketahui, supaya target tetap di
            # bawah ~4000 apa pun levelnya. Tanpa ini P6 posisi 12 dengan
            # awal 7 memberi 14336 — angka yang berhenti mendiagnosis apa
            # pun dan hanya menguji ketelitian mengalikan.
            batas_awal = max(1, 4000 // (2 ** (posisi - 1)))
            awal = rng.choice([a for a in (2, 3, 4, 5, 6, 7) if a <= batas_awal] or [1])
        else:
            posisi = rng.randint(lo3, hi3)
            batas_awal = max(1, 4000 // (3 ** (posisi - 1)))
            # P3: posisi bisa serendah 3, jadi awal=1 memberi target 9 —
            # dan 9 // rasio == 3 == kunci, malrule K-nya kolaps lagi.
            # awal >= 2 menjamin target // rasio != target (malrule B) dan
            # != kunci (kuncinya posisi, bukan nilai).
            kandidat_awal = [a for a in (2, 3) if a <= batas_awal]
            awal = rng.choice(kandidat_awal or [1])
        return {"awal": awal, "rasio": rasio, "posisi_target": posisi}

    if template_id == "siklus_hari":
        return {
            "hari_awal": rng.choice(HARI),
            "tambah": rng.choice(pf["tambah_hari"]),
        }

    if template_id == "jumlah_siklus":
        n = rng.choice([3, 4])
        pola = tuple(rng.sample(range(1, 6), n))
        lo, hi = pf["n_angka_kelipatan"]
        n_angka = rng.randint(lo, hi) * n + rng.randint(1, n - 1)  # sisa != 0
        return {"pola": pola, "n_angka": n_angka}

    if template_id == "suku_ke_n":
        # Posisi sengaja jauh: cara manual harus mati di sini. Kalau anak
        # masih sanggup menulis deretnya sampai ketemu, soal ini kehilangan
        # seluruh maksudnya.
        return {
            "awal": rng.randint(2, 12),
            "beda": rng.choice(pf["beda_aritmetika"]),
            "posisi": rng.choice(pf["posisi_suku_n"]),
        }

    if template_id == "sisa_bagi_siklus":
        # Pola untuk soal ini WAJIB punya minimal 3 huruf berbeda, tidak
        # seperti `siklus_huruf` yang boleh 2.
        #
        # Alasannya matematis, bukan selera: dengan hanya 2 huruf unik cuma
        # ada SATU jawaban salah yang mungkin, sehingga berapa pun malrule
        # yang ditulis akan menyusut jadi satu setelah penyaringan — dan
        # jalur H hampir tidak pernah selamat. Terukur: pola 2-huruf selalu
        # menyisakan 1 malrule.
        #
        # Panjang siklus juga dijaga tidak membagi habis angka bulat yang
        # umum, supaya sisanya bervariasi.
        panjang = rng.choice([4, 5, 6])
        dasar = list(HURUF_PANJANG[:panjang])
        # satu huruf diulang: tetap menuntut perhitungan siklus, tapi
        # menyisakan cukup huruf unik untuk beberapa malrule
        sumber, tujuan = rng.sample(range(panjang), 2)
        dasar[tujuan] = dasar[sumber]
        # Aturan sama dengan _pola_huruf: ujung kembar (DBCD, ABCA) membuat
        # "ambil awal" dan "ambil akhir" jadi jawaban yang sama dan pada
        # sisa 0/1 salah satunya = kunci — semua jalur K habis tersaring.
        if dasar[0] == dasar[-1]:
            pengganti = next(h for h in HURUF_PANJANG if h not in dasar)
            dasar[-1] = pengganti
        return {
            "pola": tuple(dasar),
            "posisi": rng.randint(*pf["posisi_sisa_bagi"]),
        }

    if template_id == "pola_pecahan":
        # Penyebut dijaga tetap dan tidak kecil, supaya malrule
        # "penyebut ikut naik" menghasilkan pecahan yang jelas berbeda.
        #
        # Penyebut dipilih SETELAH pembilang & beda diketahui, dan dijamin
        # lebih besar dari pembilang terjauh yang akan muncul (termasuk
        # malrule H yang melewati satu langkah). Tanpa ini 56% soal
        # menampilkan pecahan seperti 12/12 atau 15/12 — benar secara pola,
        # tapi janggal dibaca anak SD dan mengalihkan perhatian dari yang
        # sedang diuji.
        pembilang = rng.randint(1, 4)
        beda = rng.choice([1, 2, 3])
        n_tampil = 4
        # pembilang terbesar yang bisa tampil: kunci + satu langkah (malrule H)
        pemb_maks = pembilang + beda * (n_tampil + 1)
        layak = [p for p in pf["penyebut_pecahan"] if p > pemb_maks]
        penyebut = rng.choice(layak) if layak else pemb_maks + rng.choice([1, 2, 3])
        return {
            "pembilang": pembilang,
            "penyebut": penyebut,
            "beda_pembilang": beda,
            "n_tampil": n_tampil,
        }

    if template_id == "jumlah_deret":
        return {
            "awal": rng.randint(1, 9),
            "beda": rng.choice([2, 3, 4, 5]),
            "n": rng.choice(pf["n_jumlah_deret"]),
        }

    raise KeyError(f"template tidak dikenal: {template_id}")


def buat_lembar(
    seed: int,
    urutan: tuple[str, ...] | None = None,
    level: str = LEVEL_BAWAAN,
) -> Lembar:
    """Bangun satu lembar penuh dari seed. Deterministik.

    Urutan soal ditentukan level kalau tidak disebut eksplisit. Argumen
    `urutan` tetap ada supaya pemanggil bisa menyusun lembar khusus (mis.
    drill satu tipe), dan supaya test bisa memaksa komposisi tertentu.
    """
    rng = random.Random(seed)
    if urutan is None:
        urutan = susun_lembar(level)
    soal = tuple(_soal_layak(t, rng, level) for t in urutan)
    return Lembar(seed=seed, soal=soal, level=level)


def _soal_layak(
    template_id: str,
    rng: random.Random,
    level: str = LEVEL_BAWAAN,
    batas: int = 40,
) -> Soal:
    """Ambil parameter sampai dapat soal yang benar-benar bisa mendiagnosis.

    Beberapa kombinasi parameter menghasilkan soal yang sah tapi tumpul:
    seluruh malrule-nya bertabrakan dengan kunci atau satu sama lain, lalu
    dibuang oleh `saring_malrule`. Sisanya soal tanpa satu pun jalur
    diagnosis — anak tetap harus mengerjakannya, tapi jawaban salahnya tidak
    memberi tahu apa-apa. Itu beban menulis tanpa imbalan informasi.

    Contoh nyata: siklus huruf 'CBC' dengan posisi kelipatan 3. Kunci 'C',
    dan "ambil unsur terakhir siklus" juga 'C' — satu-satunya malrule
    terbuang, soal jadi kosong.

    Karena rng dipakai berurutan, penolakan tetap deterministik: seed yang
    sama menghasilkan lembar yang sama.
    """
    for _ in range(batas):
        soal = REGISTRI[template_id](**_parameter(template_id, rng, level))
        if soal.malrule:
            # Level ditempelkan di sini, bukan di dalam template: definisi
            # soal tidak perlu tahu untuk siapa ia dipakai. Pemisahan yang
            # sama dengan alasan generator.py terpisah dari templates.py.
            return replace(soal, level=level)
    raise RuntimeError(
        f"{template_id}: {batas} percobaan tanpa satu pun malrule bertahan — "
        "periksa definisi malrule template ini"
    )


def buat_soal(template_id: str, seed: int, level: str = LEVEL_BAWAAN) -> Soal:
    """Satu soal saja — untuk menambal bank soal per tipe."""
    return _soal_layak(template_id, random.Random(seed), level)
