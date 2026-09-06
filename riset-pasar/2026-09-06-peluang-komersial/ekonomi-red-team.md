# Ekonomi dan Red-Team Monetisasi Jagomat

**Tanggal:** 6 September 2026
**Status:** model eksplorasi sebelum keputusan harga penetrasi, **bukan prediksi**,
bukan harga aktif, dan bukan bukti bahwa pasar akan membeli. Angka Rp99–999 ribu
di bawah dipertahankan sebagai stress test historis, bukan penawaran Jagomat.
Keputusan aktif ada di `keputusan-positioning-harga-validasi.md` dan
`GTM-tutor-first.md`: retail Rp10.000/anak/bulan, grosir tutor mulai 10 kursi,
dan floor Rp5.000/anak pada 50 kursi.
**Lingkup:** tiga jalur yang pernah diuji secara konseptual: (A) B2C
software-only, (B) diagnosis dengan review manusia/premium, dan (C) B2B tutor
mikro. Tidak membaca data anak, database, akun, atau secret.

## 1. Ringkasan historis

Angka pada bagian ini adalah model eksplorasi sebelum keputusan harga
penetrasi. Ia dipertahankan untuk menunjukkan sensitivitas biaya, bukan untuk
menentukan penawaran aktif. GTM aktif menguji retail Rp10.000/anak/bulan dan
paket tutor 10/25/50 kursi.

1. **Belum ada dasar memilih pemenang.** Pilot gratis belum berisi data pemakaian, konversi bayar, WTP, CAC, waktu support, atau biaya review aktual. Semua angka di dokumen ini adalah asumsi yang sengaja dibuat terlihat.
2. **A paling mudah dijalankan tetapi paling mudah dikomoditisasi.** Pada harga Rp99 ribu/bulan dan biaya variabel asumsi Rp19 ribu/keluarga, kontribusinya Rp77.030 (margin kontribusi 77,8%). Ia perlu 39 pelanggan aktif untuk menutup biaya tetap Rp3 juta/bulan—sebelum CAC dan pajak.
3. **B membeli diferensiasi dengan tenaga manusia.** Pada Rp299 ribu/bulan dan biaya variabel asumsi Rp73 ribu/keluarga, kontribusinya Rp217.030 (72,6%). Ia perlu 14 pelanggan aktif untuk menutup Rp3 juta/bulan. Namun margin cepat jatuh bila review melewati jatah waktu.
4. **C paling dekat dengan kemampuan produk dan pembeli profesional, tetapi bukan SaaS sekolah.** Pada paket 15 murid Rp599 ribu/bulan, kontribusinya Rp398.030 (66,4%), sehingga perlu 8 tutor aktif untuk menutup Rp3 juta/bulan. Risiko utamanya onboarding, kebiasaan kerja tutor, churn setelah musim lomba, dan support per akun.
5. **Urutan pengujian yang paling informatif:** monetisasi cohort gratis yang sudah ada → uji B dalam cohort terbatas → uji C pada tutor mikro → uji A hanya bila orang tua terbukti mampu menjalankan review sendiri. Ini urutan eksperimen, bukan rekomendasi fitur.
6. **Kriteria berhenti harus keras:** hentikan jalur yang tidak menghasilkan deposit/transaksi, pemakaian berulang, margin positif setelah waktu manusia dicatat, atau retensi menuju bulan kedua. Jangan menutupi kegagalan WTP dengan menambah fitur.

## 2. Batas produk yang memengaruhi ekonomi

Kode lokal mendukung generator P3–P6, pengumpulan jawaban, diagnosis sebagai **usulan**, koreksi manusia, remedial yang dipilih guru/orang tua, akun anak, serta laporan pola latihan. Audit produk menyimpulkan ini cukup untuk pilot berbayar orang tua atau tutor kecil.[1]

Yang **belum ada**: payment/entitlement, review manusia sebagai layanan operasional, snapshot konfirmasi append-only, reducer siklus belajar, intervensi terarah, evaluasi berjeda, checkpoint, role institusi, dan SaaS sekolah.[1][2] Karena itu:

- penagihan dan aktivasi harus manual selama eksperimen;
- diagnosis/laporan tidak boleh dijual sebagai bukti penguasaan;
- B harus mendefinisikan review manusia secara operasional, bukan mengaku bahwa fitur produk sudah menyediakannya;
- C adalah lisensi untuk tutor kecil yang mengelola muridnya sendiri, **bukan** penawaran sekolah;
- seluruh opsi hanya boleh mengklaim “fondasi dan pola soal OSN-S/K/P”, bukan “siap juara nasional”.

## 3. Rumus dan asumsi bersama

### 3.1 Rumus

```text
pendapatan bersih setelah payment = harga × (1 − 3%)
biaya variabel = infra per unit + support per unit + review manusia per unit
kontribusi per unit = pendapatan bersih − biaya variabel
margin kontribusi = kontribusi ÷ harga
unit break-even = pembulatan ke atas (biaya tetap bulanan ÷ kontribusi per unit)
CAC maksimum untuk payback 3 bulan = kontribusi bulanan × 3
```

