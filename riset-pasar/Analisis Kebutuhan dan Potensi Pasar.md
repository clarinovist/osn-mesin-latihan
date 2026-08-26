# Analisis Kebutuhan & Potensi Pasar — Diagnosis Jenis Kesalahan (B/K/H) Matematika SD Indonesia

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

**Sanity check bottom-up** (perhitungan sendiri, bukan angka publikasi): 1% dari satu angkatan kelas 4 = ±40.000 anak × Rp 120.000/bulan (tier harga CoLearn) × 12 bulan ≈ **Rp 57,6 M/tahun (±USD 3,5 juta)**. Dengan harga tier offline (Rp 300–500rb/bulan), angkanya 2,5–4x lipat — tapi penetrasinya jauh lebih kecil. Pesannya: **potensi itu nyata untuk baji yang sempit, bukan untuk pemain luas.**

### 2.2 Di mana uangnya berada — dan bagaimana memposisikan harga

- Gradien harga teramati: **offline Rp 425–750rb/bulan** (Kumon, Sakamoto, Sparks Math) vs **online Rp 90–280rb/bulan** (CoLearn, Ruangguru Math Champs). Premium offline 3–6x.
- Zenius — 20 tahun beroperasi, tutup Januari 2024 setelah dilaporkan membakar ±USD 40 juta, kembali Juli 2024 sebagai web-only — membuktikan **konsumen Indonesia tidak mau membayar harga app untuk konten yang tidak terdiferensiasi**.
- Kesimpulan strategis riset: **harga dan posisi produk sebaiknya mengacu pada band Kumon/Sparks Math (kredibilitas diagnostik), bukan band Ruangguru/CoLearn (volume konten)**. Yang dibayar orang tua bukan konten, tapi **presisi penempatan + narasi progres manusiawi** — dan produk ini menawarkan presisi yang satu tingkat lebih dalam dari apa pun yang ada di pasar (jenis kesalahan, bukan level).

### 2.3 Jalur pasar yang realistis (berjenjang)

1. **Fase sekarang — satu keluarga (v1)**: bukan pasar, tapi **pabrik bukti**. Nilai utamanya: (a) membuktikan tesis teknis, (b) menurunkan taksonomi B/K/H dari kerja anak Indonesia (mengatasi masalah transfer Payne & Squibb), (c) mengumpulkan bukti pre/post bahwa remediasi berbasis B/K/H menaikkan hasil — bukti yang **tidak dimiliki satu pun kompetitor**.
2. **Fase 2 — perluasan B2C sempit**: orang tua kelas 4–6 di kota besar (Jabodetabek/Java urban), harga Rp 150–300rb/bulan, positioning "rapor yang bisa dibaca + resep malam ini", meniru model penempatan Sparks Math.
3. **Fase 3 — B2B (guru/sekolah) — potensi terbesar**: model Eedi (UK) membuktikan guru membeli diagnosis miskonsepsi (160.000+ guru, 19.000 sekolah) dan model ASSISTments membuktikan guru memakai data kesalahan untuk menargetkan review. Kurikulum Merdeka sudah mewajibkan asesmen diagnostik **tanpa instrumen yang siap pakai** — celah distribusi yang sudah dibuka pemerintah. Jalur ini juga yang paling tahan terhadap risiko "orang tua tidak mau bayar".

### 2.4 Keunggulan kompetitif yang bisa dipertahankan (moat)

| Aset | Kenapa sulit ditiru |
|---|---|
| **Taksonomi B/K/H lokal** | Harus diturunkan dari data anak Indonesia (Payne & Squibb); kompetitor global tidak punya data lokal, kompetitor lokal tidak punya mesin diagnosis |
| **Data goresan + sidik jari jawaban salah** | Data proses anak (bukan cuma jawaban akhir) adalah substrat yang tidak dikumpulkan siapa pun — Kumon mengumpulkan lalu membuangnya |
| **Tabel sidik jari tumbuh dari pemakaian** | Setiap koreksi orang tua memperkaya tabel; efek jaringan data satu arah |
| **Posisi bukti** | Tidak ada kompetitor dengan studi pre/post remediasi B/K/H; entrant pertama yang menerbitkannya memegang posisi yang tak bisa disaingi |
| **Privasi-by-default** | Menjadi fitur jual di pasar yang mulai sadar PP 17/2025 |

---

## Bagian 3 — Analisis Jujur: Risiko & Batasan Potensi

Bagian ini sama pentingnya dengan dua bagian pertama — potensi pasar hanya nyata kalau risikonya dikelola.

