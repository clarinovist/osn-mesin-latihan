# Latihan

Lembar soal & penilaian untuk satu sesi latihan konkret.

## Penamaan

`<YYYY-MM-DD>-<level>-<topik>-{SOAL|PENILAIAN}.{md,html,pdf}`

Contoh: `2026-08-20-p3-pola-bilangan-SOAL.md` — soal untuk anak, level P3,
topik pola bilangan, tanggal 20 Agustus 2026.

## Lapisan

- **`.md` adalah sumber** — ditulis tangan atau dibangkitkan dari
  [`../mesin/`](../mesin/).
- **`.html` / `.pdf`** adalah ekspor untuk dicetak atau dilihat. Bisa
  dibangkitkan ulang.
- **`*-ISI.*` (lembar terisi)** bukan milik repo. Begitu anak menulis
  jawabannya, lembar jadi data anak dan masuk `.gitignore` lewat pola
  `latihan/*-ISI.*`. Konvensi alternatif: taruh di `latihan/hasil/`.

Lembar kosong (SOAL/PENILAIAN) tetap boleh masuk repo — itu lapisan konten,
bukan data.
