# Desain Studi Bukti v1 — Apakah Remediasi Berbasis B/K/H Memperbaiki Hasil?

Dokumen kerja · disusun 16 Agustus 2026
Menjawab risiko terbesar dari `Analisis Kebutuhan dan Potensi Pasar.md`: **belum ada satu pun di dunia yang membuktikan bahwa remediasi berbasis jenis kesalahan menaikkan hasil belajar**. Entrant pertama yang menerbitkan bukti ini memegang posisi diferensiasi yang tak bisa disaingi — dan v1 (satu keluarga, satu anak) adalah pabrik bukti itu.

---

## 1. Klaim yang ingin dibuktikan (dan yang TIDAK)

**Klaim yang dibangun (spesifik, jujur):**
> Pada anak kelas 4 ini, topik dengan K aktif (salah konsep) yang diintervensi dengan resep B/K/H (benda nyata + loop verifikasi 3 hari) mencapai **mastery terverifikasi** — ditandai pergeseran komposisi kesalahan dari K → H → benar, dan lolos cek "dapat dari mana" — dalam rentang 4–6 minggu per topik, sementara topik yang belum diintervensi tidak berubah.

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
 █ = fase intervensi (resep K per PRD §1.2/§1.3 + verifikasi 3 hari)
```

**Logika kontrol**: kalau perbaikan muncul **tepat saat intervensi topik itu dimulai** (bukan mengikuti waktu), maka itu bukan efek kedewasaan/kebetulan — pola staggered ini adalah standar SCED untuk menyingkirkan ancaman validitas (maturation, history, testing).

### 2.1 Pemilihan topik (2–3 topik K aktif)
- Sumber: Tes Kalibrasi Minggu 0 (PRD §5.1) + kode_final dari sesi-sesi v1 (PRD §2.3/§2.5).
- Kriteria: topik dengan **K aktif (≥2 kemunculan K, PRD §1.6)** — misalnya dari 14 topik seed kalibrasi (urutan operasi, pecahan, desimal, persen, FPB/KPK, keterbagian, luas, volume, satuan, kecepatan, rata-rata, pola bilangan, pencacahan).
- Pilih 3 topik yang **independen satu sama lain** (mis. pecahan, kecepatan, luas) — bukan berantai (agar perbaikan satu topik tidak otomatis memperbaiki yang lain).
- Kalau K aktif hanya 1–2 topik: cukup 2 topik staggered (desain tetap jalan).

### 2.2 Instrumen probe (kunci pengukuran)
- **Per topik**: 5 soal probe, **angka berbeda dari soal latihan, skill sama** (aturan sama dengan verifikasi PRD §1.5).
- **Format**: campuran acak semua topik dalam satu sesi probe (anak tidak boleh tahu topik mana yang sedang diukur — mencegah fokus selektif dan efek "diajari untuk tes").
- **Frekuensi**: 1 sesi probe per minggu (10–15 soal total untuk 2–3 topik), ditambahkan di akhir sesi reguler atau dijadwalkan sebagai sesi probe mandiri.
- **Pencatatan per soal**: benar/salah · kode_final (B/K/H) · hasil cek "dapat dari mana?" (bisa jelaskan / ragu-ragu / menghafal — PRD §1.6) · catatan singkat.
- **Bank soal probe**: susun 3 varian angka per topik (A/B/C), rotasi tiap minggu supaya anak tidak menghafal jawaban; varian ke-3 dipakai untuk verifikasi 3-hari.

### 2.3 Intervensi (persis resep PRD — tidak boleh menyimpang)
- Topik masuk fase intervensi → ikuti resep K dari pustaka pra-tulis/AI (`tindakan` + `durasi_target` + `verifikasi`, PRD §1.4).
- **Benda nyata dulu, simbol belakangan** (PRD §1.2 K) — bukan sekadar latihan soal.
- Verifikasi: soal beda angka, skill sama, **3 hari setelah resep** (PRD §1.5). Lulus = benar + bisa jelaskan "dapat dari mana".
- Eskalasi kalau gagal 2x berturut-turut (PRD §1.6): cek prasyarat graf → Uji Ulang Lisan.

---

## 3. Outcome & definisi keberhasilan

| Outcome | Alat ukur | Definisi "berhasil" per topik |
|---|---|---|
| **Primer: mastery terverifikasi** | Probe mingguan + verifikasi 3-hari | Benar pada probe **dan** cek lisan "dapat dari mana" = bisa jelaskan, **2x berturut-turut dengan jeda ≥3 hari** (menyamakan state `selesai` PRD §1.5) |
| **Primer: pergeseran komposisi kesalahan** | kode_final per soal probe | Proporsi K turun (→ 0), lalu H → benar; bukan langsung benar tanpa fase K→H (menunjukkan mekanisme, bukan hafalan) |
| **Sekunder: skor tryout** | Lembar Pantau (tryout Sabtu, 10 soal campuran) | Tren naik, tidak wajib signifikan (tryout campuran = noise tinggi) |
| **Sekunder: retensi 1 bulan** | Probe varian D, 4 minggu setelah `selesai` | Tetap benar + bisa jelaskan (uji bahwa bukan hafalan jangka pendek) |
| **Sekunder: K aktif turun** | Hitungan K aktif per topik (PRD §1.6) | Semua topik intervensi keluar dari status "K aktif" |

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

## 5. Alur data & pencatatan (konsisten arsitektur v1)

```
Sesi probe anak (HP) → JSON goresan+jawaban (PRD §2.6)
        ↓ (kabel USB)
