# Lembar Penilaian — Pola Bilangan P3 (20 Agustus 2026)

Pasangan dari `2026-08-20-p3-pola-bilangan-SOAL.md`.
**Jangan diperlihatkan ke anak.**

> **Perubahan dari versi pertama.** Lembar anak sekarang punya kotak isian
> yang memisahkan kode diagnosis sendiri. Akibatnya file ini **bukan lagi
> sumber utama diagnosis** — yang dibaca adalah tulisan anak. Tabel di sini
> turun perannya jadi cadangan, dipakai hanya saat kotaknya kosong atau
> ambigu.
>
> Ini perbaikan nyata: versi pertama menebak kode dari jawaban akhir memakai
> tabel yang saya sendiri belum verifikasi. Sekarang kodenya dibaca dari
> bukti.

---

## Kode diagnosis

Dari taksonomi B/K/H (`produk/Rencana Produk - Peta Jalan.md` §02), plus dua dari
riset Newman.

| Kode | Nama | Artinya untuk kamu |
|---|---|---|
| **B** | Salah baca soal | Bukan masalah matematika. Latih membaca ulang |
| **K** | Salah konsep | **Yang paling penting.** Perlu diajar ulang |
| **H** | Salah hitung | Paling ringan. Latihan + cek ulang |
| **E** | Salah tulis akhir | Kecerobohan menyalin. Bukan konsep |
| **T** | Tidak tahu | Belum pernah ketemu tipe ini. Bukan kegagalan |
| **N** | Menebak | Bisa menyembunyikan K. Wajib ditanya lisan |

**Metrik utama = jumlah K, bukan skor.**
Anak dengan 9 H skor 3 lebih siap daripada anak dengan 3 K skor 9.

---

## Alur baca — pakai ini dulu, sebelum tabel per soal

Baca **empat kotak** di tiap soal, urut. Berhenti di kode pertama yang cocok.

```
  1. Kotak "belum pernah lihat" dicentang?
       ya  →  T   (selesai, apa pun isi kotak lain)
       tidak → lanjut

  2. Kotak "Caraku" kosong, tapi ada jawaban?
       ya  →  N   (jangan dinilai lebih jauh — tanya lisan dulu)
       tidak → lanjut

  3. Kotak "mintanya apa" salah menyebut yang diminta?
       ya  →  B   (selesai, walaupun caranya benar)
       tidak → lanjut

  4. Cara di kotak "Caraku" — aturannya benar?
       tidak →  K
       ya    → lanjut

  5. Jawaban akhir sama dengan hasil di "Caraku"?
       tidak →  E
       ya, tapi salah → H
       ya, dan benar  → benar
```

Kotak nomor 3 hanya ada di soal 5, 7, 8, 9, 10, 11, 12 — soal yang rawan
salah baca. Untuk soal 1–4 dan 6, lompati langsung ke langkah 4.

**Kalau kotaknya kosong atau ambigu**, baru pakai tabel per soal di bawah,
atau protokol 5 pertanyaan.

---

## Protokol 5 pertanyaan (cadangan, kalau kotak tidak cukup)

Tanya berurutan, berhenti di titik pertama yang macet:

1. "Coba bacakan soalnya keras-keras."       macet → **B**
2. "Soal ini mintanya apa?"                  macet → **B**
3. "Kamu pakai cara apa? Kenapa begitu?"     macet → **K**
4. "Coba kerjakan lagi sambil dijelaskan."   macet → **H**
5. "Mana jawaban akhirnya?"                  macet → **E**

Jangan pakai pertanyaan bebas seperti "coba jelaskan caramu" — hasilnya tidak
konsisten antar soal.

---

## Kunci + pola kesalahan per soal

Semua kunci di bawah diverifikasi dengan kode, bukan dihitung manual.

### Bagian A

**1.  4, 9, 14, 19 → 24, 29**  (+5)

| Jawaban | Kode | Baca dari "Caraku" |
|---|---|---|
| 24, 29 | benar | |
| 24 saja | **B** | dua isian, cuma satu dibaca |
| 23, 28 / 24, 28 | **H** | "+5" tertulis, penjumlahan meleset |
| 20, 21 | **K** | pola dikira +1 |
| 24, 34 | **K** | selisih dianggap berubah tiap langkah |

