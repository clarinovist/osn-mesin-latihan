# Rencana Spike — Coretan ke Diagnosis

**Status dokumen:** sumber kebenaran untuk eksekusi spike.
`Rencana Spike - Coretan ke Diagnosis.html` adalah render versi 14 Agustus
yang **sudah tertinggal** dari dokumen ini — biarkan sebagai artefak
historis, jangan dipakai sebagai panduan kerja.

Rencana teknis · spike · v1 · disusun 14 Agustus 2026 · direvisi 17 Agustus 2026 ·
direvisi 18 Agustus 2026

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

> **Perubahan dari versi 17 Agustus.** Bagian 1 (perekaman goresan) pindah
> dari app Android native ke halaman web statis. Alasannya di bagian
> "Keputusan — aplikasinya tidak menyentuh internet sama sekali" dan
> "Bagian 1" di bawah. Ini cuma ganti alat untuk membuktikan tesis yang
> sama — tidak mengubah satu pun keputusan di Bagian 2 (diagnosis), gerbang,
> atau protokol pengujian.

---

## Keputusan — aplikasinya tidak menyentuh internet sama sekali

Ini keputusan arsitektur terpenting di spike, dan bukan sekadar
penyederhanaan. Perekam goresan hanya merekam goresan lalu mengekspor satu
berkas JSON. Diagnosisnya dijalankan terpisah oleh skrip di Mac. Ini berlaku
sama untuk versi web spike (lihat Bagian 1) maupun versi native yang mungkin
menyusul di v1 — keputusan ini soal alur data, bukan soal platform.

- **Tidak ada API key di dalam perekam goresan.** Kunci Anthropic tidak
  pernah masuk ke perangkat. Persoalan yang biasanya makan waktu berhari-hari
  (proxy, penyimpanan kunci, rotasi) hilang seluruhnya dari spike.
- **Iterasi prompt dalam hitungan detik, bukan build.** Data goresan anak
  direkam sekali, lalu prompt diagnosis bisa diputar ulang puluhan kali
  terhadap data yang sama. Kalau AI-nya ada di dalam aplikasi, tiap perbaikan
  prompt berarti build ulang dan minta anak menulis lagi.
- **Risikonya terisolasi.** Kalau diagnosisnya gagal, yang terbuang hanya
  skrip — kanvas tulisnya tetap terpakai.

Jaminannya ditegakkan secara struktural, bukan lewat niat baik. Untuk versi
web spike: satu file HTML statis, dibuka langsung lewat `file://` (tanpa
server, tanpa dev-server lewat WiFi), nol `<script src>` ke domain luar, nol
`fetch`/`XMLHttpRequest`/`WebSocket` di kodenya — bisa diperiksa siapa saja
dengan baca satu file itu dalam sepuluh detik. Untuk versi native yang
mungkin menyusul di v1: izin `android.permission.INTERNET` tidak dicantumkan
di manifest, jaminan yang setara di level OS.

---

## Bagian 1 — Perekam goresan (web, untuk spike)

**Perubahan 18 Agustus.** Untuk spike ini, perekam goresan dibangun sebagai
satu halaman web statis, bukan app Android native. Alasannya murni
kecepatan iterasi dan menghilangkan blocker "harus punya HP Android
tertentu" — bukan perubahan pada apa yang direkam atau bagaimana datanya
dipakai. Keputusan platform native (Android vs iOS, PRD §8) ditunda sampai
setelah spike lulus dan jelas apakah presisi capture web sudah cukup.

### Tumpukan teknologi

HTML + JavaScript murni, satu file statis, tanpa framework, tanpa build
step, tanpa dependensi jaringan. Dibuka lewat `file://` — langsung di
browser, tidak butuh server. Data sesi ditulis sebagai JSON dan diunduh
lewat `Blob` + `<a download>` ke folder Downloads standar device — lihat
"Ekspor" soal kenapa ini menyederhanakan Hari 2.

### Inti teknisnya: satu fungsi

Seluruh nilai spike ini ada di ketelitian satu hal — merekam titik goresan
dengan waktu. `pointermove` polling saja tidak cukup: browser melaporkan
satu posisi per frame, sekitar 60–120 titik per detik. Yang diperlukan
adalah titik historis di antara frame — di web, itu `PointerEvent.
getCoalescedEvents()`, padanan langsung dari `getHistoricalX/Y` di
`MotionEvent` Android.

```javascript
// Ambil titik historis, bukan cuma posisi terakhir per frame.
// Satu PointerEvent bisa membawa beberapa sampel yang tertinggal
// lewat getCoalescedEvents().
function toSamples(event, t0) {
  const coalesced = event.getCoalescedEvents
    ? event.getCoalescedEvents()
    : [event];
  return coalesced.map((e) => ({
    x: e.clientX,
    y: e.clientY,
    t: e.timeStamp - t0,
  }));
}
```

