# Persona Pembayar dan Saluran Akuisisi Jagomat

**Tanggal:** 6 September 2026
**Tujuan keputusan:** memilih beachhead yang paling murah dicapai untuk validasi komersial awal.
**Status:** analisis hipotesis, bukan bukti permintaan, ukuran pasar, atau kesediaan membayar.
**Lingkup bukti:** dokumen produk, riset pasar, landing, akun, dan audit kode lokal. Tidak membaca data anak, basis data, akun nyata, atau secret. Tidak memakai riset web tambahan karena repo sudah cukup untuk keputusan tahap pilot.

## 1. Kesimpulan

**Beachhead komersial yang dipilih: tutor mikro yang dikelola pemiliknya sendiri, mengajar matematika/enrichment/OSN SD kelas 3–6, dan menangani beberapa murid secara rutin.**

**Saluran pertama yang dipilih: outreach founder secara langsung melalui relasi hangat tutor/les privat dan perkenalan berantai melalui WhatsApp, lalu demo singkat dengan data contoh.** Ini hipotesis saluran termurah, bukan fakta CAC yang sudah terukur.

Alasannya:

1. **[Hipotesis untuk divalidasi] Pengguna dan calon pembayar dapat menjadi orang yang sama.** Tutor mikro pemilik usaha mungkin dapat mencoba, menilai manfaat, dan memutuskan tanpa meminta persetujuan sekolah. Tetap tanyakan apakah pembayaran sebenarnya diputuskan pasangan, lembaga, atau diteruskan ke keluarga.
2. **Satu akun memang dapat mengelola beberapa murid; nilai ekonominya belum terbukti.** Kode saat ini mendukung satu guru mengelola beberapa siswa, akun murid, sesi, remedial, dan laporan per anak (`mesin/account_pages.py:32-141,163-185`). Hipotesisnya: ini mengurangi jumlah akun pembayar yang perlu diakuisisi untuk memperoleh cukup observasi pemakaian. Belum ada bukti retensi atau pembayaran.
3. **Produk saat ini lebih cocok sebagai alat bantu operator manusia daripada SaaS mandiri.** Diagnosis masih berupa usulan yang perlu dikoreksi guru, remedial dipilih guru, dan siklus intervensi penuh belum ada (`audit-produk.md:19-30,52-56`). **[Hipotesis untuk divalidasi]** Tutor akan lebih mampu atau lebih bersedia menanggung pekerjaan review itu daripada orang tua awam.
4. **Sekolah belum siap dilayani.** Belum ada organisasi, kelas, roster institusi, role sekolah, entitlement, pembayaran, dan kontrol consent/retensi yang memadai (`audit-produk.md:13-17,49-56`). Murah mendapat satu rapat tidak sama dengan murah mendapat pelanggan aktif.
- **Akuisisi orang tua hangat tetap berguna sebagai kelompok pembanding, bukan beachhead utama.** Landing saat ini masih menawarkan pilot gratis 10–20 keluarga (`mesin/landing.py:401-406`), tetapi GTM aktif menguji tutor-first dengan cohort keluarga terpisah. **[Hipotesis untuk divalidasi]** Dibanding tutor, keluarga individual akan memberi lebih sedikit profil anak, memerlukan trust lebih tinggi, dan menanggung beban pendampingan lebih besar.

### Batas keputusan

- **Tidak ada bukti transaksi Jagomat.** Lembar rekap wawancara dan pilot masih kosong (`wawancara-validasi-pasar/05-lembar-rekap.md:12-59`; `09-lembar-rekap-pilot.md:7-37`).
- **Tidak ada angka WTP yang sah.** Band Rp150–300 ribu di protokol lama adalah hipotesis yang belum diuji, bukan rekomendasi harga (`Protokol Wawancara Validasi Pasar.md:13-20`). Harga pesaing adalah anchor penawaran, bukan bukti kesediaan membayar Jagomat (`kompetitor-lokal.md:52-68`).
- **Tidak ada klaim TAM/SAM/SOM di keputusan ini.** Banyaknya siswa, tutor, atau sekolah tidak menjawab apakah mereka dapat dijangkau murah dan mau membayar.
- **“Paling murah” berarti hipotesis biaya akuisisi total terendah:** uang tunai + jam founder sampai satu akun benar-benar mengaktifkan murid dan memakai produk berulang. Bukan sekadar biaya per klik, lead, atau pendaftar.

## 2. Realitas produk yang membatasi persona dan pesan

