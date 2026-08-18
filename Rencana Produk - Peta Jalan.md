# Peta Jalan — Aplikasi Diagnosis Matematika Anak

**Status dokumen:** sumber kebenaran untuk arah produk & roadmap.
`Rencana Produk - Peta Jalan.html` / `.pdf` adalah render versi 14 Agustus
yang **sudah tertinggal** dari dokumen ini — biarkan sebagai artefak
historis, jangan dipakai sebagai acuan.

Rencana produk · konsolidasi · 14 Agustus 2026 · direvisi 17 Agustus 2026 ·
direvisi 18 Agustus 2026

Satu dokumen yang menggabungkan arah produk, taksonomi B/K/H, hasil riset
dua-putaran, rencana spike, dan roadmap setelahnya — supaya tidak perlu buka
lima percakapan berbeda untuk tahu di mana kita berdiri.

**Status sekarang:** siap eksekusi Fase 0 — spike 5–7 hari, belum ada satu
baris kode pun ditulis.

**Hierarki dokumen** (dibuat eksplisit karena sekarang ada empat dokumen aktif):

| Dokumen | Perannya |
|---|---|
| `PRD.md` | **Sumber kebenaran arsitektur & keputusan produk.** Kalau dokumen lain berbeda, PRD yang benar. |
| `Rencana Spike - Coretan ke Diagnosis.md` | Panduan eksekusi 5–7 hari Fase 0 |
| `Rencana Produk - Peta Jalan.md` (ini) | Konsolidasi arah + roadmap antar-fase |
| PDF instrumen (Tes Kalibrasi, Uji Ulang Lisan, Kurikulum) | Sumber konten, tidak diubah |

---

## 01 · Arah produk

Keputusan yang disepakati 14 Agustus 2026, jadi dasar semua yang lain di
dokumen ini. Tidak ada yang berubah di revisi 17 Agustus.

| | |
|---|---|
| **Lingkup v1** | Satu keluarga saja (anak sendiri), tanpa akun, tanpa multi-tenant. |
| **Target anak** | Kelas 4, TA 2026/2027. PDF sumber ditulis untuk kelas 5 menuju OSN 2027 — tidak langsung berlaku. Target OSN realistis 2028, perlu lapisan pra-fondasi yang belum ada di PDF mana pun. |
| **Bukan kalender** | Peta 20 minggu didekompilasi jadi graf topik berprasyarat. Penggeraknya kondisi anak, bukan tanggal — bolong seminggu tidak menimbulkan "utang sesi". |
| **OSN = kesimpulan** | Bukan mode yang dipilih saat daftar. Tiap soal punya tingkat `1|2|3`. Kata "OSN" tidak boleh hardcode di kode atau struktur data. |
| **AI di belakang** | Tidak pernah jadi tutor chat untuk anak. AI duduk di belakang orang tua, bukan di depan anak. |
| **Input anak** | Tulisan tangan berlangkah di kanvas HP. Jawaban akhir diketik, bukan hasil OCR — OCR tidak pernah menentukan benar/salah. |
| **Ritme** | Realistis 3 sesi/minggu, 30–40 menit — bukan 4 hari + Jumat + Sabtu seperti di modul sumber. |

> **Kenapa ini penting:** orang tua di Indonesia kebanyakan tidak mengejar
> OSN — cukup nilai matematika membaik. Nilai jual sebenarnya bukan OSN,
> melainkan diagnosis: rapor bilang "Matematika 78", aplikasi ini bilang
> penyebabnya topik apa saja.

---

## 02 · Taksonomi B/K/H

Inti mesin diagnosis — aset paling bernilai dari PDF *Tes Kalibrasi - Panduan
Orang Tua*, bukan soal-soalnya.

**B** — salah baca soal. **K** — salah konsep. **H** — salah hitung.

Metrik utama aplikasi = **jumlah K aktif per topik dan trennya**, bukan skor.
"Anak dengan sembilan H dan skor 11 sebenarnya jauh lebih siap daripada anak
dengan tiga K dan skor 15."

Tinta digital bertimestamp bisa memetakan otomatis ke B/K/H:
lancar-tanpa-ragu-tapi-salah → K; langkah benar dengan koreksi di titik
aritmetika → H; jawaban ditulis duluan lalu langkah menyusul → menebak.

**Uji Ulang Lisan** (PDF terpisah) memisahkan "tidak bisa" dari "tidak
dikerjakan".

