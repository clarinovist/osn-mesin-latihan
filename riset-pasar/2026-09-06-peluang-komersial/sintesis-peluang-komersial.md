# Sintesis Peluang Komersial Jagomat

Tanggal: 6 September 2026

Status: sintesis riset sebelum keputusan harga penetrasi. Pemetaan kompetitor,
risiko, dan batas produk tetap berlaku; rekomendasi harga/pilot tinggi di dalam
dokumen ini sudah digantikan oleh `keputusan-positioning-harga-validasi.md` dan
`GTM-tutor-first.md`. Dokumen ini bukan proyeksi penjualan, harga final,
pendapat hukum, atau klaim hasil belajar.

## Jawaban singkat

Jagomat masih punya ruang menghasilkan uang, tetapi bukan dengan menjadi “aplikasi soal OSN” atau “bimbel online” baru.

Ruang paling masuk akal adalah:

> alat kerja diagnosis dan tindak lanjut untuk tutor matematika SD/les mikro yang sudah punya murid, tetapi masih menyiapkan soal, membaca kesalahan, membuat remedial, dan menjelaskan progres secara manual.

Tutor tetap menjadi pengambil keputusan pedagogis. Jagomat menghemat persiapan, menstrukturkan review, menghasilkan latihan ulang, dan menyimpan pola per murid.

Urutan pasar yang direkomendasikan:

1. tutor mikro/enrichment/OSN SD sebagai beachhead;
2. orang tua yang sudah memiliki kebiasaan mendampingi sebagai segmen kedua;
3. sekolah ditunda sampai kontrol organisasi, bukti, privasi, dan entitlement siap.

Bukan sasaran awal:

- pemburu aplikasi latihan termurah;
- keluarga yang ingin anak belajar sepenuhnya mandiri;
- sekolah besar;
- calon pelanggan yang menuntut jaminan medali nasional;
- pengguna yang sebenarnya membutuhkan kelas live atau tutor manusia.

## 1. Mengapa perubahan terbaru penting secara bisnis

Perubahan terbaru menutup sebagian loop yang sebelumnya terputus:

- jawaban anak dikumpulkan sebelum koreksi;
- diagnosis otomatis tetap berupa usulan dan dapat dikoreksi guru;
- guru memilih kesalahan yang ingin dilatih ulang;
- remedial membuat variasi soal baru pada fokus terpilih;
- laporan mengutamakan pola lintas sesi dan tindakan, bukan skor semata;
- pendaftaran mandiri, akun anak, dan isolasi keluarga sudah tersedia.

Bukti kode dan test ada di `audit-produk.md`. Test target yang saya jalankan ulang menghasilkan `103 passed in 15.07s` untuk remedial, laporan, landing, dan latihan cepat.

Produksi juga benar-benar hidup: `/` mengembalikan 200, `/akun` tanpa kredensial 401, dan `/murid/` mengalihkan ke login. Label container menunjukkan revision `8b5909f`. Tujuh dari sembilan berkas permukaan yang diperiksa identik byte-per-byte dengan lokal. `database.py` dan `schema.py` produksi cocok dengan commit `adcb6a3`; versi lokal sedang berubah sebagai WIP sesi lain, jadi analisis kemampuan produksi tidak memakai WIP tersebut.

Namun siklus baru dalam `../../produk/Siklus Belajar Terpandu.md` belum menjadi produk utuh. Belum ada reducer `learning_cycle.py`, intervensi terstruktur, snapshot konfirmasi append-only, evaluasi tiga hari, checkpoint 28 hari, atau eskalasi. Payment dan entitlement juga belum ditemukan.

Konsekuensi komersialnya tegas:

- yang dapat dijual sekarang adalah alat bantu tutor/orang tua;
- yang belum boleh dijual adalah “pendamping adaptif yang otomatis menentukan langkah terbaik”;
- pembayaran pilot harus manual;
- laporan belum boleh disebut bukti penguasaan.

## 2. Peta arena kompetisi

### 2.1 Kelas live dan pembinaan olimpiade

Ruangguru sudah menjual program yang kuat secara layanan: diagnostic test, review konsep, past papers, simulasi, pengajar, Student Advisor, gamifikasi, dan laporan rutin orang tua.[9][10][13]

Paket Olimpiade 36 sesi tercantum promo Rp4.971.000 atau sekitar Rp138.083 per sesi.[9]

Paket OSN-K 2026 Matematika tercantum Rp1.449.000, tetapi jumlah sesinya tidak dijelaskan pada baris harga.[9]

