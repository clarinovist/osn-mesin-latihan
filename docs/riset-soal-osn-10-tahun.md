# Riset Soal OSN Matematika SD — 10 Tahun Terakhir (2016–2026)

> Dibuat 2 Sep 2026. Menjawab dua pertanyaan: (1) seperti apa soal OSN
> matematika SD sepuluh tahun terakhir, dan (2) apakah mesin latihan sudah
> mencakup semua materi OSN matematika.
>
> Dokumen format/silabus tetap di `riset-osn-sasmo-2026.md`. Yang ini adalah
> riset **berbasis soal asli**, bukan berbasis silabus.

## 0. Ringkasan eksekutif

- **Korpus:** 65 dokumen soal asli (PDF resmi Puspresnas + arsip), meliputi
  **setiap tahun 2016–2026**, semua tahap (kecamatan, OSN-K, OSN-P, semifinal,
  final: isian singkat / uraian / eksplorasi). Terekstrak **1.305 soal**,
  1.237 di antaranya cukup terbaca untuk diklasifikasi.
- **Jawaban singkat pertanyaan 2: BELUM 100%, tapi sudah kuat.**
  85 template app menutup **74,7%** soal nyata 10 tahun terakhir
  (924 dari 1.237 soal) pada level konsep utama.
- **Cakupan sangat tidak merata per tahap** — ini temuan terpenting:

  | Tahap | Cakupan template app |
  |---|---|
  | OSN-P (provinsi) | 83,3% |
  | NASIONAL-uraian | 81,1% |
  | OSN-K (kab/kota) | 78,2% |
  | OSN-S (kecamatan) | 74,8% |
  | NASIONAL-isian singkat | 70,6% |
  | **NASIONAL-eksplorasi** | **24,4%** |

  Artinya: untuk **menembus OSN-K/OSN-P**, app sudah layak dipakai. Untuk
  **bertanding di tingkat nasional** (khususnya sesi eksplorasi), materi app
  masih jauh.
- **Hanya 2 dari 85 template yang tidak pernah muncul** di soal nyata
  (`dua_besaran_selisih`, `piktogram`) — kurasi materi sejauh ini tepat
  sasaran, bukan asal tambah.
- **Gap terbesar bukan topik SD baru, melainkan cara berpikir:** aljabar/
  sistem persamaan terselubung (74 soal), ekstremal-optimasi (35),
  kriptaritma & teka-teki angka (27), kombinatorik lanjut/graf (23),
  teori bilangan lanjut (20), geometri lanjut (22).

---

## 1. Korpus & metode (supaya bisa diulang)

### Sumber

| Sumber | Isi | Catatan |
|---|---|---|
| Hub arsip defantri.com "Kumpulan Soal OSN Matematika SD" | Link Google Drive soal resmi per tahun/tahap 2003–2026 | Sumber paling lengkap yang ditemukan |
| konsep-matematika.com (Blog KoMa) | 116 berkas soal OSC/OSK/OSP/OSN SD per tahun | Link tersembunyi di `<form>`, bukan `<a>` |
| Panduan OSN 2026 SD/MI (Puspresnas) | Format, jumlah soal, durasi, **pembobotan nilai** | `drive.google.com/file/d/1V0LlqmqCwaogB0zjSOKV94Y7c9FWNQUd` |
| Silabus OSN SD (Puspresnas/BPTI, footer "Tahun 2026") | 5 topik + KD kelas III–VI + acuan IMSO 2019 | `drive.google.com/file/d/1Os-SB9IKPv-A0-q3RLfsSpBkMdL0B0OH` |

### Sebaran dokumen per tahun

2016: 5 · 2017: 8 · 2018: 7 · 2019: 9 · 2020: 5 · 2021: 5 · 2022: 2 ·
2023: 8 · 2024: 10 · 2025: 5 · 2026: 1 — **total 65 dokumen**.

### Metode

