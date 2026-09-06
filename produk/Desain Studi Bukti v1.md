# Desain Studi Bukti v1 — Apakah Remediasi Berbasis B/K/H Memperbaiki Hasil?

**Status dokumen:** protokol studi yang belum dijalankan; prinsip pengukurannya
masih relevan, tetapi alur data file/HP/Mac dan istilah `mastery/selesai` di
bawah mendahului aplikasi web sekarang. Jalankan studi ini hanya setelah
`Siklus Belajar Terpandu.md` terimplementasi; rincian kerja ada di plan lokal.

Saat dipakai nanti:

- sumber bukti adalah snapshot outcome yang dikonfirmasi dari `../mesin/`;
- unit analisis adalah kunci fokus kanonis
  `(template_id, kode_intervensi, malrule_id)`, bukan topik besar saja;
- hasil evaluasi disebut **mulai membaik**, dan **bertahan** baru setelah
  checkpoint per fokus; jangan memakai klaim “mastery/selesai”;
- desain penelitian staggered boleh mengatur kapan intervensi studi dimulai,
  tetapi tidak boleh mengubah CTA keselamatan aplikasi seperti review,
  konfirmasi, atau eskalasi.

Dokumen kerja · disusun 16 Agustus 2026
Menjawab risiko terbesar dari `Analisis Kebutuhan dan Potensi Pasar.md`: **belum ada satu pun di dunia yang membuktikan bahwa remediasi berbasis jenis kesalahan menaikkan hasil belajar**. Entrant pertama yang menerbitkan bukti ini memegang posisi diferensiasi yang tak bisa disaingi — dan v1 (satu keluarga, satu anak) adalah pabrik bukti itu.

---

## 1. Klaim yang ingin dibuktikan (dan yang TIDAK)

**Klaim yang dibangun (spesifik, jujur):**
> Pada anak ini, kunci fokus dengan K berulang yang menerima intervensi konkret,
> latihan terbimbing, penguatan mandiri, evaluasi berjeda, dan checkpoint
> menunjukkan perbaikan yang bertahan—ditandai penurunan K, jawaban tepat pada
> probe baru, dan kemampuan menjelaskan cara—sementara kandidat yang masih dalam
> baseline belum menunjukkan perubahan yang sama.

**Yang TIDAK diklaim (anti-overclaim):**
- Bukan "remediasi B/K/H menyebabkan perbaikan" secara umum (n=1).
- Bukan "aplikasi ini lebih baik dari les".
- Bukan angka efek (effect size) yang bisa digeneralisasi.

Posisi publikasi: **studi kasus / single-case experimental design (SCED)** — desain yang sah dan diterima di literatur pendidikan (digunakan di riset NEA/Counting On dan ITS). Nilainya: bukti mekanisme + template untuk studi n=10 berikutnya.

---

## 2. Desain inti: multiple baseline across topics (staggered)

Karena hanya ada satu anak (tanpa kelompok kontrol), kontrol datang dari **penundaan intervensi yang diatur sendiri**:

```
 TOPIK        MINGGU 1  2  3  4  5  6  7  8  9  10  11  12
 ─────────────────────────────────────────────────────────────
 Topik A (K)  ▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓  ████  ████  ████  ████ ...
              baseline  baseline   ← intervensi A dimulai
 Topik B (K)  ▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓  ████  ████  ████ ...
              baseline  baseline   baseline ← intervensi B dimulai
 Topik C (K)  ▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓  ▓▓▓▓▓▓  ████  ████ ...
                                   baseline  baseline ← intervensi C
 ─────────────────────────────────────────────────────────────
 ▓ = fase baseline (probe mingguan, tanpa intervensi khusus)
 █ = fase intervensi sesuai kontrak siklus aktif + evaluasi/checkpoint
```

**Logika kontrol**: kalau perbaikan muncul **tepat saat intervensi topik itu dimulai** (bukan mengikuti waktu), maka itu bukan efek kedewasaan/kebetulan — pola staggered ini adalah standar SCED untuk menyingkirkan ancaman validitas (maturation, history, testing).

### 2.1 Pemilihan target studi (2–3 kunci fokus K)
- Sumber: snapshot outcome sesi pemetaan/diagnostik yang sudah dikonfirmasi.
- Kriteria: kunci fokus kanonis `(template_id, K, malrule_id)` yang muncul pada minimal 2 sesi berbeda dan dipilih reducer.
- Untuk desain staggered, pilih 2–3 target yang cukup independen agar perubahan satu target tidak otomatis menyelesaikan yang lain.
- Batas aplikasi tetap maksimal **dua fokus aktif per putaran**. Target studi ketiga tetap baseline/pantauan dan baru masuk putaran setelah salah satu fokus sebelumnya ditutup; studi tidak boleh membuka tiga fokus aktif sekaligus.
- Jika hanya satu fokus memenuhi syarat, studi multiple-baseline belum layak dijalankan; lanjutkan pengumpulan bukti tanpa mengarang kontrol.

