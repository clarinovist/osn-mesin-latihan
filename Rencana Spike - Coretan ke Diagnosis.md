# Rencana Spike — Coretan ke Diagnosis

**Status dokumen:** sumber kebenaran untuk eksekusi spike.
`Rencana Spike - Coretan ke Diagnosis.html` adalah render versi 14 Agustus
yang **sudah tertinggal** dari dokumen ini — biarkan sebagai artefak
historis, jangan dipakai sebagai panduan kerja.

Rencana teknis · spike · v1 · disusun 14 Agustus 2026 · direvisi 17 Agustus 2026

Menguji satu asumsi sebelum membangun apa pun: apakah AI benar-benar bisa
membaca cara berpikir anak 9 tahun dari goresan tangannya di layar HP.

---

## Asumsi — yang sedang dipertaruhkan

Seluruh produk berdiri di atas satu klaim yang belum diuji: tinta bertimestamp
+ jawaban yang diketik cukup untuk mendiagnosis kesalahan anak sebagai B, K,
atau H — salah baca soal, salah konsep, atau salah hitung.

Kalau klaim itu tidak terbukti, produk ini turun jadi aplikasi latihan soal
biasa, dan tidak layak dibangun. Jadi yang dikerjakan pertama bukan
kurikulumnya, bukan graf topiknya, bukan mode anaknya — melainkan lingkaran
terkecil yang bisa membuktikan atau menggugurkan klaim itu.

| | |
|---|---|
| **Durasi** | 5–7 hari kerja |
| **Cakupan** | 10 soal dari Tes Kalibrasi Minggu 0 |
| **Penguji** | Satu anak (kelas 4), satu orang tua |
| **Keluaran** | **Dua** angka: berapa dari 10 diagnosis cocok dengan penilaian Bapak — satu untuk heuristik murni, satu untuk LLM (lihat "Dua implementasi") |

> **Perubahan dari versi 14 Agustus.** Keluarannya dulu satu angka (LLM saja).
> Sekarang dua, karena PRD §2.3.2 menetapkan Tahap B punya baseline
> deterministik yang wajib diukur berdampingan. Alasannya di bagian
> "Dua implementasi" di bawah — ini perubahan terbesar di revisi ini dan ia
> menambah pekerjaan Hari 4.

---

## Keputusan — aplikasinya tidak menyentuh internet sama sekali

Ini keputusan arsitektur terpenting di spike, dan bukan sekadar
penyederhanaan. Aplikasi Android hanya merekam goresan lalu mengekspor satu
berkas JSON. Diagnosisnya dijalankan terpisah oleh skrip di Mac.

- **Tidak ada API key di dalam APK.** Kunci Anthropic tidak pernah masuk ke
  perangkat. Persoalan yang biasanya makan waktu berhari-hari (proxy,
  penyimpanan kunci, rotasi) hilang seluruhnya dari spike.
- **Iterasi prompt dalam hitungan detik, bukan build.** Data goresan anak
  direkam sekali, lalu prompt diagnosis bisa diputar ulang puluhan kali
  terhadap data yang sama. Kalau AI-nya ada di dalam aplikasi, tiap perbaikan
  prompt berarti build ulang dan minta anak menulis lagi.
- **Risikonya terisolasi.** Kalau diagnosisnya gagal, yang terbuang hanya
  skrip — kanvas tulisnya tetap terpakai.

Jaminannya ditegakkan secara struktural, bukan lewat niat baik: izin
`android.permission.INTERNET` tidak dicantumkan di manifest. Aplikasinya
secara teknis tidak bisa mengirim apa pun ke mana pun, dan itu bisa diperiksa
siapa saja dalam sepuluh detik.

---

## Bagian 1 — Aplikasi Android, perekam goresan

### Tumpukan teknologi

