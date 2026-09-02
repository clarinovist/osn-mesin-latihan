"""Kartu rumus/teori singkat per konsep (poin c feedback Filia).

Pertanyaan Filia: "Apakah kita perlu menambahkan teori atau rumus untuk
anak pelajari, kemudian membuatkan soal lagi sesuai dengan rumus yg sudah
di pelajari?"

Jawaban yang diambil: ya, tapi TIDAK sebagai modul materi terpisah yang
harus dibaca sebelum boleh berlatih. Alasannya jujur — anak SD tidak
membaca teori yang tidak sedang ia butuhkan. Yang dipasang:

  1. kartu rumus muncul di halaman HASIL, tepat di konsep yang anak salah
     (saat ia paling siap menerima penjelasannya);
  2. kartu rumus juga bisa dibuka dari halaman kerja sebagai bantuan
     opsional (bukan gerbang).

Satu template TIDAK dapat satu kartu. 82 template hanya punya belasan
konsep; kartu dipetakan per KONSEP dan template menunjuk ke konsepnya.
Template tanpa pemetaan -> tidak ada kartu (lebih baik kosong daripada
teori basa-basi yang salah sasaran).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Kartu:
    """Satu kartu teori: judul + rumus/aturan + contoh singkat."""

    judul: str
    inti: str
    contoh: str = ""


# Kartu per KONSEP. Bahasa sengaja bahasa anak SD: rumus ditulis dengan
# kata, bukan notasi aljabar, dan selalu disertai satu contoh berangka.
KARTU: dict[str, Kartu] = {
    "rata_rata": Kartu(
        judul="Rata-rata",
        inti="Rata-rata = jumlah semua data ÷ banyaknya data.",
        contoh="Nilai 8, 6, 7 → (8+6+7) ÷ 3 = 21 ÷ 3 = 7.",
    ),
    "median_modus": Kartu(
        judul="Median dan Modus",
        inti="Median = nilai TENGAH setelah data diurutkan. "
             "Modus = nilai yang PALING SERING muncul.",
        contoh="Data 3, 7, 5 → urut jadi 3, 5, 7 → median 5. "
               "Data 2, 4, 4, 9 → modus 4.",
    ),
    "pola_bilangan": Kartu(
        judul="Pola bilangan",
        inti="Cari BEDA antara dua suku berdekatan. Kalau bedanya tetap, "
             "tambahkan beda itu untuk suku berikutnya.",
        contoh="7, 11, 15, … beda 4 → berikutnya 15 + 4 = 19.",
    ),
    "pola_geometri": Kartu(
        judul="Pola dikali",
        inti="Kalau tiap suku didapat dengan DIKALI angka yang sama, "
             "kalikan lagi untuk suku berikutnya.",
        contoh="1, 3, 9, 27, … dikali 3 → berikutnya 27 × 3 = 81.",
    ),
    "keliling_luas": Kartu(
        judul="Keliling dan Luas persegi panjang",
        inti="Keliling = 2 × (panjang + lebar). Luas = panjang × lebar.",
        contoh="p = 8, l = 3 → keliling = 2 × 11 = 22; luas = 8 × 3 = 24.",
    ),
    "luas_segitiga": Kartu(
        judul="Luas segitiga",
        inti="Luas = alas × tinggi ÷ 2. Tingginya harus TEGAK LURUS alas.",
        contoh="alas 10, tinggi 6 → 10 × 6 ÷ 2 = 30.",
    ),
    "volume": Kartu(
        judul="Volume kubus dan balok",
        inti="Volume balok = panjang × lebar × tinggi. "
             "Volume kubus = rusuk × rusuk × rusuk.",
        contoh="Balok 5 × 3 × 2 = 30. Kubus rusuk 4 → 4 × 4 × 4 = 64.",
    ),
    "sudut": Kartu(
        judul="Sudut",
        inti="Jumlah sudut dalam segitiga = 180°. "
             "Dua sudut berpelurus jumlahnya 180°; berpenyiku 90°.",
        contoh="Segitiga dengan 60° dan 70° → sudut ketiga = 180 − 130 = 50°.",
    ),
    "fpb_kpk": Kartu(
        judul="FPB dan KPK",
        inti="FPB = bilangan TERBESAR yang membagi habis keduanya. "
             "KPK = bilangan TERKECIL yang habis dibagi keduanya.",
        contoh="12 dan 18 → FPB 6, KPK 36.",
    ),
    "keterbagian": Kartu(
        judul="Ciri habis dibagi",
        inti="Habis dibagi 2 kalau satuannya genap; dibagi 3 kalau jumlah "
             "angkanya habis dibagi 3; dibagi 5 kalau satuannya 0 atau 5.",
        contoh="132 → 1+3+2 = 6, habis dibagi 3, jadi 132 habis dibagi 3.",
    ),
    "sisa_pembagian": Kartu(
        judul="Sisa pembagian",
        inti="Bagi, lalu SISANYA yang dipakai. Sisa selalu lebih kecil "
             "dari pembaginya.",
        contoh="115 ÷ 3 = 38 sisa 1 (karena 38 × 3 = 114, kurang 1).",
    ),
    "urutan_operasi": Kartu(
        judul="Urutan operasi",
        inti="Kerjakan kurung dulu, lalu kali/bagi (dari kiri), "
             "baru tambah/kurang (dari kiri).",
        contoh="2 + 3 × 4 = 2 + 12 = 14, bukan 20.",
    ),
    "pecahan": Kartu(
        judul="Pecahan",
        inti="Untuk menambah/mengurang, samakan penyebut dulu. "
             "Untuk mengali, kalikan atas dengan atas dan bawah dengan bawah.",
        contoh="1/2 + 1/3 = 3/6 + 2/6 = 5/6.",
    ),
    "perbandingan": Kartu(
        judul="Perbandingan dan skala",
        inti="Skala 1 : n berarti 1 cm di peta = n cm asli. "
             "Perbandingan senilai: kalau satu naik, yang lain ikut naik.",
        contoh="Skala 1 : 1.000 dan jarak peta 4 cm → asli 4.000 cm = 40 m.",
    ),
    "waktu": Kartu(
        judul="Satuan waktu",
        inti="1 menit = 60 detik, 1 jam = 60 menit. "
             "1 windu = 8 tahun, 1 dasawarsa = 10 tahun, 1 abad = 100 tahun.",
        contoh="70 windu = 70 × 8 = 560 tahun.",
    ),
    "kombinatorik": Kartu(
        judul="Mencacah kemungkinan",
        inti="Kalau URUTAN penting, itu permutasi. Kalau urutan TIDAK "
             "penting (sekadar memilih), itu kombinasi.",
        contoh="Memilih 2 dari 4 anak untuk piket (urutan tak penting) = 6 cara.",
    ),
}


# template_id -> konsep. Dibangun dari daftar template NYATA (bukan dikira),
# dan sengaja tidak lengkap: template yang tidak punya kartu yang benar-benar
# pas lebih baik tidak menampilkan apa pun. Guard test menjaga setiap nilai
# di sini menunjuk konsep yang ADA di KARTU dan kunci yang ADA di REGISTRI.
KONSEP_TEMPLATE: dict[str, str] = {
    # statistika
    "rata_rata": "rata_rata",
    "rata_rata_gabungan": "rata_rata",
    "median_modus": "median_modus",
    # pola bilangan
    "deret_aritmetika": "pola_bilangan",
    "deret_aritmetika_turun": "pola_bilangan",
    "deret_terbalik_aritmetika": "pola_bilangan",
    "suku_ke_n": "pola_bilangan",
    "jumlah_deret": "pola_bilangan",
    "gauss_deret": "pola_bilangan",
    "deret_geometri": "pola_geometri",
    "deret_terbalik_geometri": "pola_geometri",
    "pola_pecahan": "pecahan",
    # geometri datar
    "keliling_luas_datar": "keliling_luas",
    "luas_kotak_satuan": "keliling_luas",
    "luas_segiempat_lain": "keliling_luas",
    "luas_segitiga_jajargenjang": "luas_segitiga",
    "jumlah_sudut_segitiga": "sudut",
    "sudut_luar_segitiga": "sudut",
    "sudut_pelurus_berpenyiku": "sudut",
    # geometri ruang
    "volume_kubus_balok": "volume",
    "volume_prisma_tabung": "volume",
    # teori bilangan
    "fpb_dua_bilangan": "fpb_kpk",
    "kpk_dua_bilangan": "fpb_kpk",
    "fpb_kpk_hubungan": "fpb_kpk",
    "keterbagian": "keterbagian",
    "sisa_pembagian": "sisa_pembagian",
    "sisa_bagi_siklus": "sisa_pembagian",
    # aritmetika
    "urutan_operasi_1": "urutan_operasi",
    "pecahan_operasi_campuran": "pecahan",
    # perbandingan & pengukuran
    "skala_peta": "perbandingan",
    "perbandingan_senilai": "perbandingan",
    "perbandingan_berbalik": "perbandingan",
    "jam_menit_detik": "waktu",
    "satuan_waktu_lama": "waktu",
    # kombinatorik
    "permutasi_urutan": "kombinatorik",
    "permutasi_blok": "kombinatorik",
    "kombinasi_pilih": "kombinatorik",
    "jabat_tangan": "kombinatorik",
}


def kartu_untuk(template_id: str) -> Kartu | None:
    """Kartu teori untuk satu template, atau None kalau belum dipetakan.

    None BUKAN kegagalan: lebih baik tidak menampilkan apa pun daripada
    menempelkan teori yang tidak menjelaskan soal di depan anak.
    """
    konsep = KONSEP_TEMPLATE.get(template_id)
    return KARTU.get(konsep) if konsep else None


def kartu_untuk_banyak(template_id_list) -> list[Kartu]:
    """Kartu unik untuk sekumpulan template, urutan pertama-muncul dijaga.

    Dipakai halaman hasil: beberapa soal yang salah bisa berbagi satu
    konsep, dan anak tidak perlu membaca kartu yang sama tiga kali.
    """
    keluar: list[Kartu] = []
    terlihat: set[str] = set()
    for tid in template_id_list:
        konsep = KONSEP_TEMPLATE.get(tid)
        if konsep and konsep not in terlihat:
            terlihat.add(konsep)
            keluar.append(KARTU[konsep])
    return keluar