### Sidik jari jadi malrule — perubahan 17 Agustus

Versi 14 Agustus menyebut aset ini sebagai **tabel sidik jari**: jawaban
tertentu memetakan ke diagnosis spesifik. Contoh: 2/3 + 3/4 − 1/2 dijawab 4/5
→ pembilang & penyebut dioperasikan sendiri-sendiri, konsep pecahan belum
terbentuk.

Isinya tetap, **bentuk penyimpanannya berubah**: bukan tabel pasangan
`(soal_id, jawaban_salah) → kode`, tapi **fungsi atas parameter soal**
(PRD §2.3.1):

```yaml
malrule:
  id: pecahan.operasi_pembilang_penyebut_terpisah
  prediksi(suku): Σ(tanda·n) / Σ(tanda·d)
  kode: K
```

Untuk 2/3 + 3/4 − 1/2 fungsi ini memprediksi (2+3−1)/(3+4−2) = 4/5 — persis
jawaban yang tercatat di PDF, sementara jawaban benarnya 11/12.

Kenapa diubah: alur sesi mensyaratkan verifikasi memakai **soal beda angka,
skill sama**. Tabel literal tidak cocok lagi begitu angkanya diganti, jadi
seluruh sesi verifikasi akan jatuh ke jalur heuristik yang lebih lemah —
tepat di titik yang paling menentukan apakah sebuah topik ditutup. Fungsi
tetap berlaku ke semua soal bertemplate sama.

Riset di §03 memperkuat arah ini dari sisi lain: MalruleLib menunjukkan AI
turun 66%→40% saat menggeneralisasi satu contoh kesalahan ke template
berbeda. Generalisasi itu memang tidak boleh jadi tugas LLM — ditulis sebagai
fungsi, ia 100% dan gratis.

---

## 03 · Ringkasan riset

Dua putaran riset multi-sumber (10 sudut, 47 sumber, 38 klaim lolos
verifikasi adversarial 3-vote). Laporan lengkap dengan sitasi ada di
`gap-pasar-edtech-matematika-sd/report.md`.

**Knowledge tracing memvalidasi "jangan pakai skor".** BKT/DKT secara
struktural cuma bisa mengestimasi mastery agregat, bukan mendiagnosis akar
kesalahan — keterbatasan bentuk data (benar/salah biner), bukan soal
implementasi. Option tracing dan Graph-based Knowledge Tracing jadi preseden
akademik untuk pendekatan tagging-K dan graf topik berprasyarat.
*Peringatan:* MalruleLib menunjukkan AI kesulitan generalisasi satu contoh
kesalahan anak ke soal baru berbeda template (akurasi 66%→40%) — jangan
andalkan AI menebak miskonsepsi baru secara bebas. → **Dipakai langsung
sebagai alasan malrule-sebagai-fungsi (§02).**
`arxiv.org/2104.09043` · `arxiv.org/2105.15106` · `arxiv.org/2601.03217`

**Newman's Error Analysis — saudara akademik B/K/H.** Kerangka 1977, masih
dikutip 2019–2025. Lima tahap: Reading, Comprehension, Transformation,
Process Skills, Encoding. B≈Reading+Comprehension, K≈Transformation,
H≈Process Skills. Kategori kelima (Encoding — paham & hitung benar tapi salah
tulis jawaban akhir) tidak ada di B/K/H. Historis dioperasikan lewat protokol
wawancara 5-prompt tetap, bukan interpretasi bebas — bahkan dipasang sebagai
poster kelas di NSW. → **Dipakai sebagai protokol wawancara spike & onboarding.**
`mav.vic.edu.au (White 2009)` · `researchgate.net` · `files.eric.ed.gov`

**OCR/HME untuk coretan fisik — risiko terdokumentasi.** Model SOTA (VEHME,
EMNLP 2025) gagal 11–70% pada kanvas berstruktur. VLM punya kebiasaan
berbahaya "memperbaiki" kesalahan anak alih-alih mentranskrip apa adanya.
Confidence measure grading cuma ~73% andal (false-positive rate 0,27).
Rekomendasi: SOP ambang ganda (auto-terima/auto-tolak/rute-ke-orang tua),
selalu tampilkan transkripsi verbatim ke orang tua, kanvas bebas + OCR
halaman-penuh lebih baik dari kotak jawaban kaku. → **Relevan Fase 2 saja;
v1 tidak butuh OCR sama sekali.**
`arxiv.org/2510.22798` · `arxiv.org/2404.10690` · `arxiv.org/2408.11728` ·
`arxiv.org/2604.22774`