---

**2.  96, 88, 80, 72 → 64**  (−8)

| Jawaban | Kode | Baca dari "Caraku" |
|---|---|---|
| 64 | benar | |
| 62 / 66 | **H** | "−8" tertulis, pengurangan meleset |
| 80 | **K** | arah pola dibalik |
| 8 | **K** | dikira pembagian |

Pola turun memancing K pada anak yang terbiasa pola naik. Salah di sini tapi
benar di no.1 = sinyal kuat.

---

**3.  1, 2, 4, 8, 16 → 32**  (×2)

| Jawaban | Kode | Baca dari "Caraku" |
|---|---|---|
| 32 | benar | |
| 24 | **K** | ada "+8" di coretan → pola tambah dipaksakan ke pola kali |
| 30 / 34 | **H** | ada "×2" di coretan, perkalian meleset |
| 31 | **K** | selisih 1,2,4,8 dilanjut jadi +15 |

**24 adalah kesalahan paling informatif di lembar ini.** Prasyarat seluruh
Bagian D. Kalau muncul, jangan lanjut ke P4.

---

**4.  2, 5, 10, 17, 26 → 37**  (selisih 3, 5, 7, 9, **11**)

| Jawaban | Kode | Baca dari "Caraku" |
|---|---|---|
| 37 | benar | |
| 35 | **K** | selisih terakhir dipakai lagi — belum lihat selisihnya berpola |
| 36 / 38 | **H** | 26 + 11 meleset |
| 33 | **K** | selisih dikira selalu +7 |

Kalau di "Caraku" ada baris selisih **3 5 7 9** tapi jawabannya salah →
hampir pasti **H**. Konsepnya sudah ada.

---

### Bagian B

**5.  A B B C ... ke-20 → C**   (siklus 4; 20 ÷ 4 = 5 sisa 0 → posisi akhir)

Kotak "mintanya apa" — jawaban sehat: "huruf ke-20 itu apa".

| Jawaban | Kode | Baca dari "Caraku" |
|---|---|---|
| C | benar | |
| A | **K** | sisa 0 dikira posisi ke-1 (off-by-one) |
| B | **K** | siklus dihitung 3 huruf, bukan 4 |
| C, tapi menulis 20 huruf satu-satu | benar — **catat** | cara manual |

Kolom terakhir bukan kesalahan. Tapi catat: di P4 angkanya jadi ke-100 dan
cara manual mati di situ.

---

**6.  merah/kuning/kuning/biru ... ke-33 → merah**   (33 ÷ 4 = 8 sisa 1)

| Jawaban | Kode | Baca dari "Caraku" |
|---|---|---|
| merah | benar | |
| biru | **K** | sisa diabaikan, ambil akhir siklus |
| kuning | **H** | ada "33 ÷ 4" di coretan, sisanya salah |

Pasangan 5 & 6 sengaja: no.6 sisa 1 (mudah), no.5 sisa 0 (jebakan).
Benar di 6 salah di 5 = kasus tepi, **bukan K berat**.

---

### Bagian C

**7.  Korek api 3, 5, 7 ... ke-10 → 21**  (3 + 2×9)

Kotak "mintanya apa" — sehat: "berapa batang untuk gambar ke-10".

| Jawaban | Kode | Baca dari "Caraku" |
|---|---|---|
| 21 | benar | |
| 23 | **K** | 3 + 2×10 — off-by-one |
| 30 | **K** | 3 × 10 — tidak sadar batang dipakai bersama |
| 19 / 20 | **H** | rumus benar, hitung meleset |
| menggambar 10 segitiga → 21 | benar — **catat** | cara manual |

**30 itu K paling sering** di soal korek api. Anak melihat gambar, bukan
sambungannya.

---

**8.  Titik segitiga 1, 3, 6, 10 ... ke-7 → 28**

1, 3, 6, 10, 15, 21, 28