| Fakta yang sudah didukung repo | Implikasi untuk akuisisi |
|---|---|
| Pendaftaran mandiri tersedia untuk orang tua, guru, atau les privat; akun anak dibuat dari aplikasi (`mesin/landing.py:70-117`). | Pilot dapat berjalan tanpa onboarding teknis khusus, tetapi support akun/reset sandi masih manual. |
| Guru dapat mengelola beberapa siswa dan akun murid (`mesin/account_pages.py:32-185`). | Secara operasional tutor mikro lebih cocok daripada satu keluarga per akun. |
| Diagnosis otomatis adalah usulan; guru dapat mengoreksi. Remedial dipilih guru, belum merupakan intervensi otomatis (`audit-produk.md:23-28,38-55`). | Pesan aman: alat bantu persiapan, tinjauan, latihan ulang, dan laporan. Jangan menjual “AI/adaptif memilih langkah terbaik”. |
| Laporan sekarang belum boleh disebut bukti penguasaan atau hasil terkonfirmasi (`audit-produk.md:26-28,42-47`). | Hindari janji hasil belajar, retensi, atau penguasaan. |
| Payment dan entitlement belum ada (`audit-produk.md:30,49-50`). | Pembayaran pilot harus manual; jangan mengiklankan trial/langganan otomatis. |
| 85 template menutup 74,7% konsep korpus 1.237 soal, tetapi hanya 24,4% eksplorasi nasional (`docs/riset-soal-osn-10-tahun.md:10-39`). | Klaim aman: fondasi dan pola OSN-S/K/P. Jangan menjanjikan juara nasional. |
| Landing saat ini menargetkan orang tua serta guru/les privat dan menawarkan pilot gratis 10–20 keluarga (`mesin/landing.py:310-352,401-406`). | Pilot tutor harus tetap memperoleh persetujuan keluarga dan menjelaskan siapa yang mengoperasikan akun. |

### Guardrail sebelum wawancara atau outreach

Instrumen wawancara dan pilot telah diperbarui ke GTM tutor-first. Pakai versi
aktif di `../wawancara-validasi-pasar/`, bukan kutipan atau salinan lama dari
sesi sebelum 6 September 2026.

Guardrail yang wajib bertahan:

- Produk menyimpan data di server pengelola; fitur variasi cerita dan lampiran
  foto tertentu dapat memakai layanan AI pihak ketiga. Jangan mengklaim semua
  data hanya tersimpan di rumah (`mesin/landing.py:138-191`).
- Jangan menjanjikan “resep malam ini”, evaluasi berjeda, atau checkpoint
  otomatis. Intervensi lengkap masih roadmap (`audit-produk.md:27-30,52-55`).
- Penawaran aman: **alat bantu latihan matematika SD untuk membuat soal,
  mengumpulkan jawaban, melihat usulan diagnosis, mengoreksi hasil, memilih
  latihan ulang terarah, dan membaca pola per anak** (`audit-produk.md:63-79`).

## 3. Persona 1 — Orang tua enrichment/OSN

### Definisi sempit

Orang tua anak kelas 3–6 yang sudah aktif mencari latihan matematika tambahan, pembinaan nalar, atau persiapan OSN/SASMO; bukan semua orang tua siswa SD.

**Status seluruh butir perilaku berikut: hipotesis untuk divalidasi.** Repo belum berisi wawancara terisi atau transaksi.

| Aspek | Hipotesis |
|---|---|
| Pembayar | Orang tua/wali. |
| Pengguna utama | Anak mengerjakan sesi; orang tua membuat sesi, meninjau usulan diagnosis, memilih tindak lanjut, dan membaca laporan. |
| JTBD fungsional | “Saat anak salah atau hasil latihan stagnan, bantu saya membedakan salah baca, konsep, hitung, atau tulis dan menyiapkan latihan berikutnya tanpa membuat soal dari nol.” |
| JTBD emosional | Mengurangi rasa “sudah membayar/menemani tetapi masih tidak tahu akar masalah”, tanpa melabel anak bodoh. |
| Pemicu pembelian | Hasil tryout/seleksi turun; kesalahan yang sama berulang; orang tua tidak puas dengan laporan skor/topik; menjelang masa seleksi/lomba; tutor meminta latihan rumah tambahan. |
| Alternatif saat ini | Membahas sendiri, buku/bank soal, video, aplikasi jawaban, bimbel, tutor privat, atau tidak menindaklanjuti. |
| Keberatan utama | “Mengapa tidak cukup pakai tutor/buku gratis?”; tidak yakin diagnosisnya benar; waktu pendampingan terbatas; anak enggan latihan; isu privasi data/foto; manfaat belum terbukti; cakupan bukan nasional eksplorasi. |
| Risiko mismatch | Orang tua membeli “OSN” tetapi mengharapkan prediksi medali, kelas live, atau tutor manusia; produk sekarang adalah alat yang tetap memerlukan tinjauan orang dewasa. |

### Saluran akuisisi realistis