Ditulis sebagai fungsi murni yang menerima array titik mentah dan
mengembalikan `Sample[]` — bukan langsung membaca `event` di dalam handler
DOM — supaya bisa ditest tanpa mock browser penuh: fixture-nya cukup array
titik biasa, bukan objek `PointerEvent` sungguhan.

Ini yang membedakan "gambar tulisan tangan" dari "rekaman proses menulis".
Tanpa presisi waktu ini, seluruh tesis produk hilang.

**Fungsi ini wajib punya golden test sebelum dipakai ke anak** (PRD §8.8,
perlu disesuaikan dari `MotionEvent.toSamples()` ke versi web — lihat catatan
di bawah). Alasannya bukan disiplin umum: kegagalan di lapisan ini **tidak
bisa diperbaiki belakangan**. Kalau titik historis hilang, salah urut, atau
timestamp-nya bergeser, satu-satunya perbaikan adalah meminta anak
mengerjakan ulang soal yang sama — yang justru dilarang oleh alasan
arsitektur batch. Bentuknya: rekam sekali urutan titik nyata
(termasuk yang membawa beberapa titik terkoalisi dalam satu event), simpan
sebagai fixture (array titik biasa, lihat catatan di atas soal fungsi murni),
lalu pastikan `toSamples()` selalu mengembalikan daftar sampel yang sama
persis — jumlah, urutan, dan selisih waktu relatif terhadap `t0`.

Ini satu-satunya test yang wajib ada di spike. Sisanya menyusul di v1.

### Risiko — fallback yang gagal diam-diam

**Ditambahkan 18 Agustus.** Golden test di atas menguji `toSamples()` sebagai
fungsi murni di atas fixture array biasa. Justru karena itu, ia **buta
terhadap satu kegagalan**: apakah browser sungguhan benar-benar menyerahkan
sampel antar-frame.

Perhatikan barisnya:

```javascript
const raw = e.getCoalescedEvents
  ? e.getCoalescedEvents().map(titikDariEvent)
  : [titikDariEvent(e)];
```

Cabang `else` itu diam. Dan bahkan ketika `getCoalescedEvents` ada, spesifikasi
web hanya mewajibkannya mengembalikan *paling sedikit* satu titik — ia
best-effort per implementasi, tidak seperti `getHistoricalX/Y` yang dijamin
oleh batching `MotionEvent` di level OS. Jadi ada tiga cara gagal tanpa suara:
API-nya tidak ada; API-nya ada tapi hanya mengembalikan satu titik per frame;
atau — **ditemukan 18 Agustus** — API-nya ada, dipanggil, dan mengembalikan
array **kosong**, sehingga event mengalir tapi nol titik tersimpan.

Yang ketiga itu awalnya lolos justru dari alat yang dipasang untuk
menangkapnya: guard `rata > 0 && rata < 1.5` diam ketika rata-ratanya tepat
0,0. Penanganannya sekarang ada di `verdictKoalisi()` — lihat tabel empat
status di catatan Hari 3 (Lampiran A).

Dalam dua kasus pertama, JSON tetap terisi ribuan titik, kanvas tetap tergambar
mulus, dan golden test tetap hijau. Yang hilang cuma resolusi antar-frame —
persis hal yang menjadi seluruh nilai spike ini. Kasus ketiga lebih kasar
(JSON-nya kosong melompong), tapi dulu sama diamnya di layar.

**Kenapa ini penting justru untuk gerbangnya.** Kalau kecocokan akhirnya
5/10, tanpa instrumentasi ini tidak ada cara memisahkan dua sebab: prompt
diagnosisnya yang lemah, atau data goresannya yang cacat sejak awal. Dua
kegagalan yang berbeda jadi tak terbedakan — dan gerbang yang tidak bisa
membedakan sebab tidak bisa dipakai untuk memutuskan apa pun.

**Mitigasi — beberapa baris, dijalankan sekali di Hari 1.** Rekam sendiri
statistik koalisi selama sesi, lalu simpan di JSON:

```json
"capture": {
  "coalesced_didukung": true,
  "titik_per_event_rata2": 3.4,
  "titik_per_event_maks": 7,
  "jumlah_event_pointermove": 812,
  "browser": "Chrome/128 Android 14",
  "layar_hz": 120
}
```

Cara bacanya satu kalimat: **kalau `titik_per_event_rata2` mendekati 1,0,
alatnya yang bermasalah, bukan promptnya.** Angka sehat pada layar 120 Hz
dengan tangan bergerak cepat berada di kisaran 2–8; konsisten 1,0 berarti
perekam ini setara `pointermove` polling biasa dan tesis belum benar-benar
diuji.

Ini bukan test tambahan — ini satu angka yang membuat hasil gerbang bisa
ditafsirkan. Biayanya beberapa baris kode dan nol dependensi.