“Gross margin” dalam dokumen ini dipakai sebagai **margin kontribusi setelah payment, infra, support, dan review manusia yang dapat diatribusikan ke unit**. Angka ini belum dikurangi biaya tetap, CAC, pajak, refund, bad debt, diskon, atau biaya pengembangan.

### 3.2 Asumsi bersama

| Asumsi | Nilai model | Alasan / batas |
|---|---:|---|
| Biaya payment | 3% omzet | Sesuai permintaan model; penyedia nyata belum dipilih. Transfer manual bisa lebih murah tetapi menambah rekonsiliasi. |
| Nilai waktu support/reviewer | Rp36.000/jam | Placeholder untuk menghargai waktu manusia; **bukan tarif upah yang sudah diverifikasi**. |
| Biaya tetap bulanan — lean | Rp3 juta | Overhead, pemeliharaan konten/kode, administrasi, dan founder draw sangat terbatas; bukan biaya aktual. |
| Biaya tetap bulanan — operasi kecil | Rp8 juta | Menghargai operasi/pemeliharaan lebih realistis; bukan rencana perekrutan. |
| Biaya tetap bulanan — tim kecil | Rp15 juta | Stress test, bukan target biaya. |
| CAC | Belum diketahui | Dikeluarkan dari break-even utama dan diuji terpisah lewat batas payback. |
| Retensi | Belum diketahui | Tidak ada proyeksi LTV. Musim OSN dapat membuat umur bayar hanya 2–4 bulan. |
| Pajak/refund | Belum diketahui | Tidak dimasukkan. Margin riil akan lebih rendah. |
| Biaya pengembangan tertanam | Tidak dimasukkan | Model menilai operasi bulanan, bukan pengembalian investasi masa lalu. |

**Makna tiga biaya tetap:** break-even Rp3 juta adalah ambang bertahan sangat lean, bukan bukti bisnis sehat. Untuk bisnis yang menggaji kerja founder dan menyediakan kontinuitas layanan, angka Rp8 juta lebih berguna sebagai stress test awal.

## 4. Opsi A — B2C software-only

### 4.1 Penawaran yang dimodelkan

Akses per keluarga untuk generator, pengumpulan jawaban, usulan diagnosis, koreksi oleh orang tua, remedial pilihan orang tua, dan laporan sederhana. Tidak ada review diagnosis oleh tim Jagomat.

**Asumsi biaya variabel per keluarga/bulan:**

- infra/penyimpanan/AI placeholder: **Rp7.000**;
- support: **20 menit × Rp36.000/jam = Rp12.000**;
- review manusia: **Rp0**;
- total sebelum payment: **Rp19.000**.

Support 20 menit bukan observasi aktual. Reset sandi masih melalui pengelola dan produk belum punya entitlement, sehingga support awal bisa lebih tinggi.[1]

### 4.2 Ekonomi per tingkat harga

| Harga/bulan | Payment 3% | Infra + support | Kontribusi/unit | Margin kontribusi | Break-even Rp3 jt | Break-even Rp8 jt | Break-even Rp15 jt | CAC maks. payback 3 bln |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Rp49.000 | Rp1.470 | Rp19.000 | Rp28.530 | 58,2% | 106 keluarga | 281 | 526 | Rp85.590 |
| **Rp99.000** | Rp2.970 | Rp19.000 | **Rp77.030** | **77,8%** | **39 keluarga** | **104** | **195** | **Rp231.090** |
| Rp149.000 | Rp4.470 | Rp19.000 | Rp125.530 | 84,2% | 24 keluarga | 64 | 120 | Rp376.590 |

### 4.3 Sensitivitas harga Rp99 ribu

| Infra/keluarga | Waktu support | Biaya support | Kontribusi | Margin | Unit untuk Rp3 jt |
|---:|---:|---:|---:|---:|---:|
| Rp5.000 | 20 menit | Rp12.000 | Rp79.030 | 79,8% | 38 |
| Rp15.000 | 1 jam | Rp36.000 | Rp45.030 | 45,5% | 67 |
| Rp30.000 | 2 jam | Rp72.000 | **−Rp5.970** | **−6,0%** | Tidak tercapai |

### 4.4 Kekuatan dan kegagalan yang mungkin

- **Kekuatan:** biaya review nol; pembelian dan pembatalan bisa cepat; harga masih di bawah bimbel live dan privat lokal.[3]
- **Kegagalan utama:** orang tua harus menilai diagnosis dan menjalankan remedial. Jika mereka membayar justru untuk mengurangi beban mental, software-only memindahkan pekerjaan kepada pembeli.
- **Churn:** sangat tinggi bila dipakai hanya menjelang OSN/ujian, anak kehilangan minat, atau laporan tidak mengubah tindakan orang tua.
- **Support:** volume pelanggan besar membuat reset sandi/manual billing dan pertanyaan pedagogis menjadi mahal.
- **Posisi harga:** Rp49 ribu mudah dibandingkan dengan video/alat gratis; Rp149 ribu menuntut pembuktian nilai yang belum ada. Anchor produk digital lokal bahkan turun ke sekitar Rp23 ribu/bulan akses video.[3]