Kotlin + Jetpack Compose, minSdk 26, tanpa dependensi jaringan, tanpa
database. Satu Activity. Data sesi ditulis sebagai JSON ke penyimpanan
**internal** aplikasi (`files/`, bukan `/sdcard/`) — lihat "Ekspor" soal
kenapa lokasinya penting.

### Inti teknisnya: satu fungsi

Seluruh nilai spike ini ada di ketelitian satu hal — merekam titik goresan
dengan waktu. Compose `pointerInput` saja tidak cukup: ia melaporkan satu
posisi per frame, sekitar 60–120 titik per detik. Yang diperlukan adalah titik
historis di antara frame, yang dibawa `MotionEvent`.

```kotlin
// Ambil titik historis, bukan cuma posisi terakhir per frame.
// Satu MotionEvent bisa membawa 5–10 sampel yang tertinggal.
fun MotionEvent.toSamples(t0: Long): List<Sample> = buildList {
    for (h in 0 until historySize) {
        add(Sample(
            x = getHistoricalX(h),
            y = getHistoricalY(h),
            t = getHistoricalEventTime(h) - t0,
        ))
    }
    add(Sample(x, y, eventTime - t0))
}
```

Ini yang membedakan "gambar tulisan tangan" dari "rekaman proses menulis".
Tanpa presisi waktu ini, seluruh tesis produk hilang.

**Fungsi ini wajib punya golden test sebelum dipakai ke anak** (PRD §8.8).
Alasannya bukan disiplin umum: kegagalan di lapisan ini **tidak bisa
diperbaiki belakangan**. Kalau titik historis hilang, salah urut, atau
timestamp-nya bergeser, satu-satunya perbaikan adalah meminta anak
mengerjakan ulang soal yang sama — yang justru dilarang oleh alasan
arsitektur batch. Bentuknya: rekam sekali urutan `MotionEvent` nyata
(termasuk yang membawa `historySize > 1`), simpan sebagai fixture, lalu
pastikan `toSamples()` selalu mengembalikan daftar sampel yang sama persis —
jumlah, urutan, dan selisih waktu relatif terhadap `t0`.

Ini satu-satunya test yang wajib ada di spike. Sisanya menyusul di v1.

### Bentuk kanvas

Satu kanvas per langkah, tinggi tetap sekitar 3 cm, lebar penuh. Anak
menambah langkah sesuai kebutuhan lewat tombol manual (bukan deteksi
otomatis — PRD §6.1). Jawaban akhir diketik di kotak terpisah, dan hanya
kotak itu yang menentukan benar atau salah — tulisan tangan tidak pernah
dipakai untuk menilai.

```
┌─────────────────────────────────────────┐
│ Soal 2 · Hitunglah 2/3 + 3/4 − 1/2      │
├─────────────────────────────────────────┤
│ Langkah 1  ▏                            │  ← kanvas tinta
├─────────────────────────────────────────┤
│ Langkah 2  ▏                            │
├─────────────────────────────────────────┤
│            + tambah langkah             │
├─────────────────────────────────────────┤
│ Jawaban akhir:  [        ]  ← diketik   │
└─────────────────────────────────────────┘
```

Untuk spike, cukup satu bentuk kanvas ini. Kanvas gambar bebas untuk geometri
dan kanvas daftar berbaris untuk kombinatorik ditunda — 10 soal ujinya dipilih
yang semuanya cocok dengan kanvas berlangkah.

### Bentuk data

Vektor, bukan gambar. Gambar hanya dirender belakangan oleh skrip diagnosis.

```json
{
  "sesi_id": "2026-08-20T16:04:11",
  "soal_id": 2,
  "langkah": [
    {
      "indeks": 0,
      "goresan": [
        { "mulai_ms": 8420, "titik": [[112,44,8420],[118,41,8428]] }
      ],
      "jumlah_hapus": 0
    }
  ],
  "jawaban_diketik": "11/12",
  "jawaban_ditulis_pada_ms": 51200,
  "selesai_ms": 63800
}
```

