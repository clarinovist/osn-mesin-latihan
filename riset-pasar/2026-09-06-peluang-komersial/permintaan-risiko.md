# Sinyal permintaan dan risiko pembeli Jagomat

**Tanggal riset:** 6 September 2026
**Segmen yang diuji:** orang tua anak kelas 3–6 dan tutor kecil di Indonesia
**Batas analisis:** ini bukan estimasi TAM dan tidak membuktikan willingness-to-pay (WTP).

## Kesimpulan cepat

Ada **sinyal masalah yang nyata**, tetapi bukti komersial masih belum cukup. OSN menyediakan momen persiapan yang jelas dan resmi; mekanisme diagnosis miskonsepsi + tindak lanjut punya bukti implementasi yang menjanjikan; namun dampaknya sangat bergantung pada keterlibatan guru/tutor, kesesuaian materi, akses perangkat, dan pemakaian berulang. Untuk produk yang dipakai anak, privasi bukan fitur tambahan: persetujuan orang tua/wali, privasi tinggi secara baku, dan pembatasan pemrofilan perlu masuk desain sejak awal.

## 1. Sinyal permintaan yang dapat dipertanggungjawabkan

| Sinyal | Bukti | Arti komersial | Batas bukti |
|---|---|---|---|
| Kalender OSN memberi tenggat persiapan konkret | OSN-K SD Matematika berlangsung 8 Juni 2026, OSN-P 6 Juli 2026, dan OSN nasional dijadwalkan 25–31 Agustus 2026.[7] | Ada kebutuhan musiman untuk pemetaan kemampuan, latihan fokus, dan laporan progres sebelum tiap tahap. | Tidak membuktikan jumlah pembeli atau WTP. |
| Final nasional SD Matematika adalah ceruk kecil dan terukur | Dokumen finalis resmi menomori peserta SD Matematika dari 1 sampai 115; penghitungan programatik menemukan tepat **115 entri unik**.[1] Angka ini selaras dengan perubahan kuota resmi dari 60 menjadi 115 peserta per cabang ajang.[7] | Relevan sebagai segmen prestise dan kanal akuisisi, bukan dasar TAM. | **115 adalah finalis nasional SD Matematika, bukan seluruh pendaftar, peserta OSN-K, keluarga peminat, atau pelanggan potensial.** |
| Orang tua memiliki hambatan pendampingan yang cocok dengan produk terpandu | Studi kualitatif Indonesia melaporkan kesulitan memahami materi, keterbatasan waktu, ketidaksabaran, dan stres saat mendampingi anak.[6] | Laporan singkat, rekomendasi satu langkah, dan contoh terbimbing berpotensi lebih bernilai daripada bank soal mentah. | Sampel hanya 4 orang tua, satu sekolah, konteks pandemi; ini sinyal pain, bukan prevalensi nasional atau WTP. |
| Diagnosis dapat mengurangi pekerjaan koreksi dan membuat dukungan lebih terarah | Evaluasi independen Eedi dua tahun melaporkan guru merasakan beban koreksi lebih rendah, pemantauan progres lebih efisien, dan insight diagnostik yang dapat ditindaklanjuti.[3] | Nilai untuk tutor kecil kemungkinan berada pada **hemat waktu review + tahu intervensi berikutnya**, bukan sekadar generator soal. | Studi Inggris, siswa Year 7, bukan SD Indonesia atau OSN. Transfer konteks harus diuji lewat pilot lokal. |

## 2. Apa yang bukti implementasi katakan tentang diagnosis/remediasi

### Hasil yang mendukung

- RCT longitudinal independen Eedi menemukan efek positif pada semua titik ukur: dari `d = 0,06` pada 6 bulan menjadi `d = 0,46` pada 18 bulan dan `d = 0,30` pada 24 bulan; signifikan secara statistik pada 18 dan 24 bulan.[3]
- Efek lebih besar muncul pada murid yang menggunakan platform secara konsisten. Evaluator menyimpulkan dampak bergantung pada implementasi, bukan akses platform saja.[3]
- Mekanisme yang diuji relevan dengan Jagomat: retrieval, umpan balik, diagnosis miskonsepsi, dan informasi yang dapat ditindaklanjuti guru.[3]