**PP 17/2025 — berlaku meski satu keluarga.** "Penyelenggara Sistem
Elektronik" eksplisit mencakup perorangan, bukan cuma institusi. Wajib
persetujuan orang tua, wajib DPIA (bisa catatan ringkas), wajib hapus data
kalau consent ditarik. Arsitektur "tanpa izin INTERNET, diagnosis di Mac"
justru sejalan dengan arah minimalisasi data ini — belum ada preseden
penegakan untuk operator individu skala kecil.
`peraturan.go.id/pp-no-17-tahun-2025` · `peraturan.bpk.go.id`

**Dashboard orang tua — celah riset, bukan kesimpulan.** Hampir semua klaim
spesifik tentang pola anti-data-overload untuk orang tua awam gagal
verifikasi di kedua putaran. Satu-satunya yang lolos (IXL Trouble Spots)
adalah produk institusional untuk guru, bukan orang tua individu. Jangan
bangun dashboard berdasarkan pola dari produk institusional — kalau
dikerjakan, perlu riset+piloting terpisah.
`blog.ixl.com`

**Klaim yang gagal verifikasi — jangan diasumsikan benar.** Dynamic BKT sudah
mengenkode graf prasyarat secara otomatis — ditolak. DKT bisa menemukan
struktur konsep laten tanpa tagging manusia — ditolak. Ambang ganda terbukti
mencapai F1>0,985 dengan <3% masuk review — ditolak (pola metodologinya
valid, angka performanya dari domain lain).

---

## 04 · Rencana spike (5–7 hari)

Detail teknis lengkap ada di `Rencana Spike - Coretan ke Diagnosis.md`.
Bagian ini ringkasannya.

**Asumsi yang dipertaruhkan.** Apakah tinta bertimestamp + jawaban yang
diketik cukup untuk mendiagnosis kesalahan anak sebagai B, K, atau H. Kalau
tidak terbukti, produk ini turun jadi aplikasi latihan soal biasa.

**Keputusan arsitektur inti.** Perekam goresan hanya merekam goresan →
ekspor JSON. Diagnosis dijalankan terpisah oleh skrip Python di Mac. Tidak
menyentuh internet sama sekali — tidak ada API key yang bisa dibongkar,
iterasi prompt dalam hitungan detik tanpa build ulang, risiko gagal
terisolasi ke skrip saja.

**Perekamnya web, bukan app native — perubahan 18 Agustus.** Untuk spike,
perekam goresan dibangun sebagai satu halaman HTML statis (`PointerEvent.
getCoalescedEvents()` sebagai padanan `MotionEvent` historis di Android),
bukan app Kotlin. Alasan: iterasi jauh lebih cepat (refresh browser vs
build Gradle), dan tidak lagi butuh kepastian device Android tertentu
sebelum mulai — bisa divalidasi di trackpad Mac dulu, device sentuh apa pun
dicoba begitu tersedia. Ini keputusan level spike, bukan keputusan produk:
platform native (Android vs iOS) ditunda sampai jelas apakah presisi
capture web sudah cukup untuk v1. Detail teknis lengkap di
`Rencana Spike - Coretan ke Diagnosis.md`.

### Keluarannya dua angka, bukan satu — perubahan 17 Agustus

Tahap B (pola tinta) dijalankan dalam **dua implementasi berdampingan** atas
data yang sama:

- `tinta_heuristik` — aturan if-then murni atas turunan waktu. Deterministik,
  nol biaya, offline. **Baseline wajib.**
- `tinta_llm` — render PNG per langkah → `claude-opus-5`, adaptive thinking +
  structured output.

Alasan: tanpa baseline, pertanyaan "apakah LLM-nya sebenarnya perlu?" tidak
punya cara dijawab. Kalau heuristik murni sudah lolos gerbang, LLM keluar
dari lingkup v1 seluruhnya — penghematan permanen yang cuma bisa dibuktikan
saat data masih segar dan anak masih tersedia untuk wawancara penengah.

### Gerbang — diukur untuk kedua implementasi

**Lulus → lanjut bangun v1**
- Minimal 7 dari 10 kode B/K/H cocok dengan penilaian Bapak (setelah
  wawancara jadi penengah)