**Hipotesis yang diuji, bukan klaim:** keluarga akan membayar karena Jagomat mengurangi kebingungan “anak salah di mana”, dan cukup percaya diri melakukan review sendiri.

## 5. Opsi B — diagnosis + review manusia/premium

### 5.1 Penawaran yang dimodelkan

Paket keluarga yang sama dengan A, ditambah review manusia terbatas terhadap hasil diagnosis/laporan. Review bukan les privat dan bukan janji hasil belajar. Paket harus membatasi jatah agar biaya tidak tak terbatas.

**Asumsi biaya variabel per keluarga/bulan:**

- infra: **Rp8.000**;
- support/admin: **25 menit × Rp36.000/jam = Rp15.000**;
- review manusia: **Rp50.000** (contoh: dua review terjadwal × 30–40 menit total pada nilai waktu model);
- total sebelum payment: **Rp73.000**.

Angka Rp50 ribu adalah envelope biaya, bukan bukti durasi nyata. Bila review berubah menjadi konsultasi WhatsApp tak terbatas, model ini tidak berlaku.

### 5.2 Ekonomi per tingkat harga

| Harga/bulan | Payment 3% | Infra + support + review | Kontribusi/unit | Margin kontribusi | Break-even Rp3 jt | Break-even Rp8 jt | Break-even Rp15 jt | CAC maks. payback 3 bln |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Rp199.000 | Rp5.970 | Rp73.000 | Rp120.030 | 60,3% | 25 keluarga | 67 | 125 | Rp360.090 |
| **Rp299.000** | Rp8.970 | Rp73.000 | **Rp217.030** | **72,6%** | **14 keluarga** | **37** | **70** | **Rp651.090** |
| Rp399.000 | Rp11.970 | Rp73.000 | Rp314.030 | 78,7% | 10 keluarga | 26 | 48 | Rp942.090 |

### 5.3 Sensitivitas harga Rp299 ribu

Biaya dasar infra + support diasumsikan Rp28 ribu; yang diubah hanya biaya review.

| Biaya review/keluarga | Kontribusi | Margin | Unit untuk Rp3 jt | Interpretasi |
|---:|---:|---:|---:|---|
| Rp45.000 | Rp217.030 | 72,6% | 14 | Review singkat dan terstruktur |
| Rp90.000 | Rp172.030 | 57,5% | 18 | Waktu review kira-kira dua kali lipat |
| Rp150.000 | Rp112.030 | 37,5% | 27 | Mulai menyerupai jasa, bukan software |
| Rp240.000 | Rp22.030 | 7,4% | 137 | Secara ekonomi hampir tidak layak |

### 5.4 Kekuatan dan kegagalan yang mungkin

- **Kekuatan:** review manusia menutup gap kepercayaan diagnosis dan mengurangi tuntutan kompetensi orang tua; harga masih di bawah banyak kelas bulanan/offline dan jauh di bawah paket intensif.[3][4]
- **Kegagalan utama:** pelanggan memperlakukan paket sebagai tutor pribadi murah; pertanyaan tidak terjadwal dan review bukti anak menghabiskan waktu.
- **Churn:** dapat lebih rendah dari A bila hubungan reviewer dipercaya, tetapi churn melonjak jika reviewer lambat, berganti-ganti, atau laporan terasa generik.
- **Support/review:** kapasitas adalah bottleneck. Pada 30 pelanggan dan biaya review Rp50 ribu, envelope review hanya Rp1,5 juta/bulan; waktu nyata wajib dicatat agar margin tidak fiktif.
- **Privasi:** manusia tambahan mengakses materi anak. Persetujuan, minimisasi data, retensi, kewenangan akses, dan batas komunikasi harus lebih jelas. Kebijakan saat ini transparan tetapi gerbang consent unggahan belum granular.[1]

**Hipotesis yang diuji:** trust dan tindakan konkret dari review manusia menaikkan konversi/retensi cukup besar untuk membayar tambahan biaya manusia.

## 6. Opsi C — B2B tutor mikro

### 6.1 Penawaran yang dimodelkan

Lisensi bulanan untuk tutor independen atau lembaga les mikro, dengan kuota profil murid. Tutor tetap menjadi reviewer dan pengambil keputusan pedagogis. Jagomat menjual penghematan persiapan soal, dokumentasi diagnosis, remedial per murid, dan laporan; bukan mengganti tutor.

Ini cocok dengan kemampuan produk yang sudah bisa mengelola beberapa murid per akun, tetapi penagihan, onboarding, dan operasional tetap manual.[1] Model ini tidak diasumsikan siap sekolah atau multi-cabang.

**Asumsi biaya variabel per akun tutor/bulan:**