CoLearn menjual kelas live Matematika SD mulai Rp90.000 per bulan untuk sekali seminggu dan Rp170.000 untuk dua kali seminggu, beserta latihan mingguan dan laporan WhatsApp orang tua.[5]

KPM memiliki kelas online/offline 90 menit dengan biaya seikhlasnya; nominal per sesi tidak dipublikasikan.[15]

Implikasi: Jagomat tidak akan menang bila dibandingkan sebagai kelas. Ia tidak punya guru live, jadwal, cohort, komunitas, atau brand distribusi setara.

### 2.2 Tutor privat

Penawaran publik yang ditemukan berkisar Rp60.000 per jam di profil Superprof dan Rp87.000 per sesi 90–120 menit pada Edufio.[16][17] Tutor dapat bertanya balik, melihat ekspresi anak, mengganti penjelasan saat itu juga, dan memberi motivasi—kemampuan yang belum dimiliki Jagomat.

Implikasi: jangan mengganti tutor. Masuk ke workflow tutor agar satu tutor dapat menyiapkan, memantau, dan menindaklanjuti lebih banyak murid secara konsisten.

### 2.3 Konten dan latihan mandiri murah

ALC menawarkan E-Course Matematika SD promo Rp70.000 untuk akses tiga bulan.[14]

LOPI mencantumkan kursus OSN Matematika SD Rp1.000.000 dengan 25 video.[18][19]

Buku kumpulan soal 320 halaman dijual Rp73.500 di Jawa pada saat ekstraksi.[11]

Beast Academy menyediakan lebih dari 1.000 pelajaran, 20.000 soal, video, buku digital, parent dashboard, dan laporan progres.[2]

Matific menawarkan aktivitas adaptif, gamifikasi, dashboard orang tua, laporan kekuatan/kelemahan, dan lokalisasi Bahasa Indonesia.[4]

Implikasi: “soal tidak habis” bukan moat. Konten murah, buku, dan platform global sudah sangat kuat. Jagomat harus dibayar karena keputusan setelah anak salah, bukan karena volume soal.

### 2.4 AI umum dan gratis

ChatGPT Study Mode tersedia pada paket Free dan membimbing pengguna melalui pertanyaan, hint, refleksi, knowledge checks, dan feedback personal.[7] Alat AI umum juga lebih fleksibel dan percakapannya lebih alami.

Implikasi: klaim “AI yang menjelaskan matematika” cepat menjadi komoditas. Jagomat perlu menang lewat workflow terstruktur, taxonomy lokal, kontrol tutor, histori lintas sesi, dan bukti tindak lanjut—bukan kualitas model.

### 2.5 Benchmark diagnosis

Eedi membuktikan bahwa produk berpusat pada miskonsepsi dapat dibangun dan dipakai. Situsnya memosisikan mesin diagnosis matematika dan penyelesaian miskonsepsi sebagai inti produk.[1] Namun bukti dampaknya tidak sederhana:

- evaluasi EEF lama tidak dapat memakai hasil GCSE karena gangguan pandemi; jangan menyebutnya bukti dampak positif atau negatif.[12]
- laporan RCT satu tahun yang ditemukan menunjukkan arah positif tetapi tidak signifikan secara statistik.[20]
- laporan longitudinal dua tahun menunjukkan efek yang lebih kuat setelah penggunaan berulang, tetapi terjadi pada konteks Year 7 di Inggris, bukan SD Indonesia.[21]

Implikasi: kategori diagnosis layak, tetapi dampak bergantung implementasi dan konsistensi. Bukti Eedi tidak dapat dipindahkan menjadi klaim hasil Jagomat.

## 3. White space yang nyata

White space Jagomat bukan “tidak ada pesaing”. Pesaing ada di seluruh sisi: konten, kelas, tutor, laporan, adaptive practice, dan AI.

White space yang lebih defensibel adalah persilangan lima hal:

1. matematika SD Bahasa Indonesia;
2. fondasi dan pola soal OSN-S/K/P, bukan bank soal umum;
3. diagnosis jenis kesalahan per jawaban—baca, konsep, hitung, tulis, menebak, atau materi baru;
4. manusia tetap mengoreksi keputusan;
5. hasil diagnosis langsung menjadi latihan ulang dan laporan per murid.