**Kalau angkanya jelek**, urutannya: kunci ke browser lain di device yang
sama, lalu device lain, sebelum menyimpulkan apa pun tentang web sebagai
platform. Baru kalau semua kombinasi memberi ≈1,0, keputusan "web statis
untuk spike" perlu ditinjau ulang dan port native (PRD §8) naik jadi
prasyarat, bukan penundaan.

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
  "selesai_ms": 63800,
  "capture": {
    "coalesced_didukung": true,
    "titik_per_event_rata2": 3.4,
    "titik_per_event_maks": 7,
    "jumlah_event_pointermove": 812,
    "browser": "Chrome/128 Android 14",
    "layar_hz": 120
  }
}
```

Blok `capture` bukan data anak — ia data tentang alatnya, dan ada supaya
hasil gerbang bisa ditafsirkan. Lihat "Risiko — fallback yang gagal
diam-diam" di atas untuk cara membacanya.

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

### Ekspor: unduhan langsung, bukan `adb`

**Perubahan 18 Agustus.** Karena perekamnya sekarang halaman web, bukan app
Android dengan storage privat, file JSON sesi keluar lewat unduhan browser
biasa (`Blob` + `<a download>`) — mendarat di folder Downloads publik
device, bukan di storage internal app yang butuh `run-as` untuk dibaca. Ini
menghilangkan seluruh risiko "vendor blokir `run-as`" yang jadi kriteria
berhenti di versi sebelumnya.

Jalur ke Mac tinggal pilih salah satu, tergantung device yang dipinjam:

- Sambung kabel USB, salin manual lewat file transfer standar OS (MTP untuk
  Android, Finder untuk iOS/iPadOS lewat kabel)
- AirDrop, kalau device-nya Apple
- Kirim ke diri sendiri lewat aplikasi apa pun yang sudah ada di device itu
  (mis. catatan, email pribadi) — selama tidak dipakai buat catatan lain,
  ini masih tanpa server pihak ketiga yang menyimpan data

Tetap tanpa jaringan keluar dari sistem yang kita bangun — mekanisme
transfer ini pakai fitur bawaan OS device, bukan endpoint yang kita
operasikan. Kalau nanti port ke app native (v1, pasca-spike), pertanyaan
`adb exec-out run-as` di atas kembali relevan dan perlu diuji ulang saat itu.

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

**Prasyarat sebelum tabel ini dipakai sama sekali:** periksa
`titik_per_event_rata2` di JSON. Kalau angkanya ≈1,0, tabel di atas tidak
berlaku — berapa pun hasilnya, yang diuji bukan tesisnya melainkan perekam
yang kehilangan resolusi antar-frame. Baik "gagal" maupun "lulus" sama-sama
tidak bisa dipercaya: gagal bisa jadi karena datanya cacat, dan lulus berarti
tesisnya justru terbukti dengan data yang lebih miskin dari rancangan —
menarik, tapi bukan yang sedang diukur. Perbaiki alatnya dulu (Bagian 1),
ambil ulang data, baru baca tabel.

**Batas maksimal 3 putaran perbaikan prompt** di atas data yang sama sebelum
memutuskan lulus/gagal final — supaya tidak diam-diam overfitting ke 10 soal
satu anak ini. Batas ini dihitung dari `prompt_versi` yang tercatat, bukan
dari ingatan.

---

## Urutan — rencana harian

| Hari | Pekerjaan | Selesai kalau |
|---|---|---|
| 1 | Kanvas tinta web + perekaman titik historis (`getCoalescedEvents`) + **golden test `toSamples()`** | Menggambar di trackpad Mac terasa mulus; JSON berisi ribuan titik dengan waktu; test hijau di atas fixture titik nyata |
| 1 | **Tes 10 menit ke anak — cukup coret-coret bebas** (di device sentuh apa pun yang tersedia; boleh geser ke hari lain kalau belum ada) | Anak nyaman menulis dengan jari. **Kalau tidak, berhenti di sini.** |
| 2 | Kanvas berlangkah, kotak jawaban, 10 soal, tombol unduh JSON + **pindahkan berkas ke Mac (USB/AirDrop/kirim manual)** | Satu sesi lengkap keluar sebagai satu berkas JSON, dan berkas itu sampai ke Mac |
| 3 | Skrip render goresan jadi PNG + hitung turunan waktu | Bapak bisa melihat kembali tulisan anak per langkah |
| 3 | Tulis malrule untuk 10 soal uji (Tahap A) + sambungkan `turunan.yaml` → kode lewat `diagnosa_sesi.py` | Menjalankan Tahap A atas satu sesi 10 soal menghasilkan kode yang benar tanpa LLM |
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

---

## Lampiran A — Rencana harian operasional

Daftar periksa per hari dengan langkah konkret. Setiap hari punya: apa yang
dikerjakan, urutan langkah, kapan disebut selesai, dan kapan harus berhenti.

### Hari 1 — Kanvas tinta (web) + tes 10 menit ke anak

**Perubahan 18 Agustus:** Hari 1 & 2 dibangun sebagai halaman web statis,
bukan app Android native. Lihat Bagian 1 untuk alasannya.

**Pagi: kanvas tinta di browser**

1. Buat satu file `spike/index.html` — HTML + JS murni, tanpa framework,
   tanpa build step
2. Tambahkan satu `<canvas>` yang menangkap `pointerdown`/`pointermove`/
   `pointerup`, dengan CSS `touch-action: none` supaya scroll browser tidak
   mengganggu goresan
3. Tulis fungsi murni `toSamples(points, t0)` yang menerima array titik
   (dari `event.getCoalescedEvents()`) dan mengembalikan `Sample[]` (lihat
   kode di Bagian 1)
4. Rakit test fixture: rekam satu urutan titik nyata (termasuk event dengan
   beberapa titik terkoalisi), simpan sebagai array biasa di file test,
   lalu tulis test (Node/vitest, atau skrip assert sederhana) yang
   memastikan `toSamples()` mengembalikan jumlah, urutan, dan selisih waktu
   yang sama persis. **Tesnya harus hijau sebelum lanjut.**
5. Goresan ditulis ke array in-memory; tombol "Selesai" menutup sesi
6. Tambahkan penghitung koalisi: hitung rata-rata dan maksimum titik per
   event `pointermove`, plus flag `coalesced_didukung`, dan simpan sebagai
   blok `capture` di JSON (lihat "Risiko — fallback yang gagal diam-diam"
   di Bagian 1). Beberapa baris, tanpa dependensi.

**Sore: cek di trackpad Mac, lalu tes ke anak kalau device sudah ada**

7. Buka `index.html` langsung di browser Mac (`file://`), coba gambar pakai
   trackpad/mouse — ini sudah cukup untuk menilai kualitas datanya hari ini
   juga, tanpa perlu device sentuh apa pun