1. Unduh PDF (`drive.usercontent.google.com/download?id=<id>&export=download&confirm=t`),
   ekstrak teks `pdftotext -layout`.
2. Pecah per nomor soal dengan pelacak urutan nomor (bukan regex `^\d+\.` polos —
   nomor pilihan jawaban dan langkah pembahasan ikut tertangkap).
3. Dedup soal identik → 1.305 soal unik.
4. **Klasifikasi konsep dibaca satu per satu oleh 6 subagen paralel**, bukan
   keyword matching. Ini disengaja: percobaan awal dengan regex menghasilkan
   282 soal tak terklasifikasi dan salah label parah (kata "satuan" dan
   "jika…maka" menyeret soal ke topik yang salah).
5. Tiap soal diberi: konsep utama, konsep sekunder, tingkat keterampilan
   (hitung rutin / multi-langkah / non-rutin), butuh gambar, tak terbaca.

### Keterbatasan yang harus jujur disebut

- **31,2% soal merujuk gambar/diagram** yang hilang saat ekstraksi teks.
  Klasifikasi soal-soal itu bertumpu pada kalimatnya saja, jadi label geometri
  bisa kurang presisi. **Ini juga temuan produk, bukan sekadar keterbatasan
  riset:** sekitar sepertiga soal OSN asli tidak bisa direplikasi sebagai teks
  murni — butuh diagram (bangun arsiran, papan berpaku, petak huruf, jaring
  bangun). Bank soal berbasis kalimat saja secara struktural tak bisa menutup
  sepertiga OSN.
- Beberapa naskah 2025 (OSN-K, semifinal) **sudah tercampur pembahasan dan
  kunci jawaban** di dalam PDF-nya. Aman untuk klasifikasi, tapi kalau naskah
  ini kelak dipakai sebagai sumber bank soal, teksnya wajib dibersihkan dulu.
- Sebagian item yang terhitung "soal" ternyata potongan instruksi pengawas
  (mis. `2024-NAS-eksplorasi-11`, `2024-NAS-teori1-5`) — sudah ditandai
  `tak_terbaca` dan dikeluarkan dari hitungan.
- 68 soal (5,2%) tidak cukup terbaca dan dikeluarkan dari hitungan cakupan.
- Sebagian berkas tingkat kecamatan bersifat lokal (Denpasar, Agam, Jepara,
  Bima), bukan naskah nasional — tetap dipakai karena mencerminkan level
  penyisihan, tapi bobotnya jangan disamakan dengan naskah Puspresnas.
- Angka cakupan dihitung pada **konsep**, bukan pada kesulitan. Soal
  `luas_arsiran` tingkat nasional jauh lebih sulit daripada template
  `luas_arsiran` app walau konsepnya "tercakup". Lihat §5.

---

## 2. Seperti apa soalnya? (temuan dari 1.237 soal)

### 2.1 Format resmi 2026 (terverifikasi dari Panduan OSN 2026)

| Tahap | Durasi | Jumlah soal | Jenis |
|---|---|---|---|
| OSN-K | 60 menit | 30 | Pilihan jamak |
| OSN-P | 60 menit | 20 | Isian singkat |
| Semifinal (daring) | — | 15 isian + 5 uraian | Isian + uraian |
| Final Teori 1 | 60 menit | 25 | Isian singkat |
| Final Teori 2 | 90 menit | 13 | Uraian |
| Final Eksplorasi | 120 menit | 6 | Eksplorasi |

**Baru & belum tercatat di dokumen lama — pembobotan kesulitan.** Nilai bukan
sekadar benar/salah:

- Semifinal isian singkat (15 soal): 2 mudah (bobot 1) · 6 sedang (1,25) ·
  7 sulit (1,5). Salah/kosong = 0 (tidak ada nilai minus).
- Semifinal uraian (5 soal, maks 3 poin): 1 mudah · 2 sedang · 3 sulit
  (bobot sama 1 / 1,25 / 1,5).
- Final: isian 25×1 = 25, uraian 13×3 = 39, eksplorasi 6×6 = 36 → total 100.

