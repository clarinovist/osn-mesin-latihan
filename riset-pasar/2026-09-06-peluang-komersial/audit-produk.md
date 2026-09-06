# Audit Kesiapan Komersial Jagomat — Perubahan Lokal Terbaru

**Tanggal:** 6 September 2026
**Sifat audit:** read-only terhadap kode, test, dan dokumen produk; tidak membaca atau mengubah data anak.
**Basis kode saat audit:** `main` pada `8b5909f`; audit ini adalah snapshot waktu riset, bukan status implementasi terkini.

## Verdict

**Jagomat sudah cukup untuk dijual terbatas sebagai alat bantu latihan yang dioperasikan orang tua atau tutor kecil**, terutama untuk membuat latihan, mengumpulkan jawaban, mengoreksi diagnosis, memilih remedial terarah, dan membaca laporan perkembangan.

**Jagomat belum layak dijual sebagai “pendamping belajar adaptif”, “siklus belajar terpandu”, atau produk sekolah siap institusi.** Komponen penting siklus memang sudah dispesifikasikan, tetapi reducer `learning_cycle.py`, intervensi, snapshot konfirmasi append-only, evaluasi berjeda, checkpoint, eskalasi, pembayaran, dan entitlement belum ada di kode lokal.

| Segmen | Batas penawaran sekarang | Kesiapan |
|---|---|---|
| Orang tua | Latihan matematika SD, diagnosis sebagai usulan, koreksi manusia, remedial pilihan orang tua, laporan sederhana | **Bisa pilot berbayar/manual** |
| Tutor/les kecil | Kelola beberapa murid, buat sesi dan remedial per murid, akun anak, laporan per anak | **Bisa pilot terbatas**; operasional dan penagihan masih manual |
| Sekolah | Belum ada organisasi/kelas/roster institusi, pembagian peran guru sekolah, entitlement, pembayaran, audit konfirmasi hasil, atau siklus pedagogis lengkap | **Belum siap dijual sebagai SaaS sekolah** |

## Status klaim terhadap bukti