| Prioritas | Saluran | Mengapa mungkin murah | Risiko / yang harus diuji |
|---:|---|---|---|
| 1 | Perkenalan hangat melalui orang tua yang dikenal dan referral satu tingkat via WhatsApp | Tidak perlu belanja iklan; sesuai pola rekrutmen pilot yang sudah direncanakan. | Jaringan hangat dapat menghasilkan respons sopan tetapi pemakaian rendah; bias kedekatan membuat feedback terlalu positif. |
| 2 | Referral dari tutor mikro yang sudah memakai Jagomat | Kepercayaan dipinjam dari tutor; konteks penggunaan sudah jelas. | Tutor mungkin enggan menyerahkan hubungan ke produk atau menambah pekerjaan orang tua. |
| 3 | Komunitas orang tua/OSN/SASMO dengan izin admin, memakai contoh diagnosis sintetis | Audiens lebih terarah daripada iklan luas. | Komunitas sensitif terhadap promosi; “OSN” mudah menarik ekspektasi juara yang tidak dapat dipenuhi. |
| 4 | Konten pencarian/organik tentang pola kesalahan pada soal nyata | Dapat mengedukasi tanpa paid media dan cocok dengan aset 85 template. | Lambat, perlu konsistensi, dan trafik belum tentu menjadi pemakaian. |
| Tahan dulu | Meta/TikTok Ads luas | Bisa menguji copy dalam volume. | Belum ada bukti retensi, harga, atau funnel; biaya klik dapat membeli rasa ingin tahu, bukan penggunaan. |

### Pertanyaan wawancara berbasis perilaku

1. “Ceritakan latihan matematika terakhir yang anak kerjakan di luar sekolah. Siapa yang memilih soalnya dan apa yang terjadi setelah ada jawaban salah?”
2. “Kapan terakhir kali Anda tidak bisa menjelaskan mengapa jawaban anak salah? Apa yang Anda lakukan berikutnya?”
3. “Apa laporan terakhir dari sekolah/bimbel yang benar-benar mengubah tindakan Anda di rumah?”
4. “Dalam empat minggu terakhir, berapa kali Anda duduk mendampingi dan berapa lama tiap kali?”
5. “Produk atau jasa matematika apa yang benar-benar dibayar dalam 12 bulan terakhir? Apa yang membuat pembayaran itu layak atau dihentikan?”
6. “Kalau alat ini tetap meminta Anda meninjau dan memilih tindak lanjut, bagian mana yang terasa membantu dan mana yang terasa seperti pekerjaan tambahan?”
7. “Data/foto apa yang tidak bersedia Anda unggah? Siapa yang harus memberi persetujuan?”
8. “Apa yang harus terjadi setelah pilot agar Anda benar-benar melakukan pembayaran, bukan sekadar mengatakan tertarik?”

### Eksperimen persona

**Hipotesis P-O1:** keluarga enrichment yang sudah punya rutinitas latihan akan lebih aktif daripada keluarga yang baru tertarik karena pilot gratis.

- Rekrut dua kelompok kecil secara terpisah: keluarga dengan latihan berulang yang sudah berjalan dan keluarga tanpa rutinitas.
- Ukur: akun yang menambahkan anak, sesi pertama selesai, sesi kedua dalam tujuh hari, jumlah minggu aktif, dan apakah laporan menghasilkan tindakan nyata.
- Jangan menyimpulkan dari pendaftaran atau testimoni saja.

**Hipotesis P-O2:** diagnosis jenis kesalahan lebih bernilai sebagai pelengkap tutor daripada pengganti tutor.

- Tampilkan dua framing identik kecuali posisi: “alat pendamping latihan rumah” vs “alternatif les”.
- Ukur permintaan demo dan aktivasi; pada exit interview tanyakan apa yang akan hilang bila akses ditutup.
- Hasil baru dianggap mendukung setelah ada pemakaian berulang, bukan preferensi copy saja.

## 4. Persona 2 — Tutor mikro / les privat

### Definisi sempit

Tutor independen atau pemilik les kecil yang secara langsung mengajar matematika/enrichment/OSN SD, mengelola beberapa murid, dan masih mengambil keputusan alat serta pembayaran sendiri. Bukan lembaga cabang besar atau marketplace tutor sebagai perusahaan.

**Status seluruh butir perilaku berikut: hipotesis untuk divalidasi.** Dukungan multi-siswa adalah fakta produk; kebutuhan dan kemauan membayar tutor belum dibuktikan.