- Nol kasus sistem menyebut "K" untuk kesalahan yang sebenarnya "H"
- Anak mau menulis di layar sampai soal ke-10 tanpa mengeluh soal alat
  tulisnya

**Gagal → hentikan, ganti pendekatan**
- Anak menolak menulis dengan jari, atau tulisannya jauh lebih buruk daripada
  di kertas — hentikan di hari pertama
- `terbaca: false` muncul di lebih dari 4 dari 10 soal
- Kecocokan di bawah 5 dari 10 pada kedua implementasi, atau LLM berulang
  kali meyakinkan di atas pembacaan yang keliru

Di antara keduanya — 5 atau 6 cocok — artinya prompt yang perlu diperbaiki,
bukan tesis yang gugur. Data goresan sudah tersimpan, jadi putaran perbaikan
tidak perlu melibatkan anak lagi. **Batas 3 putaran**, dihitung dari
`prompt_versi` yang tercatat di tiap hasil diagnosis — bukan dari ingatan.

### Rencana harian

| Hari | Pekerjaan |
|---|---|
| 1 | Kanvas tinta web + perekaman titik historis + **golden test `toSamples()`** — dicek dulu di trackpad Mac |
| 1 | **Tes 10 menit ke anak** — coret-coret bebas, di device sentuh apa pun yang tersedia (boleh geser hari kalau belum ada). Kalau anak tidak nyaman, berhenti di sini. |
| 2 | Kanvas berlangkah, kotak jawaban, 10 soal, tombol unduh JSON + **pindahkan berkas ke Mac (USB/AirDrop/manual)** |
| 3 | Render goresan jadi PNG + turunan waktu; tulis malrule untuk 10 soal uji |
| 4 | `tinta_heuristik` (didahulukan), lalu `tinta_llm` + cache berkunci versi |
| 5 | Sesi uji sungguhan dengan anak — Bapak menilai sendiri lebih dulu |
| 6–7 | Wawancara NEA, bandingkan dua angka, perbaiki prompt (maks 3 putaran) |

Uji ke anak muncul di hari pertama, bukan hari terakhir: asumsi paling murah
untuk digugurkan diuji sebelum ada satu baris pun kode diagnosis ditulis.
Heuristik didahulukan dari LLM di Hari 4 karena menulis baseline *setelah*
melihat hasil LLM adalah cara paling mudah untuk tanpa sadar membuatnya
kalah.

### Tiga penyesuaian dari riset (sudah masuk rencana spike)

1. **Strukturkan wawancara pakai protokol 5-prompt NEA:** "Baca soal ini" →
   "Ceritakan apa yang diminta" → "Tunjukkan bagaimana kamu dapat jawabannya,
   ceritakan pikiranmu" → "Kerjakan sambil dijelaskan" → "Tulis jawabannya".
   Menggantikan "coba jelaskan caramu" yang bebas.
2. **Jangan tambah kategori "Encoding"** ke skema output. Jawaban akhir
   diketik (bukan OCR) jadi kesalahan tulis-akhir nyaris tidak mungkin di
   jalur ini. Kalau muncul, catat manual saat wawancara.
3. **Batas maksimal 3 putaran perbaikan prompt** untuk zona abu-abu (5–6
   cocok) di atas data yang sama, sebelum memutuskan lulus/gagal final —
   supaya tidak diam-diam overfitting ke 10 soal satu anak ini.

---

## 05 · Roadmap setelah spike

Melebar hanya kalau lapisan sebelumnya terbukti jalan — bukan bangun semua
fitur dulu baru diuji.

### Fase 0 — sekarang · 5–7 hari

**Spike: coretan ke diagnosis.** 10 soal, satu anak, satu sesi uji.
Membuktikan atau menggugurkan tesis inti sebelum satu baris kode "produk"
ditulis.

### Fase 1 — setelah spike lulus

**v1 harian, satu keluarga.** Urutannya diubah di revisi 17 Agustus —
fondasi penyimpanan didahulukan:

1. **Fondasi penyimpanan** (PRD §8.4): konten immutable / kejadian
   append-only / status sebagai turunan. **Didahulukan** karena begitu data
   anak terkumpul rutin, mengubah bentuk penyimpanan jadi jauh lebih mahal —
   dan janji "prompt bisa diiterasi di atas data yang sama" hanya berlaku
   kalau riwayat tidak pernah ditimpa.