Implikasi produk: **soal sulit bernilai 1,5× soal mudah, dan tidak ada
hukuman salah.** Strategi "kerjakan yang mudah dulu lalu tebak sisanya" valid
di OSN (berbeda dari SASMO Section A yang salah = −1). Kalau app kelak
menampilkan skor prediksi, gunakan pembobotan ini, jangan rata-rata polos.

### 2.2 Bentuk soal bergeser tajam sesuai tahap

Distribusi tingkat keterampilan hasil klasifikasi:

| Tahap | Hitung rutin | Multi-langkah | Non-rutin |
|---|---|---|---|
| OSN-S (kecamatan) | 24,1% | 65,3% | 10,6% |
| OSN-K | 16,7% | 56,9% | 26,4% |
| OSN-P | 12,5% | 54,2% | 33,3% |
| NASIONAL isian | 4,1% | 48,5% | **47,4%** |
| NASIONAL uraian | 0,0% | 52,2% | **47,8%** |
| NASIONAL eksplorasi | 0,0% | 0,0% | **100%** |

Kesimpulan yang penting untuk desain produk: **di tingkat nasional, soal yang
bisa diselesaikan dengan "terapkan satu rumus" praktis nol.** Latihan drill
angka tidak akan mengangkat anak dari OSN-P ke medali nasional.

### 2.3 Distribusi 5 topik silabus pada soal nyata

| Topik silabus | Porsi soal nyata | Cakupan template app |
|---|---|---|
| Aritmatika | 24,2% | 69,5% |
| Geometri | 23,2% | 90,6% |
| Bilangan | 21,5% | 81,5% |
| Statistika Data & Pengukuran | 16,2% | **98,9%** |
| Kombinatorik (& logika) | 14,9% | **58,7%** |

Catatan: dokumen lama menduga "Geometri paling besar". Data 10 tahun
menunjukkan **Aritmatika dan Geometri praktis seimbang di puncak (24% vs 23%)**,
dan keduanya diikuti Bilangan. Diagram lingkaran 25/25/12/38% di silabus resmi
**bukan bobot topik** — itu klip-art dekoratif di banner bab Statistika
(diverifikasi visual dari PDF). Jangan dikutip sebagai bobot.

### 2.4 Konsep yang paling sering keluar (10 tahun)

Sudah ada templatenya di app:
`luas_arsiran` (56) · `rata_rata` (46) · `pecahan_operasi` (43) ·
`keliling_luas_datar` (38) · `susun_bilangan_syarat` (37) ·
`rata_rata_gabungan` (31) · `prima_faktorisasi` (29) ·
`pola_barisan_aritmetika` (28) · `kombinasi_pilih` (27) · `keterbagian` (27) ·
`perbandingan_senilai` (26) · `kecepatan_jarak_waktu` (26) ·
`jumlah_sudut_segitiga` (24) · `volume_kubus_balok` (21) ·
`diagram_batang_garis` (21) · `lingkaran_keliling_luas` (20).

### 2.5 Tren per tahun

Cakupan app stabil 68–82% sepanjang 2016–2026 (tidak ada pergeseran silabus
mendadak), tetapi **porsi soal non-rutin naik**: 2016–2019 rata-rata ~25%,
2021 41,7%, 2023 40,0%, **2024 43,5%**. Soal makin menekankan penalaran,
bukan hafalan rumus.

---

## 3. Apakah cakupan materi sudah lengkap? — jawaban rinci

### 3.1 Angka utama

- 85 template app → 78 konsep berbeda.
- Menutup **924 dari 1.237 soal (74,7%)** pada konsep utama.
- **313 soal (25,3%)** memakai konsep di luar template app, tersebar di
  109 label konsep (ekornya sangat panjang — banyak yang muncul 1-2 kali saja).