| Paket | Kuota murid | Infra (Rp5rb/murid) | Support + onboarding teramortisasi | Total biaya variabel sebelum payment |
|---|---:|---:|---:|---:|
| Mikro 5 | 5 | Rp25.000 | Rp72.000 (2 jam) | Rp97.000 |
| Studio 15 | 15 | Rp75.000 | Rp108.000 (3 jam) | Rp183.000 |
| Kelas 30 | 30 | Rp150.000 | Rp144.000 (4 jam) | Rp294.000 |

Review diagnosis murid dilakukan tutor, bukan tim Jagomat. Nilai waktu support tetap Rp36 ribu/jam. Asumsi infra linear per murid bersifat konservatif dan belum diukur.

### 6.2 Ekonomi per tingkat paket

| Paket | Harga/bulan | Payment 3% | Biaya variabel | Kontribusi/akun | Margin | Break-even Rp3 jt | Break-even Rp8 jt | Break-even Rp15 jt | CAC maks. payback 3 bln |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Mikro 5 | Rp299.000 | Rp8.970 | Rp97.000 | Rp193.030 | 64,6% | 16 tutor | 42 | 78 | Rp579.090 |
| **Studio 15** | **Rp599.000** | Rp17.970 | Rp183.000 | **Rp398.030** | **66,4%** | **8 tutor** | **21** | **38** | **Rp1.194.090** |
| Kelas 30 | Rp999.000 | Rp29.970 | Rp294.000 | Rp675.030 | 67,6% | 5 tutor | 12 | 23 | Rp2.025.090 |

Harga efektif paket adalah sekitar Rp59.800, Rp39.933, dan Rp33.300 per kursi murid/bulan bila kuota penuh. **Kursi kosong tidak menurunkan invoice tetapi dapat menurunkan persepsi nilai dan memicu downgrade/churn.**

### 6.3 Sensitivitas utilisasi paket Studio 15

| Murid aktif | Harga efektif per murid | Implikasi |
|---:|---:|---|
| 15 | Rp39.933 | Nilai per kursi paling mudah dijelaskan |
| 10 | Rp59.900 | Masih mungkin jika menghemat waktu tutor secara nyata |
| 5 | Rp119.800 | Tutor kemungkinan memilih paket lebih kecil atau berhenti |

Break-even akunnya tidak berubah selama biaya paket dan support tetap; tetapi utilisasi rendah merusak retensi. Karena itu “akun dibayar” tidak cukup—jumlah murid aktif dan frekuensi sesi perlu diukur secara agregat tanpa mengakses isi data anak.

### 6.4 Kekuatan dan kegagalan yang mungkin

- **Kekuatan:** tutor sudah punya kompetensi review, rutinitas mengajar, dan kumpulan murid; Jagomat dapat menjadi alat kerja, bukan pengganti guru.
- **Kegagalan utama:** alur input/review lebih lambat daripada kertas/WhatsApp/Excel; tutor tidak melihat penghematan waktu atau tidak dapat menaikkan harga jasa.
- **Churn:** bergantung kalender penerimaan murid dan lomba; satu tutor hilang bernilai lebih besar daripada satu keluarga B2C.
- **Support:** onboarding dan migrasi kebiasaan mendominasi. Akun kecil bisa meminta support seperti institusi dengan ARPU kecil.
- **Sales cycle:** lebih lama dari B2C karena perlu demo, uji dengan beberapa murid, pembuktian penghematan waktu, dan keputusan pemilik; tetapi lebih pendek daripada sekolah formal.
- **Privasi:** tutor mengelola data beberapa keluarga. Harus jelas siapa pengendali data, siapa boleh melihat laporan, dan bagaimana persetujuan orang tua diberikan. Model admin global saat ini terlalu lebar untuk institusi besar.[1]

**Hipotesis yang diuji:** tutor membayar dari efisiensi kerja/retensi klien, bukan karena “AI diagnosis” terdengar menarik.

## 7. Perbandingan tiga opsi

| Dimensi | A — B2C software-only | B — review premium | C — tutor mikro |
|---|---|---|---|
| Pembayar | Orang tua | Orang tua | Tutor/pemilik les kecil |
| Pengguna review | Orang tua | Tim Jagomat + orang tua | Tutor |
| Harga model tengah | Rp99rb/bln | Rp299rb/bln | Rp599rb/bln/15 murid |
| Margin asumsi tengah | 77,8% | 72,6% | 66,4% |
| Unit untuk biaya tetap Rp3 jt | 39 keluarga | 14 keluarga | 8 tutor |
| CAC/payback risk | Tinggi: tiket kecil | Sedang: tiket cukup | Sedang: tiket lebih besar, sales lebih berat |
| Churn | **Tertinggi** | Sedang | Sedang; terkonsentrasi per akun |
| Sensitivitas waktu manusia | Support | **Review sangat sensitif** | Onboarding/support |
| Musiman OSN | Tinggi | Tinggi | Tinggi, tetapi tutor mungkin punya latihan reguler |
| Risiko privasi | Sedang | **Tinggi** karena reviewer tambahan | **Tinggi** karena banyak keluarga/akun |
| Sales cycle | Hari | Hari–minggu | Minggu–bulan |
| Kesesuaian produk sekarang | Bisa pilot manual | Bisa pilot sangat terbatas | Bisa pilot tutor kecil |
| Risiko commoditization | **Tertinggi** | Sedang | Lebih rendah bila masuk workflow tutor |
| Risiko operasional | Volume support | Kapasitas reviewer | Onboarding dan account support |

