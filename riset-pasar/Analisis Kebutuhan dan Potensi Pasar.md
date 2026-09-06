# Analisis Kebutuhan & Potensi Pasar — Diagnosis Jenis Kesalahan (B/K/H) Matematika SD Indonesia

**Status dokumen:** snapshot riset pasar 16 Agustus 2026. Temuan kompetitor,
kebutuhan, dan batas bukti tetap berguna; roadmap, bentuk teknis, strategi B2C
Rp150–300 ribu, serta instruksi “lanjutkan spike/Fase 2” di dalam dokumen ini
bukan arahan kerja aktif. Keputusan komersial terbaru memakai GTM tutor-first
dengan harga penetrasi per anak; lihat
`2026-09-06-peluang-komersial/keputusan-positioning-harga-validasi.md` dan
`2026-09-06-peluang-komersial/GTM-tutor-first.md`.
Aplikasi sekarang adalah Jagomat web SQLite di `../mesin/`; acuan pekerjaan
teknis berikutnya ada di `../CLAUDE.md` dan plan siklus belajar terpandu terbaru.

Dokumen kerja · disusun 16 Agustus 2026
Sumber utama: `gap-pasar-edtech-matematika-sd/report.md` (18 item riset, 1131 baris) · `PRD.md` · `Rencana Produk - Peta Jalan`
Pertanyaan yang dijawab: *apakah ada kebutuhan pasar nyata untuk produk ini, dan seberapa besar potensinya kalau dikembangkan?*

---

## Ringkasan Eksekutif

| Dimensi | Kesimpulan | Kekuatan bukti |
|---|---|---|
| **Kebutuhan** | NYATA dan terukur: ~32% siswa SD di bawah kompetensi minimum numerasi; 82% siswa 15 tahun di bawah Level 2 PISA; semua kompetitor berhenti di skor/nama-topik, tidak ada yang mendiagnosis **jenis** kesalahan | **Kuat** (AKM = sensus nasional; PISA = sampel representatif) |
| **Kesediaan membayar** | Terbukti, tapi di band harga offline (Rp 425–750rb/bulan/subjek): orang tua sudah membayar premium 3–6x untuk *level-placement* yang lebih presisi | **Moderat** (harga publikasi resmi = kuat; atribusi premium ke "presisi diagnostik" = inferensi) |
| **Gap kompetitif** | Struktural, bukan celah kecil: bahkan ALEKS (Knowledge Space Theory) **membuang** info jenis kesalahan sebagai noise statistik; Eedi satu-satunya yang mendiagnosis miskonsepsi — tapi satu-sumbu (konsep saja) dan tidak ada di Indonesia | **Kuat** (sumber primer vendor) |
| **Potensi pasar** | Nyata sebagai **baji sempit**: SAM online tutoring USD 1,3M–1,3B tergantung definisi; bottom-up ~Rp 58M/tahun hanya dari 1% satu angkatan kelas 4 di harga tier CoLearn. Yang membuka uang adalah kredibilitas diagnostik, bukan konten | **Moderat** (angka vendor saling konflik, order-of-magnitude saja) |
| **Risiko terbesar** | (1) Diagnosis tanpa remediasi yang baik **terbukti tidak memperbaiki hasil** (Sleeman 1989); (2) belum ada satu pun di dunia yang membuktikan error-type-diagnosis menaikkan hasil belajar — peluang sekaligus risiko; (3) edtech online Indonesia punya sejarah gagal monetisasi (Zenius tutup, Ruangguru PHK) | **Kuat** (RCT peer-reviewed) |
| **Rekomendasi** | Kebutuhan cukup untuk **melanjutkan spike**, bukan untuk langsung membangun perusahaan. Potensi pasar jangka menengah paling besar lewat posisi "alat diagnostik untuk orang tua + guru" di band harga offline — tapi itu hanya berlaku kalau tesis teknis (tinta → B/K/H) terbukti bekerja | — |

