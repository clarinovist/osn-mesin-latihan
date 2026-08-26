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

## Dipakai lewat website (cara utama)

**https://<domain-anda>** — pengguna `guru`.

Semuanya dari satu tempat, tidak perlu terminal:

**1. Buat sesi** — tombol "Buat sesi baru untuk <nama>" di halaman utama.
Seed-nya selalu baru dan berbeda antar anak, jadi soalnya tidak pernah
terulang dan Andi tidak bisa menyalin Bila.

**2. Cetak lembar** — kolom **Lembar** di tabel sesi:

- `soal` — untuk anak. Buka lalu Ctrl+P (Cmd+P).
- `kunci` — untuk kamu. Memuat kunci + tabel diagnosis, **jangan sampai
  terlihat anak**.

Cetak pada **skala 100%**, jangan "fit to page". Menyekalakan mengecilkan
kotak Caraku, padahal itu inti lembarnya.

**3. Masukkan hasil** — klik nomor sesinya. Ketik jawaban anak dan ringkasan
kotak "Caraku". Kode diagnosis muncul otomatis; kolom Kode hanya diisi kalau
kamu tidak setuju dengan usulan mesin.

**4. Baca laporan** — tautan "Lihat laporan" di tiap anak. Tiga bagian:

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

## Dipakai lokal di Mac (cadangan)

Berguna kalau VPS bermasalah, atau untuk menghasilkan PDF (container tidak
punya Chrome, jadi tautan `soal` di website menghasilkan halaman untuk
dicetak langsung dari browser, bukan berkas PDF).

```bash
cd ~/Documents/osn/mesin
./.venv/bin/python buat_lembar.py --pdf   # cetak lembar + PDF
./.venv/bin/python sajikan.py             # halaman guru di 127.0.0.1:8724
```

Basis data lokal terpisah dari VPS. Pakai salah satu saja supaya datanya
tidak bercabang.

## Akun & siswa

Tautan **"Akun & siswa"** di halaman utama:

- **Ganti sandi** — minimal 12 karakter, perlu sandi lama. Ganti sandi acak
  bawaan deploy dengan yang kamu ingat.
- **Tambah siswa** — tanpa SSH. Pakai nama panggilan atau inisial, bukan
  nama lengkap.

Siswa sengaja tidak bisa dihapus: menghapusnya ikut menghapus seluruh sesi,
jawaban, dan diagnosisnya. Kalau seorang anak berhenti, biarkan saja
datanya — tidak mengganggu apa pun.

Untuk pemasangan lokal di Mac, daftar awal ada di `SISWA` pada
`siapkan_db.py` (aman dijalankan ulang).

## Cetak ulang lembar yang hilang

Seed tercantum di kolom terakhir tabel sesi dan di lembar kunci. Sesi lama
tetap bisa dibuka lewat tautan `soal` — lembarnya dibangkitkan ulang dari
seed, jadi selalu sama persis.

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
| `web.py` | halaman guru + rute lembar |
| `sandi.py` | palang sandi |
| `sajikan.py` | menjalankan server |
| `cadangkan.sh` | tarik cadangan basis data dari VPS ke Mac |
| `Dockerfile` | container untuk VPS |

## Di VPS

| | |
|---|---|
| Alamat | https://<domain-anda> |
| Container | `osn-mesin`, restart otomatis |
| Data | `/opt/osn/data` (basis data, sandi, lembar) |
| Cadangan | harian 22:00 ke `mesin/cadangan/` di Mac |

```bash
ssh <host-vps> "sudo docker ps --filter name=osn-mesin"
ssh <host-vps> "sudo docker logs osn-mesin --tail 30"
./cadangkan.sh          # cadangan manual kapan saja
```

Perubahan kode dideploy otomatis lewat GitHub Actions:

```
push ke main -> test -> build image -> dorong ke GHCR -> VPS tarik & ganti
             -> verifikasi situs hidup dari internet
```

Cukup `git push`. Tidak ada langkah manual di VPS, dan **jangan build di
VPS** — build yang gagal di sana bisa menjatuhkan situs yang sedang jalan.

Pantau:

```bash
gh run list --repo clarinovist/osn-mesin-latihan
gh run watch <id> --exit-status
```

**Kenapa deploy memakai digest, bukan tag `latest`**: tag bisa berubah
antara build dan deploy. Yang terpasang harus persis image yang baru saja
lolos test.

**Kalau deploy gagal**, skrip di VPS memulihkan image sebelumnya sendiri.
Container hanya diganti setelah image baru terbukti ada, dan hanya
dipertahankan kalau lolos pemeriksaan sehat. Sehat berarti menjawab **401**
tanpa kredensial — server hidup dan palang sandi aktif. Menjawab 200 tanpa
diminta sandi justru berarti palangnya jebol.

### Akses deploy

Kunci deploy terpisah dari kunci pribadi, dipasang dengan `command=` di
`authorized_keys` sehingga hanya `/usr/local/bin/osn-deploy` yang bisa
jalan. Kalau kunci itu bocor, yang bisa dilakukan penyerang terbatas pada
menarik image dan mengganti satu container — bukan shell, bukan sudo.

Secret yang dipakai: `VPS_DEPLOY_KEY`, `VPS_HOST_KEY`, `VPS_HOST`,
`VPS_USER`, `SITUS`.


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