8. Kalau ada HP/tablet sentuh yang bisa dipinjam hari ini: buka file yang
   sama di browser device itu, serahkan ke anak, minta coret-coret bebas —
   tidak ada soal, tidak ada target. Observasi: apakah jari dipakai atau
   stylus? Apakah tulisannya terbaca? Apakah anak mengeluh setelah 5 menit?
9. **Baca `titik_per_event_rata2` dari device sentuh itu, bukan dari
   trackpad Mac.** Trackpad tidak membuktikan apa pun soal ini — angka yang
   dipakai untuk kesepuluh soal harus datang dari device dan browser yang
   sama yang nanti dipakai anak. Catat angkanya sebelum lanjut.
10. Kalau belum ada device sentuh: **tidak masalah, tidak blocking** — tunda
    langkah 8–9 sampai ada device, lanjut ke Hari 2 memakai data trackpad Mac
    untuk sementara

**Selesai kalau:** menggambar terasa mulus (di trackpad Mac minimal), JSON
berisi ribuan titik dengan timestamp, dan test `toSamples()` hijau.

**Berhenti kalau (begitu ada tes ke anak):** anak menolak menulis dengan
jari, atau tulisannya jauh lebih buruk daripada di kertas. Jangan lanjut ke
Hari 2 dengan asumsi itu — ini asumsi paling murah untuk digugurkan.

**Tinjau ulang alat kalau:** `titik_per_event_rata2` di device sentuh
konsisten ≈1,0. Ini bukan "berhenti" — ini "jangan percaya hasil gerbang
sebelum dicoba browser/device lain". Urutan penanganannya ada di Bagian 1.

### Hari 2 — Kanvas berlangkah + alur ekspor

**Pagi: UI sesi lengkap**

1. Rakit tiga layar di halaman web yang sama: daftar 10 soal → kanvas
   berlangkah + kotak jawaban → layar "terima kasih" dengan tombol unduh
2. Implementasikan tombol "Langkah Baru" (PRD §6.1): menekan menyegel
   kanvas aktif dan membuka kanvas kosong berikutnya. Catat timestamp
   penyegelan dan pembukaan
3. Jawaban akhir di field ketik terpisah (`<input inputmode="numeric">`),
   bukan hasil OCR kanvas
4. Saat "Selesai Sesi" ditekan: halaman membuat `Blob` JSON dan memicu
   unduhan `sesi-<timestamp>.json` lewat `<a download>` — mendarat di folder
   Downloads standar device

**Sore: pindahkan berkas ke Mac**

5. Kalau diuji di device lain (bukan Mac): sambung USB dan salin manual
   (MTP di Android/Files app; Finder untuk iOS/iPadOS lewat kabel), atau
   AirDrop kalau device-nya Apple
6. Buka file di Mac — verifikasi isinya utuh dan bisa di-parse

**Selesai kalau:** satu sesi lengkap (10 soal, goresan + jawaban) keluar
sebagai satu berkas JSON di Mac.

**Berhenti kalau:** tidak ada cara memindahkan file dari device ke Mac tanpa
internet — jauh lebih jarang terjadi sekarang karena unduhan mendarat di
folder publik, bukan storage privat app yang butuh `adb run-as`.

### Hari 3 — Render PNG + malrule

**Pagi: render dan turunan waktu**