---

## Bagian 1 — Kebutuhan Pasar (Market Need)

### 1.1 Skala masalahnya nasional dan terukur, bukan anekdot

- **PISA 2022**: Indonesia skor matematika **366** (rata-rata OECD 472), peringkat 69 dari 81 negara. Hanya **18%** siswa mencapai Level 2 ke atas (OECD: 69%) — artinya **±4 dari 5 anak Indonesia usia 15 tahun tidak bisa melakukan penalaran matematika dasar**. ([OECD GPS](https://gpseducation.oecd.org/CountryProfile?primaryCountry=IDN&topic=PI) · [OECD country note](https://www.oecd.org/en/publications/pisa-2022-results-volume-i-and-ii-country-notes_ed6fbcc5-en/indonesia_c2e1ae0e-en.html))
- **AKM / Asesmen Nasional (sensus, bukan sampel)**: proporsi siswa yang mencapai kompetensi minimum **numerasi**: 45,24% (2022) → 62,45% (2023) → **67,94% (2024)**. Membaik cepat, tapi masih **±1 dari 3 siswa SD (~23,93 juta total, ±4 juta per angkatan) di bawah minimum numerasi** pada 2024. ([Kemendikdasmen](https://www.kemendikdasmen.go.id/siaran-pers/12500-mendikdasmen-berharap-rapor-pendidikan-jadi-acuan-pengembang) · [Pojok Satu](https://www.pojoksatu.id/edugov/1085798302/hasil-rapor-pendidikan-2022-2024-dirilis-kemendikdasmen-tunjukkan-peningkatan-literasi-dan-numerasi-siswa-berikut))
- **Titik kritis produk**: verdict AKM adalah **1 bit per anak** ("mencapai" / "tidak mencapai"). Bahkan instrumen pemerintah memberi tahu orang tua bahwa anaknya gagal — tanpa memberi tahu *mengapa*. Persis ini yang produk isi.

### 1.2 Masalah yang dirasakan orang tua adalah masalah ATRIBUSI KAUSAL, bukan masalah skor

- Kurikulum Merdeka menghapus angka merah dan ranking, diganti deskripsi naratif. Reaksi terdokumentasi: orang tua tidak bisa menemukan kelemahan anaknya — *"Anak saya ini pintar atau tidak, sih? Kok bahasanya muter-muter?"*, dengan rapor berakhir di kalimat generik *"Perlu bimbingan lebih lanjut"*. ([BIC](https://bic.id/artikel/fase-pembelajaran-kurikulum-merdeka-panduan-lengkap/) · [Tirto](https://tirto.id/rentang-nilai-raport-kurikulum-merdeka-dan-cara-menghitungnya-gTwx))
- Guru menghadapi masalah cermin: kesulitan *"menerjemahkan capaian kompetensi menjadi deskripsi yang singkat, jelas"* dan menyusun instrumen asesmen yang sesuai ([transformingdigitaleducation.com](https://www.transformingdigitaleducation.com/menyusun-deskripsi-rapor-kurikulum-merdeka-sd/) · [Semantic Scholar](https://www.semanticscholar.org/paper/Analisis-Kompetensi-Guru-SD-Dalam-Merancang-Asesmen-Kompetensi-Guru/f61376f2e2329916bebaac70961c499fe8b072a2)).
- Kegagalan atribusi yang sama berulang di lapisan les: orang tua **membayar untuk usaha** (belajar keras, banyak latihan, bimbel bulanan) dan tetap tidak bisa menjelaskan kenapa hasil ujian tidak sesuai harapan — kutipan dari blog Sparks Math sendiri.

### 1.3 Gap struktural: semua kompetitor berhenti di "topik mana yang lemah", tidak ada yang sampai ke "kesalahan macam apa"

Hasil riset 18 item (10 produk/benchmark kompetitor, 5 kerangka akademik, sinyal pasar):

| Tingkat diagnosis | Siapa | Status |
|---|---|---|
| **Skor benar/salah saja** | Photomath, QANDA (untuk pengguna Indonesia) | Tidak mendiagnosis sama sekali — membaca *soal*, bukan *kerja anak* |
| **Topic-mastery map** | Ruangguru, Zenius, IXL, Matific, ALEKS, Kumon, Khan Academy Kids, DreamBox (untuk orang tua) | "Lemah di topik X" — tidak pernah "salah baca soal" vs "salah konsep" vs "salah hitung" |
| **Miskonsepsi via distraktor MCQ** | Eedi (UK) — 60.000+ soal | Satu-satunya "ya" di seluruh riset, tapi **satu-sumbu (konsep saja)**: buta terhadap kesalahan baca dan hitung; tidak ada di Indonesia |
| **Strategy-trace internal** | DreamBox (untuk guru) | Menganalisis proses anak, tapi label diagnosisnya **tidak pernah diterbitkan** dan **tidak pernah ditunjukkan ke orang tua** |

Temuan paling tajam: **ALEKS** — model siswa paling canggih di edtech komersial (Knowledge Space Theory, 4–5 juta siswa/tahun) — secara formal memodelkan "careless error" sebagai probabilitas β_q per item, lalu **membuangnya sebagai noise statistik** di update Bayesian. Informasi "anak ini salah hitung, bukan tidak paham" *ada di dalam matematikanya ALEKS* dan sengaja tidak pernah sampai ke manusia mana pun. ([JMP 2021](https://jmatayoshi.github.io/publications/JMP2021_KST_ALEKS_preprint.pdf)) Ini bukti terbersih bahwa **error-type diagnosis adalah lapisan yang belum diisi**, bukan sesuatu yang sudah dipecahkan diam-diam.

### 1.4 Gap-nya sudah "diberi nama" di copy pemasaran pasar itu sendiri

Sparks Math (les offline Singapore Math, Rp 500rb/bulan) mendekomposisi kegagalan ujian anak kelas 6 menjadi *"salah memahami soal, salah menerapkan rumus, atau kesalahan hitung yang tidak disengaja"* — **hampir persis B/K/H** — padahal satu-satunya asesmen yang benar-benar ditawarkannya adalah "Test Gaya Belajar Anak". ([Sparks Math](https://math.sparks-edu.com/blog/6-kesalahan-umum-anak-kelas-6-gagal-ujian-matematika-dan-cara-mengatasinya/))

**Implikasi**: konsepnya tidak butuh edukasi pasar — sudah ada di bahasa komersial. Yang belum ada hanyalah **instrumen pengukurnya**. Ini sinyal permintaan paling bersih yang bisa diminta.

### 1.5 Landasan teoretis: jenis kesalahan itu nyata, terukur, dan mayoritas BUKAN kesalahan hitung

- **Clements (1980)** — 6.595 kesalahan dari 634 anak: hanya **±25%** kesalahan adalah kegagalan proses hitung; **±40%** adalah kesalahan membaca/memahami/mentransformasi soal, **±30%** careless. Artinya **±7 dari 10 kesalahan matematika anak SD terjadi SEBELUM anak berhitung** — dan seluruh industri drill-and-practice hanya menangani 25%-nya.
- **Newman's Error Analysis (1977)** memetakan hampir 1-ke-1 ke B/K/H: B ≈ Reading+Comprehension, K ≈ Transformation, H ≈ Process Skills. Belum pernah dioperasionalkan jadi perangkat lunak — tetap prosedur wawancara manual satu-anak-satu-waktu. ([White 2009](https://www.mav.vic.edu.au/Tenant/C0000019/00000001/downloads/Resources/annual-conferences/2009/08White.pdf))
- **VanLehn (1983–1990)**: slip (≈H) vs bug (≈K prosedural) vs miskonsepsi — katalog 200+ bug pengurangan, tapi bug **tidak stabil** antar kesempatan dan **tidak transfer antar populasi** (Payne & Squibb 1990): taksonomi harus diturunkan ulang dari kerja anak Indonesia, tidak bisa diimpor.

### 1.6 Tailwind kebijakan

Kurikulum Merdeka **secara eksplisit mewajibkan asesmen diagnostik** di awal pembelajaran — *"mengidentifikasi kemampuan peserta didik agar guru dapat merancang pembelajaran yang sesuai"* — sementara guru secara terdokumentasi kesulitan menyusun instrumennya. Kebijakan sudah melegitimasi dan menamai pekerjaan yang akan dilakukan produk ini; instrumennya belum dibangun siapa pun.

### 1.7 Bukti permintaan nyata dari perilaku pengguna (bukan survei)

- **QANDA**: ±2,5 juta pengguna Indonesia (klaim 2020), sempat #1–2 Google Play Education mengalahkan Ruangguru & Zenius — untuk *menjawab soal*, bukan mendiagnosis. Permintaan "bantuan matematika instan" sudah jenuh; "kata tahu apa yang salah dipahami anak" belum tersentuh.
- **Photomath**: 100M+ download global, 32 bahasa termasuk Indonesia, tanpa akun orang tua, tanpa diagnosis — dan sebagian besar pemakaian nyatanya adalah **orang tua memeriksa PR anak** dengan alat yang salah. Bukti tak langsung permintaan orang tua yang tidak terlayani.
- **Kumon**: orang tua membayar Rp 430–525rb/bulan/subjek dan hadir ke orientasi bulanan untuk narasi progres yang kredibel — permintaan pelaporan orang tua **sudah mapan**, yang mereka terima hanya "berapa salah, seberapa cepat", tidak pernah "salah macam apa".

---

## Bagian 2 — Potensi Pasar (Market Potential)

### 2.1 Sizing pasar

| Lapisan | Nilai | Sumber & status |
|---|---|---|
| **TAM** — edtech Indonesia | USD 3,23 M (2024) → USD 8,81 M (2033), CAGR 11,79% | [IMARC](https://www.imarcgroup.com/indonesia-edtech-market) — estimasi vendor, metodologi tidak dipublikasi |
| **TAM sempit** — cloud K-12 edtech | USD 1,9 M (2025) → USD 3,5 M (2031), CAGR 14,8% | [Ken Research](https://www.kenresearch.com/indonesia-cloud-based-edtech-for-k-12-market) |
| **SAM** — online private tutoring | USD 1,3 M (2025) | [Ken Research](https://www.kenresearch.com/indonesia-online-private-tutoring-market) |
| **Denominator demografis** | ±23,93 juta siswa SD; **±4 juta per angkatan kelas** | [Databoks/Kemendikdasmen](https://databoks.katadata.co.id/pendidikan/statistik/66fe4973ec087) — resmi |

**Sanity check bottom-up lama (historis, bukan target):** versi awal memakai 1%
dari satu angkatan kelas 4 × Rp120.000/bulan untuk menggambarkan skala. Setelah
keputusan tutor-first dan harga penetrasi, hitungan itu tidak relevan untuk
operasi. Model aktif harus dihitung dari anak aktif per tutor, biaya support,
CAC, dan renewal. Contoh: 1.000 anak pada harga rata-rata Rp6.000 menghasilkan
omzet Rp6 juta/bulan sebelum payment, infrastruktur, support, pajak, dan churn.
Angka ini hanya aritmetika skenario—bukan perkiraan pelanggan atau pendapatan.

### 2.2 Harga pasar sebagai pembanding, bukan strategi aktif

- Gradien harga teramati: **offline Rp425–750 ribu/bulan** (Kumon,
  Sakamoto, Sparks Math) vs **online Rp90–280 ribu/bulan** (CoLearn,
  Ruangguru Math Champs). Angka ini menunjukkan alternatif yang sudah dibeli,
  bukan harga yang wajib ditiru Jagomat.
- Zenius—20 tahun beroperasi, tutup Januari 2024 setelah dilaporkan membakar
  sekitar USD40 juta, lalu kembali sebagai web-only—menjadi peringatan bahwa
  konten digital yang tidak terdiferensiasi sulit dimonetisasi.
- **Keputusan aktif berbeda dari rekomendasi awal:** Jagomat memakai harga
  penetrasi per anak dan distribusi tutor-first. Nilai yang dijual adalah alat
  kerja tutor—latihan, review diagnosis, remedial, dan laporan—bukan layanan
  pengajaran premium setara Kumon.

### 2.3 Jalur pasar aktif

1. **Beachhead—tutor/les mikro:** tutor matematika SD dengan 8–30 murid,
   memberi tugas rutin, dan masih mengelola persiapan/koreksi secara manual.
2. **Segmen kedua—orang tua pendamping aktif:** orang tua yang benar-benar
   mengajar anak sendiri; bukan keluarga yang mencari aplikasi mandiri.
3. **Ekspansi tertunda—sekolah:** baru setelah organisasi/role, consent-retensi,
   provenance, entitlement, dan bukti penggunaan tutor siap.
4. **Harga uji:** retail Rp10.000/anak/bulan; grosir 10 anak Rp75.000,
   25 anak Rp150.000, dan 50 anak Rp250.000 per bulan. WTP hanya terbukti lewat
   pembayaran dan pembaruan, bukan jawaban wawancara.

### 2.4 Keunggulan kompetitif yang bisa dipertahankan (moat)

| Aset | Kenapa sulit ditiru |
|---|---|
| **Taksonomi B/K/H lokal** | Aturan diagnosis yang diuji pada konteks Indonesia dan dikoreksi tutor dapat menjadi aset; keunggulan ini masih harus dibuktikan lewat data pilot aman. |
| **Pola jawaban salah berparameter** | Malrule deterministik berlaku pada variasi angka baru dan tidak bergantung pada AI menebak bebas. |
| **Umpan balik koreksi tutor** | Koreksi manusia dapat menunjukkan malrule mana yang membantu atau menyesatkan, tetapi baru menjadi moat setelah volume dan kualitas datanya memadai. |
| **Posisi bukti** | Belum ada bukti dampak Jagomat; kesempatan diferensiasi muncul bila pilot dan studi berikutnya mengukur workflow serta outcome dengan jujur. |
| **Privasi yang transparan** | Dapat menjadi kepercayaan bila consent, minimisasi, retensi, akses admin, dan penggunaan pihak ketiga benar-benar dijalankan—bukan sekadar klaim. |

---

## Bagian 3 — Analisis Jujur: Risiko & Batasan Potensi

Bagian ini sama pentingnya dengan dua bagian pertama — potensi pasar hanya nyata kalau risikonya dikelola.

1. **Diagnosis saja TIDAK memperbaiki hasil belajar.** Sleeman et al. (1989), 3 studi terkontrol: remediasi berbasis model (MBR) **tidak lebih baik** dari sekadar mengajar ulang; hanya pendekatan *cognitive conflict* (mengonfrontasi anak dengan akibat kesalahannya) yang menang. IMPLIKASI: produk yang menjual taksonomi cantik tanpa **aktivitas remediasi yang baik** menjual separuh yang mati. Nilai harus dibangun di resep tindakan (PRD §1), bukan di label B/K/H.
2. **Klaim "error-type diagnosis menaikkan hasil" belum terbukti secara empiris di pasar mana pun.** Eedi punya RCT terbaik (2–4 bulan progres tambahan), tapi menguji bundel utuh, bukan lapisan diagnosisnya. Ini peluang (tidak ada yang bisa menyangkal) sekaligus risiko (belum ada yang membuktikan).
3. **Sejarah monetisasi edtech online Indonesia buruk**: Zenius tutup, Ruangguru PHK massal 2022, CoLearn bergeser dari foto-soal ke bimbel live berlangganan. Pasar menghukum konten tak terdiferensiasi.
4. **Bukti keluhan orang tua masih lemah** (vignette media, bukan survei besar; n=30 dan n=10 pada proksi terdekat). Sebelum investasi besar: perlu riset validasi kecil (mis. 20–30 wawancara orang tua) untuk mengonfirmasi masalah atribusi dan WTP.
5. **Angka market size vendor saling konflik** (IMARC 11,79% vs 24,5% CAGR) — perlakukan sebagai order-of-magnitude.
6. **Keterbatasan teknis historis**: rancangan awal memakai HP pinjaman, tanpa internet, dan satu anak per device. Aplikasi sekarang sudah web multi-keluarga dan jalur foto sudah ada; risiko skala harus dinilai ulang dari runtime aktif, bukan roadmap Fase 2 lama.
7. **Kunci fokus K sebagai metrik utama** belum tervalidasi untuk usia SD kelas 4; pantau bersama status evaluasi/checkpoint, bukan hitungan K topik secara tunggal.
8. **PP 17/2025**: kepatuhan sekarang preventif, belum teruji hukum untuk operator individu skala kecil.

---

## Bagian 4 — Kesimpulan & Rekomendasi

### Kebutuhan pasar: **TERBUKTI**
Skala masalah terukur secara nasional (AKM sensus + PISA), gap kompetitif struktural (dibuktikan bahkan oleh ALEKS dan copy pemasaran Sparks Math), landasan teoretis 50 tahun, dan tailwind kebijakan (mandat asesmen diagnostik tanpa instrumen). Tidak ada pertanyaan "apakah ada kebutuhan" — pertanyaannya hanya "apakah produknya bekerja dan bisa dijual".

### Potensi pasar: **LAYAK DIUJI, dengan syarat**
- Sinyal kebutuhan cukup untuk pilot niche, tetapi belum ada transaksi Jagomat;
  jangan annualisasi denominator siswa atau harga pesaing menjadi pendapatan.
- **Syarat 1 — loop utuh terbukti**: diagnosis terkonfirmasi harus berlanjut ke
  intervensi, latihan terbimbing, evaluasi, dan checkpoint.
- **Syarat 2 — nilai operasional tutor terbukti**: waktu persiapan/koreksi turun,
  diagnosis direview, remedial digunakan, dan laporan dibahas.
- **Syarat 3 — bukti lokal aman**: kumpulkan bukti agregat/pseudonim dari pemakaian
  anak Indonesia; jangan memindahkan jawaban atau identitas anak ke repo riset.
- **Syarat 4 — harga penetrasi tetap ekonomis**: biaya AI, support, CAC, serta
  churn harus diukur per anak aktif dan per akun tutor.

### Syarat produk bila riset ini dipakai sekarang

1. **Tesis produk diuji dari loop utuh**, bukan volume soal atau kanal goresan.
2. **Nilai berada di tindakan**, bukan label; intervensi pra-tulis dan direview
   manusia, bukan tindakan AI langsung ke anak.
3. **Bukti lokal:** snapshot outcome pseudonim/agregat, bukan data anak mentah.
4. **Validasi pasar utama:** discovery dan pilot berbayar terhadap 5 tutor yang
   mengelola beberapa murid; cohort orang tua pendamping menjadi pembanding.
5. **Bukti komersial:** pembayaran awal dan invoice kedua, bukan skor WTP.

Instruksi urutan spike/B2C dan arsitektur YAML/Mac pada versi awal dokumen ini
sudah superseded; lihat banner status.

---

*Dokumen ini menyintesis `gap-pasar-edtech-matematika-sd/report.md` (18 item, 47+ sumber, 38 klaim terverifikasi 3-vote) plus pengecekan pasar terbaru. Angka market size vendor bersifat order-of-magnitude. Semua klaim kunci punya sumber di report.md — lihat bagian "Sources" per item untuk detail.*