| Aspek | Hipotesis |
|---|---|
| Pembayar | Tutor/pemilik les mikro; alternatifnya biaya diteruskan ke keluarga, tetapi model itu harus diuji dan tidak boleh diasumsikan. |
| Pengguna utama | Tutor membuat sesi, meninjau diagnosis, memilih remedial, dan memakai laporan; murid mengerjakan; orang tua menerima ringkasan atau tindak lanjut. |
| JTBD fungsional | “Di antara sesi mengajar, bantu saya menyiapkan variasi soal, melihat pola kesalahan per murid, memberi latihan ulang, dan menjelaskan progres ke orang tua tanpa spreadsheet/manual authoring.” |
| JTBD bisnis | Menangani beberapa murid dengan kualitas tindak lanjut yang lebih konsisten tanpa menambah jam persiapan secara linear. |
| Pemicu pembelian | Jumlah murid mulai membuat persiapan/koreksi berulang; orang tua bertanya progres; kesalahan murid berulang; tutor membutuhkan tugas antarpertemuan; ingin membedakan layanan dari bank soal biasa. |
| Alternatif saat ini | Soal cetak/Google Drive, spreadsheet/WhatsApp, buku OSN, koreksi manual, dan ingatan tutor. |
| Keberatan utama | Setup murid dan akun menambah admin; tetap harus review diagnosis; remedial belum intervensi penuh; laporan belum bukti penguasaan; belum ada kelas/roster/billing; topik/format mungkin tidak cocok dengan silabus tutor; privasi keluarga menjadi tanggung jawab tambahan. |
| Risiko mismatch | Tutor mencari LMS kelas lengkap, live teaching, pembayaran murid, atau bank soal nasional eksplorasi; Jagomat belum memenuhi itu. |

### Saluran akuisisi realistis

| Prioritas | Saluran | Mengapa mungkin murah | Risiko / yang harus diuji |
|---:|---|---|---|
| 1 | Outreach 1:1 ke tutor yang punya hubungan hangat dengan founder/pengguna, melalui WhatsApp | Tidak perlu iklan; keputusan berada pada satu orang; feedback bisa langsung ke workflow nyata. | Tidak diketahui apakah jaringan hangat yang relevan benar-benar ada. Harus dihitung jam founder per aktivasi. |
| 2 | Perkenalan berantai: setiap tutor yang aktif mengenalkan satu tutor sejawat | Trust lebih tinggi daripada cold outreach dan persona cenderung berjejaring. | Referral dapat berhenti jika manfaat belum cukup nyata atau dianggap membuka keunggulan tutor ke pesaing. |
| 3 | Outreach terpilih ke profil tutor publik/komunitas tutor matematika, dengan pesan personal dan demo sintetis | Target dapat disaring berdasarkan SD/OSN; lebih murah daripada iklan luas bila daftar kecil. | Cold message rawan dianggap spam; jangan scrape/kirim massal. Pastikan mematuhi aturan platform/komunitas. |
| 4 | Sesi demo kecil 30 menit untuk 3–5 tutor, fokus satu workflow nyata | Satu demo dapat melayani beberapa prospek dan memperlihatkan alat, bukan klaim. | Kehadiran tidak sama dengan aktivasi; demo generik akan gagal jika tidak memakai kasus kerja tutor. |
| Tahan dulu | Partnership dengan marketplace/bimbel besar | Potensi distribusi besar. | Negosiasi, integrasi, dan pembagian nilai lebih kompleks sebelum bukti penggunaan ada. |

### Pertanyaan wawancara berbasis perilaku

1. “Ambil satu murid minggu lalu: bagaimana Anda memilih latihan, mengoreksi, dan menentukan tugas berikutnya?”
2. “Berapa lama persiapan dan koreksi di luar jam mengajar untuk semua murid dalam satu minggu terakhir?”
3. “Kapan terakhir kali orang tua meminta penjelasan progres? Apa yang Anda kirimkan?”
4. “Kesalahan murid apa yang paling sering lolos dari skor benar/salah? Bagaimana Anda membedakannya sekarang?”
5. “Alat apa yang saat ini dibayar untuk mengelola materi, murid, atau laporan? Siapa yang memutuskan pembelian?”
6. “Apakah Anda bersedia meninjau usulan diagnosis per sesi? Pada jumlah murid berapa beban itu tidak masuk akal?”
7. “Apakah akun dan data dikelola Anda atau keluarga? Izin apa yang biasanya Anda minta?”
8. “Jika alat ini menghemat persiapan tetapi belum punya billing, kelas, dan intervensi otomatis, apakah cukup berguna untuk workflow Anda sekarang? Tunjukkan bagian yang akan/tidak akan dipakai.”
9. “Jika akses dihentikan setelah pilot, workflow lama apa yang terpaksa Anda lakukan lagi?”
10. “Siapa selain Anda yang harus setuju sebelum pembayaran benar-benar dilakukan?”

### Eksperimen persona

**Hipotesis P-T1:** tutor mikro memperoleh nilai paling awal dari pengurangan kerja persiapan dan dokumentasi, bukan dari klaim peningkatan hasil belajar.