1. Tulis skrip Python `render.py` yang membaca `sesi-<id>.json`, merender
   goresan tiap langkah jadi satu PNG per langkah
2. Hitung empat turunan waktu per soal (PRD §2.2):
   - Jeda sebelum goresan pertama
   - Durasi per langkah
   - Jumlah hapus per langkah
   - Apakah jawaban ditulis sebelum langkah selesai
3. Output: satu folder per sesi berisi PNG per langkah + `turunan.yaml`

**Sore: tulis malrule untuk 10 soal uji**

4. Buka Panduan Orang Tua, identifikasi pola kesalahan yang sudah tercatat
   untuk 10 soal uji
5. Untuk tiap pola, tulis sebagai:
   ```yaml
   template_id: pecahan_operasi_campuran
   parameter:
     suku: [ {n: 2, d: 3, tanda: +}, {n: 3, d: 4, tanda: +}, {n: 1, d: 2, tanda: -} ]
   malrule:
     id: pecahan.operasi_pembilang_penyebut_terpisah
     prediksi(suku): Σ(tanda·n) / Σ(tanda·d)
     kode: K
   ```
6. Tulis `tahap_a.py` yang menjalankan tiap malrule atas parameter soal,
   lalu mencocokkan prediksi ke jawaban anak
7. Tes dengan jawaban salah buatan: misal input `"4/5"` untuk soal pecahan,
   `tahap_a.py` harus mengembalikan `kode: K` tanpa LLM

**Selesai kalau:** Bapak bisa melihat tulisan anak per langkah sebagai PNG,
dan Tahap A menghasilkan kode yang benar untuk jawaban salah yang sudah diketahui
pola salahnya — tanpa panggilan API apa pun.

**Status 18 Agustus — tuntas, dengan dua perbaikan yang lahir dari verifikasi.**

Yang sudah berdiri: `render.py`, `malrule.yaml` (10 template), `tahap_a.py`
(14 kasus hijau, nol tumbukan). Yang kurang saat ditinjau ulang: keduanya
belum pernah diuji pada bentuk data Hari 5 yang sesungguhnya — sesi berisi
sepuluh soal — dan tidak pernah bersambung satu sama lain.

Ditambahkan untuk menutupnya:

- `render_test.py` — `hitung_turunan()` sebelumnya nol test. Sekarang empat
  kasus batas ikut terkunci: langkah belum tersegel (`segel_ms: null`),
  langkah tanpa goresan, sesi tanpa goresan sama sekali, dan render penuh
  10 soal (20 PNG + `turunan.yaml` terverifikasi isinya).
- `diagnosa_sesi.py` — mata rantai yang hilang. `render.py` berhenti di
  `turunan.yaml`, `tahap_a.py` hanya menjalankan daftar kasus di dalam
  dirinya sendiri; tidak ada yang membaca sesi nyata lalu mengeluarkan kode.
  Sekarang: satu sesi 10 soal → `B=2, H=2, K=4, benar=1, tidak_pasti=1`,
  9/10 terjawab Tahap A, nol panggilan API.
- `test.sh` — satu perintah untuk seluruh test spike.

**Bug yang ditemukan dan sudah diperbaiki.** Saat mencoba mengisi sesi lewat
event sintetis, 28 `pointermove` terkirim dan **nol titik** terekam —
`getCoalescedEvents()` mengembalikan array kosong untuk event non-trusted.
Yang penting bukan event sintetisnya, melainkan bahwa **alat ukurnya diam**:
guard lama berbunyi `rata > 0 && rata < 1.5`, sehingga rata-rata tepat 0,0
lolos tanpa peringatan apa pun. Kegagalan terparah — perekaman mati total —
justru dilaporkan seolah normal, persis kebalikan dari maksud instrumentasi
di Bagian 1.

Bagian 1 menyebut dua cara gagal tanpa suara (API tidak ada; API ada tapi
mengembalikan satu titik per frame). Ternyata ada **yang ketiga**: API ada,
dipanggil, dan mengembalikan nol. Perbaikannya `verdictKoalisi()` di
`toSamples.js` — membedakan empat keadaan, bukan dua:

| status | arti | tindakan |
|---|---|---|
| `kosong` | belum ada `pointermove` sama sekali | sesi belum digores, bukan kerusakan |
| `rusak` | ada event, **nol** titik | data tidak bisa dipakai, hentikan |
| `degradasi` | ada titik, ~1 per event | resolusi antar-frame hilang, cek browser/device |
| `sehat` | ≥1,5 titik per event | lanjut |

Status ikut tertulis ke `capture.verdict` di JSON sesi, jadi sesi yang cacat
ketahuan saat dibaca ulang, bukan hanya saat diunduh. Test regresinya mengunci
persis kasus 28-event-nol-titik itu.