### Turunan waktu yang dihitung aplikasi

Empat angka per soal, dihitung dari goresan, dikirim bersama JSON supaya
tahap diagnosis tidak perlu menurunkannya sendiri:

| Ukuran | Artinya kalau nilainya tinggi |
|---|---|
| Jeda sebelum goresan pertama | Macet di memahami soal, bukan di menghitung |
| Durasi per langkah | Menunjukkan langkah mana yang sulit, bukan cuma soal mana |
| Jumlah hapus per langkah | Menumpuk di satu titik = konsep goyah persis di situ |
| Jawaban ditulis sebelum langkah selesai | Menebak lalu mengarang prosesnya |

### Yang dibangun, persisnya

- **Layar 1** — daftar 10 soal, tandai mana yang sudah dikerjakan
- **Layar 2** — kanvas berlangkah + kotak jawaban + tombol selesai
- **Layar 3** — "terima kasih", lalu tombol ekspor untuk orang tua

Tidak ada akun, tidak ada pengaturan, tidak ada nilai yang ditampilkan ke
anak, tidak ada suara, tidak ada animasi perayaan. Anak tidak boleh tahu
skornya.

### Ekspor: jalur adb yang harus diverifikasi Hari 2

Rencana: tarik file lewat kabel USB dari internal storage app.

```bash
adb exec-out run-as <pkg> cat files/sesi-<id>.json > sesi-<id>.json
```

**Ini belum pernah diuji di HP target dan tidak boleh diasumsikan jalan.**
Sejak Android 11, akses `adb pull` ke `/sdcard/Android/data/<pkg>/`
diperketat dan bisa gagal tergantung versi OS dan vendor. `run-as` bekerja
karena APK ini self-signed dan debuggable (tidak pernah masuk Play Store) —
tapi sebagian vendor tetap membatasinya.

Verifikasi ini masuk Hari 2 dengan sengaja: kalau gagal, ketahuan sebelum ada
data anak yang tersandera di HP. **Fallback:** `ACTION_SEND` ke folder lokal
Mac (AirDrop/kabel) — tetap tanpa jaringan keluar, cuma lebih manual.

---

## Bagian 2 — Diagnosis: di Mac, bukan di HP

Diagnosis berjalan dua tahap otomatis (A dan B) lalu satu tahap manusia (C).
Ini struktur yang sama dengan PRD §2.3, dipakai apa adanya di spike supaya
yang diuji memang pipeline yang akan dipakai v1, bukan versi pendeknya.

### Tahap A — malrule (deterministik, tanpa LLM)

Cocokkan jawaban akhir anak ke **prediksi malrule**, bukan ke tabel pasangan
`(soal, jawaban_salah)`.

Malrule adalah *aturan salah* yang dinyatakan sebagai fungsi atas parameter
soal. Contoh, dari sidik jari yang sudah ada di Panduan Orang Tua:

```yaml
template_id: pecahan_operasi_campuran
parameter:
  suku: [ {n: 2, d: 3, tanda: +}, {n: 3, d: 4, tanda: +}, {n: 1, d: 2, tanda: -} ]
  # ditampilkan ke anak sebagai: 2/3 + 3/4 − 1/2
jawaban_benar: fungsi(suku)          # → 11/12

malrule:
  id: pecahan.operasi_pembilang_penyebut_terpisah
  prediksi(suku): Σ(tanda·n) / Σ(tanda·d)
  kode: K
  alasan_singkat: "pembilang & penyebut dioperasikan sendiri-sendiri"
```

Untuk parameter di atas malrule memprediksi (2+3−1)/(3+4−2) = **4/5** —
persis jawaban salah yang tercatat di Panduan Orang Tua, sementara jawaban
benarnya 11/12.