- Rekrut 5 tutor secara concierge; masing-masing diminta memakai Jagomat pada minimal tiga murid dengan persetujuan keluarga selama 6–8 minggu.
- Sebelum pilot, catat workflow dan waktu aktual melalui diary satu minggu, bukan ingatan umum.
- Selama pilot, ukur: tutor yang membuat murid sendiri, sesi selesai per murid, review/koreksi diagnosis, remedial yang benar-benar dibuat, laporan yang dibagikan/dibahas, menit support, pembayaran awal, dan invoice kedua.
- Gunakan penawaran uji yang diputuskan: Rp225.000 untuk tiga bulan/maksimal 10 anak. Ini parameter eksperimen, bukan harga final publik.

**Hipotesis P-T2:** outreach langsung ke tutor menghasilkan biaya per akun aktif lebih rendah daripada rekrut satu keluarga satu per satu.

- Jalankan dua batch kecil pada periode sama: outreach tutor dan outreach orang tua hangat.
- Catat untuk setiap batch: pesan terkirim, balasan relevan, demo, akun dibuat, anak aktif, akun dengan sesi kedua, jam founder, dan biaya tunai.
- Bandingkan **biaya total per akun dengan pemakaian berulang** dan **biaya total per murid aktif**, bukan click-through atau jumlah daftar.

**Hipotesis P-T3:** tutor bersedia membayar setelah manfaat workflow nyata terlihat.

- Sebelum pilot berakhir, tetapkan satu penawaran manual yang benar-benar dapat dipenuhi saat ini; jangan memasukkan siklus/adaptif yang belum ada.
- Setelah exit interview, kirim invoice/tautan pembayaran nyata dengan tenggat dan syarat yang sama kepada cohort yang relevan.
- “Tertarik”, skor WTP, atau janji membayar tidak dihitung sebagai WTP. Hanya pembayaran yang berhasil—dan, lebih kuat lagi, pembaruan berikutnya—menjadi bukti perilaku.
- Nilai harga telah diputuskan sebagai parameter eksperimen penetrasi di
  `GTM-tutor-first.md`; penerimaan harga tetap harus dibuktikan lewat transaksi
  dan invoice kedua, bukan disimpulkan dari band lama atau harga pesaing.

## 5. Persona 3 — Sekolah

### Definisi sempit

Sekolah dasar swasta atau koordinator matematika yang memiliki kewenangan mencoba alat dengan satu kelompok kecil. Ini tetap persona masa depan, bukan beachhead sekarang.

**Status seluruh butir perilaku berikut: hipotesis untuk divalidasi.** Mandat asesmen diagnostik dalam riset lama dapat menjadi konteks, tetapi bukan bukti sekolah akan membeli Jagomat.

| Aspek | Hipotesis |
|---|---|
| Pembayar | Yayasan/sekolah/unit akademik; pengguna harian guru; penerima dampak murid dan orang tua; pemberi izin dapat mencakup kepala sekolah, IT, legal, atau wali. |
| JTBD fungsional | “Bantu guru memetakan pola kesalahan, menugaskan tindak lanjut, dan menunjukkan intervensi per murid/kelas secara konsisten.” |
| JTBD organisasi | Membuat asesmen diagnostik dapat dijalankan dan diaudit tanpa setiap guru membangun instrumen sendiri. |
| Pemicu pembelian | Hasil asesmen/kompetisi menurun; program numerasi/OSN baru; pimpinan meminta bukti intervensi; guru kewalahan menyiapkan diferensiasi. |
| Alternatif saat ini | Asesmen buatan guru, spreadsheet, LMS umum, buku/tryout, vendor bimbel, atau tidak ada tindak lanjut sistematis. |
| Keberatan utama | Tidak ada organisasi/kelas/roster/role; admin global terlalu luas; consent dan retensi data; hard-delete/provenance belum sesuai; belum ada SSO, procurement, SLA, invoice, pelatihan, atau bukti dampak; beban review guru. |
| Risiko mismatch | Sekolah membeli ekspektasi “platform adaptif institusional” sementara produk saat ini masih alat tutor/orang tua dengan operasi manual. |

### Saluran akuisisi realistis — nanti, setelah readiness

| Prioritas masa depan | Saluran | Catatan skeptis |
|---:|---|---|
| 1 | Guru/tutor pengguna yang menjadi champion internal | Lebih kredibel daripada cold sales, tetapi baru masuk akal setelah ada penggunaan tutor yang nyata. |
| 2 | Pilot satu klub matematika/kelas kecil melalui relasi sekolah hangat | Batasi scope dan data; persetujuan institusi tetap dapat memakan waktu. |
| 3 | Komunitas guru/KKG atau workshop asesmen diagnostik | Cocok untuk discovery dan edukasi, tetapi peserta workshop bukan otomatis buyer. |
| Tahan | Cold email massal ke sekolah, tender, reseller, dinas | Sales cycle, compliance, dan kesiapan produk belum mendukung. Volume lead tidak memperbaiki gap produk. |