**Catatan alat, bukan produk.** Sesi 10 soal di atas memakai fixture sintetis
untuk membuktikan pipeline, bukan tulisan anak. Goresan sungguhan tetap Hari 5.
Upaya mengotomatiskan pengisian lewat CDP `Input.dispatchMouseEvent` gagal —
domain `Input` menggantung di harness ini (`Runtime` menjawab seketika, `Input`
timeout 5 detik, dan hanya pulih sesaat setelah daemon di-restart). Kalau nanti
perlu sesi terisi otomatis, jalurnya Playwright/`puppeteer` yang menggerakkan
pointer sungguhan, bukan `PointerEvent` buatan — event sintetis tidak akan
pernah menghasilkan koalisi, jadi ia menguji hal yang salah.

### Hari 4 — tinta_heuristik (pagi) + tinta_llm (sore)

**Pagi: tinta_heuristik — baseline deterministik**

1. Tulis `tinta_heuristik.py` — aturan if-then atas turunan waktu:
   - Lancar (jeda awal pendek, sedikit hapus) tapi jawaban salah → condong K
   - Langkah benar, koreksi terkonsentrasi di titik hitung → condong H
   - Jawaban ditulis sebelum langkah selesai → curiga menejak/B
   - Sinyal campur atau lemah → `tidak_pasti`
2. Jalankan atas data sesi uji (kalau Hari 5 sudah jalan) atau atas data
   buatan
3. Catat hasil: berapa dari 10 soal dapat kode, berapa `tidak_pasti`

**Sore: tinta_llm — prompt + structured output**

4. Tulis `tinta_llm.py`:
   - Render PNG per langkah (sudah ada dari Hari 3)
   - Ringkasan waktu dari `turunan.yaml`
   - Kirim ke `claude-opus-5` dengan adaptive thinking + structured output
   - Response diparsing ke skema §2.5
5. Implementasikan cache berkunci `hash(data + prompt_versi + model)`:
   jalankan sekali, catat biaya; jalankan ulang, harus membaca cache
6. Jalankan atas data yang sama dengan heuristik

**Selesai kalau:** kedua implementasi mengembalikan JSON diagnosis untuk 10
soal, dan `tinta_llm` bisa dijalankan ulang tanpa memanggil API (cache
hijau).

**Urutan sengaja:** heuristik didahulukan. Menulis baseline setelah melihat
hasil LLM adalah cara paling mudah untuk tanpa sadar membuatnya kalah.

**Status 18 Agustus — kedua implementasi berdiri, menunggu data sungguhan.**

Berkas baru: `tinta_heuristik.py` + `tinta_heuristik_test.py` (12 test),
`tinta_llm.py` + `tinta_llm_test.py` (10 test). Seluruhnya hijau lewat
`bash spike/test.sh`, nol panggilan API sungguhan.

`tinta_heuristik` — lima aturan berurutan atas turunan waktu, dengan ambang
dikumpulkan di satu tempat (`JEDA_PANJANG_MS` dst.) supaya jelas mana yang
arbitrer:

| Sinyal | Kode | Alasannya |
|---|---|---|
| Jawaban ditulis duluan **dan** total pengerjaan ≤6 detik | B | condong menebak |
| Jeda awal ≥8 detik | K | tertahan sebelum mulai — tidak tahu caranya |
| Jeda awal ≤3 detik **dan** nol hapus | K | lancar tapi salah = keyakinan yang keliru |
| Total hapus ≥2 | H | mengoreksi berulang = tersandung di hitungan |
| selain itu | `tidak_pasti` | sengaja menyerah |

Dua batas yang ditulis sebagai test, bukan sebagai niat baik. Pertama,
syarat durasi pada aturan B: tanpa itu, anak yang mencatat dugaan lalu
benar-benar mengerjakan lama akan salah dituduh menebak. Kedua, urutan
"banyak hapus → H" mendahului kesimpulan K mana pun — itu garis pertahanan
langsung terhadap false-K, kegagalan yang gerbang sebut paling mahal.
Tahap A juga tidak pernah ditimpa: kalau malrule sudah memutuskan, heuristik
menyerahkan apa adanya.

`tinta_llm` — PNG per langkah + ringkasan waktu + malrule yang berlaku
beserta prediksinya, dikirim ke `claude-opus-5`, respons divalidasi ke skema
Bagian 2 sebelum dipakai (`kode` di luar B/K/H/benar ditolak, `terbaca` wajib
boolean). Cache berkunci `sha256(soal + konteks + isi PNG + prompt_versi +
model + teks instruksi)`. Yang dikunci test: panggilan kedua atas data sama
**tidak** menyentuh API, entri lama **tidak** terpakai begitu `prompt_versi`
naik — tanpa sifat kedua itu, batas "maksimal 3 putaran" tidak bisa dihitung,
hanya diingat-ingat.

`cache_llm/` masuk `.gitignore` bersama `turunan/`: isinya diagnosis atas
coretan anak, turunan langsung dari data anak.