Skrip diagnosis Tahap A+B di Mac (PRD §8.1.3)
        ↓
Tinjauan Bapak → kode_final per soal (PRD §2.5)
        ↓
File graf topik update status (PRD §8.4)
        ↓
Lembar studi: tabel probe per minggu (template §7)
```

Semua yang dicatat sudah merupakan bagian dari arsitektur v1 — **studi ini tidak menambah satu komponen pun**, hanya menambahkan (a) jadwal probe terstruktur, (b) pemilihan 3 topik target, (c) template pencatatan.

---

## 6. Timeline & ritme

- **Durasi studi**: 12 minggu pemakaian v1 normal (3 sesi/minggu).
- **Minggu 0**: Tes Kalibrasi ulang singkat atau review data kalibrasi awal → tetapkan 3 topik target + status baseline awal.
- **Minggu 1–2**: baseline semua topik target (2 probe), tanpa intervensi.
- **Minggu 3**: intervensi Topik A dimulai (baseline B & C berlanjut).
- **Minggu 5**: intervensi Topik B dimulai.
- **Minggu 7**: intervensi Topik C dimulai.
- **Minggu 12**: akhir fase intervensi + probe retensi 1-bulan (minggu 16).
- **Output**: grafik 3 panel (per topik), tabel ringkas, narasi 2–3 halaman (Bagian 8).

Ritme ini menyesuaikan PRD §4.3 — sesi probe dan intervensi masuk sebagai prioritas slot biasa; tidak ada jadwal tambahan di luar 3 sesi/minggu.

---

## 7. Template pencatatan (satu baris per soal probe)

```csv
tanggal,topik_id,varian,soal_id,benar,kode_final,dapat_dari_mana,fase,catatan
2026-08-24,pecahan,A,P1-1,salah,K,menghafal,baseline,"2/3+3/4=5/7, yakin benar"
2026-08-24,kecepatan,A,P3-1,benar,,-,baseline,"cepat, tanpa coretan"
...
```

Kolom `dapat_dari_mana`: `bisa | ragu | menghafal` (PRD §1.6). Kolom `fase`: `baseline | intervensi | verifikasi | retensi`.

---

## 8. Laporan akhir (kerangka 2–3 halaman)

1. **Konteks**: anak kelas 4, ritme 3x/minggu, periode studi, topik target & alasannya.
2. **Grafik 3 panel** (probe % benar per minggu, garis intervensi ditandai) + komposisi B/K/H per topik.
3. **Hasil per topik**: baseline vs pasca-intervensi; jumlah verifikasi sampai `selesai`; retensi 1 bulan; pergeseran K→H→benar teramati atau tidak.
4. **Keterbatasan**: n=1, tanpa kontrol, penilai tunggal (dengan langkah mitigasi yang diambil).
5. **Klaim yang boleh dikutip** (persis Bagian 1) + **yang tidak boleh**.
6. **Jejak untuk studi berikutnya**: berapa soal probe yang dibutuhkan, varian mana yang bocor (anak hafal), topik mana yang paling responsif — input untuk studi n=10.

---

## 9. Keputusan yang ditentukan SEBELUM data (anti-rasionalisasi)

- **Gerbang lulus studi**: ≥2 dari 3 topik target mencapai `selesai` (mastery terverifikasi 2x) dalam 12 minggu **dan** pola staggered terlihat (perbaikan mengikuti garis intervensi per topik).
- **Gerbang gagal**: tidak ada topik yang selesai dalam 12 minggu, ATAU semua topik membaik bersamaan sejak minggu 1 (menunjukkan bukan efek intervensi), ATAU cek "dapat dari mana" selalu "menghafal" meski jawaban benar (Correct Answer Trap — PRD §1.2).
- **Di antara keduanya** (1 topik selesai, pola tidak jelas): lanjut 4 minggu lagi sebelum mengambil kesimpulan.

---

## 10. Kaitan dengan keputusan bisnis

| Hasil studi | Implikasi |
|---|---|
| Lulus (≥2 topik selesai, pola staggered) | Bukti mekanisme ada → lanjut Fase 2 roadmap; bahan untuk studi n=10 dan klaim pemasaran |
| 1 topik selesai | Perbaiki resep K (PRD §1.3 — naik kelas resep yang bekerja jadi pra-tulis); lanjutkan |
| Gagal total | Tesis remediasi tidak terbukti di kasus ini → tinjau ulang PRD §1 (mungkin loop verifikasi, mungkin konten resep, mungkin taksonomi) SEBELUM menambah fitur apa pun |

---

*Dokumen ini memakai mekanisme yang sudah ada di PRD (loop verifikasi §1.5, threshold K aktif §1.6, batch diagnosis §2.6, arsitektur file §8) — studi ini adalah formalisasi pengukuran, bukan komponen baru.*