### Pertanyaan wawancara berbasis perilaku

1. “Ceritakan asesmen diagnostik matematika terakhir yang benar-benar dijalankan. Siapa membuat, siapa membaca, dan tindakan apa yang berubah?”
2. “Siapa yang dapat menyetujui pilot satu kelas, dan dokumen apa yang wajib lolos?”
3. “Data murid apa yang boleh masuk vendor? Berapa lama boleh disimpan dan siapa yang boleh mengakses?”
4. “Berapa banyak waktu review tambahan per guru yang masih dapat diterima?”
5. “Alat pendidikan terakhir yang dibeli sekolah: siapa pengusul, pembayar, penghambat, dan berapa lama prosesnya?”
6. “Apakah kebutuhan terbesar laporan per murid, per kelas, remedial, atau komunikasi orang tua? Tunjukkan artefak yang dipakai sekarang.”
7. “Bukti apa yang harus tersedia sebelum sekolah membayar: keamanan, studi dampak, referensi sekolah, atau efisiensi waktu?”

### Eksperimen persona

**Hipotesis P-S1:** sekolah tidak ekonomis sebagai beachhead sebelum workflow tutor terbukti dan fitur institusional minimum tersedia.

- Lakukan 5–8 wawancara discovery tanpa menawarkan kontrak.
- Petakan buyer, champion, veto, requirement data, cycle steps, dan artefak procurement.
- Jangan menjalankan pilot data anak sekolah sampai kontrol organisasi/role, consent/retensi, dan provenance memenuhi kebutuhan yang ditemukan.
- Hipotesis ditolak hanya bila ada sekolah yang dapat menjalankan pilot aman dengan workflow saat ini dan jalur keputusan yang pendek—bukan hanya menyatakan tertarik.

## 6. Perbandingan skeptis tiga persona

Penilaian ini adalah **ranking keputusan**, bukan data pasar. “Lebih baik” berarti lebih cocok untuk pilot komersial dengan produk yang ada sekarang.

| Kriteria | Orang tua enrichment/OSN | Tutor mikro | Sekolah |
|---|---|---|---|
| Otoritas keputusan | **Hipotesis:** relatif tinggi, tetapi dapat melibatkan pasangan/anak | **Hipotesis:** relatif tinggi pada tutor pemilik; keputusan akhir wajib ditanya | **Hipotesis:** rendah karena melibatkan banyak pihak |
| Kecocokan dengan fitur saat ini | Sedang | **Tinggi** | Rendah |
| Beban edukasi/onboarding | **Hipotesis:** tinggi untuk diagnosis dan review | **Hipotesis:** lebih rendah karena tutor terbiasa membaca kerja murid | **Hipotesis:** tinggi + pelatihan institusi |
| Murid per akun yang diakuisisi | **Hipotesis:** biasanya sedikit | Kapabilitas beberapa murid ada; pemakaian nyatanya perlu diuji | Banyak secara potensial, tetapi belum dapat dilayani aman |
| Siklus penjualan | **Hipotesis:** lebih pendek dari sekolah | **Hipotesis:** lebih pendek dari sekolah | **Hipotesis:** panjang |
| Kebutuhan fitur yang belum ada | Siklus terpandu, dukungan orang tua ringan | Billing/kelas membantu tetapi pilot masih mungkin manual | **Banyak blocker inti** |
| Kanal termurah yang masuk akal | **Hipotesis:** warm WA/referral | **Hipotesis utama:** warm WA/direct outreach/referral sejawat | **Hipotesis:** champion internal/relasi sekolah |
| Risiko utama | Tidak dipakai karena waktu/anak; trust | Produk menambah admin; tutor tidak melihat penghematan | Procurement, privasi, role, readiness |
| Keputusan sekarang | Kelompok pembanding dan sumber referral | **Beachhead untuk diuji** | Tunda |

## 7. Rencana akuisisi minimum: tutor mikro sebagai beachhead

### Penawaran pilot yang jujur

> Jagomat membantu tutor matematika SD membuat latihan bervariasi, mengumpulkan jawaban, melihat usulan jenis kesalahan yang tetap ditinjau tutor, memilih latihan ulang, dan membaca pola per murid.

Jangan menyebut:

- otomatis memilih langkah belajar terbaik;
- siklus adaptif/intervensi/checkpoint yang sudah berjalan;
- bukti penguasaan atau peningkatan hasil;
- siap sekolah/kelas besar;
- siap juara nasional;
- langganan atau pembayaran otomatis.

### Funnel concierge