### Hasil yang menahan overclaim

- Evaluasi EEF sebelumnya tidak dapat memakai hasil GCSE untuk mengestimasi dampak pada capaian matematika karena penutupan sekolah parsial 2020 dan pembatalan ujian. Artinya, studi itu tidak boleh dipakai sebagai bukti dampak positif maupun negatif.[8]
- RCT satu tahun pada 16 sekolah dan 2.296 murid menghasilkan `g = 0,10` dengan CI 95% `-0,08 hingga 0,28`, `p = 0,27`: arah positif tetapi **tidak signifikan secara statistik**.[2]
- Analisis murid dengan keterlibatan tinggi lebih positif, tetapi laporan sendiri menyebut analisis kepatuhan tersebut eksploratif.[2]
- Implementasi menemui hambatan: kesenjangan pemetaan kurikulum, akses perangkat, dan variasi budaya pekerjaan rumah.[3]

**Implikasi produk:** generator + diagnosis saja belum cukup. Janji yang lebih defensibel ialah: **membantu guru/tutor menemukan pola kesalahan, memilih intervensi, lalu memeriksa ulang setelah jeda**. Siklus intervensi/evaluasi berjeda Jagomat yang masih berupa spesifikasi adalah bagian penting dari proposisi nilai; jangan dipasarkan sebagai outcome yang sudah terbukti di produk saat ini.

## 3. Tantangan pembeli yang perlu diuji

| Tantangan | Hipotesis desain/penawaran | Uji paling ringan |
|---|---|---|
| Orang tua tidak yakin cara menjelaskan kesalahan | Tampilkan satu fokus dan satu contoh terbimbing dalam bahasa nonteknis; diagnosis tetap direview guru/tutor. | 8–12 sesi observasi: apakah orang tua dapat menjalankan rekomendasi tanpa bantuan tambahan? |
| Tutor kecil kekurangan waktu untuk mengoreksi dan menyusun remedial | Jual alur `jawaban → review diagnosis → remedial → laporan`, bukan jumlah soal. | Pilot 4 minggu; ukur menit review per anak dan persentase rekomendasi yang benar-benar dijalankan. |
| Penggunaan putus setelah tes awal | Jadwalkan probe ulang dan evaluasi berjeda, dengan CTA tunggal. | Ukur penyelesaian pemetaan, intervensi, dan probe berjeda per keluarga—bukan login. |
| Materi tidak selaras kebutuhan tutor/OSN | Kaitkan setiap diagnosis dan remedial ke konsep serta tahap OSN yang eksplisit. | Tutor menilai 30 kasus diagnosis: tepat/tidak, tindakan berguna/tidak. |
| Kekhawatiran data anak menghambat adopsi | Akun orang tua sebagai pengendali, minimisasi data, retensi/penghapusan jelas, privasi tinggi secara baku. | Uji pemahaman pemberitahuan privasi dan keberhasilan alur persetujuan; minta telaah hukum sebelum klaim patuh. |

## 4. Risiko privasi anak

- UU PDP menggolongkan **data anak** sebagai data pribadi yang bersifat spesifik.[5]
- Pasal 24 mewajibkan pengendali dapat menunjukkan bukti persetujuan; Pasal 25 menyatakan pemrosesan data pribadi anak dilakukan secara khusus dan wajib mendapat persetujuan orang tua dan/atau wali.[5]
- PP 17/2025 (PP TUNAS) mencakup produk/layanan yang dirancang untuk anak **atau mungkin digunakan anak**. PP ini mewajibkan mekanisme verifikasi pengguna anak, persetujuan orang tua/wali, penilaian dampak pelindungan data pribadi, dan pengaturan privasi tinggi secara baku; juga melarang pengumpulan geolokasi tepat dan pemrofilan anak.[4]
- Konsekuensi produk yang konservatif: jangan kumpulkan tanggal lahir presisi, lokasi, kontak, foto lembar, atau identifier tambahan bila tidak diperlukan; dokumentasikan tujuan dan retensi setiap field; pisahkan permukaan anak dari diagnosis internal; sediakan penghapusan/pencabutan persetujuan yang nyata.