Kenapa fungsi dan bukan tabel: begitu angkanya diganti (yang akan terjadi
terus-menerus di v1 untuk sesi verifikasi), tabel literal tidak cocok lagi
dan diagnosis jatuh ke jalur heuristik yang lebih lemah. Fungsi tetap
berlaku. Untuk spike ini juga menghemat kerja — 10 soal uji cukup diwakili
beberapa malrule, bukan 10 entri terpisah.

Kalau **dua malrule berkode berbeda** memprediksi jawaban yang sama, Tahap A
tidak memilih; ia menyerahkan ke Tahap B. Tidak ada jalur di mana ambiguitas
berujung otomatis ke K.

### Tahap B — pola tinta, dua implementasi

**Ini perubahan terbesar dari rencana 14 Agustus.** Versi lama langsung
memakai LLM. Versi ini menjalankan dua implementasi berdampingan atas data
yang sama:

| Implementasi | Bentuk | Biaya |
|---|---|---|
| `tinta_heuristik` | Aturan if-then murni atas turunan waktu: lancar-tanpa-ragu-tapi-salah → K; langkah benar dengan koreksi di titik hitung → H; jawaban ditulis duluan → menebak/B; sinyal campur → tidak pasti | Nol, offline, deterministik |
| `tinta_llm` | Render PNG per langkah + ringkasan waktu → `claude-opus-5`, adaptive thinking + structured output | API, per soal |

Alasan baseline ini wajib ada: tanpa dia, pertanyaan **"apakah LLM-nya
sebenarnya perlu?"** tidak punya cara dijawab. Kalau heuristik murni ternyata
sudah ≥7/10 dan nol false-K, LLM keluar dari lingkup v1 seluruhnya — dan itu
penghematan permanen yang cuma bisa dibuktikan sekarang, saat datanya masih
segar dan anak masih tersedia untuk wawancara penengah. Kalau heuristik
gagal, selisih dua angka itu adalah pembenaran konkret untuk biaya LLM,
bukan asumsi.

Heuristiknya sengaja ditulis sederhana. Tujuannya bukan menang, tapi
**menetapkan lantai**: berapa yang bisa dicapai tanpa AI sama sekali.

### Yang diterima `tinta_llm`

- Soal dan jawaban benarnya
- Jawaban yang diketik anak
- Satu gambar per langkah, berurutan
- Ringkasan waktu: jeda awal, durasi tiap langkah, jumlah hapus, apakah
  jawaban mendahului langkah
- Malrule yang berlaku untuk template soal itu, beserta prediksinya

### Yang harus dikembalikan model

```json
{
  "kode":       "B | K | H | benar",
  "keyakinan":  "tinggi | sedang | rendah",
  "bukti":      "apa yang terlihat di goresan atau waktunya",
  "diagnosis":  "satu kalimat untuk orang tua, tanpa istilah teknis",
  "topik":      "pecahan | satuan waktu | urutan operasi | …",
  "terbaca":    true
}
```

Kolom `terbaca` itu penting. Model harus boleh menyerah. Diagnosis percaya
diri di atas tulisan yang sebenarnya tidak terbaca jauh lebih berbahaya
daripada mengaku tidak tahu — dan berapa sering kolom itu bernilai `false`
adalah salah satu hasil utama spike ini.

### Jejak versi & cache

Tiap hasil diagnosis menyimpan `aturan_versi`, `prompt_versi`, dan `model`
(PRD §2.5). Ini bukan administrasi: batas **maksimal 3 putaran perbaikan
prompt** (lihat "Gerbang") tidak bisa ditegakkan — bahkan tidak bisa
dihitung — kalau hasil tidak membawa identitas aturan yang menghasilkannya.

Respons LLM di-cache berkunci hash `(data mentah + prompt_versi + model)`.
Iterasi yang tidak mengubah ketiganya membaca cache, bukan memanggil API
ulang. Efeknya: memutar ulang seluruh 10 soal jadi gratis dan angka
gerbangnya selalu bisa direproduksi persis.