2. **Lapisan pra-fondasi kelas 4** diputuskan lebih dulu atau bersamaan —
   PDF sumber tidak langsung cocok (mengasumsikan operasi dasar sudah
   otomatis).
3. **Graf topik berprasyarat** menggantikan 10-soal-hardcoded.
4. **Orkestrator `osn sync`** (PRD §8.7) — satu perintah untuk seluruh
   siklus HP→Mac→tinjauan→HP. Masuk Fase 1, bukan ditunda: 10 langkah manual
   × 3 sesi/minggu adalah bentuk kegagalan yang tidak muncul di gerbang
   teknis mana pun tapi menghentikan produk di minggu ketiga.
5. **Antrean pengulangan & buku kesalahan**, menyusul graf topik.
6. **Pipeline diagnosis tetap di Mac** — jangan pindahkan AI ke dalam
   aplikasi.
7. **Catatan DPIA ringkas** ditulis di awal fase ini, sebelum data anak
   terkumpul rutin.

> **Koreksi terhadap versi 14 Agustus.** Dokumen lama menyebut langkah
> pertama setelah spike adalah "memindahkan panggilan API dari Mac ke
> belakang layanan sederhana, karena kunci Anthropic tidak boleh berakhir di
> dalam APK." Itu **tidak lagi berlaku** — PRD §7.1/§8.6 menetapkan diagnosis
> tetap di Mac untuk seluruh v1, tanpa layanan perantara apa pun. Kalau
> `tinta_heuristik` lolos gerbang spike, bahkan tidak ada panggilan API yang
> perlu dipindahkan.

### Fase 2 — setelah v1 stabil

**Foto kertas fisik.**
- SOP ambang ganda (auto-terima/auto-tolak/rute-ke-Bapak), bukan satu ambang
  tunggal
- Transkripsi verbatim selalu ditampilkan ke Bapak sebelum diagnosis jalan
- Kanvas bebas + OCR halaman-penuh dengan guard, bukan kotak jawaban kaku
- Pustaka pola kesalahan terkurasi (perluasan pustaka malrule), bukan AI
  menebak bebas

### Fase 3 — opsional, belum tentu perlu

**Dashboard orang tua.** Riset gagal menemukan pola tervalidasi untuk konteks
non-institusi. Bapak sendiri yang jadi pengguna utama — `osn status` (laporan
teks) mungkin cukup lama sebelum ada alasan nyata membangun UI. Kalau
dikerjakan, perlakukan sebagai riset+piloting kecil sendiri.

**Tetap "ditunda", tidak berubah:** mode anak terkunci, kanvas geometri &
daftar berbaris, AI di dalam aplikasi.

---

## 06 · Risiko & pertanyaan terbuka

### Klaim yang belum diverifikasi

Dipisah dari "risiko" karena sifatnya beda: ini klaim teknis yang **sudah
dipakai sebagai dasar keputusan** tapi belum pernah diuji di perangkat/data
nyata (PRD §9.4).

| Klaim | Kalau salah | Diverifikasi |
|---|---|---|
| `adb exec-out run-as` bisa baca internal storage app di HP target | Mekanisme transfer diganti fallback `ACTION_SEND` | Hari 2 spike |
| `tinta_heuristik` cukup ≥7/10 tanpa LLM | `tinta_llm` masuk lingkup v1 dengan biaya & cache-nya | Hari 6–7 spike |
| Anak nyaman menulis dengan jari sampai soal ke-10 | Seluruh kanal tinta gugur; mundur ke foto kertas/jawaban akhir saja | Hari 1 spike |
| 20 soal kalibrasi cukup menghasilkan malrule berguna lintas kurikulum | Cakupan deterministik tumbuh jauh lebih lambat; authoring manual harus dijadwalkan eksplisit | Beberapa minggu data v1 |

### Risiko