Pesaing lokal mempublikasikan diagnostic test dan laporan perkembangan, tetapi dari laman publik yang diperiksa belum dapat diverifikasi bahwa mereka membuka taxonomy jenis kesalahan serta memberi tutor kontrol remedial per pola. Ini adalah gap bukti publik, bukan bukti mutlak bahwa fitur mereka tidak ada.

Moat potensial hanya muncul bila Jagomat mengumpulkan dengan aman:

- malrule yang akurat pada variasi parameter;
- koreksi tutor terhadap usulan mesin;
- hubungan diagnosis → tindakan → probe baru;
- pola lintas sesi yang tidak dimiliki AI chat satu kali;
- bukti lokal bahwa workflow menghemat waktu atau memperbaiki keputusan tutor.

Tanpa penggunaan dan outcome nyata, taxonomy hanya fitur yang dapat ditiru.

## 4. Segmentasi dan pilihan beachhead

| Segmen | Kecocokan produk sekarang | Nilai yang mungkin dibayar | Hambatan | Putusan |
|---|---|---|---|---|
| Tutor mikro/enrichment/OSN | Tinggi | Hemat persiapan, review terstruktur, remedial, laporan orang tua | Harus review; onboarding; privasi beberapa keluarga | Masuk pertama |
| Orang tua yang sudah rutin mendampingi | Sedang | Mengetahui akar kesalahan dan tindak lanjut | Beban review, trust, disiplin anak, support | Uji sebagai pembanding |
| Sekolah | Rendah | Standardisasi diagnosis dan remedial | Role, roster, consent, procurement, SLA, provenance, bukti dampak | Tunda |
| Anak belajar mandiri | Rendah | Latihan dan feedback langsung | Produk sengaja membutuhkan orang dewasa; anak di bawah umur | Jangan targetkan |

Tutor mikro dipilih bukan karena terbukti punya WTP tertinggi. Belum ada transaksi Jagomat. Ia dipilih karena hipotesis akuisisi dan operasinya paling efisien:

- pembeli dan operator bisa orang yang sama;
- satu akun membawa beberapa murid;
- tutor mampu menilai usulan diagnosis;
- keputusan pembelian lebih pendek daripada sekolah;
- produk melengkapi jasa yang sudah dijual tutor.

## 5. Tiga model bisnis historis

Seluruh angka pada bagian ini adalah stress test lama, bukan harga uji aktif.
Harga dan urutan eksperimen terbaru ada di `GTM-tutor-first.md`.

Semua angka berikut adalah skenario, bukan harga final. Asumsi model: biaya payment 3%, nilai waktu manusia Rp36.000/jam, dan biaya tetap diuji pada Rp3 juta, Rp8 juta, serta Rp15 juta per bulan. CAC, pajak, refund, biaya pengembangan, dan retensi belum diketahui.

| Model | Harga uji tengah | Kontribusi asumsi | Break-even biaya tetap Rp3 jt | Risiko utama |
|---|---:|---:|---:|---|
| A. B2C software-only | Rp99.000/keluarga/bulan | Rp77.030 | 39 keluarga | Orang tua tidak mampu/mau review; kalah dengan CoLearn/gratis |
| B. B2C + review manusia terbatas | Rp299.000/keluarga/bulan | Rp217.030 | 14 keluarga | Waktu review meledak; berubah menjadi tutor murah |
| C. Tutor mikro, 15 murid | Rp599.000/tutor/bulan | Rp398.030 | 8 tutor | Onboarding/support, utilisasi kursi, churn terkonsentrasi |

Skenario lengkap dan sensitivitasnya ada di `ekonomi-red-team.md`.

### Rekomendasi aktif

Gunakan GTM tutor-first dan harga penetrasi terbaru:

1. retail keluarga Rp10.000/anak/bulan, pilot Rp30.000/3 bulan;
2. tutor 10 kursi Rp75.000/bulan, pilot Rp225.000/3 bulan;
3. 25 kursi Rp150.000/bulan dan 50 kursi Rp250.000/bulan baru dibuka setelah
   penggunaan nyata melampaui 10 kursi;
4. jalankan observasi 6–8 minggu dan lanjutkan sampai invoice kedua jatuh tempo;
5. WTP hanya terbukti dari pembayaran aktual dan invoice kedua.

## 6. Tantangan yang paling mungkin menggagalkan bisnis

### High — nilai produk belum selesai

Remedial sekarang masih soal baru pada fokus terpilih, belum intervensi berbeda yang mengajarkan ulang. Spesifikasi siklus justru benar: diagnosis → intervensi → penguatan → evaluasi berjeda → checkpoint. Jika produk berhenti pada diagnosis dan drill, pengguna bisa merasa mendapat laporan yang menarik tetapi tidak mendapat perubahan.