| Area | Status | Bukti kode/test | Batas klaim komersial |
|---|---|---|---|
| Pengumpulan terpisah dari koreksi | **Ada; test target lulus** | Murid punya `Simpan sementara` dan `Selesai & kirim`; submit final mengunci perubahan, sedangkan POST koreksi guru ditolak sebelum `selesai` (`mesin/web.py:967-1029`, `mesin/web.py:1686-1704`; kontrak test `mesin/__tests__/test_alur_sesi_submit.py:1-122`). | Aman menyebut “jawaban dikumpulkan dulu, lalu diperiksa guru”. Jangan menyebut hasil langsung final. |
| Diagnosis dan override guru | **Ada; test target lulus** | `kode_usulan` dan `kode_final` dipisah (`mesin/schema.py:153-165`); guru dapat memilih kode atau benar dan penyimpanan menandai override manual (`mesin/teacher_pages.py:1567-1617`). | Aman menyebut “diagnosis otomatis sebagai usulan yang dapat dikoreksi guru”. |
| Remedial pilihan guru | **Ada; test target lulus** | Form menampilkan kandidat dan memungkinkan maksimal tiga tipe (`mesin/teacher_pages.py:63-111`); generator memvalidasi sumber selesai+direview, kandidat, jumlah, dan membuat soal baru seimbang (`mesin/database.py:583-692`); rute mengulang validasi server-side (`mesin/web.py:1347-1442`). Test UI dan perilaku mencakup pilihan fokus, sumber sesi, tampering, batas jumlah, dan kepemilikan (`mesin/__tests__/test_remedial_ui.py:64-232`; `mesin/__tests__/test_sesi_remedial.py:123-214`). | Aman menyebut “guru memilih latihan ulang berdasarkan kesalahan terbaru”. Belum aman menyebut “sistem otomatis memilih intervensi terbaik”. |
| Laporan perkembangan | **Ada; test target lulus** | Laporan memisahkan K berulang lintas sesi dari materi T, memberi tindakan, menurunkan skor menjadi konteks sekunder, dan menyimpan detail teknis dalam lipatan (`mesin/reports.py:321-512`; `mesin/__tests__/test_laporan_ortu.py:121-140,207-241`). | Aman menyebut “laporan pola latihan dan saran tindak lanjut”. Belum aman menyebut “status penguasaan” atau “retensi terbukti”. |
| Konfirmasi/snapshot bukti | **Belum ada** | Skema hanya memiliki `selesai`, `direview`, diagnosis mutable, dan metadata remedial (`mesin/schema.py:90-111,153-165`). Membuka halaman sesi otomatis mengisi `direview` (`mesin/web.py:592-614`), sedangkan spesifikasi mewajibkan konfirmasi eksplisit dan snapshot outcome append-only (`produk/Siklus Belajar Terpandu.md:28-48`). | Jangan memakai kata “terkonfirmasi”, “terverifikasi”, atau “bukti penguasaan” untuk laporan saat ini. |
| Siklus belajar terpandu | **Masih spesifikasi** | Kontrak produk menetapkan pemetaan → fokus → intervensi → latihan terbimbing → penguatan → evaluasi berjeda → checkpoint → maju/eskalasi (`produk/Siklus Belajar Terpandu.md:21-26,95-128`). File `mesin/learning_cycle.py` dan `mesin/interventions.py` tidak ada. | Jangan menjual “rencana belajar otomatis”, evaluasi 3 hari, checkpoint 28 hari, pendekatan alternatif, atau eskalasi sebagai fitur tersedia. |
| Self-service akun | **Ada; test target lulus** | Pendaftaran publik membuat akun guru dan auto-login dengan persetujuan privasi (`mesin/landing.py:70-117`; `mesin/web.py:878-915`; `mesin/__tests__/test_register.py:35-131`). Orang tua/guru dapat membuat dan mengelola akun anak; daftar disaring per keluarga (`mesin/account_pages.py:32-115`). | Aman menyebut “daftar mandiri dan buat akun anak”. Reset sandi orang tua masih melalui pengelola, bukan self-service penuh. |
| Pembayaran dan entitlement | **Tidak ada di kode yang ditelusuri** | Pencarian produksi/test untuk pembayaran, subscription/langganan, checkout, invoice, dan entitlement tidak menemukan implementasi. Pendaftaran saat ini langsung membuat akun guru tanpa gerbang paket (`mesin/web.py:878-915`). | Penjualan sekarang harus memakai invoice/aktivasi manual atau akses gratis. Jangan klaim paket, trial otomatis, batas murid berbayar, atau penghentian akses otomatis. |
| Isolasi keluarga dan palang anak | **Ada; test target lulus** | Rute data keluarga lain mengembalikan 404 (`mesin/__tests__/test_family_isolation.py:1-75`); test palang membuat akses sisi anak ke `kunci`, malrule, dan diagnosis meledak (`mesin/__tests__/test_students.py:1-69`). | Cukup untuk pilot terbatas, tetapi bukan pengganti audit keamanan independen. |
| Transparansi privasi | **Ada, dengan gap operasional** | Kebijakan menyebut data, AI pihak ketiga, akses pengelola lintas keluarga, dan tidak adanya gerbang persetujuan khusus per unggahan (`mesin/landing.py:120-191`). | Aman menyebut kebijakan transparan. Jangan menyebut consent unggahan foto sudah granular; kebijakan sendiri menyatakan belum ada gerbang khusus. |

## Temuan prioritas

### High

1. **“Direview” belum sama dengan konfirmasi manusia.** Membuka hasil sesi yang selesai langsung menandai `direview` (`mesin/web.py:599-614`). Diagnosis dan `kode_final` tetap dapat ditimpa (`mesin/database.py:795-832`). Ini bertentangan dengan syarat snapshot konfirmasi eksplisit (`produk/Siklus Belajar Terpandu.md:28-44`).
   - Dampak: remedial dan laporan bisa terlihat lebih sah daripada bukti sebenarnya.
   - Batas jual: posisikan keputusan sebagai bantuan untuk orang tua/tutor, bukan keputusan pedagogis otomatis.

2. **Laporan memakai sesi selesai, bukan hanya hasil yang dikonfirmasi guru.** `ringkasan()` dan peta laporan memfilter `selesai` tetapi tidak `direview`/konfirmasi (`mesin/database.py:838-905`). Diagnosis otomatis dibuat saat submit final (`mesin/web.py:991-1006`).
   - Dampak: laporan dapat memuat hasil otomatis yang belum diperiksa manusia.
   - Batas jual: jangan menjanjikan laporan sebagai hasil evaluasi guru sampai gerbang bukti diperbaiki.

3. **Hard-delete masih tersedia untuk sesi beserta jawaban, diagnosis, dan lampiran** (`mesin/database.py:715-727`; `mesin/web.py:1651-1663`), sedangkan kontrak siklus melarang penghapusan sesi berbukti dan meminta arsip/pembatalan (`produk/Siklus Belajar Terpandu.md:161-178`).
   - Dampak: provenance untuk klaim perkembangan belum dapat diandalkan.