### 2.2 Instrumen probe
- **Per fokus**: minimal 4 soal evaluasi untuk status “mulai membaik” dan minimal 3 soal checkpoint untuk “bertahan”; parameter berbeda, kunci fokus sama.
- **Format studi**: fokus boleh dicampur dengan soal pembanding, tetapi komposisi tidak boleh mengurangi minimum probe aplikasi.
- **Frekuensi**: baseline/probe studi mengikuti slot yang dibuat orkestrator dan tidak boleh mendahului review, konfirmasi, evaluasi jatuh tempo, atau eskalasi.
- **Pencatatan per soal**: referensi snapshot/konfirmasi · kunci fokus · benar/salah · `kode_final` · cek cara (`bisa_menjelaskan | ragu | menghafal`) · fase studi.
- **Variasi soal**: gunakan seed/parameter baru dan simpan identitas occurrence agar retest sah dapat dibedakan dari duplikasi.

### 2.3 Intervensi (mengikuti kontrak siklus aktif)
- Fokus K menjalani tindakan konkret/visual dan contoh terbimbing sebelum penguatan mandiri—bukan sekadar latihan soal.
- Evaluasi memakai angka baru untuk kunci fokus yang sama, tersedia **3 hari setelah penguatan selesai dan hasilnya dikonfirmasi**. Lulus awal = minimal 75% dari ≥4 probe fokus, nol K, dan bisa menjelaskan cara.
- Status setelah evaluasi adalah **mulai membaik**, bukan selesai. Bukti retensi datang dari checkpoint pertama 28 hari setelah evaluasi sukses, minimal 3 probe fokus.
- Gagal pertama memakai `pendekatan_id` berbeda; gagal kedua atau ketiadaan alternatif memicu cek prasyarat statis/uji ulang lisan.

---

## 3. Outcome & definisi keberhasilan

| Outcome | Alat ukur | Definisi "berhasil" per topik |
|---|---|---|
| **Primer: mulai membaik** | Evaluasi berjeda | ≥75% dari minimal 4 probe fokus benar, nol K, dan cek cara = bisa menjelaskan |
| **Primer: pergeseran komposisi kesalahan** | Snapshot `kode_final` per probe | Proporsi K turun; H boleh muncul sebagai kemajuan mekanisme, tetapi tidak diwajibkan sebagai urutan universal sebelum benar |
| **Sekunder: skor mixed** | Sesi campuran | Tren naik, tidak wajib signifikan karena campuran memiliki noise tinggi |
| **Primer retensi: bertahan** | Checkpoint per fokus, 28 hari setelah evaluasi sukses | Minimal 3 probe fokus benar, nol K, dan tetap bisa menjelaskan; diulang berkala untuk mendeteksi kekambuhan |
| **Sekunder: fokus aktif turun** | Reducer siklus | Kunci fokus keluar dari putaran aktif tanpa menghapus histori lama |

**Pola yang dicari (visual analysis SCED):** per topik, grafik probe mingguan — baseline datar/rendah → titik perbaikan **tepat di garis intervensi** → stabil. Ini dibaca secara visual dulu (standar SCED), bukan statistik.

---

## 4. Ancaman validitas & pengendaliannya

| Ancaman | Cara mengendalikan |
|---|---|
| **Maturation** (anak makin pintar karena waktu) | Staggered start: kalau perbaikan hanya muncul saat intervensi tiap topik (bukan bersamaan), maturation tidak menjelaskan pola |
| **Testing** (makin sering probe, makin pintar) | Rotasi varian angka; probe tidak diberi umpan balik jawaban benar (hanya "oke" — aturan Uji Ulang Lisan); gap ≥3 hari |
| **Teaching-to-test** (resep mengajarkan persis soal probe) | Probe = angka beda, skill sama; resep tidak pernah menyebut bentuk probe |
| **Efek penilai tunggal** (Bapak menilai sendiri) | Kode_final ditetapkan sebelum melihat grafik; simpan rekaman jawaban untuk audit; kalau ada keraguan, minta penilai kedua (pasangan/teman) pada sampel 20% soal |
| **Harapan (expectancy)** | Fase baseline dilakukan tanpa memberi tahu anak ada "program khusus"; intervensi tetap menyatu dengan alur sesi normal v1 |
| **Data hilang (bolong 2 minggu)** | Prinsip non-kalender: probe ditunda, tidak dibatalkan; grafik tetap bisa dibaca (SCED toleran gap) |

---

## 5. Alur data & pencatatan (aplikasi web sekarang)

```
Sesi probe/evaluasi/checkpoint di Jagomat
        ↓
Diagnosis otomatis → tinjauan dan koreksi guru
        ↓
Konfirmasi eksplisit → snapshot outcome append-only
        ↓
Reducer siklus → status fokus dan rekomendasi berikutnya
        ↓
Ekspor data studi agregat/pseudonim bila analisis terpisah diperlukan
```