### Tahap C — tinjauan orang tua

Skrip menulis satu file YAML per sesi berisi `kode_awal` + `alasan_singkat` +
jejak versi, dengan `kode_final` **dikosongkan**. Bapak mengisinya di editor.
Tidak ada UI.

> **Satu aturan yang tidak boleh dilanggar.** OCR tidak pernah menentukan
> benar atau salah. Benar-salah datang dari kotak jawaban yang diketik anak.
> Tulisan tangan hanya bahan untuk mendiagnosis proses. Sekali anak merasa
> dicurangi karena angka 4-nya dibaca 9, kepercayaannya hilang dan tidak
> kembali.

---

## Bagian 3 — Protokol pengujian

1. **Hari uji.** Anak mengerjakan 10 soal di HP, sekitar 30 menit, tanpa
   didampingi. Katakan terus terang ini bukan ujian dan tidak ada nilainya.
2. **Bapak menilai lebih dulu.** Buka hasilnya, lihat coretan digitalnya,
   tentukan sendiri kode B/K/H untuk tiap soal yang salah. Tulis di kertas.
   Ini dilakukan **sebelum** menjalankan skrip — kalau tidak, penilaian Bapak
   akan terpengaruh jawaban AI dan pengujiannya jadi tidak berarti.
3. **Baru jalankan skrip.** Bandingkan kode per soal, **untuk kedua
   implementasi Tahap B secara terpisah.**
4. **Wawancara.** Besoknya, tanyakan 3–4 soal yang salah. Ini yang menentukan
   kode mana yang sebenarnya benar kalau Bapak dan sistem berbeda pendapat.

### Wawancara memakai protokol 5-prompt NEA

Menggantikan "coba jelaskan caramu" yang bebas. Urutannya tetap, tidak
diimprovisasi:

1. "Baca soal ini."
2. "Ceritakan apa yang diminta."
3. "Tunjukkan bagaimana kamu dapat jawabannya, ceritakan pikiranmu."
4. "Kerjakan sambil dijelaskan."
5. "Tulis jawabannya."

Alasan: Newman's Error Analysis adalah saudara akademik B/K/H (B≈Reading+
Comprehension, K≈Transformation, H≈Process Skills) dan secara historis
dioperasikan lewat protokol tetap, bukan interpretasi bebas. Pertanyaan bebas
membuat penengah jadi ikut menebak — padahal justru wawancara inilah wasit
yang menentukan angka gerbang.

**Jangan tambah kategori "Encoding"** (paham & hitung benar tapi salah tulis
jawaban akhir) ke skema output. Jawaban akhir diketik, bukan OCR, jadi
kesalahan tulis-akhir nyaris tidak mungkin di jalur ini. Kalau muncul, catat
manual saat wawancara — jangan ubah skema kode.

---

## Gerbang — kriteria lulus dan gagal

Ditetapkan sekarang, sebelum ada data — supaya hasilnya tidak bisa
dirasionalisasi belakangan. **Diukur dua kali: sekali untuk
`tinta_heuristik`, sekali untuk `tinta_llm`.**

### Lulus → lanjut bangun v1

- Minimal **7 dari 10** kode B/K/H cocok dengan penilaian Bapak (setelah
  wawancara jadi penengah)
- **Nol** kasus sistem menyebut "K" untuk kesalahan yang sebenarnya "H" —
  salah tuduh konsep itu yang paling mahal, karena mengirim anak mengulang
  materi yang sebenarnya sudah dipahami
- Anak mau menulis di layar sampai soal ke-10 tanpa mengeluh soal alat
  tulisnya

### Gagal → hentikan, ganti pendekatan

- Anak menolak menulis dengan jari, atau tulisannya jadi jauh lebih buruk
  daripada di kertas — hentikan di hari pertama, jangan diteruskan sampai 10
  soal