### High — klaim landing lebih maju dari mekanisme kode

Landing mengatakan anak “menuliskan caranya” lalu sistem menunjukkan letak salah. Kode `diagnosis.py:11-14` menjelaskan bahwa isi kotak Caraku tidak dinilai benar-salah; mesin terutama mencocokkan jawaban akhir terhadap malrule. Contoh landing seolah membaca langkah 5 + 8 secara semantik, sedangkan implementasi saat ini tidak melakukan itu secara umum.

Ini bukan sekadar copy issue. Bila pembeli berharap analisis tulisan/proses dan mendapat pencocokan pola jawaban, trust dapat rusak. Sebelum penjualan berbayar, copy perlu dibatasi menjadi “jawaban dan informasi yang diisi anak dipakai untuk memberi usulan diagnosis; guru meninjau hasilnya”.

### High — laporan belum memakai bukti terkonfirmasi

`direview` dapat terisi saat halaman dibuka; diagnosis mutable dan laporan memakai sesi selesai. Snapshot outcome append-only belum ada. Karena itu “bukti penguasaan”, evaluasi berjeda, dan retensi belum boleh menjadi klaim.

### High — privasi anak

UU PDP menempatkan data anak sebagai data pribadi spesifik dan mensyaratkan pemrosesan khusus dengan persetujuan orang tua/wali.[23] PP 17/2025 menambah kewajiban perlindungan untuk sistem yang dirancang atau mungkin digunakan anak, termasuk privasi tinggi secara baku dan penilaian dampak.[22]

Jagomat sudah punya isolasi keluarga, palang murid, dan kebijakan yang jujur.[6]

Namun foto tulisan anak dapat dikirim ke AI pihak ketiga, consent per upload belum granular, admin dapat mengakses semua keluarga, dan hard-delete/provenance belum sejalan dengan siklus baru.[6]

Ini cukup untuk pilot terlayani dengan guardrail kuat, belum cukup untuk klaim compliance atau penjualan sekolah.

### Medium — seasonality

OSN memberi tanggal pembelian yang konkret tetapi final nasional adalah ceruk, bukan TAM. Permintaan dapat menumpuk menjelang OSN-K/P lalu hilang. Retensi harus dipisah antara penggunaan OSN musiman, enrichment reguler, dan remediasi sekolah.

### Medium — support memakan margin

Reset sandi orang tua, aktivasi, billing, pertanyaan pedagogis, dan review masih manual. Waktu founder harus dicatat sebagai biaya. Margin spreadsheet tidak berarti jika setiap akun meminta bantuan satu-dua jam per bulan.

### Medium — tutor mungkin hanya memakai generator

Jika tutor mengabaikan diagnosis, remedial, dan laporan, Jagomat menjadi generator soal yang mudah diganti. Keberhasilan pilot harus diukur pada workflow inti, bukan jumlah soal atau login.

## 7. Paket pilot yang disarankan

### Posisi

> Jagomat membantu tutor matematika SD menyiapkan latihan bervariasi, meninjau usulan jenis kesalahan, memilih latihan ulang, dan menjelaskan pola perkembangan per murid.

### Isi

- 5 atau 15 profil murid;
- soal P3–P6 dari fondasi dan pola OSN-S/K/P;
- pengerjaan HP atau cetak;
- usulan diagnosis yang harus direview tutor;
- remedial berdasarkan fokus pilihan tutor;
- laporan per murid;
- onboarding satu kali;
- support terbatas dengan jam dan kanal jelas.

### Yang tidak termasuk

- kelas live;
- review oleh tim Jagomat;
- jaminan nilai/medali;
- soal eksplorasi nasional lengkap;
- keputusan belajar otomatis;
- evaluasi berjeda/checkpoint otomatis;
- billing otomatis;
- konsultasi WhatsApp tak terbatas.

### Copy outreach

> Saya sedang menguji Jagomat untuk tutor matematika SD yang mengelola beberapa murid. Alatnya membuat latihan bervariasi, memberi usulan apakah jawaban salah lebih dekat ke salah baca, konsep, atau hitung, lalu tutor tetap meninjau dan memilih latihan ulang. Ini bukan pengganti tutor dan belum diklaim meningkatkan nilai. Boleh 15 menit saya lihat cara Anda menyiapkan dan mengoreksi latihan sekarang? Jika cocok, kita uji enam minggu pada beberapa murid dengan persetujuan orang tua.