- ⚠️ **Cakupan sangat bergantung jenis keterampilan:**
  hitung rutin 79,7% · multi-langkah 80,4% · **non-rutin hanya 61,6%**.
  Dari 370 soal non-rutin, **142 (38,4%) konsepnya tidak ada di app.**
  Soal non-rutin = 29,9% dari seluruh korpus. Jadi gap bukan tersebar merata:
  ia terkonsentrasi tepat di jenis soal yang menentukan kelolosan ke nasional.

### 3.2 Gap dikelompokkan per tema (bukan per label)

| Tema gap | Jumlah soal | Contoh konsep |
|---|---|---|
| **Aljabar & sistem persamaan** | 74 | sistem persamaan dua variabel, aljabar linear SD, persamaan Diophantine, bilangan berpangkat, akar kuadrat |
| **Ekstremal / optimasi** | 35 | nilai minimum-maksimum, casework pencacahan, konstruksi susunan |
| **Pecahan-desimal-persen (urut & konversi)** | 28 | mengurutkan campuran pecahan/desimal/persen, persen "sisa dari sisa" |
| **Kriptaritma & teka-teki angka** | 27 | kriptaritma, persegi ajaib, pencacahan digit, nol akhir faktorial |
| **Kombinatorik lanjut / graf** | 23 | graf-jaringan, pewarnaan, pengubinan domino, Menara Hanoi, probabilitas dasar |
| **Geometri lanjut** | 22 | Pythagoras, menghitung bangun di dalam gambar, perbandingan luas, potong-susun |
| **Teori bilangan lanjut** | 20 | sisa simultan (CRT versi SD), deret teleskopik |
| Ekor panjang lain-lain | 84 | 73 konsep, masing-masing ≤2 soal |

### 3.3 Tiga gap yang paling layak ditutup (dengan bukti soal asli)

**(a) Sistem persamaan terselubung — 35 soal, gap tunggal terbesar.**
Ini BUKAN aljabar SMP; di OSN SD disajikan sebagai cerita dan diselesaikan
dengan *model method* / eliminasi sederhana. Contoh nyata:

- 2016-NAS-uraian-12: "Bila setiap kamar diisi 3 siswa, 8 siswa tidak dapat
  kamar. Bila diisi 4 siswa, ada 1 kamar kosong…" (dua persamaan tersembunyi)
- 2017-OSN-K-19: "Setiap pasangan dari tiga bilangan dijumlahkan hasilnya
  2017, 2018, 2035. Bilangan terbesar adalah…"
- 2017-NAS-isian-23: 456a + 654b = 2325 dan 654a + 456b = 3225 → cari
  (a+b)².

App punya `jumlah_selisih` dan `dua_besaran_selisih`, tapi keduanya kasus
paling sempit (jumlah & selisih diketahui langsung). Pola "n objek per wadah,
sisa/kurang" dan "jumlah berpasangan" belum ada.

**(b) Ekstremal / optimasi — 35 soal sebagai konsep utama, tapi 72 soal bila
konsep sekunder ikut dihitung.** Ini koreksi penting: pola "cari nilai
minimum/maksimum yang mungkin" jarang berdiri sendiri — ia menempel pada soal
bilangan, geometri, atau kombinatorik sebagai *lapisan kedua*. Pertanyaannya
"paling sedikit / paling banyak / minimal / maksimum", bukan "berapa hasilnya":

- 2016-NAS-isian-7: bentuk kelompok lomba, cari konfigurasi tertentu
- 2017-NAS-isian-17: cari a yang membuat total selisih minimal
- 2024-OSN-K-10 (contoh sejenis): "Berapa kali paling sedikit Naomi menjadi
  juara ke-3?"

Bila klaster ekstremal + konstruksi + casework digabung (utama ATAU sekunder),
totalnya **103 soal = 8,3% dari seluruh korpus**. App sudah punya
`sarang_merpati` (satu jenis ekstremal), tapi tidak punya kelas soal umum
"cari nilai ekstrem dari konfigurasi" — dan inilah lapisan berpikir yang
paling membedakan soal nasional dari soal kabupaten.