| Risiko | Kenapa penting | Kapan diputuskan |
|---|---|---|
| Distribusi B/K/H pada anak SD kelas 4 belum tervalidasi | Studi NEA yang ditemukan semua pada anak SMP+; kalau "K" tidak dominan di usia ini, metrik utama perlu ditinjau | Setelah beberapa minggu data v1 riil |
| Overfitting prompt ke 10 soal satu anak | Bisa lolos gerbang teknis tanpa generalisasi | Sebelum mulai iterasi — pakai batas 3 putaran, dihitung dari `prompt_versi` |
| PP 17/2025 belum ada preseden penegakan individu skala kecil | Kepatuhan sekarang preventif, bukan teruji hukum | Makin penting begitu Fase 2 simpan foto di cloud, bukan lokal |
| Ambang OCR dari literatur berasal dari ujian universitas | Angka spesifik kemungkinan tidak langsung berlaku ke anak SD | Piloting internal begitu Fase 2 dimulai |
| Dashboard orang tua mungkin tidak dibutuhkan sama sekali | Menghindari kerja yang tidak perlu | Ditinjau ulang setelah Fase 1 jalan beberapa bulan |

---

## 07 · Bentuk aplikasinya

Bukan aplikasi belajar yang bertambah fitur seiring waktu — alat diagnosis
yang mulai sangat sempit dan baru melebar kalau tiap lapisan terbukti jalan.

**Untuk anak.** Buka HP, lihat daftar soal — bukan level, bukan XP, bukan
lencana. Kanvas kosong berlangkah untuk coret-coret, jawaban akhir diketik
terpisah. Tidak ada skor yang ditampilkan. Tidak ada AI yang mengobrol
dengannya. Selesai ~10 soal atau 30–40 menit, 3x seminggu.

**Untuk Bapak.** Bukan rapor angka — peta topik mana yang punya K aktif dan
trennya. "Salah konsep di pengurangan pecahan berpenyebut beda, sudah 3x
dalam 2 minggu" — lengkap bukti dari coretan anak. Bapak yang memutuskan mau
diapakan.

**Peran AI.** Selalu di belakang layar, tidak pernah bicara ke anak. Membaca
coretan + waktu pengerjaan, menerjemahkan jadi kode B/K/H dengan bukti — dan
boleh mengaku tidak tahu kalau tulisannya memang tidak terbaca. Kalau
`tinta_heuristik` lolos gerbang spike, peran AI di v1 bisa hilang seluruhnya
dari jalur diagnosis rutin.

**Bentuk teknis v1** (PRD §8.1 — enam komponen):

1. App Android tiga layar, tanpa izin internet, tanpa akun, tanpa server
2. Pemindahan file HP↔Mac lewat kabel USB (`adb`)
3. Tool dekompilasi kurikulum PDF → graf + template soal (sekali jalan, bukan
   runtime)
4. Skrip diagnosis Tahap A (malrule) + Tahap B (heuristik / LLM)
5. Tinjauan orang tua lewat file YAML di editor — tanpa UI
6. Konten immutable + kejadian append-only + status turunan

Semuanya dibungkus satu perintah `osn sync`. Pilihan sengaja, bukan
keterbatasan sementara: pada skala satu anak, satu orang tua yang juga
developer, satu Mac, satu HP, ini ukuran yang tepat — bukan utang teknis.

> **Catatan 18 Agustus.** Komponen 1 ("App Android") di atas masih deskripsi
> v1 pasca-spike, belum diputuskan ulang. Untuk spike Fase 0, perekam
> goresannya web (lihat §04) — kalau presisi capture web ternyata cukup,
> komponen 1 di v1 bisa jadi tetap web (dibungkus jadi app lewat WebView atau
> serupa) alih-alih native Kotlin. Keputusan ini menunggu hasil spike, tidak
> perlu diambil sekarang.

| Kapan | Bentuknya | Yang dibuktikan |
|---|---|---|
| Minggu ini | Spike — 10 soal, satu anak, satu sesi | Apakah cara berpikir anak beneran bisa dibaca dari coretannya — dan apakah butuh AI untuk itu |
| Setelah spike lulus | v1 harian — fondasi penyimpanan + graf topik + `osn sync` | Dipakai beneran 3x/minggu, bukan cuma uji coba |
| Bulan-bulan berikutnya | + jalur foto kertas fisik, SOP ketat | Diagnosis tidak lagi terbatas ke layar HP |
| Kalau perlu | Dashboard/laporan lebih rapi | Baru kalau `osn status` ternyata kurang |

---

Sumber: memori keputusan produk (14 Agustus 2026) · `PRD.md` (revisi 17
Agustus 2026) · `Rencana Spike - Coretan ke Diagnosis.md` · laporan riset
dua-putaran (47 sumber, 38 klaim terverifikasi).

Dokumen kerja — perbarui setiap kali keputusan baru diambil, jangan biarkan
basi.