## 8. Eksperimen 6–8 minggu

### Minggu 1 — discovery

- Wawancarai 5 tutor mikro dan 5 orang tua aktif sebagai pembanding.
- Minta mereka menunjukkan workflow minggu lalu, bukan pendapat abstrak.
- Catat waktu persiapan/koreksi, alat yang dibayar, pertanyaan orang tua, dan siapa pemutus pembayaran.

### Minggu 2 — komitmen

- Tawarkan lima slot tutor.
- Minta deposit Rp100.000 yang dikreditkan ke invoice.
- Jangan menghitung “tertarik” sebagai WTP.

### Minggu 2–7 — pemakaian

Per tutor:

- minimal 3 murid aktif;
- minimal dua minggu pemakaian berulang;
- tutor membuat sesi tanpa founder;
- tutor meninjau diagnosis;
- tutor membuat remedial;
- tutor menggunakan atau membahas laporan;
- catat seluruh menit onboarding dan support;
- catat waktu persiapan sebelum/sesudah melalui diary mingguan singkat.

Jangan mengekspor jawaban atau identitas anak ke repo. Metrik operasional cukup agregat/pseudonim.

### Minggu 8 — invoice kedua

Keberhasilan sementara:

- minimal 3 dari 5 tutor mengaktifkan minimal 3 murid;
- minimal 3 dari 5 membayar invoice kedua;
- margin kontribusi aktual setelah seluruh waktu manusia minimal 50%;
- support bulan berikutnya maksimal dua jam per akun;
- tutor memakai diagnosis/remedial/laporan, bukan generator saja;
- tidak ada insiden privasi material.

Hentikan atau ubah arah bila:

- kurang dari 3 pembayaran/deposit setelah 20 penawaran relevan;
- penggunaan hanya terjadi saat founder mengingatkan;
- administrasi tutor tidak turun atau malah naik;
- mayoritas hanya memakai generator;
- median murid aktif kurang dari 40% kuota;
- tidak ada pembayaran invoice kedua;
- keberatan utama adalah fitur institusional atau intervensi yang memang belum ada.

## 9. Roadmap yang mengikuti bukti, bukan intuisi

### Opsi A — paling cepat menghasilkan uang

Jual pilot tutor mikro secara manual sekarang.

Trade-off: klaim harus sempit; support dan privasi dioperasikan ketat. Ini rekomendasi utama.

### Opsi B — nilai produk lebih kuat

Selesaikan lebih dulu fondasi siklus: konfirmasi append-only, reducer, intervensi pra-tulis, evaluasi berjeda, checkpoint, arsip non-destruktif, lalu uji B2C premium.

Trade-off: lebih defensibel, tetapi menunda bukti WTP.

### Opsi C — sekolah

Bangun tenant organisasi, role, roster, consent/retensi, audit trail, entitlement, ekspor/rekap kelas, SLA, dan bukti dampak sebelum menjual.

Trade-off: potensi kontrak lebih besar, tetapi sales cycle dan risiko jauh lebih besar. Bukan prioritas sekarang.

## 10. Keputusan yang saya sarankan

1. Jangan masuk perang konten atau harga murah.
2. Jangan memosisikan Jagomat sebagai pengganti tutor.
3. Pilih tutor mikro sebagai beachhead.
4. Jual efisiensi workflow dan kejelasan tindak lanjut, bukan “AI” atau jumlah soal.
5. Uji harga penetrasi melalui invoice manual: pilot tutor Rp225.000/3 bulan
   untuk maksimal 10 anak; retail keluarga Rp30.000/3 bulan.
6. Batasi pilot lima tutor, enam sampai delapan minggu.
7. Minta pembayaran nyata dan invoice kedua sebelum menambah fitur komersial.
8. Perbaiki mismatch klaim “membaca Caraku” sebelum meminta pembayaran.
9. Pertahankan batas produk: fondasi + pola OSN-S/K/P, bukan siap juara nasional.
10. Bila tutor tidak memakai diagnosis/remedial/laporan atau tidak membayar ulang, jangan memaksa bisnis; Jagomat masih dapat menjadi alat internal yang berguna.

## 11. Yang sudah dan belum terbukti