**(c) Kriptaritma & teka-teki angka — 27 soal**, muncul konsisten dari 2016
sampai eksplorasi 2019/2023. Contoh: 2017-OSN-P-8 (isi A−B=8, C+D=12 dengan
bilangan yang sesuai), 2019-NAS-isian-17 (nilai (A×B+C)×D), 2019-NAS-eksplorasi-6
(isi petak dengan digit 0–9 berbeda agar ketaksamaan benar). Silabus SASMO
menyebut cryptarithms eksplisit; app belum punya satu pun template ini.

### 3.4 Gap ke-4 yang mudah tapi sering: `desimal_persen` (28 soal)

Mengurutkan campuran bentuk (mis. `5/2 ; 0,48 ; 8/3 ; 39%` dari terbesar) dan
persen bertingkat berbasis cerita. App punya `pecahan_operasi_campuran` dan
`persen_*`, tapi tidak punya template **konversi & pengurutan lintas bentuk** —
padahal ini soal OSN-K/kecamatan yang murah dibuat dan tinggi frekuensinya.
Kandidat quick win terbaik.

### 3.5 Cakupan terbalik: template app yang tidak terpakai

Dari 85 template, hanya **2 yang tidak pernah muncul** di 1.237 soal:
`dua_besaran_selisih` (P6) dan `piktogram` (P3/P4). Tujuh lainnya langka
(≤2 kemunculan): `benar_salah_pengandaian`, `fpb_kpk_hubungan`,
`jangkauan_data`, `pola_pecahan`, `sisa_bagi_siklus`, `susun_bilangan`,
`titik_segitiga`.

Rekomendasi: **jangan dihapus.** `piktogram` dan `jangkauan_data` ada di
silabus resmi (Lingkup Materi Statistika menyebut picto-gram eksplisit) dan
relevan untuk kurikulum sekolah — app bukan hanya alat OSN. Cukup dicatat
bahwa prioritas penambahan variasi untuk template ini rendah.

---

## 4. Rekomendasi prioritas (usulan, belum dikerjakan)

Diurut berdasarkan (frekuensi soal nyata) x (kemudahan implementasi):

### Prioritas 1 — quick win, dampak langsung di OSN-K
1. `urut_bentuk_campuran` — mengurutkan pecahan/desimal/persen (28 soal).
   Malrule alami: samakan penyebut salah, bandingkan pembilang saja,
   perlakukan 0,48 sebagai 48.
2. `wadah_sisa_kurang` — "diisi 3 sisa 8, diisi 4 kurang 1 kamar"
   (bagian dari 35 soal aljabar terselubung). Ini pola paling sering.
3. `jumlah_berpasangan` — tiga bilangan, jumlah tiap pasangan diketahui.

### Prioritas 2 — menutup kelas soal yang hilang total
4. `kriptaritma_sederhana` — huruf/petak diganti digit (27 soal).
   Perlu desain jawaban non-numerik; cocok untuk mode uraian.
5. `ekstrem_konfigurasi` — "paling sedikit/paling banyak yang mungkin".
   35 soal sebagai konsep utama, **72 soal** bila konsep sekunder dihitung;
   klaster ekstremal+konstruksi+casework = 103 soal (8,3%). Prioritas
   tertinggi di kelompok ini.
6. `sisa_simultan` — bersisa 1 dibagi 2, bersisa 4 dibagi 5, dst (10 soal).
7. `casework_pencacahan` — enumerasi kasus sistematis (13 soal utama+sekunder).
   Sering jadi lapisan kedua soal kombinatorik nasional.

### Prioritas 3 — level nasional
8. `pythagoras_sd`, `pencacahan_bangun_dalam_gambar`, `perbandingan_luas`.
9. Kombinatorik lanjut: pewarnaan, pengubinan, graf/jaringan.

### Yang TIDAK direkomendasikan
- Mengejar 100% cakupan konsep. Ekor 73 konsep @<=2 soal adalah soal
  eksplorasi sekali-pakai; membuat template untuk itu tidak sepadan.