| Jawaban | Kode | Baca dari "Caraku" |
|---|---|---|
| 28 | benar | |
| 21 | **B** | deret benar sampai 21, berhenti di gambar ke-6 |
| 15 | **B** | berhenti di ke-5 |
| 22 | **K** | selisih dikira tetap +4 |
| 27 / 29 | **H** | penjumlahan beruntun meleset |

21 dan 15 sering **salah didiagnosis sebagai K padahal B** — polanya benar
sempurna, anak cuma berhenti di baris yang salah. Cek deret di "Caraku":
kalau benar sampai 21, itu B.

---

### Bagian D — paling penting

Ini lompatan yang bikin anak mentok di P5: pertanyaan dibalik dari "nilai
suku" jadi "nomor suku".

**9.  5, 8, 11, 14, 17 ... di mana 41? → urutan ke-13**

Kotak "mintanya apa" **memisahkan B secara langsung di sini**:
- sehat: "cari 41 itu urutan ke berapa"
- **B**: "cari bilangan setelah 17" / "lanjutkan polanya"

| Jawaban | Kode | Baca dari "Caraku" |
|---|---|---|
| 13 | benar | |
| 41 | **B** | dikira minta nilainya |
| 12 | **K** | (41−5)÷3 = 12, lupa +1 untuk suku pertama |
| 14 | **H** | menulis deret, salah hitung di tengah |
| menulis deret 5,8,...,41 lalu hitung → 13 | benar | manual, sah untuk P3 |

**Menjawab 41 adalah B, bukan K.** Anak paham polanya; dia tidak paham
pertanyaannya. Obatnya baca soal, bukan ajar ulang pola.

---

**10.  3, 6, 12, 24 ... di mana 96? → urutan ke-6**

3, 6, 12, 24, 48, 96

| Jawaban | Kode | Baca dari "Caraku" |
|---|---|---|
| 6 | benar | |
| 96 | **B** | sama seperti no.9 |
| 5 | **H** | berhenti di 48, salah hitung urutan |
| 32 | **K** | 96 ÷ 3 — dikira pola kelipatan 3 |

Bandingkan dengan no.3. Kalau no.3 = 24 (K) **dan** no.10 = 32 (K), itu satu
K yang sama muncul dua kali: pola perkalian belum terbentuk. Catat sebagai
**satu** miskonsepsi, bukan dua.

---

### Bagian E

**11.  Selasa + 30 hari → Kamis**   (30 ÷ 7 = 4 sisa 2)

| Jawaban | Kode | Baca dari "Caraku" |
|---|---|---|
| Kamis | benar | |
| Selasa | **K** | sisa diabaikan — dikira 30 kelipatan 7 |
| Rabu | **K** | sisa dihitung dari hari ini, bukan besok |
| Jumat / Senin | **H** | 30 ÷ 7 meleset |
| menghitung kalender satu-satu → Kamis | benar — **catat** | manual |

Ini no.5 dan no.6 dalam bungkus cerita. Kalau 5 & 6 benar tapi 11 salah,
kodenya **B** (tidak mengenali ini soal siklus), bukan K. Kotak "mintanya
apa" biasanya langsung menunjukkannya.

---

**12. ★ 1,2,3 berulang, jumlah 20 angka pertama → 39**

20 ÷ 3 = 6 siklus sisa 2. 6 × 6 = 36, sisa 1+2 = 3. Total **39**.

| Jawaban | Kode | Baca dari "Caraku" |
|---|---|---|
| 39 | benar | |
| 36 | **K** | sisa 2 angka tidak dihitung |
| 40 | **K** | sisa dikira 1+3 |
| 20 | **B** | dikira menghitung banyak angka, bukan jumlahnya |
| 42 | **H** | 7 siklus × 6 — pembagian meleset |
| kosong + centang "belum pernah lihat" | **T** | wajar, setara P5 |

Kosong di sini **bukan sinyal buruk**. Dipasang untuk melihat apakah anak
mencoba atau langsung menyerah.

---

## Rekap — isi setelah menilai

| No | "Mintanya apa" | Jawaban | Kode | Catatan |
|---|---|---|---|---|
| 1 | — | | | |
| 2 | — | | | |
| 3 | — | | | |
| 4 | — | | | |
| 5 | | | | |
| 6 | — | | | |
| 7 | | | | |
| 8 | | | | |
| 9 | | | | |
| 10 | | | | |
| 11 | | | | |
| 12 ★ | | | | |