1. **Diagnosis saja TIDAK memperbaiki hasil belajar.** Sleeman et al. (1989), 3 studi terkontrol: remediasi berbasis model (MBR) **tidak lebih baik** dari sekadar mengajar ulang; hanya pendekatan *cognitive conflict* (mengonfrontasi anak dengan akibat kesalahannya) yang menang. IMPLIKASI: produk yang menjual taksonomi cantik tanpa **aktivitas remediasi yang baik** menjual separuh yang mati. Nilai harus dibangun di resep tindakan (PRD §1), bukan di label B/K/H.
2. **Klaim "error-type diagnosis menaikkan hasil" belum terbukti secara empiris di pasar mana pun.** Eedi punya RCT terbaik (2–4 bulan progres tambahan), tapi menguji bundel utuh, bukan lapisan diagnosisnya. Ini peluang (tidak ada yang bisa menyangkal) sekaligus risiko (belum ada yang membuktikan).
3. **Sejarah monetisasi edtech online Indonesia buruk**: Zenius tutup, Ruangguru PHK massal 2022, CoLearn bergeser dari foto-soal ke bimbel live berlangganan. Pasar menghukum konten tak terdiferensiasi.
4. **Bukti keluhan orang tua masih lemah** (vignette media, bukan survei besar; n=30 dan n=10 pada proksi terdekat). Sebelum investasi besar: perlu riset validasi kecil (mis. 20–30 wawancara orang tua) untuk mengonfirmasi masalah atribusi dan WTP.
5. **Angka market size vendor saling konflik** (IMARC 11,79% vs 24,5% CAGR) — perlakukan sebagai order-of-magnitude.
6. **Keterbatasan teknis yang membatasi skala**: HP pinjaman, tanpa internet (privacy-by-default), satu anak per device — bagus untuk tesis, tetapi memperlambat akusisi massal; mode foto kertas (Fase 2 roadmap) adalah jalan keluar yang sudah direncanakan.
7. **K aktif sebagai metrik utama** belum tervalidasi untuk usia SD kelas 4 (distribusi B/K/H yang diketahui dari NEA adalah anak SMP+). Keputusan ini ditangguhkan sampai data v1 riil terkumpul (sudah dicatat sebagai risiko di peta jalan).
8. **PP 17/2025**: kepatuhan sekarang preventif, belum teruji hukum untuk operator individu skala kecil.

---

## Bagian 4 — Kesimpulan & Rekomendasi

### Kebutuhan pasar: **TERBUKTI**
Skala masalah terukur secara nasional (AKM sensus + PISA), gap kompetitif struktural (dibuktikan bahkan oleh ALEKS dan copy pemasaran Sparks Math), landasan teoretis 50 tahun, dan tailwind kebijakan (mandat asesmen diagnostik tanpa instrumen). Tidak ada pertanyaan "apakah ada kebutuhan" — pertanyaannya hanya "apakah produknya bekerja dan bisa dijual".

### Potensi pasar: **NYATA, dengan syarat**
- Sebagai **baji sempit**: jelas ada (order Rp miliaran/tahun bahkan dari 1% satu angkatan; band harga offline sudah membuktikan WTP).
- **Syarat 1 — tesis teknis terbukti**: seluruh potensi bergantung pada spike (tinta → B/K/H, ≥7/10 kecocokan, nol false-K). Kalau gagal, produk turun jadi app latihan biasa tanpa diferensiasi.
- **Syarat 2 — nilai di remediasi, bukan diagnosis**: sesuai PRD §1 (resep pra-tulis + AI-generate, loop verifikasi 3 hari, eskalasi), bukan sekadar laporan.
- **Syarat 3 — bukti lokal**: kumpulkan data B/K/H anak Indonesia sejak v1; taksonomi impor tidak valid.
- **Syarat 4 — harga & posisi di band offline-diagnostik**, bukan band konten-online.

### Rekomendasi konkret
1. **Tetap jalankan spike 5–7 hari dulu** (tidak ada perubahan rencana) — ini gerbang kebutuhan-teknis yang menentukan segalanya.
2. **Paralel, tanpa menunggu spike selesai**: rancang studi bukti v1 (pre/post sederhana, satu anak, 3x/minggu) supaya begitu v1 stabil, sudah ada data yang bisa diterbitkan sebagai klaim diferensiasi.
3. **Sesudah spike lulus**: lakukan validasi pasar ringan (20–30 wawancara orang tua di Jabodetabek/Java urban) untuk mengonfirmasi masalah atribusi kausal + WTP sebelum menambah fitur apa pun — ini menutup titik terlemah riset (bukti keluhan orang tua).
4. **Arsitektur sejak awal mendukung jalur B2B**: skema data dan format laporan v1 (YAML/CSV, Mac) dirancang agar bisa diturunkan jadi laporan guru/sekolah — jalur yang paling mungkin membuka potensi penuh dan paling tahan terhadap risiko monetisasi B2C.

---

*Dokumen ini menyintesis `gap-pasar-edtech-matematika-sd/report.md` (18 item, 47+ sumber, 38 klaim terverifikasi 3-vote) plus pengecekan pasar terbaru. Angka market size vendor bersifat order-of-magnitude. Semua klaim kunci punya sumber di report.md — lihat bagian "Sources" per item untuk detail.*