**Catatan penting:** margin tengah C lebih rendah dari A, tetapi kebutuhan unit break-even lebih kecil. Itu bukan otomatis lebih baik: delapan tutor mungkin jauh lebih sulit diperoleh daripada 39 keluarga, dan churn satu tutor membawa beberapa murid sekaligus.

## 8. Sensitivitas CAC, retensi, dan musim

### 8.1 Batas CAC dari kontribusi, bukan dari omzet

| Opsi tengah | Kontribusi/bln | CAC maks. payback 1 bln | 3 bln | 6 bln |
|---|---:|---:|---:|---:|
| A Rp99rb | Rp77.030 | Rp77.030 | Rp231.090 | Rp462.180 |
| B Rp299rb | Rp217.030 | Rp217.030 | Rp651.090 | Rp1.302.180 |
| C Rp599rb | Rp398.030 | Rp398.030 | Rp1.194.090 | Rp2.388.180 |

Ini **batas matematis**, bukan anggaran iklan yang disarankan. Jika umur bayar aktual hanya tiga bulan karena musim OSN, CAC tiga-bulan menghabiskan seluruh kontribusi dan menyisakan nol untuk biaya tetap. Agar ada ruang untuk biaya tetap, target CAC riil harus jauh di bawah angka tersebut.

### 8.2 Kontribusi umur pelanggan sebelum CAC

| Opsi tengah | Jika bertahan 2 bln | 4 bln | 8 bln |
|---|---:|---:|---:|
| A | Rp154.060 | Rp308.120 | Rp616.240 |
| B | Rp434.060 | Rp868.120 | Rp1.736.240 |
| C | Rp796.060 | Rp1.592.120 | Rp3.184.240 |

Belum ada data untuk memilih horizon mana pun. Jangan memakai “12 bulan” sebagai default: latihan OSN bersifat musiman, anak naik level, dan pembeli bisa berhenti segera setelah seleksi.

### 8.3 Risiko musim

- Permintaan bisa terkonsentrasi 2–4 bulan sebelum OSN-K/P atau kompetisi tertentu.
- Pendapatan bulanan rata-rata tahunan dapat terlihat sehat di musim puncak tetapi tidak menutup pemeliharaan sepanjang tahun.
- Diskon tahunan dapat mengunci kas tetapi juga memperbesar refund/ekspektasi layanan dan menyembunyikan churn produk.
- Eksperimen harus melaporkan cohort berdasarkan tanggal masuk dan alasan membeli: OSN musiman, latihan reguler, remediasi, atau pelengkap les.

## 9. Red-team: mengapa alternatif mengalahkan Jagomat

| Alternatif | Mengapa bisa menang | Di mana Jagomat kalah sekarang | Bukti yang diperlukan agar Jagomat layak dibayar |
|---|---|---|---|
| **Gratis**: soal sekolah, YouTube, Roboguru, materi komunitas | Harga nol, sudah dikenal, tidak perlu onboarding atau review diagnosis | Jagomat meminta waktu orang tua dan membawa kategori baru yang belum terbukti mengubah hasil | Transaksi nyata dan bukti bahwa laporan menghasilkan tindakan berulang, bukan sekadar “menarik” |
| **CoLearn / kelas live** | Ada guru manusia, jadwal, cohort, latihan mingguan, laporan, dan brand; harga riset sekitar Rp90–170rb/bulan untuk paket live tertentu[4] | A Rp99rb berdekatan dengan harga live namun tidak menyertakan guru; B lebih mahal dan belum menjadi kelas | Keluarga memilih Jagomat setelah membandingkan langsung, bukan hanya dalam survei hipotetis |
| **Buku/bank soal** | Sekali beli, familiar, tanpa akun/data, bisa dicoret, mudah dipakai tutor; resale/share mungkin | Generator “soal tak habis” tidak penting bila keluarga hanya butuh 20 soal bermutu dan pembahasan | Frekuensi penggunaan ulang dan penghematan waktu persiapan/koreksi yang terukur |
| **ChatGPT/AI umum** | Gratis/murah, fleksibel, bisa menjelaskan foto/teks seketika, percakapan natural | Jagomat lebih sempit, membutuhkan input terstruktur, dan intervensi lengkap belum ada | Kepercayaan lebih tinggi, diagnosis lebih konsisten, jejak progres lebih berguna, serta risiko jawaban ngawur lebih rendah—diukur, bukan diklaim |
| **Tutor privat** | Melihat ekspresi/langkah anak, bertanya balik, memotivasi, menyesuaikan penjelasan, dan bertanggung jawab pada proses | Diagnosis otomatis Jagomat masih usulan; remedial sekarang masih soal ulang, belum intervensi penuh[1] | B harus meningkatkan kualitas/kecepatan keputusan manusia, atau C harus menghemat waktu tutor tanpa menurunkan kualitas |
| **KPM/seikhlasnya atau komunitas** | Trust, komunitas, guru, dan harga fleksibel; sulit dikalahkan lewat diskon[3] | Jagomat tidak memiliki komunitas, reputasi hasil, atau mentor | Referral/retensi dari pembeli nyata, bukan hanya keunikan teknologi |
| **Ruangguru MathChamps/Olympiad Academy** | Brand besar, diagnostic test, past papers, simulasi, advisor, dan laporan orang tua[3] | Jagomat belum punya layanan terpandu lengkap dan tidak boleh mengklaim siap nasional | Menang pada segmen sangat spesifik: tutor/orang tua yang ingin workflow diagnosis dan kontrol sendiri |