- `terbaca: false` muncul di lebih dari 4 dari 10 soal
- Kecocokan di bawah 5 dari 10 pada **kedua** implementasi, atau LLM berulang
  kali membangun diagnosis yang terdengar meyakinkan di atas pembacaan yang
  keliru

### Membaca dua angka itu

| Heuristik | LLM | Artinya |
|---|---|---|
| Lulus | — | **LLM keluar dari lingkup v1.** Tahap B jalan tanpa biaya dan tanpa jaringan. Hasil terbaik yang mungkin. |
| Gagal | Lulus | Selisihnya adalah pembenaran biaya LLM. Heuristik tetap dipertahankan sebagai pembanding regresi tiap kali prompt berubah. |
| Gagal | Gagal | Kanal tinta yang gugur, **bukan produknya** — Tahap A malrule + tinjauan orang tua masih berdiri sendiri. |

Di antara keduanya — 5 atau 6 cocok — artinya promptnya yang perlu
diperbaiki, bukan tesisnya yang gugur. Karena data goresan sudah tersimpan,
putaran perbaikan berikutnya tidak perlu melibatkan anak sama sekali.

**Batas maksimal 3 putaran perbaikan prompt** di atas data yang sama sebelum
memutuskan lulus/gagal final — supaya tidak diam-diam overfitting ke 10 soal
satu anak ini. Batas ini dihitung dari `prompt_versi` yang tercatat, bukan
dari ingatan.

---

## Urutan — rencana harian

| Hari | Pekerjaan | Selesai kalau |
|---|---|---|
| 1 | Kanvas tinta + perekaman titik historis + **golden test `toSamples()`** | Menggambar di layar terasa mulus; JSON berisi ribuan titik dengan waktu; test hijau di atas fixture `MotionEvent` nyata |
| 1 | **Tes 10 menit ke anak — cukup coret-coret bebas** | Anak nyaman menulis dengan jari. **Kalau tidak, berhenti di sini.** |
| 2 | Kanvas berlangkah, kotak jawaban, 10 soal, alur ekspor + **verifikasi `adb exec-out run-as` di HP nyata** | Satu sesi lengkap keluar sebagai satu berkas JSON, dan berkas itu benar-benar sampai ke Mac lewat jalur yang direncanakan (atau fallback sudah dipilih) |
| 3 | Skrip render goresan jadi PNG + hitung turunan waktu | Bapak bisa melihat kembali tulisan anak per langkah |
| 3 | Tulis malrule untuk 10 soal uji (Tahap A) | Menjalankan Tahap A atas jawaban salah buatan menghasilkan kode yang benar tanpa LLM |
| 4 | **`tinta_heuristik`** — aturan if-then atas turunan waktu | Skrip mengembalikan kode untuk 10 soal, tanpa panggilan API sama sekali |
| 4 | **`tinta_llm`** — prompt + structured output + cache berkunci versi | Skrip mengembalikan JSON diagnosis untuk 10 soal; menjalankan ulang membaca cache, bukan memanggil API |
| 5 | Sesi uji sungguhan dengan anak | Data terkumpul; Bapak sudah menilai sendiri lebih dulu |
| 6–7 | Wawancara NEA, bandingkan **dua** angka, perbaiki prompt (maks 3 putaran) | Dua angka kecocokan final ada, dan keputusan lingkup LLM untuk v1 sudah diambil |

Perhatikan bahwa uji ke anak muncul di hari pertama, bukan hari terakhir.
Asumsi paling murah untuk digugurkan — anak tidak mau menulis di layar —
diuji sebelum ada satu baris pun kode diagnosis ditulis.

Hari 4 sekarang memuat dua pekerjaan. Heuristiknya sengaja didahulukan:
menulis baseline setelah melihat hasil LLM adalah cara paling mudah untuk
tanpa sadar membuatnya kalah.

---

## Ditunda — yang sengaja tidak dikerjakan