- Menghapus `piktogram`/`dua_besaran_selisih` (lihat 3.5).

---

## 5. Peringatan penting: "tercakup" bukan berarti "setara"

Angka 74,7% adalah cakupan KONSEP. Kesulitan adalah dimensi terpisah dan di
situ jurangnya lebih lebar.

Contoh konkret: `luas_arsiran` adalah konsep tersering (56 soal) dan app
punya templatenya. Tapi versi app memberi bangun standar dengan ukuran
langsung, sedangkan versi nasional menuntut memotong-susun bangun,
menyimpulkan ukuran dari relasi, atau menghitung tanpa ukuran eksplisit.
Konsepnya sama, jenis berpikirnya beda.

Bukti kuantitatifnya ada di 2.2: pada tahap nasional, 0% soal berupa
hitung rutin. Sementara template app --- karena harus deterministik dan
punya kunci tunggal serta malrule yang bisa dideteksi --- secara struktural
condong ke hitung rutin dan multi-langkah.

Konsekuensi jujur untuk positioning produk:

- Klaim yang AMAN: "melatih fondasi dan pola soal OSN tingkat sekolah,
  kabupaten, dan provinsi, dengan diagnosis letak kesalahan."
- Klaim yang TIDAK didukung data: "menyiapkan anak juara OSN nasional".
  Untuk tahap nasional dibutuhkan soal eksplorasi terbuka yang tidak punya
  kunci tunggal --- bertentangan dengan arsitektur diagnosa/malrule saat ini.

Ini juga menjelaskan kenapa cakupan NASIONAL-eksplorasi hanya 24,4%: soal
eksplorasi meminta anak MEMBUAT sesuatu (konstruksi, strategi, pembuktian),
bukan menjawab angka. Mesin latihan berbasis kunci tidak bisa menilai itu
tanpa guru --- dan itu bukan kekurangan yang bisa ditutup dengan menambah
template.

---

## 6. Data mentah & cara reproduksi

Artefak riset (lokal, tidak di-commit karena besar):

- `/tmp/osn_riset/pdf/`, `/tmp/osn_riset/pdf2/` — 65 PDF soal + hasil
  `pdftotext`.
- `/tmp/osn_riset/resmi/` — Panduan OSN 2026 + Silabus OSN SD resmi.
- `/tmp/osn_riset/soal_klas.json` — 1.305 soal terekstrak (id, tahun,
  tahap, teks).
- `/tmp/osn_riset/klasifikasi_final.json` — hasil klasifikasi per soal
  (konsep, konsep sekunder, keterampilan, butuh_gambar, tak_terbaca).
- `/tmp/osn_riset/app_konsep.json` — pemetaan 85 template app ke 78 konsep.

Untuk memperbarui riset saat naskah baru terbit:

1. Buka hub `defantri.com/2017/10/kumpulan-soal-osn-matematika-sdmi.html`,
   ambil id Drive baru dari daftar tahun.
2. Unduh via `drive.usercontent.google.com/download?id=<id>&export=download&confirm=t`
   (link `drive.google.com/file/d/<id>/view` biasa akan mengembalikan HTML
   halaman consent, bukan PDF --- periksa 5 byte pertama harus `%PDF-`).
3. Ekstrak, klasifikasi ulang, bandingkan dengan `app_konsep.json`.

Catatan teknis yang menghemat waktu di kemudian hari:

- Berkas OSN sebelum 2016 di arsip Drive butuh login Google; yang 2016+
  bisa diunduh anonim.
- Blog KoMa menyembunyikan link unduh di dalam `<input type="hidden">`
  di dalam `<form>`, bukan `<a href>` --- ekstraktor biasa tidak melihatnya.
- Teks PDF beberapa naskah disisipi watermark URL di tengah kalimat dan
  karakter zero-width; bersihkan sebelum parsing nomor soal.