| Klaim | Status |
|---|---|
| Produk live dan permukaan utama merespons | Terverifikasi |
| Remedial pilihan guru dan laporan ada di kode/test | Terverifikasi |
| Payment/entitlement tersedia | Tidak ada |
| Siklus intervensi–evaluasi–checkpoint tersedia | Belum ada |
| Tutor mikro akan membayar | Hipotesis |
| Harga penetrasi retail/grosir diterima | Hipotesis eksperimen; ukur pembayaran dan invoice kedua |
| Diagnosis Jagomat meningkatkan hasil belajar | Belum terbukti |
| Jagomat patuh penuh UU PDP/PP TUNAS | Belum diaudit secara hukum |
| Pasar cukup besar untuk bisnis skala venture | Tidak diteliti dan tidak diperlukan untuk pilot |

## Dokumen pendukung

- `audit-produk.md` — bukti kemampuan kode dan batas klaim.
- `kompetitor-lokal.md` — harga, bentuk, dan unit penawaran lokal.
- `permintaan-risiko.md` — sinyal permintaan, bukti Eedi, dan privasi.
- `persona-channel.md` — persona, channel, pertanyaan wawancara, dan funnel.
- `ekonomi-red-team.md` — model unit economics, sensitivitas, dan kill criteria.
- `rencana-riset.md` — scope dan batas riset.

## Sources

[1] https://www.eedi.com — The intelligence that powers effective learning
[2] https://beastacademy.com/online/enroll — Enroll in Online Math Curriculum for Elementary Students | Beast Academy
[4] https://www.matific.com/id/id/home/parents — Matific | Aktivitas matematika berbasis permainan yang memenangkan penghargaan. Dirancang oleh Para Ahli Matematika.
[5] https://colearn.id — Aplikasi belajar online, bantu kamu belajar dari mana aja - CoLearn
[6] https://osn.lesprivate.id — Jagomat
[7] https://openai.com/index/chatgpt-study-mode — Introducing study mode | OpenAI
[9] https://www.ruangguru.com/blog/informasi-produk-ruangguru-yang-jadi-unggulan — Info Produk & Harga Paket Ruangguru SD, SMP, SMA, SMK TA 2025/2026
[10] https://www.ruangguru.com/mathchamps — Kursus Matematika & Logika Kurikulum Singapore Math by Ruangguru
[11] https://yrama-widya.co.id/shop/kategori/buku-sekolah/pelajaran-sd-mi/pelengkap-pelajaran/olimpiade-sains/buku-kumpulan-soal-pembahasan-olimpiade-matematika-sd-jilid-2 — Kumpulan Soal & Pembahasan Olimpiade Matematika SD Jilid 2 - Yrama Widya Official
[12] https://educationendowmentfoundation.org.uk/projects-and-evaluation/projects/diagnostic-questions — Eedi | EEF
[13] https://www.ruangguru.com/olympiad-academy — Ruangguru Olympiad Academy | Kelas Persiapan Olimpiade
[14] https://alcindonesia.co.id/package/list — ALC Indonesia — Daftar Paket Belajar
[15] https://www.read1kpmseikhlasnya.com/program — KPM — Daftar Program
[16] https://www.superprof.co.id/guru-tentor-privat-olimpiade-matematika-atau-persiapan-osn-olimpiade-sains-nasional-dan-kompetisi-sains-madrasah-ksm.html — Superprof — Tutor Olimpiade Matematika SD
[17] https://edufio.com/bimbel-olimpiade-jogja — Edufio — Les Privat Olimpiade OSN
[18] https://siplah.lopi.co.id/courses — LOPI — Daftar Kelas
[19] https://siplah.lopi.co.id/course-view/ksn-p-matematika-sd — LOPI — Pelatihan OSN Matematika SD
[20] https://cdn.prod.website-files.com/68b00fd42843f377c633738c/6a394544536154d2e1b6b3fd_WWEd_Eedi_STAR_2024-25.pdf — Eedi STAR 2024–25 Evaluation Report
[21] https://cdn.prod.website-files.com/68b00fd42843f377c633738c/6a3943a429b2a2ecd92f92dc_Eedi_NWEA_Longitudinal_Final_2026.pdf — Eedi NWEA Longitudinal Final 2026
[22] https://jdih.komdigi.go.id/produk_hukum/view/id/965/t/peraturan+pemerintah+nomor+17+tahun+2025 — PP Nomor 17 Tahun 2025
[23] https://jdih.komdigi.go.id/produk_hukum/view/id/832/t/undangundang+nomor+27+tahun+2022 — UU Nomor 27 Tahun 2022 tentang PDP