### Serangan terhadap tesis inti

1. **“Jenis kesalahan” mungkin menarik, tetapi bukan pekerjaan yang dibayar.** Orang tua membeli disiplin, jadwal, guru, dan ketenangan—bukan taksonomi B/K/H/E/T/N.
2. **Diagnosis tanpa intervensi kuat adalah laporan yang cantik tetapi mati.** Riset internal sendiri mencatat diagnosis/remediasi berbasis model belum otomatis lebih baik daripada mengajar ulang.[5]
3. **Orang tua bukan reviewer yang reliabel.** Jika mereka tidak bisa membedakan salah konsep vs salah hitung, opsi A kehilangan fondasi operasionalnya.
4. **Tutor tidak ingin alat tambahan.** Produk baru menambah login, input, dan administrasi; spreadsheet/kertas mungkin cukup.
5. **Keunikan tidak sama dengan moat.** Pesaing besar atau AI umum dapat meniru label diagnosis. Moat baru muncul bila workflow dipakai berulang dan menghasilkan bukti lokal berkualitas—yang belum ada.
6. **Pasar OSN kecil dan episodik.** Fondasi P3–P6 lebih luas, tetapi positioning terlalu OSN dapat menyempitkan demand; positioning terlalu umum menghilangkan diferensiasi.
7. **Harga premium belum memiliki bukti hasil.** Anchor bimbel offline tidak otomatis memindahkan WTP ke software. Harga publik pesaing adalah penawaran, bukan transaksi Jagomat.
8. **Privasi bisa menjadi rem, bukan nilai.** Penyimpanan data anak, foto, akses admin, dan review pihak lain menambah kekhawatiran. Klaim “privasi-by-default” lama juga tidak boleh diulang seolah seluruh data hanya di rumah; produk sekarang adalah web dan kebijakan menyebut AI pihak ketiga untuk unggahan tertentu.[1]
9. **Support dapat memakan margin.** Tanpa entitlement/self-service reset, tiap pelanggan membentuk pekerjaan manual. Gross margin spreadsheet bisa semu bila waktu founder diberi nilai nol.
10. **Pilot gratis bias.** Pengguna gratis lebih toleran, founder lebih banyak membantu, dan jawaban “mau bayar” tidak sama dengan pembayaran berhasil.

## 10. Kriteria berhenti

Kriteria ini dinilai per jalur. **Deposit atau pembayaran aktual lebih kuat daripada jawaban survei.** Setiap eksperimen harus membatasi cohort, waktu, dan jumlah interaksi agar kegagalan tidak berubah menjadi support tak terbatas.

### 10.1 Kill criteria lintas opsi

Hentikan monetisasi aktif dan kembali ke riset masalah—tanpa menambah fitur—jika salah satu terjadi:

1. Setelah **20 penawaran eksplisit** kepada calon yang sesuai, kurang dari **3 orang/akun membayar atau memberi deposit non-token**.
2. Dari minimal **10 pembeli**, kurang dari **60% mengaktifkan dan menjalankan satu sesi bernilai dalam 7 hari**.
3. Kurang dari **50% pembeli aktif bulan pertama memperpanjang ke bulan kedua**, setelah mengecualikan kegagalan teknis berat yang terdokumentasi.
4. Margin kontribusi aktual, setelah mencatat seluruh menit support/review, **<50% selama dua cohort berturut-turut** pada harga yang diuji.
5. Median payback CAC terukur **>3 bulan** sementara median retensi bayar belum terbukti lebih dari 4 bulan.
6. Lebih dari **10% pembeli meminta refund/berhenti karena tidak percaya diagnosis atau khawatir privasi**, atau ada satu insiden privasi material; hentikan akuisisi sampai akar masalah ditutup.
7. Pemakaian naik hanya saat founder mengingatkan secara manual dan turun tanpa reminder; ini tanda jasa founder, bukan produk.

### 10.2 Kill criteria A

Hentikan A bila, pada minimal 10 keluarga berbayar:

- <50% menyelesaikan **2 sesi per minggu** pada 3 dari 4 minggu;
- <40% melakukan tindak lanjut/remedial setidaknya sekali;
- support median >60 menit/keluarga/bulan pada harga Rp99 ribu;
- <50% memperpanjang bulan kedua;
- mayoritas alasan beli adalah “murah untuk coba”, bukan pengurangan kebingungan atau rutinitas yang jelas.

### 10.3 Kill criteria B

Hentikan atau ubah menjadi jasa berharga lebih tinggi bila:

- review aktual median >90 menit/keluarga/bulan;
- biaya review + support >40% harga selama dua bulan;
- waktu respons yang dijanjikan gagal pada >10% review;
- konversi B tidak minimal **1,5× A** atau retensi bulan kedua tidak minimal **15 poin persentase di atas A**, sementara harga/biaya jauh lebih tinggi;
- pelanggan terus meminta pengajaran live, menandakan mereka membeli tutor privat dan paket didefinisikan salah.

### 10.4 Kill criteria C

Hentikan C bila, pada minimal 5 tutor berbayar selama 6–8 minggu:

- <3 tutor mengaktifkan minimal 3 murid dalam 14 hari;
- median murid aktif <40% kuota paket pada minggu ke-4;
- tutor melaporkan waktu administrasi **tidak turun** atau justru naik setelah minggu ke-3;
- support >4 jam/akun pada bulan pertama atau >2 jam/akun pada bulan berikutnya untuk paket Studio 15;
- <60% tutor menyatakan akan memperpanjang **dan benar-benar membayar invoice kedua**;
- satu kebutuhan akun berubah menjadi role/tenant sekolah formal; jangan memaksakan produk tutor mikro menjadi SaaS sekolah.

## 11. Urutan eksperimen historis (jangan dieksekusi)

Bagian ini merekam desain sebelum keputusan harga penetrasi. Urutan, harga,
dan cohort aktif sekarang ada di `GTM-tutor-first.md` dan instrumen
`../wawancara-validasi-pasar/`; jangan menjalankan eksperimen Rp49–599 ribu di
bawah sebagai offer Jagomat.

### Eksperimen 0 — konversi cohort gratis yang sudah ada

- **Tujuan:** memisahkan pujian dari WTP.
- **Penawaran:** akhir trial, tawarkan kelanjutan satu bulan dengan dua harga acak sederhana, misalnya Rp99 ribu software-only dan Rp299 ribu dengan review terbatas; jangan memberi keduanya kepada responden yang sama sebelum pilihan pertama dicatat.
- **Sampel:** 10 keluarga pilot gratis yang sudah direncanakan; jika belum aktif, jangan menyebut hasil.
- **Bukti utama:** pembayaran/deposit, aktivasi 7 hari, sesi per minggu, tindak lanjut dikerjakan, menit support, alasan menolak.
- **Gerbang:** lanjut bila minimal 5/10 membayar pada salah satu paket sebagaimana ambang rekap pilot lama; bila <3/10, hentikan harga/offer itu dan lakukan wawancara kehilangan—bukan menambah fitur.[6]

### Eksperimen 1 — B premium terlayani, cohort 10 keluarga

- **Mengapa dulu:** menguji apakah manusia adalah bagian yang dibayar dan sekaligus mengukur biaya review nyata.
- **Harga tes:** Rp199 ribu vs Rp299 ribu/bulan; jatah review sama dan eksplisit.
- **Durasi:** 4 minggu + invoice pembaruan bulan kedua.
- **Catat:** menit review, menit support, jumlah sesi, tindak lanjut, perubahan/override diagnosis, respons time, refund, konversi invoice kedua.
- **Lulus:** ≥50% memperpanjang; margin aktual ≥50%; median review ≤90 menit; ≥40% keluarga melakukan tindak lanjut.
- **Jika gagal:** pisahkan gagal trust/WTP dari gagal operasional. Jangan mengklaim software-only pasti lebih baik.

### Eksperimen 2 — C tutor mikro, 5 akun berbayar

- **Rekrut:** tutor independen/les kecil yang sudah mengajar P3–P6 dan memiliki 5–20 murid; hindari sekolah formal.
- **Harga tes:** deposit/setup Rp100 ribu yang dikreditkan ke invoice, lalu Rp299 ribu/5 murid atau Rp599 ribu/15 murid.
- **Durasi:** 6–8 minggu agar ada waktu onboarding dan invoice kedua.
- **Catat:** waktu onboarding, support, jumlah murid aktif agregat, sesi per tutor, waktu persiapan sebelum/sesudah menurut log mingguan, laporan yang dibagikan, invoice kedua.
- **Lulus:** ≥3/5 tutor aktif dengan ≥3 murid; ≥3/5 membayar invoice kedua; margin aktual ≥50%; support bulan lanjutan ≤2 jam/akun.

### Eksperimen 3 — A software-only, cohort dingin 20 keluarga