**Jumlah K: ___**  ← angka yang dipantau

**Jumlah T (centang "belum pernah lihat"): ___**  ← bukan kegagalan, ini
peta materi yang belum diajarkan

Daftar K yang muncul (tulis miskonsepsinya, bukan nomor soalnya):

1. ______________________________________________
2. ______________________________________________
3. ______________________________________________

---

## Cara membaca hasilnya

**K = 0, H banyak** → konsep pola sudah terbentuk. Yang kurang aritmetika
dasar. Jangan tambah soal pola; latih perkalian/penjumlahan cepat.

**K = 1–2, terkonsentrasi di satu tipe** → sasaran jelas. Ajar ulang satu
topik itu saja, lalu uji dengan **soal beda angka, skill sama**. Jangan
mengulang soal yang sama persis — anak bisa hafal jawabannya.

**K ≥ 3 tersebar** → jangan naik ke P4. Turunkan dulu: kembali ke pola
selisih tetap sampai otomatis, baru naik ke bertingkat.

**B banyak (≥3)** → bukan masalah matematika, dan tidak akan membaik dengan
tambah soal. Latihannya: kotak "mintanya apa" itu sendiri. Minta anak
mengisinya dulu untuk semua soal sebelum mulai menghitung apa pun.

**T banyak** → bukan masalah sama sekali. Ini daftar materi yang belum
diajarkan. Berguna untuk menyusun urutan belajar, bukan untuk menilai.

**N banyak (jawaban tanpa "Caraku")** → hentikan penilaian, tanya lisan
dulu. Semua kode di atas tidak bisa dipercaya tanpa coretan.

**Bagian D dua-duanya dijawab 41 dan 96** → satu B, bukan dua. Anak belum
pernah ketemu soal terbalik. Ini materi baru, bukan kelemahan.

---

## Sinyal tambahan yang cuma muncul di format kotak ini

Tiga hal yang tidak terlihat di lembar versi pertama:

**"Caraku" isinya cuma menyalin ulang soal** → anak tidak tahu harus mulai
dari mana, tapi enggan mencentang "belum pernah lihat". Perlakukan sebagai
**T**, bukan K. Dan pertimbangkan mengubah kalimat centangnya supaya terasa
lebih aman diakui.

**"Mintanya apa" benar, tapi "Caraku" mengerjakan hal lain** → anak paham
pertanyaannya lalu lupa di tengah jalan. Ini bukan B dan bukan K — ini beban
memori kerja. Biasanya membaik kalau soal dipecah jadi langkah bernomor.

**Cara manual dipakai di semua soal siklus (5, 6, 11)** → konsepnya benar,
tapi belum ada jalan pintas pembagian. Ini penanda **kesiapan naik level**,
bukan kesalahan. Di P4 angka jadi ke-100 dan cara manual berhenti bekerja.

---

## Perkiraan yang belum terverifikasi

Ditulis terbuka supaya tidak dianggap fakta:

- Tabel "jawaban salah → kode" disusun dari bentuk soalnya, **bukan** dari
  data kesalahan anak nyata. Sebagian pasti meleset. Kalau anak menjawab di
  luar tabel, alur baca 5-langkah dan protokol Newman yang menang.
- Penyetaraan "setara SASMO P3" berdasarkan bentuk soal umum di level itu,
  bukan dari past paper tahun tertentu.
- Soal 12 kemungkinan besar terlalu berat untuk P3 murni. Sengaja, sebagai
  pengukur, bukan target.
- **Format 4 kotak ini belum pernah diuji ke anak.** Risiko yang saya
  antisipasi: 12 soal × banyak isian bisa bikin anak lelah menulis dan
  berhenti bukan karena tidak bisa. Karena itu kotak "mintanya apa" hanya
  dipasang di 7 soal, bukan 12. Kalau sesi pertama menunjukkan anak mulai
  mengosongkan kotak di paruh kedua, **kurangi jumlah soal jadi 8**, jangan
  kurangi kotaknya.
