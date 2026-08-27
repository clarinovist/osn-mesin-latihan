# OSN — Mesin Latihan & Eksperimen Pendukung

Repo untuk satu keluarga: dua anak, latihan pola bilangan, dan eksperimen
alat untuk produk yang lebih besar di belakang hari.

## Peta singkat

| Folder | Apa isinya |
|---|---|
| [`mesin/`](mesin/README.md) | **Aplikasi utama** — generator soal, diagnosis otomatis, lembar cetak, laporan per anak. Sudah dipakai. Mulai dari sini. |
| [`spike/`](spike/README.md) | Eksperimen perekam goresan jari (Fase 0) — ortogonal dari `mesin/`, tidak bergantung padanya. |
| [`riset-pasar/`](riset-pasar/README.md) | Validasi kebutuhan & pemetaan kompetitor. Acuan keputusan produk, bukan kode. |
| [`produk/`](produk/README.md) | PRD, peta jalan, desain studi bukti. Dokumen hidup — apa yang harus dibuat. |
| [`kurikulum/`](kurikulum/README.md) | Acuan: kurikulum OSN SD 2027 + instrumen tes. PDF, tidak ada kode. |
| [`latihan/`](latihan/README.md) | Lembar soal & penilaian untuk satu sesi konkret. Pola penamaan: `<tanggal>-<level>-<topik>-{SOAL,PENILAIAN}.{md,html,pdf}`. Lembar yang sudah diisi (`*-ISI.*`) di-gitignore. |
| [`docs/`](docs/README.md) | Catatan keputusan & diskusi internal. `plan/` masuk .gitignore. |

## Untuk siapa

- **Guru (pengguna aplikasi)** → [`mesin/README.md`](mesin/README.md)
- **Penjaga repo / kontributor** → mulai dari struktur di atas, lalu baca
  `produk/PRD.md` untuk konteks keputusan.

## Aturan privasi

Tidak ada data anak yang boleh masuk repo. Basis data, hash sandi, lembar
terisi, dan cache LLM semuanya masuk `.gitignore` **sebelum** ada datanya —
lihat komentar di `.gitignore` untuk alasannya.
