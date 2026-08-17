# PRD — Aplikasi Diagnosis & Remediasi Matematika SD

Dokumen hidup, dibangun bertahap per sesi diskusi. Konteks produk & keputusan
sebelumnya ada di memory (`osn-app-arah-produk`, `osn-taksonomi-bkh`) dan riset
pasar di `gap-pasar-edtech-matematika-sd/report.md`. Bagian pertama yang
dibahas: **Remediasi** — apa yang terjadi setelah sebuah kesalahan
terdiagnosis B/K/H.

## Revisi arsitektur (sesi ini)

Empat keputusan diubah/ditambahkan setelah menelusuri konsistensi antar
bagian. Tiga yang pertama adalah koreksi tabrakan internal, bukan preferensi
gaya:

| # | Perubahan | Kenapa | Bagian |
|---|---|---|---|
| 1 | Sidik jari → **malrule sebagai fungsi** atas parameter soal; soal disimpan sebagai template+parameter | Lookup literal `(soal, jawaban)` membuat **semua sesi verifikasi** (§4.3 prioritas 1 memakai "soal beda angka") jatuh ke Tahap B — lapisan deterministik hilang tepat di titik paling menentukan | §2.3.1, §2.4, §2.5 |
| 2 | Status topik **bukan field yang ditimpa** — konten immutable / kejadian append-only / status turunan | Mutasi YAML bertabrakan dengan janji §2.6 & §7.3 ("iterasi berkali-kali di atas data yang sama"); `kode_final` (data termahal di sistem — butuh anak & wawancara) tidak boleh disimpan di tempat yang bisa ditimpa | §8.4, §1.5, §5.6 |
| 3 | Tahap B punya **dua implementasi yang diukur berdampingan** (`tinta_heuristik` wajib, `tinta_llm` kondisional) | PRD lama menulis heuristik if-then, spike mengimplementasikan LLM — dua hal berbeda biaya & testability. Tanpa baseline, "apakah LLM perlu?" tidak bisa dijawab | §2.3.2, §2.7, §9.1 |
| 4 | Siklus §8.5 dibungkus satu perintah `osn sync` | 10 langkah manual × 3 sesi/minggu adalah bentuk kegagalan yang tidak muncul di gerbang teknis mana pun tapi menghentikan produk di minggu ketiga (§9.2 mensyaratkan berminggu-minggu berturut-turut) | §8.7, §9.2 |

Tambahan pendukung: jejak `aturan_versi`/`prompt_versi`/`model` + cache LLM
(§2.5) supaya batas 3 putaran prompt dari Peta Jalan bisa **dihitung**, bukan
diingat; golden test `MotionEvent.toSamples()` sebagai satu-satunya test wajib
hari pertama (§8.8); dan §9.4 memisahkan klaim yang **belum diverifikasi** dari
keputusan yang sengaja ditunda.

Yang **tidak** berubah: file-based tanpa server/DB, tanpa izin INTERNET,
tanpa OCR, tanpa UI review, satu operator, batch bukan real-time. Ukuran
arsitektur §8.6 tetap dinilai tepat untuk skala satu keluarga.

## 1. Remediasi

### 1.1 Kenapa ini bukan opsional

Riset akademik (Cognitive Tutor / ASSISTments RCT) menunjukkan: memberi tahu
jenis kesalahan saja, tanpa remediasi yang tepat sasaran, **tidak**
memperbaiki hasil belajar. Diagnosis tanpa resep tindakan hanya jadi laporan,
bukan produk. Ini juga persis gap yang ditemukan di riset pasar: kompetitor
Indonesia berhenti di angka/skor/nama-topik, tidak pernah sampai ke "apa yang
harus dilakukan orang tua di rumah malam ini".

Sudah ada preseden tertulis untuk ini: `Tes Kalibrasi - Panduan Orang Tua.pdf`
dan `Uji Ulang Lisan - Tindak Lanjut.pdf` sudah berisi resep manual per
kode B/K/H dan per pola jawaban salah. v1 pada dasarnya **mendigitalkan dan
menskalakan pola yang sudah terbukti di dua dokumen itu**, bukan merancang
dari nol.

### 1.2 Tiga arketipe remediasi

| Kode | Sifat masalah | Tindakan | Target durasi | Berat konten |
|---|---|---|---|---|
| **B** — salah baca | Bukan lubang matematika | Pegang pensil, tandai angka & yang ditanya, ucapkan ulang soal dengan kalimat sendiri sebelum menghitung | 2–3 minggu, biasanya hilang sendiri | Ringan — cukup generik lintas topik |
| **K** — salah konsep | Paling serius: anak konsisten pakai cara keliru dan yakin benar | Diulang dari konsep pakai **benda nyata** (concrete) sebelum kembali ke simbol/angka. Tidak cukup membetulkan jawabannya | 4–6 minggu per lubang topik | Berat — harus spesifik per topik |
| **H** — salah hitung | Caranya benar, angkanya meleset | Bukan materi baru — pembiasaan "tulis langkah, periksa ulang". Kalau H menumpuk di banyak soal → gejala terburu-buru, bukan gejala paham | Tidak perlu jeda kurikulum, cukup ubah kebiasaan sesi | Ringan — hampir template |

Kasus khusus yang wajib ditangani: **jawaban benar tapi tidak bisa jelaskan
"dapat dari mana"** = K terselubung. Ini bukan hipotetis — riset frontier
2025-2026 ("Correct Answer Trap") menunjukkan bahkan LLM canggih gagal
menangkap ini, dan dua PDF di atas sudah mengantisipasinya lewat wawancara
lisan. Skor benar **tidak boleh** otomatis menutup sebuah topik di graf.

### 1.3 Sumber konten resep: pustaka pra-tulis dulu, AI generate sebagai fallback

Keputusan: untuk setiap `(topik, kode)`, sistem cari dulu di **pustaka
pra-tulis** (ditulis manusia, gaya & kehati-hatian sama seperti dua PDF di
atas). Kalau belum ada entri untuk kombinasi itu, **AI generate on the fly**
lewat pipeline diagnosis yang sudah ada (skrip Python di Mac, offline).

Alasan urutannya begini (bukan sebaliknya):
- **K butuh pustaka pra-tulis lebih dulu.** Ini paling berisiko kalau
  kontennya asal — analogi benda nyata yang keliru bisa menanamkan
  miskonsepsi baru, bukan membetulkan. Prioritas authoring manual: mulai
  dari topik-topik yang sudah muncul di Tes Kalibrasi Minggu 0 (urutan
  operasi, pecahan, desimal, persen, FPB/KPK, keterbagian, luas, volume,
  satuan, kecepatan, rata-rata, pola bilangan, pencacahan) — 14 topik ini
  sudah punya *seed* dari pola jawaban salah yang ada di PDF — yang jadi
  bahan malrule pertama (§2.3.1).
- **B dan H boleh AI-generate sejak awal** tanpa banyak pra-authoring — dua
  arketipe ini secara alami generik lintas topik (strategi baca soal,
  kebiasaan periksa ulang tidak banyak berubah per topik).
- **Human-in-the-loop otomatis ada di v1** karena orang tua = founder =
  operator skrip Python. Resep AI-generated dibaca founder sendiri sebelum
  dipakai ke anak — tidak perlu mekanisme approval terpisah dulu. Kalau nanti
  keluar dari lingkup satu keluarga, baru perlu gerbang review eksplisit.
- Field `sumber: pra-tulis | ai-generated` disimpan di tiap resep yang
  terpakai — bukan untuk ditampilkan ke orang tua, tapi jadi jejak audit buat
  menilai nanti resep AI mana yang layak "naik kelas" jadi pra-tulis.

### 1.4 Bentuk data satu "resep"

Setiap resep, pra-tulis maupun AI-generated, wajib punya bentuk yang sama
(meniru struktur yang sudah terbukti di PDF):

```
topik_id
kode: B | K | H
sifat_masalah      # 1-2 kalimat, bahasa orang tua awam, bukan register pedagogis
tindakan           # langkah konkret, bukan teori — parent bisa langsung eksekusi
durasi_target       # kapan wajar mulai membaik
verifikasi          # kapan & bagaimana re-test (default: 3 hari, soal beda angka sama skill)
sumber: pra-tulis | ai-generated
```

Guardrail yang dibawa dari PDF, berlaku ke semua resep tanpa kecuali:
- **Tidak pernah ditampilkan ke anak.** Kesimpulan B/K/H adalah data orang
  tua, bukan bahan ceramah ke anak di hari yang sama.