1. **Daftar prospek kecil dan relevan:** tutor matematika SD yang benar-benar mengajar 8–30 murid dan memberi tugas rutin; utamakan relasi hangat dan perkenalan satu tingkat.
2. **Pesan personal:** sebut workflow yang diuji—persiapan, diagnosis, latihan ulang, laporan—bukan “platform AI”.
3. **Discovery 15 menit:** minta tutor menunjukkan workflow minggu lalu sebelum demo.
4. **Demo 15 menit dengan data sintetis:** buat satu siswa contoh, satu sesi, tinjau diagnosis, pilih remedial, lihat laporan. Jangan menggunakan data anak nyata dalam demo.
5. **Aktivasi concierge:** tutor membuat akun dan profil murid pseudonim dengan persetujuan keluarga. Founder membantu onboarding, bukan mengoperasikan akun seterusnya.
6. **Pilot berbayar 6–8 minggu:** target minimal tiga murid per tutor; paket uji Rp225.000/3 bulan/maksimal 10 anak.
7. **Review perilaku:** gunakan metrik agregat/pseudonim, diary waktu tutor, dan wawancara; jangan pindahkan jawaban anak ke repo.
8. **Uji retensi:** minta invoice kedua/pembaruan nyata. Tidak ada tagihan diam-diam.

### Pesan outreach awal — hipotesis copy

> Halo Kak/Bu/Pak, saya sedang menguji Jagomat untuk tutor matematika SD yang mengelola 8–30 murid. Alatnya membuat latihan bervariasi, memberi usulan apakah kesalahan murid lebih dekat ke salah baca/konsep/hitung, lalu tutor tetap meninjau dan memilih latihan ulang. Saya belum mengklaim alat ini meningkatkan nilai atau menggantikan tutor. Boleh 15 menit saya lihat dulu cara Anda menyiapkan dan mengoreksi latihan sekarang? Kalau workflow-nya cocok, ada pilot terbatas 6–8 minggu; detail harga dan batas paket dijelaskan sebelum aktivasi, tanpa tagihan diam-diam.

Copy ini harus diuji. Jangan menganggap respons positif sebagai bukti nilai.

### Instrumentasi minimum

| Tahap | Metrik yang dicatat | Bukan keberhasilan |
|---|---|---|
| Reach | Prospek relevan dihubungi, sumber relasi, jam founder | Impression |
| Respons | Balasan relevan, discovery terjadwal | “Menarik” tanpa jadwal |
| Aktivasi | Akun dibuat, murid ditambah, sesi pertama selesai | Registrasi saja |
| Penggunaan berulang | Sesi kedua pada minggu berbeda; lebih dari satu murid | Banyak sesi uji oleh founder |
| Workflow value | Diagnosis direview, remedial dibuat, laporan dibahas | Halaman hanya dibuka |
| Komersial | Invoice dibayar; kelak pembaruan dibayar | WTP survei/testimoni |
| Biaya akuisisi | Uang tunai + jam founder per tutor aktif dan per murid aktif | CPC/lead mentah |

## 8. Urutan eksperimen 6–8 minggu

Angka batch di bawah adalah desain eksperimen, bukan estimasi pasar.

### Minggu 1 — discovery dan baseline

- Wawancarai tutor mikro yang memenuhi ICP; orang tua aktif menjadi pembanding terpisah.
- Gunakan pertanyaan perilaku dan pitch aktif yang sesuai privasi serta fitur nyata.
- Catat workflow, waktu aktual melalui diary, alat yang dibayar, dan siapa pembuat keputusan.

### Minggu 2 — uji saluran dan transaksi

- Kirim outreach personal kepada tutor hangat/referral; catat orang tua pembanding secara terpisah.
- Beri kode sumber manual pada setiap lead; tidak perlu memasang analytics pihak ketiga.
- Tawarkan paket tutor Rp225.000/3 bulan/maksimal 10 anak dengan syarat identik.
- Bandingkan jam founder dan biaya tunai sampai pembayaran serta aktivasi, bukan hanya reply rate.

### Minggu 2–8 — pilot penggunaan

- Pilih 5 tutor dengan workflow yang cocok; target minimal tiga murid aktif per tutor dengan persetujuan keluarga.
- Gunakan check-in maksimal satu kali per minggu melalui instrumen tutor-first aktif.
- Catat minggu aktif, review/override diagnosis, remedial, laporan, waktu sebelum/sesudah, dan support.

### Akhir observasi dan jatuh tempo berikutnya

- Putuskan berdasarkan pemakaian berulang, beban support, penghematan workflow, pembayaran, dan alasan penolakan.
- Kirim invoice kedua pada tenggat normal; jangan menggantinya dengan pertanyaan niat.
- Jangan mengubah harga dari jawaban survei. WTP hanya dinyatakan setelah pembayaran aktual.

## 9. Kriteria keputusan awal