- **Mengapa terakhir:** cohort dingin menguji apakah produk dapat hidup tanpa review founder; ini berbeda dari pengguna pilot yang sudah dekat.
- **Harga tes:** Rp49 ribu dan Rp99 ribu; pembayaran di muka satu bulan, tanpa review manusia.
- **Catat:** CAC per kanal, aktivasi 7 hari, sesi berulang, remedial, support, churn/refund, invoice kedua.
- **Lulus:** ≥3 pembayaran dari 20 penawaran berkualitas untuk sinyal awal; pada 10 pembeli, ≥50% renewal dan margin aktual ≥50%.
- **Hentikan:** jika harga Rp49 ribu tetap tidak mengonversi atau support membuat kontribusi negatif. Harga lebih murah tidak memperbaiki produk yang tidak menjadi kebiasaan.

### Eksperimen 4 — perbandingan pemenang, bukan feature sprint

Hanya setelah dua jalur memiliki minimal 10 pembeli:

- bandingkan kontribusi setelah CAC dan seluruh waktu manusia;
- bandingkan renewal invoice kedua, bukan niat memperpanjang;
- bandingkan alasan churn dan ketergantungan pada founder;
- pilih satu jalur utama untuk dua cohort berikutnya;
- jalur yang kalah harus diparkir, bukan dipertahankan lewat bundling rumit.

## 12. Data yang masih hilang

| Data hilang | Mengapa menentukan | Cara mengumpulkan tanpa membaca isi data anak |
|---|---|---|
| Pembayaran/deposit aktual | WTP survei lemah | Rekap invoice: ditawarkan, dibayar, nominal, tanggal |
| Aktivasi 7 hari | Membuktikan onboarding | Event agregat per akun, tanpa jawaban anak |
| Frekuensi sesi/minggu | Membuktikan kebiasaan | Hitung sesi agregat/pseudonim |
| Tindak lanjut/remedial dijalankan | Menguji nilai inti | Event agregat; jangan ekspor isi jawaban |
| Menit support per akun | Menentukan margin | Timesheet kategori masalah |
| Menit review B | Menentukan kapasitas | Timer per review, tanpa menyalin materi anak |
| Infra per keluarga/murid aktif | Mengganti placeholder | Tagihan hosting/API dibagi unit aktif |
| CAC per kanal | Menentukan payback | Belanja kanal ÷ pembeli baru teratribusi |
| Renewal bulan 2/3/4 | Mengukur seasonality/churn | Cohort invoice, bukan jawaban niat |
| Refund dan alasan churn | Menemukan kegagalan trust/nilai | Kode alasan + verbatim orang dewasa dengan izin |
| Utilisasi kursi tutor | Menentukan value C | Murid aktif agregat ÷ kuota |
| Waktu tutor sebelum/sesudah | Menguji efisiensi C | Self-log mingguan 10 menit |
| Musim/alasan pembelian | Memisahkan OSN vs reguler | Satu field alasan pada invoice/onboarding |
| Insiden/keberatan privasi | Risiko penghenti | Log insiden dan kategori keberatan, tanpa data sensitif |

## 13. Aturan keputusan

1. **Pilih berdasarkan kontribusi setelah CAC dan waktu manusia, bukan omzet.**
2. **Renewal dibayar mengalahkan survei WTP.** Deposit mengalahkan “tertarik”.
3. **Jangan mencampur metrik unit:** keluarga, akun tutor, dan kursi murid adalah denominator berbeda.
4. **Jangan menghitung waktu founder sebagai gratis.** Gunakan minimal Rp36 ribu/jam sampai ada angka opportunity cost yang lebih tepat.
5. **Jangan annualisasi bulan puncak OSN.** Laporkan cohort dan alasan beli.
6. **Jangan memperbaiki kegagalan monetisasi dengan feature sprint** sebelum diketahui apakah masalahnya trust, beban orang tua, harga, onboarding, atau tidak ada kebutuhan berulang.
7. **Berhenti adalah hasil yang sah.** Bila semua jalur gagal kill criteria, Jagomat dapat tetap menjadi alat internal/pilot gratis tanpa memaksakan bisnis langganan.

## Referensi internal

[1] `audit-produk.md` — audit kesiapan komersial kode lokal, 6 September 2026.
[2] `../../produk/Siklus Belajar Terpandu.md` — spesifikasi aktif siklus; sebagian besar masih belum diimplementasikan.
[3] `kompetitor-lokal.md` — harga dan bentuk penawaran lokal, diakses 6 September 2026.
[4] `../gap-pasar-edtech-matematika-sd/report.md` — profil CoLearn, Ruangguru, produk gratis/AI, dan kompetitor diagnostik.
[5] `../Analisis Kebutuhan dan Potensi Pasar.md` — kebutuhan, batas bukti, risiko diagnosis tanpa remediasi, dan sejarah monetisasi edtech.
[6] `../wawancara-validasi-pasar/09-lembar-rekap-pilot.md` — instrumen pilot tutor-first: pemakaian, tindakan, transaksi, dan invoice kedua.