> **Ditunda 18 Agustus — `tinta_llm` tidak dijalankan sampai ada keputusan
> eksplisit.**
>
> `tinta_llm` mengirim PNG tulisan tangan anak ke API Anthropic. PRD §7.1
> menetapkan sebaliknya, dan itu kebijakan produk, bukan detail
> implementasi: *"tidak ada cloud, tidak ada API pihak ketiga, tidak ada data
> anak yang pernah meninggalkan device+Mac keluarga itu sendiri… kecuali
> diputuskan ulang secara eksplisit"*. Alasan keduanya bukan soal API key
> melainkan soal persetujuan — *"anak kelas 4 tidak punya cara memberi
> persetujuan berarti atas ke mana data tulisan tangannya pergi"*.
>
> Jaminan "tidak menyentuh internet" di Bagian 1 berlaku untuk **perekamnya**,
> bukan untuk skrip diagnosis di Mac. Jadi §7.1 dan `tinta_llm` memang
> bertabrakan, dan pintu "kecuali diputuskan ulang" itu belum pernah dilewati
> secara sadar.
>
> **Keputusan: heuristik diukur lebih dulu.** Hari 5 mengambil data anak,
> Hari 6–7 membandingkan `tinta_heuristik` dengan penilaian Bapak. Kalau
> hasilnya ≥7/10 dengan nol false-K, LLM keluar dari lingkup v1 seluruhnya
> (lihat tabel "Membaca dua angka itu") — dan pertanyaan privasi ini tidak
> pernah perlu dijawab sama sekali.
>
> Kodenya tetap disimpan lengkap dan teruji, supaya kalau nanti keputusan itu
> memang perlu diambil, yang tersisa hanya menyalakan — bukan menulis ulang
> sambil terburu-buru. Sampai saat itu: **jangan set `ANTHROPIC_API_KEY` dan
> jangan jalankan `tinta_llm.py` tanpa `--dry-run`.** Sampai hari ini belum
> ada satu pun goresan yang pernah terkirim.
>
> Kalau nanti dijalankan, konsekuensinya juga perlu jadi bagian dari
> keputusan, bukan kejutan belakangan: `tinta_llm` butuh model **vision** —
> seluruh nilainya ada pada membaca bentuk coretan. LLM teks-saja hanya akan
> membaca ringkasan waktu, yaitu persis yang sudah dikerjakan
> `tinta_heuristik` secara gratis dan offline.

**Yang belum terjawab, dan tidak bisa dijawab hari ini.** Angka gerbang
(berapa dari 10 cocok, berapa `terbaca: false`) belum ada — dan memang belum
seharusnya ada. Keduanya butuh dua hal yang baru muncul Hari 5: coretan
sungguhan dari anak, dan penilaian independen Bapak sebagai pembanding.
Menjalankan `tinta_llm` atas fixture sintetis hanya akan menghasilkan angka
yang terlihat resmi tapi tidak mengukur apa pun — goresan buatan tidak memuat
proses berpikir siapa pun.

Satu catatan jujur dari uji coba di fixture: pada sesi sintetis, heuristik
tidak menambah satu kode pun di atas Tahap A (9/10 sebelum dan sesudah).
Itu **bukan** temuan tentang heuristiknya — fixture memakai pola waktu yang
seragam untuk semua soal, jadi tidak ada variasi untuk dibaca. Angka
sesungguhnya baru berarti setelah Hari 5.

### Hari 5 — Sesi uji sungguhan dengan anak

**Pagi: persiapan**

1. Cek HP: app terpasang, storage cukup, baterai penuh
2. Siapkan ruangan: tenang, tidak ada gangguan, anak tidak lapar/ngantuk
3. Buka 10 soal di app, pastikan semua tampil dengan benar

**Sore: sesi uji**

4. Serahkan HP ke anak. Katakan: "Ini bukan ujian, tidak ada nilainya.
   Kerjakan saja sebisanya."
5. Anak mengerjakan ~30 menit, tanpa didampingi
6. Setelah selesai: ekspor JSON, pindah ke Mac

**Malam: Bapak menilai sendiri**

7. Buka PNG per langkah + turunan waktu
8. Untuk tiap soal yang salah, tentukan kode B/K/H sendiri
9. **Tulis di kertas, bukan di komputer** — kalau input ke sistem dulu,
   penilaian akan terpengaruh oleh `kode_awal` yang sudah ada

**Selesai kalau:** data sesi tersimpan di Mac, dan Bapak punya penilaian
independen tertulis di kertas.

### Hari 6–7 — Wawancara, bandingkan, putuskan

**Hari 6: wawancara NEA**

1. Pilih 3–4 soal yang salah dari sesi uji — fokus yang Bapak dan sistem
   berbeda pendapat, atau yang Bapak ragu
2. Jalankan protokol 5-prompt NEA untuk tiap soal:
   - "Baca soal ini."
   - "Ceritakan apa yang diminta."
   - "Tunjukkan bagaimana kamu dapat jawabannya, ceritakan pikiranmu."
   - "Kerjakan sambil dijelaskan."
   - "Tulis jawabannya."