Ambang berikut adalah **aturan eksperimen yang diusulkan**, bukan benchmark industri.

### Lanjut fokus tutor

Lanjutkan satu cohort lagi bila:

- mayoritas tutor pilot mengaktifkan sendiri lebih dari satu murid;
- penggunaan tidak berhenti pada sesi demo dan berulang pada minggu berbeda;
- tutor benar-benar meninjau diagnosis serta memakai remedial/laporan;
- beban support founder menurun setelah onboarding pertama;
- setidaknya ada pembayaran nyata dari penawaran yang sama.

Tidak ditetapkan persentase “pasar” atau proyeksi pendapatan dari cohort kecil.

### Ubah fokus ke orang tua

Pertimbangkan orang tua sebagai beachhead hanya bila batch pembanding menunjukkan:

- biaya total per keluarga aktif lebih rendah daripada biaya per tutor aktif setelah dinormalisasi per murid aktif;
- orang tua dapat menjalankan review dan tindak lanjut tanpa support intensif;
- penggunaan berulang dan pembayaran nyata lebih kuat;
- ekspektasi mereka tetap sesuai batas produk, bukan jaminan OSN/les pengganti.

### Hentikan ekspansi sementara

Hentikan akuisisi dan perbaiki produk/workflow bila:

- tutor hanya memakai generator soal tetapi mengabaikan diagnosis/remedial/laporan;
- review diagnosis menambah kerja lebih banyak daripada yang dihemat;
- keluarga tidak mengizinkan workflow data yang diperlukan;
- penggunaan jatuh setelah minggu pertama;
- minat tinggi tetapi tidak ada satu pun pembayaran nyata;
- keberatan utama adalah fitur inti yang memang belum ada, bukan copy atau onboarding.

### Sekolah tetap ditahan sampai

- role organisasi, kelas/roster, consent/retensi, provenance non-destruktif, dan entitlement siap;
- workflow tutor telah membuktikan penggunaan berulang;
- ada bukti keamanan/operasional dan studi dampak yang dapat dijelaskan jujur;
- ada champion sekolah dan jalur procurement yang sudah dipetakan dari wawancara nyata.

## 10. Daftar hipotesis yang wajib ditutup

| ID | Hipotesis | Bukti minimum untuk menerima sementara |
|---|---|---|
| H-01 | Tutor mikro adalah beachhead termurah. | Biaya total per tutor aktif dan per murid aktif lebih rendah daripada cohort orang tua pembanding. |
| H-02 | Tutor merasakan penghematan workflow. | Diary sebelum/sesudah menunjukkan tugas nyata hilang tanpa beban review/support lebih besar. |
| H-03 | Multi-siswa meningkatkan nilai akun. | Tutor mengaktifkan dan memakai produk pada lebih dari satu murid tanpa didorong founder tiap sesi. |
| H-04 | Diagnosis/remedial, bukan generator saja, menjadi nilai. | Fitur review, remedial, dan laporan benar-benar dipakai dan disebut sebagai kehilangan bila akses ditutup. |
| H-05 | Tutor dapat menjadi saluran ke keluarga/tutor lain. | Referral menghasilkan aktivasi, bukan hanya kontak. |
| H-06 | Orang tua enrichment cukup disiplin menjalankan workflow. | Penggunaan berulang dan tindak lanjut terjadi tanpa support concierge berat. |
| H-07 | Sekolah terlalu mahal dicapai sekarang. | Wawancara menunjukkan banyak gate/requirement yang belum dipenuhi; revisi bila ada pilot aman dengan jalur singkat. |
| H-08 | Ada kesediaan membayar. | Pembayaran nyata untuk penawaran yang benar-benar tersedia; survei tidak cukup. |
| H-09 | Klaim “fondasi + pola OSN-S/K/P” menarik tanpa memicu ekspektasi nasional. | Responden dapat mengulang batas produk dan tetap mengaktifkan/membayar. |
| H-10 | WhatsApp direct/referral adalah kanal termurah. | Jam founder + biaya tunai per akun aktif lebih rendah daripada kanal pembanding. |

## 11. Keputusan akhir

**Pilih tutor mikro sebagai beachhead komersial untuk diuji dan WhatsApp founder-led melalui relasi hangat/referral sebagai hipotesis saluran pertama.** Gunakan orang tua enrichment sebagai kelompok pembanding dan sumber referral. Tunda sekolah.

Keputusan ini bukan pernyataan bahwa tutor pasti mau membayar atau bahwa pasarnya besar. Ini hanya urutan pengujian dengan risiko dan biaya awal paling rendah berdasarkan kemampuan produk saat ini: satu pengambil keputusan, beberapa murid per akun, kompetensi untuk meninjau diagnosis, dan tidak memerlukan fitur institusional yang belum ada.