Semuanya sudah dibicarakan dan semuanya masuk v1 — tapi tidak satu pun perlu
ada untuk menjawab pertanyaan spike ini.

| Ditunda | Alasan |
|---|---|
| Graf topik berprasyarat | 10 soal sudah cukup untuk menguji diagnosis |
| Antrean pengulangan & buku kesalahan | Butuh graf topik dulu |
| Orkestrator `osn sync` | Untuk 10 soal sekali jalan, langkah manual masih wajar; ia jadi wajib begitu ritme 3 sesi/minggu dimulai |
| Penyimpanan append-only penuh (`kejadian/`, `derive`) | Spike tidak punya status topik untuk diturunkan; cukup file datar |
| Mode Anak yang mengunci layar | Lihat catatan di bawah |
| Kanvas geometri & kanvas daftar | 10 soal ujinya dipilih yang cocok kanvas berlangkah |
| Foto kertas buram | Kanal tinta digital lebih kaya; foto menyusul |
| Lapisan pra-fondasi kelas 4 | Baru relevan setelah mesin diagnosisnya terbukti |
| AI di dalam aplikasi | Sengaja dihindari — lihat Bagian 2 |

> **Koreksi soal penguncian layar.** Screen Pinning Android mematikan tombol
> home dan recents secara penuh hanya kalau aplikasi dipasang sebagai *device
> owner* — tidak realistis untuk HP pribadi. Pada mode biasa, Android
> menampilkan dialog izin saat `startLockTask()` dipanggil, dan anak masih
> bisa keluar dengan menekan tombol kembali + recents bersamaan. Yang
> membuatnya tetap layak: kalau opsi "Minta PIN sebelum melepas sematan"
> dinyalakan sekali di Pengaturan, kombinasi itu memunculkan layar kunci,
> sehingga anak tidak bisa mencapai isi HP yang lain. Jadi ini kunci lunak
> yang butuh satu penyalaan manual oleh orang tua, bukan kunci keras. Cukup
> untuk tujuannya, tapi harus disebut apa adanya.
>
> Di v1 perannya berubah lagi: karena kunci jawaban dan diagnosis memang
> tidak pernah dikirim ke HP (PRD §7.4), Screen Pinning tidak lagi melindungi
> rahasia — ia cuma menjaga fokus anak. Kalaupun gagal, yang paling buruk
> ter-expose adalah soal yang memang sedang ia kerjakan.

---

## Setelah — kalau spike-nya lulus

Yang pertama dibangun sesudahnya bukan fitur, melainkan **fondasi
penyimpanan v1** (PRD §8.4): konten immutable, kejadian append-only, status
sebagai turunan. Ini didahulukan karena begitu data anak mulai terkumpul
rutin, mengubah bentuk penyimpanan jadi jauh lebih mahal — dan janji "prompt
bisa diiterasi di atas data yang sama" hanya berlaku kalau riwayatnya tidak
pernah ditimpa.

Sesudah itu: graf topik, antrean pengulangan, orkestrator `osn sync`, lalu
Mode Anak.

Catatan yang berubah dari versi 14 Agustus: dokumen lama menyebut langkah
pertama setelah spike adalah "memindahkan panggilan API dari Mac ke belakang
layanan sederhana, karena kunci Anthropic tidak boleh berakhir di dalam APK."
Itu **tidak lagi berlaku** — PRD §7.1/§8.6 menetapkan diagnosis tetap di Mac
untuk seluruh v1, tanpa layanan perantara apa pun. Kalau `tinta_heuristik`
lolos gerbang, bahkan tidak ada panggilan API yang perlu dipindahkan.

Kalau gagal, yang gugur cuma satu kanal masukan, bukan produknya. Foto kertas
buram, penilaian dari jawaban akhir saja, dan wawancara terpandu yang
naskahnya disusun AI semuanya masih di meja — semuanya lebih lemah, tapi
tidak satu pun nol.