- **Tidak ada resep tanpa tindakan konkret.** Label kode saja (mis. "K di
  topik pecahan") tidak pernah dikirim sendirian — selalu menempel dengan
  `tindakan`.

### 1.5 Loop verifikasi (uji ulang berjeda)

Pola dari PDF: soal yang salah dipindah ke "buku kesalahan", dikerjakan ulang
dari nol setelah jeda (default 3 hari), bukan langsung di sesi yang sama —
supaya yang terukur adalah retensi, bukan hafalan jangka pendek.

Status topik di graf prasyarat (menambah state yang sudah disepakati
sebelumnya — non-kalender, berbasis kondisi anak):

```
belum_dicoba → dicoba → ditandai(B|K|H) → resep_diberikan
             → menunggu_verifikasi (dijadwalkan, bukan tanggal kalender —
               dipicu sesi berikutnya yang menyentuh topik sama)
             → selesai (retensi terbukti) | masih_bermasalah (loop balik,
               eskalasi — lihat 1.6)
```

`menunggu_verifikasi` tidak boleh otomatis dianggap "selesai" hanya karena
jawaban berikutnya benar — kalau ada indikasi menghafal (lihat kasus khusus
1.2), tetap butuh cek "dapat dari mana" versi digital.

Catatan implementasi (§8.4): state ini **tidak disimpan sebagai field yang
ditimpa** di node graf. Ia dihitung dari riwayat kejadian —
`status(topik) = derive(kejadian)`. Konsekuensi yang relevan untuk bagian ini:
sebuah topik tidak pernah "kehilangan" jejak bahwa ia dulu pernah `K`, karena
yang tersimpan adalah kemunculannya, bukan status terakhirnya. Ini yang
membuat ambang §1.6 ("≥2 kemunculan K", "gagal verifikasi 2x") bisa dihitung
sama persis kapan pun, termasuk berbulan-bulan setelah kejadiannya.

### 1.6 Keputusan: eskalasi, verifikasi lisan, dan threshold

Tiga hal ini diputuskan bersama karena saling mengunci — satu prinsip
konfirmasi (2x) dipakai konsisten di ketiganya, bukan angka ambang yang
beda-beda di tempat berbeda.

**Threshold "K aktif": ≥2 kemunculan kode K di topik yang sama** (tidak harus
berturut-turut dalam satu sesi). Klasifikasi B/K/H dari tinta digital adalah
heuristik, bukan kepastian (spike sendiri menoleransi ~30% meleset — target
lulus "≥7 dari 10 kode cocok"). Satu kemunculan terlalu rawan alarm palsu
yang memblokir anak salah sasaran. Efeknya **soft gate**, bukan kunci mati:
topik-topik lanjutan yang mensyaratkan topik berstatus "K aktif" turun
prioritas di rekomendasi, tapi tidak dikunci total — konsisten dengan prinsip
non-kalender yang sudah disepakati (bolong tidak menimbulkan utang sesi, jadi
gating pun tidak boleh kaku).

**Eskalasi kalau K yang sama gagal verifikasi 2x berturut-turut** (bukan
sekadar perpanjang durasi — itu logika H, bukan K):
1. Cek topik prasyarat langsung di graf. Kalau prasyaratnya sendiri belum
   pernah terverifikasi kokoh → mundur ke sana dulu. Ini logika yang sama
   dengan "Bagian 1 banyak salah → tunda kurikulum, benahi fondasi dulu" di
   Tes Kalibrasi — remediasi di topik lanjutan percuma kalau fondasinya
   goyah.
2. Kalau prasyaratnya sudah kokoh (bukan soal fondasi), eskalasi ke **Uji
   Ulang Lisan** — instrumen wawancara yang sudah ada, dipakai sebagai
   diagnosis lapis kedua, bukan mengulang remediasi tertulis yang sama untuk
   ketiga kalinya.

**Versi digital "dapat dari mana?": masuk v1, versi ringan.** Ini inti klaim
diferensiasi produk (Correct Answer Trap — jawaban benar tidak berarti
paham), jadi tidak bisa ditunda ke v2 tanpa melubangi klaim diagnosis itu
sendiri. Tapi tidak perlu sesi 12-soal terpisah untuk tiap topik — cukup nudge
kontekstual di dua titik: (a) saat topik akan ditandai "selesai", (b) jawaban
benar pertama setelah topik lepas dari status "K aktif". Orang tua diminta
tanya lisan sebentar, lalu catat lewat 3 pilihan singkat: **bisa jelaskan /
ragu-ragu / menghafal**. "Menghafal" atau "ragu-ragu" mencegah topik ditutup
meski jawaban tertulisnya benar. Sesi Uji Ulang Lisan penuh (12 soal
terstruktur) tetap jadi instrumen terpisah untuk kasus eskalasi (poin 2 di
atas), bukan dijalankan rutin per topik.

## 2. Diagnosis

Bagaimana goresan tangan di layar HP dipetakan jadi kode B/K/H secara
otomatis. Ini jantung teknis produk — tapi ternyata lebih sempit lingkupnya
dari yang terlihat, begitu dipecah sesuai bukti yang sudah ada.

### 2.1 Prinsip

- **Tidak butuh OCR/pengenalan tulisan tangan sama sekali di v1.** Ini temuan
  penting saat memecah sumber sinyal (lihat 2.2) — jawaban akhir sudah
  diketik (bukan digoreskan), jadi teks biasa. Sinyal dari tinta yang tersisa
  (kanvas per langkah) hanya dipakai lewat **waktu dan geometri** (jeda,
  jumlah koreksi, urutan kanvas disentuh) — bukan lewat membaca *apa* yang
  digoreskan. Ini menyederhanakan v1 drastis: tidak ada model ML terpisah
  untuk mengenali tulisan, cocok dengan keputusan "tanpa izin INTERNET" di
  spike (tidak ada API OCR eksternal yang dibutuhkan).
- **Orang tua tetap wasit akhir, bukan sistem.** Skrip Python menghasilkan
  kode *draf* (`kode_awal`); tidak ada kode yang menghitung ke status topik
  atau ke ambang "K aktif" (§1.6) sebelum orang tua meninjau dan
  mengonfirmasi/mengoreksinya jadi `kode_final`. Ini pola yang sama dengan
  §1.3 (resep AI-generated dibaca founder dulu) — sengaja konsisten.
- **Asimetri biaya kesalahan: false-K lebih mahal dari false-H.** K memicu
  remediasi berat (4-6 minggu, benda nyata) dan soft-gate progres; H cuma
  butuh pembiasaan periksa ulang. Ini sudah jadi gerbang lulus spike sendiri:
  "nol kasus AI menyebut K untuk kesalahan yang sebenarnya H". Konsekuensi
  desain: kalau sinyal tinta ambigu antara K dan H, sistem **default ke kode
  yang lebih ringan** (H) atau "tidak pasti", tidak pernah menebak ke arah K.

### 2.2 Sumber sinyal (tanpa OCR)

| Sinyal | Dari mana | Dipakai di tahap |
|---|---|---|
| Jawaban akhir (teks, diketik) | Input keyboard langsung | A — pencocokan prediksi malrule (§2.3.1) |
| Waktu antar-goresan per kanvas | Timestamp stroke | B — heuristik pola tinta |
| Jumlah & titik koreksi/coretan | Event hapus/coret per kanvas | B |
| Urutan kanvas disentuh | Urutan interaksi (jawaban ditulis duluan atau belakangan) | B |
| Jalur soal (berlangkah / gambar bebas / daftar berbaris) | Tipe soal | Kalibrasi fitur B — bentuknya beda per jalur, "ragu" di kanvas gambar bebas ≠ "ragu" di kanvas berlangkah |

### 2.3 Pipeline: dua tahap otomatis + satu tahap manusia

```
Tahap A — Malrule (deterministik, tanpa LLM)
  Untuk soal yang punya template + parameter (§2.3.1), jalankan tiap
  malrule yang berlaku untuk template itu, lalu cocokkan hasil
  prediksinya ke jawaban akhir anak (teks, diketik)
  → kalau tepat satu malrule memprediksi persis jawaban salah anak:
    kode_awal ditetapkan tinggi-percaya, tanpa analisis tinta sama sekali
  → kalau lebih dari satu malrule memprediksi jawaban yang sama:
    ambigu, turun ke Tahap B (jangan pilih yang paling berat, §2.1)

Tahap B — Pola tinta (dipakai kalau tidak ada malrule yang cocok)
  lancar tanpa ragu tapi salah          → condong K
  langkah benar, koreksi di titik hitung → condong H
  jawaban ditulis duluan, langkah menyusul → curiga menebak/B
  sinyal campur atau lemah               → "tidak pasti" (bukan dipaksa K)
  Dua implementasi paralel — lihat §2.3.2

Tahap C — Tinjauan orang tua (wajib, bukan opsional)
  kode_awal ditampilkan + alasan singkat → orang tua konfirmasi/koreksi
  → kode_final (satu-satunya yang dihitung ke §1.5/§1.6)
```

### 2.3.1 Malrule sebagai fungsi, bukan tabel pasangan literal

**Keputusan: sidik jari disimpan sebagai fungsi atas parameter soal yang
dieksekusi saat diagnosis — bukan sebagai tabel lookup
`(soal_id, jawaban_salah) → kode`.**

Alasan utamanya bukan keanggunan, tapi tabrakan langsung dengan §4.3
prioritas 1: sesi verifikasi memakai **soal beda angka, skill sama**. Kalau
sidik jari dikunci ke string jawaban satu soal tertentu, maka begitu
angkanya diganti tidak ada entri yang cocok — dan **semua sesi verifikasi
otomatis jatuh ke Tahap B**, jalur paling lemah, persis di titik paling
menentukan (topik ditutup `selesai` atau dilempar ke `masih_bermasalah`).
Bentuk lookup literal membuat lapisan deterministik menghilang tepat saat
paling dibutuhkan.

Konsekuensinya soal disimpan sebagai **template + parameter**, bukan teks
mati:

```
template_id: pecahan_operasi_campuran
bentuk: rantai suku — [(pembilang, penyebut, tanda), …]
parameter:
  suku: [ {n:2, d:3, tanda:+}, {n:3, d:4, tanda:+}, {n:1, d:2, tanda:-} ]
  # ditampilkan ke anak sebagai: 2/3 + 3/4 − 1/2
jawaban_benar: fungsi(suku)      # dihitung, tidak ditulis manual → 11/12

malrule:
  id: pecahan.operasi_pembilang_penyebut_terpisah
  berlaku_untuk: [pecahan_operasi_campuran, pecahan_penjumlahan]
  prediksi(suku): Σ(tanda·n) / Σ(tanda·d)
  kode: K
  alasan_singkat: "pembilang & penyebut dioperasikan sendiri-sendiri"
```

Untuk parameter di atas, malrule ini memprediksi
(2+3−1)/(3+4−2) = **4/5** — persis jawaban salah yang tercatat di
`Tes Kalibrasi - Panduan Orang Tua.pdf` untuk soal ini, sementara jawaban
benarnya 11/12.

Perhatikan bentuk fungsinya: ia beroperasi atas **seluruh daftar suku**, bukan
atas dua suku pertama, dan ia menghormati tanda operasinya. Ini bukan detail
sepele — malrule yang hanya menjumlahkan dua suku pertama akan memprediksi 5/7
dan gagal mengenali kesalahan yang sebenarnya terjadi. Konsekuensi desainnya:
`parameter` harus berbentuk **daftar berstruktur**, bukan slot bernama tetap
(`a,b,c,d,…`), supaya satu malrule berlaku untuk soal dengan dua suku maupun
lima suku tanpa ditulis ulang. Inilah juga alasan test "malrule tidak saling
bertumbukan" (§8.8) dijalankan atas rentang parameter, bukan atas satu contoh.

Tiga akibat yang mengubah lingkup kerja, bukan cuma bentuk data:

- **Cakupan Tahap A bukan ~20 soal.** Klaim lama ("Tahap A hanya mencakup
  soal yang sudah punya entri, mayoritas kurikulum jatuh ke Tahap B")
  sebagian adalah akibat cara keying-nya, bukan kekurangan konten. Satu
  malrule berlaku ke **semua soal bertemplate sama** — jadi cakupan
  deterministik tumbuh per *template*, bukan per soal.
- **Soal verifikasi bisa dibangkitkan, bukan diauthor.** Karena template dan
  parameternya terpisah, "soal beda angka, skill sama" (§4.3 prioritas 1)
  didapat dengan me-reparametrisasi template yang sama — dan malrule-nya
  tetap berlaku, jadi verifikasi dapat diagnosis deterministik yang sama
  kuat dengan sesi pertama.
- **Generalisasi tidak diserahkan ke AI.** Riset yang sudah dicatat di Peta
  Jalan menunjukkan MalruleLib turun 66%→40% saat menggeneralisasi satu
  contoh kesalahan ke template berbeda. Fungsi eksplisit menyelesaikan
  masalah yang sama dengan akurasi 100% dan biaya nol — jadi generalisasi
  memang tidak boleh jadi tugas LLM di sini.

Guardrail asimetri §2.1 tetap berlaku dan berpindah ke sini: kalau dua
malrule memprediksi jawaban yang sama (mis. satu berkode K, satu H), Tahap A
**tidak memilih**, ia turun ke Tahap B dan ke tinjauan orang tua. Tidak ada
jalur di mana ambiguitas berujung otomatis ke K.

### 2.3.2 Tahap B punya dua implementasi, dan keduanya diukur

PRD versi sebelumnya menuliskan Tahap B sebagai heuristik if-then, sementara
rencana spike mengimplementasikannya sebagai `claude-opus-5` dengan satu PNG
per langkah. Dua hal itu berbeda jauh dalam biaya, kecepatan iterasi, dan
kemampuan diuji — dan PRD tidak boleh menggantung di antara keduanya.

**Keputusan: Tahap B adalah satu antarmuka dengan dua implementasi
tertukar.**

| Implementasi | Sifat | Peran |
|---|---|---|
| `tinta_heuristik` | Aturan murni atas turunan waktu (§2.2), deterministik, tanpa biaya, jalan offline | **Baseline wajib.** Selalu dijalankan. |
| `tinta_llm` | Render PNG per langkah + ringkasan waktu → model (spike: `claude-opus-5`) | Dijalankan berdampingan, bukan menggantikan |

Gerbang §2.7 diukur untuk **keduanya, atas data sesi yang sama**. Kalau
heuristik murni sudah ≥7/10 dan nol false-K, `tinta_llm` tidak perlu masuk
v1 sama sekali — dan itu penghematan yang hanya bisa dibuktikan kalau
baseline-nya ada. Kalau heuristik gagal, angka selisih kedua implementasi
adalah pembenaran konkret untuk biaya LLM, bukan asumsi. Tanpa baseline,
pertanyaan "apakah LLM-nya perlu?" tidak punya cara dijawab.

### 2.4 Pustaka malrule tumbuh dari pemakaian, bukan ditulis sekali di depan

Setiap kali orang tua mengoreksi `kode_awal` jadi `kode_final` yang berbeda
untuk sebuah jawaban salah yang belum tertangkap malrule mana pun, itu adalah
kandidat entri baru. Yang "dinaikkan" founder ke pustaka permanen adalah
**malrule (fungsi prediksi + template yang berlaku)**, bukan pasangan literal
`(soal, jawaban_salah)` — konsisten dengan §2.3.1.

Langkah promosinya jadi sedikit lebih menuntut dari sekadar menyalin baris,
dan itu memang disengaja: founder harus merumuskan *aturan salah* yang
menjelaskan jawaban itu (mis. "pembilang & penyebut dijumlahkan
sendiri-sendiri"), lalu menyatakannya sebagai fungsi. Imbalannya sepadan —
satu perumusan berlaku ke seluruh soal bertemplate sama, sekarang dan yang
dibangkitkan nanti untuk verifikasi (§4.3 prioritas 1), bukan cuma ke satu
soal yang kebetulan muncul.

Pengaman promosi: sebuah malrule kandidat baru boleh masuk pustaka hanya
kalau ia **tidak mengubah `kode_awal` pada riwayat kejadian yang sudah
ditinjau** menjadi bertentangan dengan `kode_final` yang sudah diputuskan
orang tua. Ini bisa diperiksa otomatis karena data mentah disimpan permanen
(§7.3) dan status bersifat turunan (§8.4) — cukup replay pustaka baru atas
seluruh riwayat dan bandingkan. Malrule yang terlalu longgar (menangkap
jawaban yang dulu dinilai H jadi K) tertangkap di sini, sebelum dipakai ke
anak.

Pola ini sama dengan §1.3 (resep AI-generated yang layak naik kelas jadi
pra-tulis) — dua bagian PRD ini memakai mekanisme pertumbuhan konten yang
sama secara sengaja, supaya tidak ada dua cara berbeda untuk hal yang sama.

### 2.5 Bentuk data satu hasil diagnosis

```
soal_id
template_id                 # §2.3.1 — soal adalah template+parameter
parameter                   # angka konkret yang dilihat anak
jawaban_anak
kode_awal: B | K | H | tidak_pasti
tahap_asal: malrule | tinta_heuristik | tinta_llm
malrule_id                  # terisi hanya kalau tahap_asal = malrule
alasan_singkat              # kenapa sistem menebak begitu — ditampilkan ke orang tua saat tinjauan
aturan_versi                # versi pustaka malrule + heuristik yang dipakai
prompt_versi                # null kalau tahap_asal bukan tinta_llm
model                       # null kalau tahap_asal bukan tinta_llm
kode_final: B | K | H       # diisi orang tua, wajib sebelum dihitung ke manapun
```

Tiga field jejak (`aturan_versi`, `prompt_versi`, `model`) bukan hiasan:
Peta Jalan menetapkan **batas maksimal 3 putaran perbaikan prompt** di zona
abu-abu supaya tidak diam-diam overfitting ke 10 soal satu anak. Batas itu
tidak bisa ditegakkan — bahkan tidak bisa dihitung — kalau tiap hasil
diagnosis tidak membawa identitas aturan/prompt yang menghasilkannya. Karena
diagnosis bersifat batch dan boleh diulang di atas data yang sama (§2.6),
tanpa field ini riwayat jadi campuran beberapa generasi aturan yang tidak
bisa dipisahkan lagi.

Untuk `tinta_llm`, respons di-cache berkunci hash dari
`(data mentah soal + prompt_versi + model)`. Iterasi prompt yang tidak
mengubah ketiganya membaca cache, bukan memanggil API ulang — putaran
perbaikan jadi murah, dan angka gerbang §2.7 selalu bisa direproduksi persis.

### 2.6 Sifat batch, bukan real-time

Sejalan dengan arsitektur spike: aplikasi Android hanya merekam ke JSON
selama sesi anak berlangsung. Diagnosis (Tahap A+B) dan tinjauan (Tahap C)
terjadi **setelah** sesi selesai, lewat skrip terpisah — bukan live saat anak
masih memegang HP. Ini bukan keterbatasan teknis yang perlu ditutup nanti,
ini keputusan sengaja: kunci jawaban & diagnosis tidak boleh tersentuh anak
saat sesi berlangsung (kriteria uji dari §1 memory produk), dan prompt/aturan
Tahap B bisa diiterasi berkali-kali di atas data yang sama tanpa melibatkan
anak lagi.

Janji terakhir itu ("diiterasi berkali-kali di atas data yang sama") punya
syarat penyimpanan yang tidak boleh dilanggar: data mentah disimpan permanen
(§7.3) **dan** status topik tidak pernah ditimpa di tempat (§8.4). Kalau salah
satunya tidak dipenuhi, iterasi kedua kehilangan basis pembanding dan sifat
batch ini kehilangan manfaat utamanya. Perintah `osn replay` (§8.7) adalah
bentuk konkret janji ini.

### 2.7 Kriteria lulus (dari spike, dibawa jadi acceptance criteria v1)

Diukur **terpisah untuk `tinta_heuristik` dan `tinta_llm`** (§2.3.2), atas
data sesi yang sama:

- ≥7 dari 10 `kode_final` (setelah tinjauan orang tua terhadap `kode_awal`)
  cocok dengan penilaian orang tua yang independen.
- Nol kasus `kode_awal` = K padahal kebenarannya H — asimetri di §2.1 diuji
  langsung di sini, bukan cuma prinsip di atas kertas.

Aturan keputusan atas dua angka itu:
- Kalau `tinta_heuristik` sudah lolos keduanya → `tinta_llm` **keluar dari
  lingkup v1**; Tahap B jalan tanpa biaya dan tanpa jaringan.
- Kalau hanya `tinta_llm` yang lolos → selisihnya adalah pembenaran biaya
  LLM, dan `tinta_heuristik` tetap dipertahankan sebagai pembanding regresi
  tiap kali prompt berubah.
- Kalau keduanya gagal → yang gugur adalah kanal tinta, bukan produknya
  (Tahap A malrule + tinjauan orang tua masih berdiri sendiri).

## 3. Graf Topik & Prasyarat

Bagaimana peta 20 minggu di `KurikulumFondasiMatematikaOSNSD2027.pdf`
di-decompile jadi graf, sesuai keputusan lama: bukan kurikulum berkalender,
penggeraknya kondisi anak.

### 3.1 Prinsip: decompile, bukan tulis ulang

Modul sumbernya sudah terstruktur rapi per sel **(jalur, minggu)** — tiap sel
sudah berisi tujuan belajar, "Bekal untuk Bapak", contoh soal, dan 3 latihan.
Isi ini **dipakai langsung**, bukan ditulis ulang. Yang dibuang cuma satu
lapisan: pemetaan sel ke hari-kalender-tertentu (Senin/Selasa/Rabu/Kamis,
tanggal 24-30 Agustus dst). Yang dipertahankan sebagai **default**: urutan
minggu di dalam satu jalur, karena itu representasi keputusan pedagogis
penyusun modul, bukan artefak kalender.

### 3.2 Node = satu sel (jalur, minggu)

```
topik_id
jalur: bilangan | geometri | kombinatorik-logika | aritmatika-statistika-pengukuran
urutan_asal        # nomor minggu asli (M1..M16) — dipakai sebagai HINT urutan
                    # default, bukan jadwal. Lihat 3.3.
tujuan              # "Anak menyelesaikan operasi campuran tanpa keliru urutan." dst — sudah ada di PDF
bekal_untuk_bapak   # dipakai LANGSUNG sebagai konten resep K, lihat §1.3
contoh_soal         # dipakai untuk sesi "bahas bersama"
latihan             # 3 soal — disimpan sebagai template+parameter (§2.3.1),
                    #   sekaligus bahan awal pustaka malrule (§2.4) begitu dikerjakan
tingkat_tersedia    # [1,2,3] — tingkat soal yang ada untuk node ini; "OSN" tidak
                    #   pernah jadi field/nilai, ia kesimpulan dari tingkat (Peta Jalan §01)
```

Catatan: `status` **tidak** disimpan di sini. Node graf adalah konten
(immutable, versi terkontrol); status tiap node adalah turunan dari riwayat
kejadian — lihat §8.4. Ini perubahan dari draf sebelumnya yang menempelkan
`status` ke dalam node.

Field `bekal_untuk_bapak` inilah yang mengisi celah §1.3 lebih cepat dari
dugaan awal — bukan cuma 14 topik dari Tes Kalibrasi Minggu 0, tapi berpotensi
sebanyak node yang berhasil di-decompile dari modul (~16 minggu × 4 jalur =
kandidat 64 node untuk Fase A+B saja). Tetap perlu ditinjau satu per satu
sebelum dipakai (lihat 3.7 soal kesesuaian usia), tapi ini bahan baku siap
pakai, bukan harus ditulis dari nol.

### 3.3 Edge (prasyarat): linear di dalam jalur secara default, lintas-jalur ditinjau manual

Aturan default: dalam satu jalur, `urutan_asal` minggu ke-n mensyaratkan
minggu ke-(n-1) di jalur yang sama selesai. Ini asumsi kerja yang wajar
karena modul sumber memang disusun bertahap per jalur (mis. Jalur 1: urutan
operasi → sifat operasi → ciri keterbagian → ... → pecahan), tapi **bukan
kebenaran mutlak** — tidak semua topik benar-benar butuh SEMUA topik
sebelumnya di jalur yang sama, dan beberapa mungkin justru butuh topik dari
jalur lain (mis. pecahan di Jalur 1 mungkin relevan untuk "perbandingan
senilai" di Jalur 4). Prasyarat lintas-jalur **tidak diinfer otomatis di
v1** — ditambahkan manual saat konten ditinjau, bukan tugas arsitektur
sekarang.

### 3.4 Empat jalur = kategori konten independen, bukan hari

`jalur` jadi properti topik, bukan pemicu jadwal. Ini sengaja memutus
pemetaan asli "Senin=Jalur1, Selasa=Jalur2, dst" — realistis 3 sesi/minggu
(sudah disepakati di memory produk) tidak muat untuk 4 jalur/minggu seperti
rencana aslinya. **Bagaimana sesi berikutnya memilih jalur mana yang
dikerjakan** (round-robin, prioritas jalur dengan K aktif, dst) belum
diputuskan di sini — itu logika rekomendasi, bagian PRD tersendiri (lihat
Bagian 4).

### 3.5 Fase (Fondasi/Naik Level/Konsolidasi) = label tampilan, bukan gerbang

Fase A/B/C di modul sumber kemungkinan besar berguna sebagai pengelompokan
kasar untuk laporan ke orang tua ("anak sudah di area Fase B") — tapi bukan
mekanisme pemblokiran terpisah dari graf. Kalau prasyarat topik sudah
terpenuhi, topik itu tersedia, tidak peduli fase aslinya di modul.

### 3.6 Yang BUKAN node di graf

Sel "Jumat — bedah kesalahan" dan "Sabtu — tryout campuran" di modul sumber
bukan topik baru, jadi bukan node prasyarat. Ini tipe *aktivitas sesi* yang
menyilang banyak topik sekaligus (bedah kesalahan = revisit topik yang
salah; tryout = campuran semua jalur). Begitu juga M19-20 ("latihan
campuran", "tryout dan rekap") — bukan konten baru, jadi tidak di-decompile
jadi node. Keduanya lebih cocok jadi mekanisme di lapisan sesi/rekomendasi
(Bagian 4), bukan bagian dari graf topik itu sendiri.

### 3.7 Gap konten yang belum tertutup: pra-fondasi di bawah M1

Modul sumber mengasumsikan titik mulai "kemampuan rata-rata" (lihat halaman
sampul: *"Titik mulai: Kemampuan rata-rata, motivasi ada"*) — M1 langsung
mulai dari "urutan operasi hitung", mengasumsikan operasi dasar (7×8, 72:8,
dst) sudah otomatis. Tes Kalibrasi & Uji Ulang Lisan sendiri sudah
mengantisipasi kasus ini tapi **belum menyediakan kontennya**: cabang
"di bawah 9" dan "Bagian 1 banyak salah" cuma bilang "tunda 4-8 minggu,
mantapkan operasi dasar" tanpa "Bekal untuk Bapak" tertulis untuk minggu-
minggu itu. Ini persis lapisan pra-fondasi yang sudah diidentifikasi di
memory produk sejak awal (anak kelas 4, bukan kelas 5) — statusnya di sini
dikonfirmasi ulang: **belum ada satu pun node teratur untuk lapisan ini**,
harus ditulis baru sebelum root graf yang sekarang (M1 tiap jalur) bisa jadi
titik mulai yang aman untuk anak kelas 4. (Lihat §5.4 untuk keputusan cara
v1 menangani anak yang jatuh ke kondisi ini sebelum konten itu ditulis.)

## 4. Alur Sesi & Rekomendasi

Bagian yang sengaja ditunda dari §3.4: begitu graf dan status tiap topik ada,
apa yang sebenarnya disodorkan ke orang tua saat mereka membuka aplikasi?

### 4.1 Prinsip: non-kalender tetap, satu fokus per sesi

Modul sumber memberi satu topik per hari (bekal + contoh + 3 latihan,
45-60 menit). Pola **satu topik/aktivitas per sesi** dipertahankan — bukan
mencampur beberapa topik dalam satu duduk — karena ini yang sudah terbukti
jalan di modul asli dan cocok dengan aturan "berhenti tepat waktu, bahkan
saat sedang lancar" (Bagian 1, Panduan Memakai Modul). Yang diubah cuma
**apa yang mengisi slot itu**: bukan lagi ditentukan hari-dalam-minggu,
tapi ditentukan status graf saat sesi dimulai.

### 4.2 Kapan sesi terjadi

Orang tua yang memulai sesi kapan pun siap (~30-40 menit, 3x/minggu
realistis). Sistem tidak mendorong jadwal, tidak ada pengingat/notifikasi
yang memaksa — konsisten dengan "bolong 2 minggu tidak menimbulkan utang
sesi" dan dengan tidak adanya infrastruktur push notification di spike
(tanpa izin INTERNET).

### 4.3 Prioritas pemilihan aktivitas sesi

Saat sesi dimulai, sistem mengevaluasi urutan berikut dan menyajikan slot
tunggal untuk prioritas tertinggi yang berlaku:

| # | Kondisi pemicu | Aktivitas slot |
|---|---|---|
| 1 | Ada topik `menunggu_verifikasi` yang sudah jatuh tempo (≥3 hari sejak resep) | Uji ulang topik itu — **template sama, parameter diacak ulang** (§2.3.1), sehingga malrule Tahap A tetap berlaku dan verifikasi tidak kehilangan lapisan deterministik |
| 2 | Ada topik `masih_bermasalah` (verifikasi gagal 2x, lihat §1.6) | Eskalasi: cek prasyarat atau jalankan Uji Ulang Lisan (§4.5) |
| 3 | Ada topik `resep_diberikan` yang aktivitas remediasinya (K) belum dijalankan | Sesi remediasi K — ikuti `tindakan` dari resep, biasanya kerja dengan benda nyata, bukan latihan soal biasa |
| 4 | Tidak ada di atas | Topik baru di frontier graf (semua prasyarat `selesai`) — pilih dari **jalur yang paling lama tidak disentuh**, bukan round-robin kaku, supaya 4 jalur tetap merata meski cuma 3 sesi/minggu |
| 5 | Sejumlah topik sudah `selesai` sejak tryout campuran terakhir (ambang, bukan tanggal) | Tryout campuran / bedah kesalahan — pengganti ritme Jumat/Sabtu asli, dipicu kondisi bukan hari |

Prioritas 1-2 didahulukan karena itu loop yang sudah terbuka (menunda hanya
menambah utang keterangan); prioritas 4 baru membuka loop baru.

### 4.4 B dan H tidak butuh slot sendiri — K dan verifikasi butuh

Remediasi B (teknik baca soal) dan H (kebiasaan periksa ulang) adalah teknik
yang **ditempel ke sesi topik apa pun** yang sedang berjalan sampai hilang
sendiri (2-3 minggu untuk B; H malah tidak butuh jeda materi sama sekali,
lihat §1.2) — tidak perlu baris prioritas terpisah di atas. Hanya K yang
butuh slot berdedikasi, karena `tindakan`-nya (benda nyata, 4-6 minggu)
secara nyata beda aktivitas dari latihan soal biasa.

### 4.5 Uji Ulang Lisan: dua pemicu, bukan satu

Dari `Uji Ulang Lisan - Tindak Lanjut.pdf`, tujuannya memisahkan "tidak
bisa" dari "tidak dikerjakan". Dua kondisi yang memicunya (di luar konteks
onboarding — untuk pemicu khusus onboarding, lihat §5.5):

1. **Level topik** — eskalasi dari §1.6 / baris 2 tabel di atas: K gagal
   verifikasi 2x dan prasyaratnya sudah kokoh.
2. **Level sesi** — anak menyelesaikan sesi jauh lebih cepat dari
   kebiasaannya sendiri (bukan angka mutlak — dibandingkan riwayat durasi
   anak itu sendiri, karena kecepatan wajar beda-beda per anak). Ini sinyal
   langsung dari PDF sumber ("anak yang mengisi seluruh soal tertulis lalu
   selesai jauh lebih cepat dari waktunya biasanya bukan tidak mampu — ia
   hanya tidak berhenti untuk menghitung") dan bisa dideteksi dari data
   waktu yang sudah dikumpulkan di §2.2, tanpa sinyal baru.

### 4.6 Rekomendasi menunggu tinjauan orang tua, bukan data mentah

Karena diagnosis bersifat batch (§2.6), status graf yang dipakai algoritma
4.3 adalah status dari `kode_final` yang **sudah ditinjau**, bukan
`kode_awal` mentah dari sesi terakhir. Kalau orang tua belum sempat
menjalankan skrip dan meninjau sesi sebelumnya, sistem tidak memaksa maju
dengan data tak-tertinjau — pilihan yang aman adalah sesi netral (tryout
campuran atau latihan bebas topik yang sudah lama `selesai`) yang tidak
bergantung pada status K/verifikasi terbaru, sampai tinjauan selesai.

## 5. Onboarding & Kalibrasi Awal

### 5.1 Prinsip: kalibrasi dulu, graf belakangan

Anak tidak pernah masuk ke graf topik (§3) dengan node kosong berstatus
`belum_dicoba` semua. Tes Kalibrasi tertulis 20 soal (60 menit, di atas
kertas — lihat §5.5 kenapa ini penting) adalah langkah wajib pertama,
sebelum satu pun sesi digital dimulai. Hasilnya bukan sekadar "boleh mulai
atau tidak" — ia menentukan *starting_point* per jalur dan mengisi
node-node yang bersinggungan dengan 20 soal itu dengan data nyata, bukan
status kosong. Ini konsisten dengan §2.3: 20 soal ini adalah sumber
**template + malrule** pertama untuk Tahap A (§2.3.1), jadi kalibrasi awal
dan seed diagnosis Tahap A adalah satu aktivitas, dua manfaat. Karena yang
di-seed adalah template (bukan 20 soal literal), cakupan Tahap A yang lahir
dari kalibrasi langsung berlaku juga ke soal-soal kurikulum bertemplate sama
— termasuk soal verifikasi yang diparametrisasi ulang nanti.

### 5.2 Alur end-to-end

1. **Tes Kalibrasi tertulis** (di luar app, di atas kertas, 60 menit, tanpa
   pendampingan — persis instruksi PDF).
2. **Skoring** oleh orang tua pakai kunci jawaban, dilakukan setelah anak
   tidak di ruangan. Skor mentah 0-20 dicatat ke app.
3. **Kategori & starting_point ditentukan otomatis** dari skor (tabel §5.3),
   tapi belum dikunci — lihat langkah 4-5.
4. **Cek pemicu Uji Ulang Lisan onboarding** (§5.5) — kalau terpicu,
   dijalankan sebelum starting_point dikunci.
5. **Wawancara sepuluh menit**, besok/lusa (bukan hari yang sama): 3-4 soal
   salah dipilih, orang tua input kode_awal B/K/H per soal ke app (§5.6).
   Ini yang menyalakan pustaka malrule (§2.4) untuk pola kesalahan yang
   belum pernah tercatat. Wawancaranya memakai **protokol 5-prompt NEA**
   ("Baca soal ini" → "Ceritakan apa yang diminta" → "Tunjukkan bagaimana
   kamu dapat jawabannya" → "Kerjakan sambil dijelaskan" → "Tulis
   jawabannya"), bukan pertanyaan bebas — sesuai penyesuaian yang sudah
   ditetapkan di Peta Jalan §04.
6. **App mengunci `kalibrasi_awal`** dan menginisialisasi status node graf
   yang bersinggungan dengan 20 soal kalibrasi (lihat §5.6). Node lain di
   luar 20 soal tetap `belum_dicoba` seperti biasa.
7. **Sesi pertama** diambil lewat prioritas §4.3 seperti biasa — kalibrasi
   hanya menentukan *dari mana* frontier itu mulai, bukan jalur khusus di
   luar mesin rekomendasi yang sudah ada.

### 5.3 Skor → kategori → starting_point & tempo

| Skor | Kategori | starting_point per jalur | tempo (efek ke §4.3 prioritas 4) |
|---|---|---|---|
| 17-20 | kokoh | M1 tiap jalur, tempo penuh | frontier maju normal; boleh selipkan 1 soal ekstra per sesi |
| 13-16 | normal | M1 tiap jalur | frontier maju normal, tanpa perubahan |
| 9-12 | lubang-dasar | M1 tiap jalur | frontier **separuh**: topik baru butuh 2x hitungan `selesai` terverifikasi sebelum topik berikut dibuka (menggantikan "M1-4 dikerjakan 2 minggu" versi non-kalender) |
| < 9 | belum-siap | **bukan M1** — masuk jalur pra-fondasi (§5.4) | frontier tertutup sampai gate pra-fondasi lulus |

Untuk kategori kokoh/normal/lubang-dasar, node graf yang **bersinggungan**
dengan salah satu dari 20 soal kalibrasi tidak dimulai dari `belum_dicoba` —
statusnya diisi langsung dari hasil kalibrasi (lihat §5.6), sisanya (topik
di luar 20 soal itu) tetap `belum_dicoba` normal.

### 5.4 Keputusan: gap pra-fondasi (skor <9 atau Bagian 1 Uji Ulang Lisan "banyak salah")

§3.7 sudah mengonfirmasi: belum ada satu pun node graf tertulis untuk
lapisan di bawah M1. Keputusan v1: **tidak blocking, tidak juga dipaksa
masuk M1 — dibuka mode pra-fondasi non-graf yang AI-generate sejak hari
pertama**, dengan gate keluar berbasis kondisi bukan tanggal. Alasannya,
dipetakan ke prinsip yang sudah ada:

- **Kenapa bukan blocking penuh ("app belum siap dipakai")**: app ini
  satu-keluarga, orang tua = founder = operator. Menutup app total selama
  4-8 minggu berarti tidak ada yang menopang 3 sesi/minggu yang tetap harus
  jalan di dunia nyata — bertentangan dengan alasan app ini dibuat.
  Blocking juga tidak konsisten dengan pola yang sudah dipakai di §1.3:
  AI-generate-on-the-fly sudah diizinkan untuk konten yang sifatnya
  prosedural (B, H), dan drilling operasi dasar (perkalian/pembagian
  bersusun) jauh lebih dekat ke H (kelancaran prosedural) daripada K (butuh
  benda nyata + pemahaman konsep) — jadi tidak perlu menunggu pustaka
  pra-tulis seperti K.
- **Kenapa bukan langsung dipaksa M1**: PDF eksplisit — "melanjutkan tanpa
  ini hanya membuat anak frustrasi". Memaksa M1 tanpa fondasi melanggar
  guardrail "tidak boleh membuat anak frustrasi" yang sudah jadi salah satu
  dari tiga uji keputusan teknis di PRD ini.
- **Bentuk konkret v1**: sesi pra-fondasi dibangkitkan AI on-the-fly,
  berbasis bentuk soal Bagian 1 Uji Ulang Lisan (perkalian/pembagian dasar,
  tanpa timer, boleh bersusun/pakai jari) — bukan node topik permanen di
  graf (tidak punya `topik_id`, tidak dicatat B/K/H per §3.2/§1.4), cukup
  dicatat sebagai sesi dengan skor drill ringan (benar/salah per soal, tanpa
  klasifikasi B/K/H karena bukan kesalahan konsep yang perlu didiagnosis,
  murni kelancaran fakta dasar).
- **Gate keluar — kondisi, bukan kalender**: bukan "tunggu 6 minggu lalu
  otomatis buka M1". Orang tua yang memutuskan kapan mengulang cek ringan
  (subset item operasi dasar, atau ulang Bagian 1 Uji Ulang Lisan) — kalau
  lancar, jalur pra-fondasi ditutup dan starting_point M1 dibuka normal per
  §5.3; kalau belum, sesi pra-fondasi berlanjut. PDF menyarankan 4-8 minggu
  sebagai perkiraan durasi wajar, dipakai sebagai *saran tampilan*, bukan
  gate otomatis — konsisten dengan prinsip non-kalender dan human-in-the-loop
  (orang tua tetap wasit akhir, sama seperti kode_final di §2.1).
- **Jejak audit**: field `sumber: pra-fondasi-ai-generated` dicatat di
  riwayat anak supaya kelak, kalau founder menulis node pra-fondasi permanen
  (sesuai catatan terbuka di §3.7), riwayat ini bisa dipetakan ulang — sama
  seperti pola "naik kelas" di §2.4/§1.3.

### 5.5 Uji Ulang Lisan khusus titik onboarding

Dua pemicu di §4.5 (eskalasi topik gagal verifikasi 2x, dan sesi selesai
jauh lebih cepat dari kebiasaan anak) tidak berlaku langsung saat onboarding
— belum ada "kebiasaan" untuk dibandingkan. Titik onboarding punya dua
pemicu sendiri, sesuai anjuran PDF sumber ("dipakai kalau hasil tertulis
meragukan"):

1. **Skor di perbatasan kategori**: skor mentah 8, 9, 12, 13, 16, atau 17
   (persis di garis batas §5.3) — selisih satu soal mengubah cabang
   tempo/pra-fondasi secara drastis, terlalu berisiko dikunci dari satu
   titik data.
2. **Waktu pengerjaan mencurigakan**: orang tua melaporkan anak selesai
   jauh di bawah alokasi 60 menit (app tidak bisa mengukur ini otomatis
   karena tes di atas kertas, jadi ini input manual — checkbox "anak
   terlihat terburu-buru/menebak" saat input skor).

Kalau salah satu terpicu: Uji Ulang Lisan penuh (12 soal, 4 bagian)
dijalankan sebagai langkah 4 di alur §5.2, **sebelum** starting_point
dikunci. Hasil Bagian 1 dipakai untuk disambiguasi kategori (tabel hasil
sudah ada di dokumen sumber: Bagian 1 lancar/hampir-benar → tetap masuk M1
dengan aturan "wajib tulis langkah + periksa ulang" ditempel ke sesi;
Bagian 1 banyak salah/sangat lama → dialihkan ke mode pra-fondasi §5.4
terlepas dari skor tertulisnya). Wawancara sepuluh menit (§5.2 langkah 5)
tetap jalan terpisah — perannya beda, mengisi kode B/K/H per soal, bukan
menentukan kategori.

### 5.6 Skema data hasil kalibrasi awal

```
kalibrasi_awal:
  tanggal
  skor_mentah: 0-20
  kategori: kokoh(17-20) | normal(13-16) | lubang-dasar(9-12) | belum-siap(<9)
  tempo: penuh | normal | separuh | tunda-ke-pra-fondasi
  uji_ulang_lisan_dipakai: boolean
  uji_ulang_lisan_alasan: skor-perbatasan | selesai-terlalu-cepat | null
  starting_point:
    bilangan: topik_id | "pra-fondasi"
    geometri: topik_id | "pra-fondasi"
    kombinatorik-logika: topik_id | "pra-fondasi"
    aritmatika-statistika-pengukuran: topik_id | "pra-fondasi"
  catatan_soal_kalibrasi: [
    { soal_id, topik_id, jawaban_anak, benar: boolean,
      kode_awal: B|K|H|null,          # null kalau benar dan tidak diwawancara
      sumber_kode: wawancara-10-menit | uji-ulang-lisan | null,
      kode_final: B|K|H|null }        # wajib diisi orang tua sebelum dihitung ke §1.5/§1.6
  ]
```

Efek ke graf saat dikunci (langkah 6, §5.2): untuk tiap baris
`catatan_soal_kalibrasi` yang punya `topik_id` (pemetaan statis
soal→node, dibuat sekali saat digitisasi) — kalau `benar`, node itu tidak
otomatis `selesai` (anti "Correct Answer Trap", §1.2), cukup ditandai sudah
punya bukti awal dan masuk giliran verifikasi lebih dini; kalau salah, node
itu langsung ke status `ditandai(kode_final)` → `resep_diberikan`,
melompati `belum_dicoba`/`dicoba` karena bukti nyata sudah ada. Node graf
yang tidak tersentuh 20 soal kalibrasi tetap `belum_dicoba`, ditemukan lewat
prioritas 4 §4.3 seperti biasa.

Mekanismenya (§8.4): "mengunci kalibrasi" berarti **meng-append satu kejadian
`kalibrasi_dikunci`** berisi seluruh isi skema di atas ke `events.jsonl`, lalu
menjalankan `derive`. Tidak ada status yang dituliskan langsung ke node graf —
efek yang diuraikan di paragraf sebelumnya adalah hasil `derive` atas kejadian
itu, bukan operasi tulis terpisah. Konsekuensi praktisnya: kalau pemetaan
soal→node ternyata perlu dikoreksi kelak, kalibrasi bisa dihitung ulang tanpa
mengulang tes ke anak.

## 6. Input Tulisan Tangan & Kanvas

### 6.1 Pembukaan kanvas baru: tombol manual, bukan deteksi otomatis

**Keputusan: kanvas baru dibuka lewat tombol "Langkah Baru →" yang ditekan
anak sendiri — bukan deteksi otomatis baris kerja baru.**

Alasan, tiga hal sekaligus:
- Anak kelas 4 memegang HP pinjaman orang tua. UI harus serendah mungkin
  kompleksitasnya dan hasilnya harus bisa diprediksi — satu tombol, satu
  aksi, satu akibat.
- Auto-detect (mis. mendeteksi anak sudah "pindah baris" dari posisi pena)
  butuh heuristik yang bisa meleset. Kesalahan deteksi menambah kanvas palsu
  atau menggabung dua langkah jadi satu — itu noise langsung ke sinyal §2.2
  (jeda, urutan kanvas disentuh), padahal diagnosis Tahap B butuh sinyal
  bersih. Noise di sini tidak bisa diperbaiki belakangan karena tidak ada
  OCR yang bisa mengoreksi secara post-hoc.
- Tombol manual menambah sedikit friksi (anak harus ingat menekan sebelum
  lanjut), tapi capture-nya presisi 100% dan tidak butuh model/ML tambahan
  apa pun — konsisten dengan prinsip §2.1: v1 sengaja tidak butuh OCR/ML
  sama sekali.

Perilaku tombol: menekan "Langkah Baru" menyegel kanvas aktif (goresan
setelahnya tidak lagi tercatat ke kanvas itu; anak masih bisa menggulir
mundur untuk melihat, tapi tidak mengedit) dan membuka kanvas kosong
berikutnya. Waktu penyegelan dan waktu pembukaan kanvas baru keduanya
dicatat sebagai timestamp — ini yang mengisi kolom "waktu antar-goresan per
kanvas" di §2.2 pada batas antar-langkah.

### 6.2 Tiga bentuk jalur — pemetaan ke soal kurikulum

Bentuk kanvas **bukan** dideteksi saat runtime. Bentuk ditentukan oleh
**field pada data soal** (bagian dari skema topik §3, dikurasi saat konten
soal ditulis), sehingga saat sesi dimulai app sudah tahu persis kanvas apa
yang harus disodorkan untuk soal itu — tidak ada logika "menebak" bentuk
dari isi soal.

| Bentuk kanvas | Cara kerja | Soal konkret dari kurikulum |
|---|---|---|
| **Berlangkah** | Kanvas berurutan, dibuka satu-satu lewat tombol §6.1; satu kanvas = satu langkah kerja hitung | Jalur 1: "Urutan operasi hitung" (48 − 12 × 3 + 20 : 4, dikerjakan bersusun/berlangkah). Jalur 4: konversi satuan (2,5 m³ + 400 dm³ = ... liter), setiap konversi antara jadi satu kanvas |
| **Gambar bebas** | Satu kanvas kosong, tanpa tombol "Langkah Baru" — seluruh soal adalah satu gambar utuh, anak menggambar sesukanya di satu bidang | Jalur 2: "Sudut dan hubungannya" (gambarkan dua sudut saling berpelurus lalu hitung besarnya), "Segitiga dan jumlah sudutnya". Jalur 3: "Diagram pohon" |
| **Daftar berbaris** | Kanvas dengan baris-baris kosong; tombol "Baris Baru" (varian tombol §6.1 khusus jalur ini) menambah baris; satu baris = satu entri daftar | Jalur 3: "Mendaftar secara sistematis" — soal "daftarkan terurut: 12, 13, 21, 23, 31, 32" — tiap dua-angka yang didaftar anak jadi satu baris |

Catatan konsistensi: "gambar bebas" adalah satu-satunya bentuk yang **tidak**
memakai konsep langkah dari §6.1 sama sekali — geometri dan diagram pohon
secara alami satu kesatuan visual, memaksa segmentasi langkah di situ hanya
menambah friksi tanpa manfaat diagnosis. "Daftar berbaris" memakai
mekanisme tombol yang identik dengan §6.1 (tekan → baris disegel → baris
baru terbuka), hanya beda label dan beda satuan capture (baris, bukan
kanvas penuh) — ini tetap tunduk pada keputusan yang sama di §6.1 dan bukan
pengecualian arsitektur baru.

### 6.3 Dari interaksi UI ke sinyal mentah §2.2

Capture UI ini **tidak menganalisis apa pun** — ia hanya mencatat event
mentah, persis lima baris tabel §2.2, tanpa membaca isi goresan:

- **Waktu antar-goresan per kanvas**: setiap sentuh-tahan-lepas pena di
  kanvas adalah satu event stroke dengan timestamp mulai (jari/stilus
  menyentuh layar) dan timestamp selesai (terangkat). Deretan event ini per
  kanvas menghasilkan kolom "waktu antar-goresan".
- **Jumlah & titik koreksi/coretan**: tombol hapus/coret di toolbar kanvas,
  saat ditekan, menghasilkan satu event hapus dengan timestamp dan (kalau
  anak mencoret area tertentu, bukan hapus-semua) koordinat area yang
  dicoret. Jumlah event ini per kanvas = "jumlah koreksi"; koordinatnya =
  "titik koreksi".
- **Urutan kanvas disentuh**: setiap kali fokus interaksi berpindah —
  menekan "Langkah Baru"/"Baris Baru", menggulir balik ke kanvas sebelumnya
  untuk melihat, atau berpindah ke field jawaban akhir (§6.4) — dicatat
  sebagai satu entri log dengan kanvas_id/field_id dan timestamp. Barisan
  log ini menghasilkan "urutan kanvas disentuh", termasuk apakah anak
  menyentuh field jawaban akhir *sebelum* menyelesaikan langkah kerja
  (sinyal curiga menebak di §2.3 Tahap B).

Field kalibrasi jalur (§2.2 baris terakhir) otomatis terpenuhi karena tiap
event di atas sudah dicatat dengan bentuk-kanvas-nya (berlangkah/gambar
bebas/daftar berbaris) sebagai bagian dari kanvas_id — skrip diagnosis di
Mac tinggal membaca jalur itu untuk mengalibrasi heuristik, tanpa app perlu
tahu apa arti "ragu" per jalur.

### 6.4 Jawaban akhir: keyboard, terpisah dari kanvas kerja

Jawaban akhir diisi lewat **field ketik terpisah** (papan ketik numerik
untuk jawaban angka, papan ketik teks biasa untuk jawaban berupa
daftar/kata), diletakkan di posisi tetap di layar (mis. pita di bagian
atas, selalu terlihat di sepanjang seluruh kanvas kerja soal itu) — **bukan**
hasil pembacaan tulisan tangan di kanvas mana pun.

Ini menegaskan ulang §2.1: karena jawaban akhir adalah teks yang diketik
langsung, Tahap A diagnosis (pencocokan prediksi malrule, §2.3.1) berjalan
deterministik dan presisi 100% tanpa OCR apa pun. Tulisan tangan di kanvas kerja tidak
pernah dituntut untuk "dibaca" — perannya murni sebagai sumber waktu dan
geometri (§2.2), bukan sebagai sumber isi jawaban. Memisahkan field ini
dari kanvas juga menutup celah desain yang tergoda menambah OCR "supaya
praktis" di versi mendatang — jawaban akhir yang diketik sudah cukup dan
lebih akurat daripada OCR manapun.

### 6.5 Mode sesi sebagai kebutuhan UI

HP yang dipakai anak adalah **HP pinjaman orang tua**, bukan device anak
sendiri. Ini menuntut app punya state **"sesi aktif"** yang eksplisit di
lapisan UI — batas ini juga yang menentukan kapan paket sesi (§7.4) berlaku
dan kapan file JSON sesi (§2.6) ditutup:

- **Mulai sesi**: layar/tombol "Mulai Sesi" ditekan (oleh orang tua, sebelum
  HP diserahkan ke anak) — ini batas jelas kapan app mulai merekam ke file
  JSON sesi (§2.6). Sebelum titik ini, tidak ada capture sama sekali.
- **Akhir sesi**: layar/tombol "Selesai Sesi" — ditekan setelah semua soal
  pada sesi itu dijawab — ini batas jelas kapan app berhenti merekam dan
  file JSON sesi ditutup/disegel, siap dipindah ke Mac untuk diagnosis
  batch (§2.6).

Kebutuhan intinya: anak tidak boleh berada dalam keadaan ambigu "sedang di
app tapi tidak jelas sedang mengerjakan soal atau tidak" — UI harus selalu
tahu dan menunjukkan dengan jelas apakah sesi sedang berjalan atau tidak,
karena batas ini yang menentukan rentang waktu file JSON yang nanti dibaca
skrip diagnosis di Mac.

## 7. Data, Penyimpanan & Privasi

### 7.1 Prinsip privacy-by-default

Ini KEBIJAKAN produk, bukan cuma detail implementasi: **tidak ada cloud,
tidak ada API pihak ketiga, tidak ada data anak yang pernah meninggalkan
device+Mac keluarga itu sendiri**, di v1 maupun rencana selanjutnya kecuali
diputuskan ulang secara eksplisit. Keputusan "APK tanpa izin INTERNET"
(lihat §2.6 dan spike arsitektur) awalnya diambil supaya tidak ada API key
yang bisa diekstrak dari APK — di sini ditambahkan alasan kedua yang berdiri
sendiri: anak kelas 4 tidak punya cara memberi persetujuan berarti atas ke
mana data tulisan tangannya pergi, jadi defaultnya adalah data itu **tidak
pergi ke mana-mana**. Kedua alasan saling memperkuat keputusan yang sama,
tidak saling menggantikan — produk ini tetap offline-only walau salah satu
alasan hilang.

Konsekuensi kebijakan ini: tidak ada telemetry, tidak ada crash reporting
berbasis jaringan, tidak ada backup otomatis ke akun Google/cloud manapun
untuk file data anak (goresan, JSON sesi, hasil diagnosis). Detail komponen
yang menegakkan ini (permission manifest, penyimpanan lokal) ada di §8.

### 7.2 Siklus hidup data goresan mentah: HP → Mac

Data goresan+timestamp mentah (lihat skema di §2.6) tersimpan di HP **hanya
selama masa transit**, bukan sebagai arsip permanen di HP. Alasan: HP itu
**pinjaman orang tua**, dipakai juga untuk hal lain sehari-hari (bukan
device khusus anak) — data sensitif anak yang menumpuk di device serba-guna
itu tetap berisiko privasi walau cuma dalam satu keluarga (HP bisa dipakai
anggota keluarga lain, hilang, dijual, dipinjam lagi ke orang lain, dsb).

Keputusan: **file JSON goresan mentah dihapus dari HP segera setelah
berhasil dipindahkan dan terverifikasi terbaca oleh skrip Tahap A di Mac**
— bukan segera setelah sesi selesai (supaya tidak ada risiko kehilangan
data sebelum sempat dipindah), dan bukan dibiarkan menumpuk tanpa batas
waktu (supaya HP pinjaman tidak jadi gudang data anak). Mekanisme
verifikasi-lalu-hapus (USB/kabel, checksum, siapa yang memicu penghapusan)
adalah detail komponen — lihat §8. Yang menjadi keputusan kebijakan di sini
adalah: **HP bukan tempat penyimpanan jangka panjang untuk data apa pun
milik anak.**

### 7.3 Retensi jangka panjang data goresan mentah (di Mac)

Keputusan: data goresan mentah **disimpan permanen di Mac**, tidak dihapus
otomatis setelah `kode_final` terkonfirmasi.

Alasan eksplisit: §2.6 sudah menyatakan "prompt/aturan Tahap B bisa
diiterasi berkali-kali di atas data yang sama tanpa melibatkan anak lagi."
Ini secara langsung mensyaratkan data mentah tetap tersedia — kalau data
mentah dihapus setelah `kode_final`, iterasi algoritma diagnosis di masa
depan akan butuh anak mengerjakan ulang soal yang sama, yang bertentangan
dengan tujuan arsitektur batch ini.

Ukuran data (goresan + JSON, satu anak, bertahun-tahun sekolah dasar)
diperkirakan kecil dibanding kapasitas storage Mac modern — **retensi
permanen bukan concern v1**, dan tidak perlu mekanisme housekeeping/expiry
otomatis. Penghapusan data mentah di Mac hanya boleh terjadi lewat
**tindakan manual eksplisit orang tua** (misal storage Mac benar-benar jadi
masalah nyata suatu hari), tidak pernah otomatis oleh sistem. Selama tidak
ada tindakan manual itu, data mentah dianggap arsip permanen keluarga.

### 7.4 Kunci jawaban & diagnosis tidak pernah ada di HP — bukan soal akses, soal keberadaan

Screen Pinning bawaan Android tidak cukup sebagai kunci keras: tanpa status
device owner, anak masih bisa keluar lewat tombol kembali+recents kecuali
opsi "Minta PIN sebelum melepas sematan" dinyalakan manual di Pengaturan HP
— dan app tidak boleh berasumsi orang tua ingat menyalakan setting itu.

Tapi solusinya bukan membangun gerbang PIN di dalam app Android untuk
melindungi sebuah dashboard tinjauan — itu bertentangan dengan §8
(arsitektur v1 sengaja tidak punya UI review terpisah, semua tinjauan
terjadi lewat file di Mac, §8.3/§8.6). Keputusan yang lebih kuat dan lebih
sederhana: **kunci jawaban, kode_awal/kode_final, alasan diagnosis, dan
status graf topik tidak pernah dikirim ke HP sama sekali** — bukan
disembunyikan di balik PIN, tapi memang tidak pernah ada di device itu
secara fisik. "Tidak bisa disentuh anak" dipenuhi secara struktural, bukan
lewat kontrol akses yang bisa gagal.

Yang dikirim balik dari Mac ke HP sebelum sesi berikutnya (lewat kabel USB
yang sama, lihat §8.5) hanyalah **paket sesi**: topik_id yang direkomendasikan
(§4.3), daftar soal, dan jenis kanvas per soal (§6.2) — tanpa kunci
jawaban, tanpa kode B/K/H, tanpa alasan diagnosis apa pun. App Android
tidak perlu tahu jawaban benar suatu soal untuk menyajikannya; kebenaran
jawaban baru dicek nanti di Tahap A (§2.3), di Mac, dari jawaban yang
diketik anak.

Screen Pinning OS tetap dicoba diaktifkan saat Mode Sesi berjalan (§6.5)
sebagai lapisan tambahan — tapi perannya berubah: bukan lagi melindungi
rahasia (karena tidak ada rahasia di device), melainkan menjaga fokus anak
supaya tidak keluar ke app lain di tengah sesi di HP pinjaman orang tua.
Kalaupun gagal (anak berhasil keluar), yang paling buruk ter-expose adalah
soal-soal yang memang sedang ia kerjakan — bukan kunci jawaban atau
diagnosis apa pun.

### 7.5 Ringkasan klasifikasi data

| Data | Lokasi permanen | Boleh keluar device+Mac keluarga? | Terlihat ke anak? |
|---|---|---|---|
| Goresan+timestamp mentah | Mac (permanen, §7.3) — HP hanya transit (§7.2) | Tidak, tidak pernah (§7.1) | Tidak |
| `kode_awal`, `kode_final`, alasan_singkat | Mac saja — tidak pernah dikirim ke HP (§7.4) | Tidak | Tidak |
| Status graf topik per anak | Mac saja — tidak pernah dikirim ke HP (§7.4) | Tidak | Tidak |
| Resep remediasi B/K/H | Mac saja — tidak pernah dikirim ke HP (§7.4) | Tidak | Tidak — sesuai guardrail §1 |
| Paket sesi berikutnya (topik, soal, jenis kanvas — tanpa kunci jawaban) | HP, sementara per sesi (dikirim dari Mac, §7.4/§8.5) | Tidak | Ya — ini yang memang dikerjakan anak |

## 8. Arsitektur Teknis v1

### 8.1 Komponen v1

Enam komponen, tidak lebih:

```
1. App Android (capture-only)
   - TANPA android.permission.INTERNET (lihat spike, keputusan final)
   - Output: 1 file JSON per sesi — goresan (stroke+timestamp) + jawaban akhir yang diketik

2. Mekanisme pemindahan file (HP ↔ Mac, dua arah — lihat §8.2 & §8.5)
   - Kabel USB via adb; dibungkus orkestrator §8.7, bukan dijalankan tangan per sesi

3. Tool dekompilasi konten (SEKALI JALAN, bukan runtime)
   - Input: PDF kurikulum → output: node graf (§3.2) + template soal (§2.3.1)
   - Dipisah dari skrip runtime: jalan sekali per revisi konten, hasilnya
     di-commit sebagai konten (§8.4), bukan dihitung ulang tiap sesi

4. Skrip Python — Tahap A+B (§2.3)
   - Baca file JSON sesi
   - Jalankan malrule (A); kalau tidak ada yang cocok, jalankan Tahap B
     (tinta_heuristik selalu, tinta_llm bila masih dalam lingkup — §2.3.2)
   - Output: file tinjauan berisi kode_awal + alasan_singkat + jejak versi (§2.5)

5. Mekanisme tinjauan orang tua — Tahap C (§2.3)
   - File YAML per sesi, dibaca-edit langsung oleh founder di $EDITOR (§8.3)
   - Output: kode_final per soal, ditulis balik ke file tinjauan yang sama

6. Konten + kejadian + turunan (§3, §1.5, §8.4)
   - konten/   : graf topik, template soal, malrule, resep — read-only saat runtime
   - kejadian/ : events.jsonl append-only — satu-satunya sumber kebenaran riwayat
   - turunan/  : status graf hasil derive(kejadian) — selalu boleh dibuang & dibangun ulang
```

Tidak ada backend server, tidak ada database formal, tidak ada API. Lihat
§8.6 untuk alasan skala ini disengaja, bukan kekurangan sementara. Untuk
kebijakan penyimpanan/retensi/privasi dari file-file ini, lihat §7 — bagian
ini hanya membahas komponen dan alur data.

Komponen 3 dipisahkan dari komponen 4 dengan sengaja: dekompilasi PDF adalah
pekerjaan authoring yang berjalan sekali dan hasilnya ditinjau manusia (§3.7
soal kesesuaian usia), sementara skrip runtime berjalan tiap sesi dan tidak
boleh punya kemampuan mengubah konten. Mencampur keduanya membuat konten bisa
berubah diam-diam di tengah pemakaian.

### 8.2 Pemindahan file JSON: HP → Mac

**Keputusan: kabel USB lewat `adb`, dipicu oleh satu perintah orkestrator
(§8.7) — bukan rangkaian langkah manual per sesi.**

Ini satu-satunya opsi yang konsisten dengan keputusan "tanpa internet" di
spike. Cloud sync (Drive, iCloud, dsb.) langsung kontradiksi dengan alasan
eksplisit spike: data goresan anak tidak boleh keluar dari perangkat lewat
jalur mana pun yang membutuhkan koneksi jaringan.

**Jalur adb yang dipakai perlu diverifikasi di HP nyata, bukan diasumsikan.**
Sejak Android 11, akses `adb pull` ke `/sdcard/Android/data/<pkg>/` diperketat
dan bisa gagal tergantung versi OS dan vendor. Karena APK ini self-signed dan
debuggable (tidak pernah masuk Play Store), jalur yang lebih tahan lintas
versi adalah membaca dari internal storage app:

```
adb exec-out run-as <pkg> cat files/sesi-<id>.json > sesi-<id>.json
```

Status: **belum diuji** pada HP target. Ini item verifikasi Hari 2 rencana
spike (alur ekspor), bukan asumsi yang boleh dibawa sampai v1. Kalau
`run-as` ternyata terhalang, fallback-nya adalah `ACTION_SEND` ke folder
lokal Mac lewat AirDrop/kabel — tetap tanpa jaringan keluar.

Opsi lain sengaja TIDAK dipertimbangkan lebih jauh untuk v1:
- **Bluetooth** — butuh pairing, driver, dan penanganan transfer
  gagal/putus; overhead implementasi tidak sepadan untuk kebutuhan "satu HP,
  satu Mac, satu operator" yang duduk di ruangan yang sama.
- **NFC** — tidak cocok untuk transfer file berukuran variabel (goresan
  kanvas bisa besar), dan menambah dependensi hardware yang tidak perlu.
- **QR code encoding data** — cocok untuk payload kecil (puluhan byte),
  bukan untuk JSON goresan+timestamp per sesi yang jauh lebih besar; akan
  butuh multi-frame encoding, kompleksitas jauh melebihi manfaatnya.

Kabel USB adalah mekanisme yang paling sederhana, paling dapat diandalkan,
dan sudah tersedia tanpa instalasi tambahan. Untuk skala satu keluarga,
satu perangkat, satu Mac, ini bukan penyederhanaan berlebihan — ini ukuran
yang tepat.

### 8.3 Mekanisme tinjauan orang tua (Tahap C)

**Keputusan: satu file YAML per sesi, dibuka otomatis di `$EDITOR` oleh
orkestrator (§8.7) dan diedit langsung oleh founder — BUKAN CSV, BUKAN UI
review terpisah.**

Bentuk file tinjauan mengikuti skema §2.5, dengan `kode_final` sengaja
dikosongkan oleh skrip Tahap A+B dan diisi manual oleh orang tua saat
meninjau. Skrip lanjutan menolak melanjutkan ke §8.4 kalau ada baris dengan
`kode_final` kosong (menegakkan §4.6: tidak maju dengan data tak-tertinjau).

**YAML, bukan CSV** — alasannya praktis: `alasan_singkat` adalah prosa satu
sampai dua kalimat yang bisa memuat koma, tanda kutip, dan (untuk Tahap B)
uraian bukti waktu. Di CSV itu berarti quoting bertingkat yang menyakitkan
justru saat file sedang diedit tangan, tiga kali seminggu, oleh satu orang
yang sedang lelah. YAML menampung prosa multi-baris tanpa escape dan tetap
bisa di-diff baris per baris.

Bentuk file tinjauan per sesi:

```yaml
sesi_id: 2026-08-20T16:04:11
aturan_versi: malrule-2026.08.3
soal:
  - soal_id: 2
    template_id: pecahan_operasi_campuran
    parameter:
      suku: [ {n: 2, d: 3, tanda: +}, {n: 3, d: 4, tanda: +}, {n: 1, d: 2, tanda: -} ]
    jawaban_anak: "4/5"
    jawaban_benar: "11/12"
    kode_awal: K
    tahap_asal: malrule
    malrule_id: pecahan.operasi_pembilang_penyebut_terpisah
    alasan_singkat: >
      Pembilang & penyebut dioperasikan sendiri-sendiri:
      (2+3−1)/(3+4−2) = 4/5, persis jawaban anak.
      Konsep pecahan senama belum terbentuk.
    prompt_versi: null
    model: null
    kode_final:        # ← DIISI ORANG TUA
```

Alasan eksplisit tetap seperti sebelumnya: founder adalah satu-satunya
operator sistem ini DAN developer teknisnya sendiri. Membangun UI review
terpisah (form, tombol konfirmasi, dsb.) untuk pengguna tunggal yang juga
pembuat sistem adalah pekerjaan yang tidak akan pernah terbayar balik pada
skala ini (YAGNI) — file-based lebih cepat dibangun, lebih cepat diiterasi,
dan sudah cukup karena tidak ada orang lain yang perlu antarmuka yang lebih
ramah.

Catatan perubahan: keputusan ini layak ditinjau ulang kalau produk keluar
dari lingkup satu keluarga (banyak operator/reviewer, bukan founder
sendiri) — pada titik itu, gerbang review eksplisit dan UI terpisah baru
punya nilai, konsisten dengan prinsip yang sama yang sudah disebut di §1.3
untuk resep remediasi.

### 8.4 Penyimpanan: konten immutable, kejadian append-only, status turunan

**Keputusan: file lokal (bukan database formal), dipisah tiga lapis menurut
sifat tulisnya — dan status topik TIDAK PERNAH ditimpa di tempat.**

Draf sebelumnya menyimpan status di dalam node graf lalu "menulis balik
status baru" tiap kali `kode_final` masuk. Itu mutasi destruktif, dan ia
bertabrakan langsung dengan janji §2.6 dan §7.3: *"prompt/aturan Tahap B bisa
diiterasi berkali-kali di atas data yang sama tanpa melibatkan anak lagi."*
Kalau status ditimpa, iterasi kedua kehilangan basis pembandingnya — dan
lebih buruk, `kode_final` yang sudah diputuskan orang tua bisa ikut tergerus
oleh jalannya skrip berikutnya. Keputusan manusia adalah data paling mahal di
sistem ini (butuh anak, butuh wawancara, tidak bisa dibangkitkan ulang); ia
tidak boleh disimpan di tempat yang bisa ditimpa.

```
konten/                    IMMUTABLE saat runtime, versi terkontrol (git)
  graf/topik.yaml            node §3.2 — tanpa field status
  soal/template.yaml         template + parameter §2.3.1
  malrule/*.yaml             fungsi prediksi §2.3.1
  resep/*.yaml               pustaka pra-tulis §1.3
  → hanya diubah oleh tool dekompilasi (§8.1 komponen 3) atau tangan founder,
    NEVER oleh skrip runtime

kejadian/                  APPEND-ONLY — satu-satunya sumber kebenaran
  events.jsonl               satu baris = satu kejadian, tidak pernah diedit/dihapus
  mentah/sesi-<id>.json      goresan+timestamp (§7.3, permanen)
  tinjauan/sesi-<id>.yaml    file Tahap C yang sudah terisi kode_final (§8.3)

turunan/                   SELALU BOLEH DIHAPUS & DIBANGUN ULANG
  status.yaml                = derive(konten, kejadian) — cache untuk dibaca manusia
  cache_llm/<hash>.json      §2.5 — berkunci (data+prompt_versi+model)
```

Bentuk satu baris kejadian:

```jsonl
{"t":"2026-08-20T17:31:02","jenis":"kode_final_dikonfirmasi","sesi_id":"…","soal_id":2,"topik_id":"b-m7","kode":"K","aturan_versi":"malrule-2026.08.3"}
{"t":"2026-08-21T09:02:11","jenis":"resep_diberikan","topik_id":"b-m7","resep_id":"…","sumber":"pra-tulis"}
{"t":"2026-08-24T16:40:55","jenis":"hasil_verifikasi","topik_id":"b-m7","hasil":"masih_bermasalah"}
{"t":"2026-08-24T16:41:10","jenis":"cek_lisan","topik_id":"b-m7","jawaban":"menghafal"}
```

Status topik jadi **fungsi murni atas riwayat**, bukan variabel:

```
status(topik) = derive(events.filter(topik))
```

State machine §1.5 dan ambang §1.6 ("≥2 kemunculan K", "gagal verifikasi 2x")
diimplementasikan sebagai fungsi ini — dan karena murni, keduanya bisa diuji
unit tanpa file nyata: kirim urutan kejadian buatan, periksa status yang
keluar. Ambang-ambang itu adalah aturan bisnis paling halus di seluruh PRD
(salah hitung = anak salah di-gate); ia layak diuji langsung, bukan
diverifikasi lewat inspeksi YAML.

Empat manfaat yang langsung menjawab kebutuhan yang sudah tertulis di PRD:

- **Replay aman.** Aturan Tahap A/B boleh diganti dan seluruh riwayat
  dihitung ulang, tanpa menyentuh `kode_final` — memenuhi §2.6, dan
  memungkinkan pengaman promosi malrule di §2.4 (bandingkan hasil replay
  dengan keputusan orang tua yang tersimpan).
- **Batas 3 putaran prompt bisa dihitung.** Kejadian membawa `aturan_versi`,
  jadi "sudah berapa putaran" adalah query, bukan ingatan.
- **Crash tidak merusak.** Append gagal di tengah paling buruk meninggalkan
  satu baris rusak yang bisa dibuang; mutasi YAML yang gagal di tengah bisa
  meninggalkan file graf yang tidak bisa di-parse dan kehilangan seluruh
  status.
- **Diff bermakna.** `git diff` pada `kejadian/` memperlihatkan apa yang
  *terjadi* di sesi itu, bukan sekadar bahwa sebuah field berubah nilai.

Alasan tetap tidak pakai database formal, sama seperti sebelumnya: database
memberi manfaat pada concurrent write, banyak reader/writer, atau query
kompleks lintas ribuan baris — tidak satu pun berlaku di sini. Skalanya
puluhan node, satu anak, satu proses batch (§2.6). Yang berubah dari draf
lama bukan pilihan "file vs DB", tapi **cara menulis ke file itu**: append
sekali, derive sesuai kebutuhan.

### 8.5 Alur data end-to-end

```
Anak pegang HP, kerjakan sesi
        │
        ▼
App Android (capture-only, tanpa INTERNET)
  → tulis 1 file JSON per sesi (goresan+timestamp+jawaban akhir)
        │
        ▼  (kabel USB / adb — §8.2, dipicu `osn sync` §8.7)
kejadian/mentah/sesi-<id>.json  (append, permanen §7.3)
        │
        ▼
Skrip Python — Tahap A (malrule §2.3.1) → Tahap B (§2.3.2) bila tak ada yang cocok
  → tulis kejadian/tinjauan/sesi-<id>.yaml:
    kode_awal + alasan_singkat + jejak versi, kode_final KOSONG
        │
        ▼
Orang tua isi kode_final di $EDITOR (§8.3) — Tahap C
  → satu kejadian `kode_final_dikonfirmasi` per soal di-APPEND ke events.jsonl
    (tidak ada file yang ditimpa; §8.4)
        │
        ▼
derive(konten, kejadian) → turunan/status.yaml sesuai §1.5/§1.6
  (fungsi murni; boleh dijalankan berapa kali pun, hasilnya sama)
        │
        ▼
Alur sesi berikutnya (§4.3) baca status turunan yang sudah ditinjau (§4.6)
  → hasilkan rekomendasi topik; soal verifikasi diparametrisasi ulang
    dari template yang sama (§2.3.1)
        │
        ▼  (kabel USB — arah balik dari §8.2)
Paket sesi (topik_id, soal, jenis kanvas — TANPA kunci jawaban/diagnosis,
lihat §7.4) → dipindah ke HP
        │
        ▼
Verifikasi checksum di Mac → hapus JSON mentah dari HP (§7.2)
```

Setiap panah adalah batas komponen yang jelas dan file adalah satu-satunya
kontrak antar komponen — tidak ada komponen yang memanggil komponen lain
secara langsung (tidak ada API, tidak ada proses yang saling terhubung
lewat jaringan). Perbedaan dari draf lama: tidak ada satu pun panah yang
"update status di file graf" — status hanya muncul sebagai hasil `derive`,
dan satu-satunya tulisan yang bertahan adalah append ke `kejadian/`.

### 8.6 Skala v1: alat command-line untuk satu operator

Arsitektur ini secara sengaja adalah **kumpulan skrip dan satu app
capture-only**, dijalankan manual oleh satu operator (founder) — BUKAN
aplikasi mobile penuh dengan dashboard, backend, atau API server. Tidak ada
autentikasi, tidak ada multi-user, tidak ada sinkronisasi lintas perangkat.

Ini tepat untuk sekarang karena skalanya benar-benar satu pengguna: satu
anak, satu orang tua yang juga developer, satu Mac, satu HP. Pada skala
ini, kebutuhan yang sebenarnya adalah memvalidasi cepat apakah pipeline
diagnosis-remediasi bekerja (lihat gerbang lulus spike) — bukan
mempercantik produk untuk pengguna yang belum ada. Membangun dashboard atau
backend sekarang berarti menghabiskan waktu pada permukaan yang tidak akan
diuji oleh siapa pun selain founder sendiri.

Prinsip ini sama dengan yang sudah dipakai di §1.3 untuk resep remediasi
("kalau nanti keluar dari lingkup satu keluarga, baru perlu gerbang review
eksplisit / arsitektur berbeda") — berlaku juga di sini untuk arsitektur
secara umum: begitu sistem ini dipakai lebih dari satu keluarga atau lebih
dari satu operator, barulah database formal, UI review, mekanisme transfer
otomatis, dan lapisan backend punya alasan untuk dibangun. Sebelum titik
itu, kesederhanaan ini bukan utang teknis — ini keputusan yang benar untuk
kecepatan validasi.

Satu klarifikasi terhadap kata "dijalankan manual" di atas: yang manual
adalah **keputusannya** (kapan sesi terjadi, kode_final apa, kapan
pra-fondasi ditutup), bukan **langkah mekanisnya**. Rangkaian langkah
mekanis dibungkus satu perintah — lihat §8.7. Membiarkan langkah mekanis
tetap manual bukan kesederhanaan, itu gesekan.

### 8.7 Satu perintah untuk seluruh siklus

**Keputusan: seluruh §8.5 dibungkus satu perintah — `osn sync` — bukan
sepuluh langkah yang diingat dan dijalankan sendiri tiap sesi.**

Ini bukan kenyamanan, ini soal kelangsungan hidup sistem. §9.2 menetapkan
kriteria sukses operasional: siklus berjalan penuh **selama beberapa minggu
berturut-turut pada ritme nyata 3 sesi/minggu**. Titik gagal yang paling
mungkin bukan akurasi diagnosis — itu sudah dijaga gerbang §2.7 — melainkan
gesekan operasional: colok kabel, ingat perintah adb, jalankan skrip, buka
file, jalankan skrip lagi, push balik, hapus dari HP. Sepuluh langkah dikali
tiga kali seminggu, dijalankan oleh orang tua yang juga bekerja, adalah
bentuk kegagalan yang tidak muncul di gerbang teknis mana pun tapi
menghentikan produk di minggu ketiga. Arsitektur yang benar tapi tidak
dipakai adalah arsitektur yang gagal.

```
osn sync
  1. adb: tarik JSON sesi baru dari HP                          (§8.2)
  2. tulis ke kejadian/mentah/                                  (§7.3)
  3. Tahap A (malrule) + Tahap B                       (§2.3, cache LLM §2.5)
  4. tulis kejadian/tinjauan/sesi-<id>.yaml, buka di $EDITOR     (§8.3)
     ── berhenti di sini sampai founder menyimpan & menutup ──
  5. validasi: tolak lanjut kalau ada kode_final kosong          (§4.6)
  6. append kejadian kode_final_dikonfirmasi ke events.jsonl     (§8.4)
  7. derive → turunan/status.yaml                                (§8.4)
  8. susun paket sesi berikutnya                                 (§4.3)
  9. adb: push paket sesi ke HP                                  (§7.4)
 10. verifikasi checksum, lalu hapus JSON mentah dari HP          (§7.2)
```

Perintah pendamping, sengaja sedikit:

| Perintah | Untuk apa |
|---|---|
| `osn sync` | Siklus penuh di atas — satu-satunya perintah yang rutin dipakai |
| `osn status` | Baca `turunan/status.yaml` sebagai teks: K aktif per topik + trennya (§9.2) |
| `osn replay [--aturan V]` | Hitung ulang diagnosis atas seluruh riwayat dengan versi aturan tertentu, laporkan selisihnya terhadap `kode_final` — ini pengaman promosi malrule (§2.4) sekaligus penghitung batas 3 putaran prompt (§2.5) |
| `osn kalibrasi` | Input hasil Tes Kalibrasi awal (§5.2 langkah 2-6), sekali per anak |

Yang **tidak** ada, dan sengaja: perintah untuk mengedit konten (itu
pekerjaan editor + git), perintah untuk mengubah status langsung (status
adalah turunan, §8.4), dan mode daemon/watcher (batch, §2.6).

Dua sifat orkestrator ini yang harus dijaga:

- **Tipis.** Tidak mengandung logika diagnosis, aturan state machine, atau
  heuristik apa pun — hanya urutan pemanggilan. Arsitektur §8.1–§8.5 tidak
  berubah sedikit pun karena ia ada; ia lapisan pemanggil di atasnya.
- **Gagal dengan aman.** Langkah 10 (hapus data dari HP) tidak pernah jalan
  kalau ada langkah sebelumnya yang gagal. Ini menegakkan §7.2 secara
  mekanis: data anak tidak pernah hilang dari HP sebelum benar-benar terbaca
  dan terverifikasi di Mac. Kalau `osn sync` dihentikan di tengah (Ctrl-C
  saat mengisi tinjauan), menjalankannya ulang harus melanjutkan dari
  langkah 4, bukan menarik ulang atau menduplikasi kejadian — sifat
  append-only §8.4 yang membuat ini mungkin.

### 8.8 Satu-satunya test yang wajib ada sejak hari pertama

**Keputusan: golden test untuk `MotionEvent.toSamples()` ditulis sebelum
kanvas dipakai anak. Sisanya menyusul.**

PRD ini bukan dokumen yang mewajibkan coverage tinggi di mana-mana — untuk
alat satu operator, sebagian besar bug cukup diperbaiki saat ketemu. Tapi ada
satu lapisan dengan sifat berbeda: **kegagalan di perekaman sampel goresan
tidak bisa diperbaiki belakangan.** Kalau titik historis `MotionEvent`
hilang, salah urut, atau timestamp-nya bergeser, seluruh sinyal Tahap B
(§2.2) rusak dan satu-satunya perbaikan adalah meminta anak mengerjakan ulang
soal yang sama — yang justru dilarang oleh alasan arsitektur batch (§2.6).
Rencana spike menyebut fungsi ini "seluruh nilai spike ada di ketelitian satu
hal"; kalimat itu konsekuensinya adalah sebuah test, bukan cuma catatan.

Bentuknya golden test: rekam sekali urutan `MotionEvent` nyata (termasuk yang
membawa `historySize` > 1), simpan sebagai fixture, lalu pastikan
`toSamples()` selalu mengembalikan daftar sampel yang sama persis — jumlah,
urutan, dan selisih waktu relatif terhadap `t0`.

Dua test lain yang sepadan ongkosnya, tapi tidak menahan hari pertama:
- **`derive()` state machine (§8.4)** — kirim urutan kejadian buatan, periksa
  status yang keluar. Ini menguji ambang §1.6 ("≥2 kemunculan K", "gagal
  verifikasi 2x") secara langsung; salah hitung di sini berarti anak
  di-soft-gate pada topik yang salah.
- **Malrule tidak saling bertumbukan (§2.3.1)** — untuk tiap template, jalankan
  seluruh malrule atas rentang parameter; kalau dua malrule berkode berbeda
  memprediksi jawaban yang sama, itu harus terdeteksi sebagai ambigu (turun ke
  Tahap B), bukan diam-diam dipilih salah satu. Ini yang menegakkan asimetri
  "jangan pernah menebak ke arah K" (§2.1) di tingkat kode.

## 9. Ruang Lingkup v1 & Metrik Sukses

Sintesis dari semua keputusan di atas — apa yang v1 secara eksplisit
**bukan**, dan bagaimana "berhasil" diukur di luar gerbang teknis spike.

### 9.1 Di luar cakupan v1 (sengaja)

- **Multi-anak / multi-keluarga / akun** — v1 satu keluarga, satu anak,
  tanpa sistem akun.
- **Kurikulum berkalender / jadwal harian tetap** — diganti graf
  non-kalender (§3) + rekomendasi kondisi-driven (§4).
- **OCR/pengenalan tulisan tangan** — v1 tidak butuh sama sekali (§2.1,
  §6.4).
- **Koneksi internet dalam bentuk apa pun di app Android** — tanpa izin
  INTERNET, tanpa cloud, tanpa API pihak ketiga (§7.1, §8.2).
- **Dashboard/UI review terpisah, backend server, database formal** —
  diganti file lokal + satu perintah CLI (§8.3, §8.4, §8.6, §8.7).
- **`tinta_llm` sebagai komponen wajib** — status barunya *bergantung hasil
  gerbang*: kalau `tinta_heuristik` lolos §2.7, LLM keluar dari lingkup v1
  seluruhnya (§2.3.2). Ini satu-satunya butir lingkup yang belum final di
  dokumen ini, dan itu memang disengaja — diputuskan oleh angka, bukan
  ditebak sekarang.
- **AI sebagai tutor percakapan ke anak** — AI tidak pernah bicara langsung
  ke anak, hanya menghasilkan draf untuk orang tua (§1.3, §2.1, §5.4).
- **Mata pelajaran IPA** — sumber PDF mencakup IPA juga, tapi seluruh PRD
  ini sengaja hanya membahas Matematika; IPA di luar cakupan sampai
  dinyatakan lain.
- **Konten pra-fondasi tertulis permanen** — masih gap terbuka (§3.7),
  ditutup sementara oleh mode AI-generate non-graf (§5.4), bukan solusi
  akhir.

### 9.2 Kriteria "berhasil" untuk v1 (di luar gerbang spike §2.7)

- Gerbang spike (§2.7) tetap jadi syarat teknis minimum: ≥7/10 `kode_final`
  cocok penilaian orang tua, nol false-K — diukur untuk `tinta_heuristik`
  dan `tinta_llm` secara terpisah (§2.3.2).
- **Operasional**: siklus HP→Mac→tinjauan→HP (§8.5) berjalan penuh tanpa
  hambatan selama beberapa minggu berturut-turut dengan ritme nyata 3
  sesi/minggu — bukan cuma diuji sekali di kondisi terkendali. Ukuran
  konkretnya: **`osn sync` (§8.7) selesai penuh tanpa intervensi manual di
  luar mengisi `kode_final`**, pada ≥90% sesi. Kalau founder rutin harus
  turun tangan menjalankan langkah manual, itu kegagalan operasional
  meski diagnosisnya akurat.
- **Diagnostik**: jumlah K aktif per topik (bukan skor) benar-benar dipakai
  orang tua untuk memutuskan tindakan nyata di rumah — ini validasi tesis
  inti (§1.1), bukan cuma soal aplikasi berjalan secara teknis.
- **Cakupan deterministik**: proporsi diagnosis dengan
  `tahap_asal: malrule` **naik dari waktu ke waktu** seiring pustaka tumbuh
  (§2.4). Ini metrik kesehatan arsitektur §2.3.1 — kalau proporsinya
  mandek rendah, berarti template/malrule tidak menangkap pola nyata
  kesalahan anak dan Tahap B menanggung beban yang seharusnya deterministik.
- **Guardrail**: tidak ada satu pun pelanggaran tiga uji inti sepanjang
  pemakaian — anak tidak pernah bicara ke AI, kunci jawaban tidak pernah
  tersentuh anak (§7.4), sistem tetap berjalan meski bolong 2 minggu.

### 9.3 Sengaja belum diputuskan (boleh ditunda)

- **Skala melampaui satu keluarga** (§1.3, §8.6) — arsitektur & privasi
  akan berubah signifikan kalau ini terjadi; sengaja tidak dirancang
  sekarang.
- **Prasyarat lintas-jalur di graf** (§3.3) — ditambahkan manual seiring
  waktu, bukan tugas hari-1.
- **Pustaka malrule & pustaka resep K di luar cakupan awal** (§1.3, §2.4)
  — tumbuh dari pemakaian, bukan ditulis di depan.
- **Node pra-fondasi permanen** (§3.7) — ditutupi sementara oleh
  AI-generate (§5.4), ditulis manual kalau pola pra-fondasi anak sudah
  cukup jelas dari data pemakaian nyata.

### 9.4 Perlu diverifikasi, bukan diasumsikan

Dibedakan dari §9.3 dengan sengaja: yang di bawah ini **bukan** keputusan
yang ditunda, melainkan klaim teknis yang sudah dipakai sebagai dasar
keputusan tapi belum pernah diuji di perangkat/data nyata. Masing-masing
punya titik verifikasi yang sudah ditentukan.

| Klaim yang belum diuji | Kalau salah, yang berubah | Diverifikasi di |
|---|---|---|
| `adb exec-out run-as` bisa membaca internal storage app di HP target (§8.2) | Mekanisme transfer §8.2 diganti fallback `ACTION_SEND`; §8.7 langkah 1/9 menyesuaikan | Hari 2 spike (alur ekspor) |
| `tinta_heuristik` cukup untuk ≥7/10 tanpa LLM (§2.3.2) | `tinta_llm` masuk lingkup v1, dengan biaya dan cache-nya (§2.5) | Hari 6-7 spike |
| Anak nyaman menulis dengan jari sampai soal ke-10 | Seluruh kanal tinta gugur; produk mundur ke jalur foto kertas/jawaban akhir saja | Hari 1 spike — sengaja paling awal |
| 20 soal kalibrasi cukup menghasilkan template+malrule yang berguna lintas kurikulum (§5.1) | Cakupan Tahap A tumbuh jauh lebih lambat dari perkiraan §2.3.1; authoring manual harus dijadwalkan eksplisit | Beberapa minggu data v1 nyata |
| Distribusi B/K/H pada anak SD kelas 4 (riset NEA semuanya pada SMP+) | Metrik utama "K aktif per topik" perlu ditinjau ulang | Beberapa minggu data v1 nyata |