4. **Tidak ada payment/entitlement.** Semua akun pendaftar langsung aktif.
   - Dampak: belum ada kontrol paket, limit penggunaan, masa aktif, rekonsiliasi pembayaran, atau pemutusan akses.

### Medium

1. **Remedial masih “soal baru berdasarkan kesalahan”, belum intervensi.** Kode membuat drill pada template yang dipilih, tetapi belum memiliki konten konkret/visual, `pendekatan_id`, latihan terbimbing, probe, atau eskalasi sebagaimana spesifikasi (`produk/Siklus Belajar Terpandu.md:76-114`).
2. **Privasi unggahan foto masih berbasis pemberitahuan umum.** Kebijakan jujur menyatakan belum ada gerbang persetujuan khusus setiap upload (`mesin/landing.py:154-162`). Untuk sekolah, ini perlu kontrol consent dan kebijakan retensi yang lebih formal.
3. **Model admin bersifat global.** Kebijakan menyatakan pengelola dapat mengakses dan mengelola data murid semua keluarga (`mesin/landing.py:166-175`). Ini dapat diterima untuk layanan kecil yang dikelola langsung, tetapi terlalu lebar untuk organisasi sekolah tanpa tenant/role institusional.

### Low

1. **Istilah “Remedial” tampil ke anak** pada riwayat, sementara kontrak baru meminta istilah netral seperti “Pelajari bersama” dan “Coba mandiri” (`produk/Siklus Belajar Terpandu.md:180-192`). Ini bukan kebocoran kode diagnosis, tetapi belum selaras dengan bahasa produk akhir.
2. **Reset sandi orang tua bergantung pada WA pengelola**, karena aplikasi sengaja tidak menyimpan email/telepon (`mesin/landing.py:199-230`). Cocok untuk pilot berlayanan, belum ideal untuk SaaS volume besar.

## Apa yang bisa dijual sekarang

**Paket yang jujur:**

> Alat bantu latihan matematika SD untuk orang tua dan tutor: buat soal baru, kumpulkan jawaban anak, lihat usulan diagnosis, koreksi hasil, pilih latihan ulang terarah, dan baca pola perkembangan per anak.

**Klaim yang harus ditahan:**

- “pendamping belajar adaptif”;
- “otomatis menentukan langkah belajar terbaik”;
- “membuktikan konsep sudah dikuasai”;
- “evaluasi berjeda dan checkpoint otomatis”;
- “siap sekolah/multi-kampus”;
- “langganan dan pembayaran otomatis”;
- “siap juara nasional”.

Batas materi yang aman tetap **fondasi dan pola soal OSN-S/K/P**, bukan jaminan prestasi nasional.

## Rekomendasi jalur komersial

| Opsi | Cocok untuk | Kelebihan | Konsekuensi |
|---|---|---|---|
| **A. Pilot berbayar terlayani sekarang** | 10–30 orang tua atau beberapa tutor kecil | Bisa menguji willingness-to-pay dengan fitur yang benar-benar ada; onboarding, invoice, dan support dikerjakan manual | Harus memakai copy terbatas di atas; pengelola memikul reset sandi, pembayaran, dan dukungan privasi |
| **B. Tunda penjualan sampai fondasi siklus + entitlement** | Target sekolah atau SaaS mandiri | Klaim produk lebih kuat dan risiko bukti pedagogis lebih rendah | Menunda validasi harga; perlu snapshot konfirmasi, reducer, intervensi, evaluasi/checkpoint, arsip non-destruktif, serta payment/entitlement |

**Rekomendasi:** ambil **Opsi A** untuk orang tua/tutor kecil dengan cohort terbatas, sambil melarang klaim siklus adaptif. Jangan masuk sekolah sebelum fondasi bukti, role institusional, consent/retensi, dan entitlement selesai.

## Verifikasi yang benar-benar dijalankan

```text
161 passed in 26.62s
```

Test target yang dijalankan:

- `test_sesi_remedial.py`
- `test_remedial_ui.py`
- `test_laporan_ortu.py`
- `test_alur_sesi_submit.py`
- `test_register.py`
- `test_family_isolation.py`
- `test_students.py`
- `test_landing.py`

**Batas verifikasi:** bukan full suite; tidak menjalankan server produksi, pembayaran nyata, migrasi produksi, uji visual, atau alur dengan data anak. Karena itu laporan ini membuktikan **kode lokal + test target**, bukan bahwa fitur sudah terdeploy atau berfungsi di produksi.