3. Catat kode final berdasarkan wawancara

**Sore: bandingkan dua angka**

4. Buat tabel perbandingan:
   ```
   soal | jawaban | heuristik | llm | bapak | wawancara | cocok?
   ```
5. Hitung: berapa dari 10 cocok untuk heuristik? Berapa untuk LLM?
6. Catat: ada kasus false-K (sistem bilang K, sebenarnya H)?

**Hari 7: putuskan**

7. Kalau 5–6 cocok (zona abu-abat): perbaiki prompt, jalankan ulang atas
   data yang sama (baca cache kalau prompt_versi tidak berubah). **Maksimal
   3 putaran** — dihitung dari `prompt_versi` yang tercatat
8. Setelah 3 putaran atau kalau sudah jelas lulus/gagal: tulis keputusan
   final

**Keputusan final:**

| Hasil | Tindakan |
|---|---|
| Heuristik ≥7/10, nol false-K | LLM keluar dari v1. Tahap B jalan tanpa biaya. Lanjut bangun v1. |
| Hanya LLM ≥7/10 | LLM masuk v1 dengan biaya. Heuristik tetap sebagai pembanding regresi. Lanjut bangun v1. |
| Keduanya <5/10 | Kanal tinta gugur. Produk mundur ke jalur foto kertas / jawaban akhir saja / wawancara terpandu. |
| 5–6 cocok setelah 3 putaran | Tesis tidak gugur, tapi butuh data tambahan (lebih banyak soal, anak lain) sebelum keputusan final. |

**Selesai kalau:** dua angka kecocokan final ada di tangan, dan keputusan
lingkup LLM untuk v1 sudah diambil.

---

## Lampiran B — Prasyarat sebelum Hari 1

Hal-hal yang harus siap sebelum mulai, supaya Hari 1 tidak habis untuk setup.

**Lingkungan perekam goresan (web) — perubahan 18 Agustus**
- Browser modern (Chrome disarankan — dukungan `getCoalescedEvents()`
  paling matang lintas platform), tidak perlu instalasi apa pun
- Tidak butuh Android Studio, SDK, `adb devices`, atau USB Debugging untuk
  Hari 1–2 spike ini — itu baru relevan kalau nanti (pasca-spike) port ke
  app native
- Device sentuh untuk tes ke anak (Hari 1 langkah 7) **tidak wajib siap
  sebelum mulai** — trackpad Mac cukup untuk validasi teknis awal, device
  sentuh cukup didapat begitu tersedia

**Lingkungan Mac**
- Python 3.11+ terinstal
- Library: `anthropic` (untuk Hari 4), `pyyaml`, `pillow` (render PNG)
- Kunci API Anthropic tersedia di environment variable `ANTHROPIC_API_KEY`
  (tidak pernah masuk ke perekam goresan, hanya di Mac)
- Folder kerja: `~/Documents/osn/spike/`
- (Opsional) Node.js kalau golden test `toSamples()` ditulis pakai
  vitest/Jest — atau cukup skrip assert JS sederhana tanpa dependency

**Konten soal**
- 10 soal dari Tes Kalibrasi Minggu 0 sudah dipilih dan diketik sebagai
  template + parameter (bukan teks mati)
- Kunci jawaban untuk 10 soal sudah ada (tidak masuk HP, hanya di Mac)

**Anak**
- Tahu bahwa Ayah akan meminta mengerjakan sesuatu di HP/tablet, tapi tidak
  tahu kapan — jangan jadwalkan, biarkan spontaneous saat Bapak siap
- Tidak sedang ujian sekolah, tidak sakit, tidak terlalu lelah

---

## Lampiran C — Yang TIDAK dikerjakan di spike

Setiap item di bawah ini sudah dibicarakan di PRD dan masuk v1 — tapi tidak
perlu ada untuk menjawab pertanyaan spike. Kalau tergoda menambahkannya,
ingat: spike ini menguji SATU asumsi. Bukan membangun produk.

| Tidak dikerjakan | Kenapa |
|---|---|
| Graf topik berprasyarat | 10 soal hardcoded sudah cukup |
| Antrean pengulangan & buku kesalahan | Butuh graf topik dulu |
| Orkestrator `osn sync` | 10 soal sekali jalan, langkah manual masih wajar |
| Penyimpanan append-only (kejadian/, derive) | Spike tidak punya status topik |
| Mode Anak / Screen Pinning | Bukan target spike |
| Kanvas geometri & daftar berbaris | 10 soal pilih yang cocok kanvas berlangkah |
| Foto kertas buram | Kanal tinta lebih kaya; foto menyusul Fase 2 |
| Pra-fondasi kelas 4 | Baru relevan setelah diagnosis terbukti |
| AI di dalam aplikasi | Sengaja dihindari |
| Port ke app Android/iOS native | Web sudah cukup untuk membuktikan tesis; keputusan platform native ditunda sampai jelas apakah presisi web cukup (perubahan 18 Agustus) |