**Catatan hukum:** ini pemetaan kewajiban dan risiko produk, bukan pendapat hukum atau klaim kepatuhan. Definisi operasional “pemrofilan”, bentuk verifikasi usia/persetujuan yang memadai, DPIA, retensi, dan penerapan aturan pelaksana perlu ditinjau penasihat hukum Indonesia sebelum peluncuran berbayar.

## 5. Putusan riset

**Layak lanjut sebagai pilot problem–solution fit, belum layak memakai klaim pasar besar.** Fokus pilot:

1. Orang tua/tutor benar-benar menindaklanjuti diagnosis, bukan hanya melihat skor.
2. Waktu review guru/tutor turun tanpa menurunkan akurasi diagnosis.
3. Anak menyelesaikan intervensi dan evaluasi berjeda.
4. Alur persetujuan dan penghapusan data dipahami orang tua.
5. WTP diuji langsung dengan penawaran berbayar kecil; jangan disimpulkan dari jumlah finalis OSN, penggunaan gratis, atau testimoni.

## Klaim yang jangan dipakai

- “Pasar OSN SD berisi 115 peserta” — salah; itu hanya finalis nasional **per cabang**, dan dokumen finalis membuktikan 115 khusus SD Matematika.
- “Diagnosis otomatis terbukti meningkatkan hasil anak SD Indonesia” — belum ada bukti lokal yang ditemukan.
- “Eedi membuktikan platform selalu efektif” — salah; RCT satu tahun tidak signifikan dan studi dua tahun menunjukkan ketergantungan pada penggunaan konsisten.
- “Orang tua bersedia membayar” — belum ada bukti transaksi, eksperimen harga, atau survei WTP dalam riset ini.
- “Jagomat sudah patuh PP TUNAS/UU PDP” — perlu audit produk dan telaah hukum terpisah.

## Sources

[1] [Pengumuman Finalis OSN Tingkat Nasional Jenjang DIKDAS 2026](https://drive.google.com/file/d/1X2onkxzWU5mPrVHtxP5mqDgTn0IM9nvm/view?usp=sharing)
[2] [Eedi STAR 2024–25 Evaluation Report](https://cdn.prod.website-files.com/68b00fd42843f377c633738c/6a394544536154d2e1b6b3fd_WWEd_Eedi_STAR_2024-25.pdf)
[3] [Eedi NWEA Longitudinal Final 2026](https://cdn.prod.website-files.com/68b00fd42843f377c633738c/6a3943a429b2a2ecd92f92dc_Eedi_NWEA_Longitudinal_Final_2026.pdf)
[4] [PP Nomor 17 Tahun 2025 (PP TUNAS)](https://jdih.komdigi.go.id/produk_hukum/view/id/965/t/peraturan+pemerintah+nomor+17+tahun+2025)
[5] [UU Nomor 27 Tahun 2022 tentang Pelindungan Data Pribadi](https://jdih.komdigi.go.id/produk_hukum/view/id/832/t/undangundang+nomor+27+tahun+2022)
[6] [Identifikasi Kendala Orang Tua Siswa Sekolah Dasar dalam Mendampingi Anak Belajar di Rumah](https://jbasic.org/index.php/basicedu/article/view/1958)
[7] [Informasi Perubahan Panduan OSN Jenjang Pendidikan Dasar Tahun 2026](https://pusatprestasinasional.kemendikdasmen.go.id/uploads/lampiran_pengumuman/2790228_1779583744_Surat-Informasi_update.pdf)
[8] [Eedi — Education Endowment Foundation](https://educationendowmentfoundation.org.uk/projects-and-evaluation/projects/diagnostic-questions)