Studi tidak membaca DB produksi dengan skrip ad-hoc dan tidak memakai file
YAML sebagai sumber kebenaran. Semua outcome studi harus berasal dari snapshot
konfirmasi; identitas anak tidak masuk artefak studi. Penjadwalan probe
terstruktur adalah kebutuhan studi tambahan, bukan alasan membuat status
pedagogis kedua di luar reducer aplikasi.

---

## 6. Timeline & ritme

- **Durasi studi**: minimal 12 minggu pemakaian normal; dapat memanjang sampai checkpoint 28 hari terakhir selesai.
- **Awal studi**: pilih fokus yang sudah memenuhi ambang bukti dan kumpulkan minimal dua probe baseline tanpa intervensi khusus.
- **Intervensi staggered**: mulai fokus A, B, dan C pada waktu berbeda hanya setelah CTA keselamatan aplikasi selesai; tanggal aktual dicatat, bukan dipaksakan ke minggu kalender tertentu.
- **Akhir analisis**: tidak boleh sebelum setiap fokus yang dinilai mempunyai evaluasi sah dan kesempatan checkpoint pertama.
- **Output**: grafik per fokus, tabel ringkas snapshot, dan narasi 2–3 halaman.

---

## 7. Template pencatatan (satu baris per soal probe)

```csv
tanggal,konfirmasi_id,template_id,kode_intervensi,malrule_id,occurrence,benar,kode_final,cek_pemahaman,fase_studi,catatan
2026-09-10,42,pecahan_operasi,K,penyebut_tidak_disamakan,1,salah,K,menghafal,baseline,"yakin dengan cara lama"
2026-10-15,87,pecahan_operasi,K,penyebut_tidak_disamakan,2,benar,,bisa_menjelaskan,checkpoint,"menjelaskan penyamaan penyebut"
```

Kolom `cek_pemahaman`: `bisa_menjelaskan | ragu | menghafal`. Kolom
`fase_studi`: `baseline | intervensi | evaluasi | checkpoint`. Baris ekspor
merujuk `konfirmasi_id`; jangan menyalin nama anak atau membaca diagnosis
mutable langsung.

---

## 8. Laporan akhir (kerangka 2–3 halaman)

1. **Konteks**: profil anak dan level efektif, ritme pemakaian, periode studi, kunci fokus target, dan alasannya.
2. **Grafik per fokus** (probe % benar, garis intervensi ditandai) + komposisi B/K/H/E/T/N.
3. **Hasil per fokus**: baseline vs pascaintervensi; jumlah evaluasi sampai “mulai membaik”; checkpoint sampai “bertahan”; kekambuhan; perubahan jenis kesalahan yang benar-benar teramati.
4. **Keterbatasan**: n=1, tanpa kontrol, penilai tunggal (dengan langkah mitigasi yang diambil).
5. **Klaim yang boleh dikutip** (persis Bagian 1) + **yang tidak boleh**.
6. **Jejak untuk studi berikutnya**: jumlah probe yang dibutuhkan, varian yang bocor, dan fokus yang paling responsif—input untuk studi n=10.

---

## 9. Keputusan yang ditentukan SEBELUM data (anti-rasionalisasi)

- **Gerbang lulus studi**: ≥2 dari 3 kunci fokus target mencapai “bertahan” dalam masa studi **dan** pola staggered terlihat—perbaikan mengikuti awal intervensi masing-masing fokus.
- **Gerbang gagal**: tidak ada fokus yang mencapai “mulai membaik” dalam 12 minggu, ATAU semua fokus membaik bersamaan sejak minggu 1 (tidak mendukung efek intervensi), ATAU cek cara selalu “menghafal” meski jawaban benar.
- **Di antara keduanya**: ada fokus “mulai membaik” tetapi checkpoint belum cukup atau pola tidak jelas; lanjutkan sampai checkpoint 28 hari yang sudah dijadwalkan, bukan menutup kesimpulan lebih awal.

---

## 10. Kaitan dengan keputusan bisnis

| Hasil studi | Implikasi |
|---|---|
| Lulus (≥2 fokus bertahan, pola staggered) | Bukti mekanisme pada kasus ini ada → susun protokol studi n=10; jangan otomatis memperluas arsitektur/fitur |
| Ada fokus mulai membaik tetapi belum bertahan | Perbaiki intervensi atau tunggu checkpoint yang sah; jangan klaim retensi lebih awal |
| Gagal total | Tesis remediasi tidak terbukti di kasus ini → tinjau konten intervensi, loop evaluasi, dan taksonomi sebelum menambah fitur |

---

*Dokumen ini memformalkan pengukuran. Saat dijalankan, istilah status, sumber
bukti, dan urutan tindakan wajib mengikuti reducer siklus belajar yang aktif,
bukan state/file historis PRD.*
