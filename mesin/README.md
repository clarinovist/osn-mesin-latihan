# Mesin Latihan Pola Bilangan

Alur mingguan: cetak lembar -> anak kerjakan di kertas -> masukkan hasil ->
baca laporan.

## Sekali saja (sudah dilakukan)

```bash
cd ~/Documents/osn/mesin
python3 -m venv .venv
./.venv/bin/pip install pytest
./.venv/bin/python siapkan_db.py
```

## Tiap sesi latihan

**1. Cetak lembar**

```bash
cd ~/Documents/osn/mesin
./.venv/bin/python buat_lembar.py --pdf
```

Menghasilkan 4 berkas di `lembar/` — SOAL dan PENILAIAN untuk tiap anak.
Seed-nya berbeda tiap kali dan berbeda antar anak, jadi soalnya selalu baru
dan Andi tidak bisa menyalin Bila.

Cetak pada **skala 100%**, jangan "fit to page". Menyekalakan mengecilkan
kotak Caraku, padahal itu inti lembarnya.

Berikan yang `-SOAL.pdf` ke anak. Simpan yang `-PENILAIAN.pdf` untuk diri
sendiri — memuat kunci dan tabel diagnosis.

**2. Masukkan hasil**

```bash
./.venv/bin/python sajikan.py
```

Buka `http://127.0.0.1:8724`, pilih sesinya. Untuk tiap soal ketik jawaban
anak dan ringkasan isi kotak "Caraku". Kode diagnosis muncul otomatis; kolom
Kode hanya diisi kalau kamu tidak setuju dengan usulan mesin.

Kalau mau memasukkannya dari HP sambil memegang kertas:

```bash
./.venv/bin/python sajikan.py --jaringan
```

**3. Baca laporan**

Tautan "Lihat laporan" di tiap anak. Tiga bagian:

- **Tren per sesi** — yang dipantau kolom K, bukan Benar
- **Miskonsepsi yang bertahan** — muncul di >1 sesi berarti belum tuntas
  meski angkanya sudah diganti
- **Materi yang belum diajarkan** — dari centang "belum pernah lihat"

## Membaca kodenya

| Kode | Artinya | Tindakan |
|---|---|---|
| **K** | salah konsep | **yang paling penting** — ajar ulang |
| **B** | salah baca soal | latih baca, bukan ajar ulang materi |
| **H** | salah hitung | paling ringan, latihan saja |
| **E** | salah tulis akhir | kecerobohan menyalin |
| **T** | belum pernah lihat | bukan kegagalan, ini peta materi |
| **N** | menebak | berhenti nilai, tanya lisan dulu |

**Metrik utama jumlah K, bukan skor.** Anak dengan 9 H skor 3 lebih siap
daripada anak dengan 3 K skor 9.

Cara membaca polanya:

- **K = 0, H banyak** -> konsep sudah terbentuk; latih aritmetika, jangan
  tambah soal pola
- **K = 1-2 terkumpul di satu tipe** -> sasaran jelas, ajar ulang satu topik
  itu lalu uji dengan soal beda angka
- **K >= 3 tersebar** -> jangan naik level, turunkan dulu
- **B banyak** -> bukan masalah matematika; latihannya kotak "mintanya apa"
- **N banyak** -> hentikan penilaian, tanya lisan; kode lain tidak bisa
  dipercaya tanpa coretan

## Menambah anak

Tambahkan namanya ke daftar `SISWA` di `siapkan_db.py`, lalu jalankan lagi.
Aman diulang — yang sudah ada tidak terduplikasi.

## Cetak ulang lembar yang hilang

Seed tercetak di lembar PENILAIAN.

```bash
./.venv/bin/python buat_lembar.py --siswa Andi --seed 9593439 --pdf
```

## Menjalankan test

```bash
./.venv/bin/python -m pytest __tests__/ -q
```

## Susunan berkas

| Berkas | Isi |
|---|---|
| `templates.py` | 12 tipe soal — soal, kunci, dan malrule dihitung dari parameter |
| `generator.py` | seed -> parameter, dengan batas yang menjaga level P3 |
| `skema.py` | definisi tabel |
| `basis.py` | akses basis data |
| `diagnosa.py` | jawaban -> kode B/K/H/E/T/N |
| `cetak.py` | render HTML lembar soal & penilaian |
| `buat_lembar.py` | perintah cetak |
| `web.py` | halaman guru |
| `sajikan.py` | menjalankan server |

## Batas yang diketahui

- **Lembar 12 soal = 5 halaman.** Sudah dicoba dipadatkan; memangkas kotak
  Caraku mengurangi ruang tulis tanpa mengurangi halaman. Kotak yang terlalu
  kecil membuat anak berhenti menulis, dan kotak kosong tidak bisa dibedakan
  dari tidak bisa mengerjakan.

- **Tiga tipe soal variasinya tipis**: `titik_segitiga` 7 varian,
  `deret_geometri` 18, `deret_terbalik_geometri` 24. Batas matematis, bukan
  bug — memperlebar akan melewati level P3. Untuk 2 anak mingguan,
  `titik_segitiga` mulai berulang setelah ~2 bulan. Solusinya menambah tipe
  soal baru, bukan memaksa parameter yang ada.

- **Tabel malrule belum diuji ke anak nyata.** Disusun dari bentuk soalnya.
  Sebagian pasti meleset. Kalau anak menjawab di luar tabel, mesin mengaku
  tidak tahu dan menyerahkan ke guru — itu disengaja. Kolom `kode_usulan`
  dan `kode_final` disimpan terpisah supaya nanti bisa diukur seberapa
  sering mesin salah.

- **Data anak tidak masuk git.** `latihan.db` dan `lembar/` diblokir
  .gitignore.
