# OSN — Mesin Latihan & Eksperimen Pendukung

Repo aplikasi web Jagomat untuk beberapa keluarga: latihan matematika SD,
diagnosis kesalahan, remedial, laporan, serta eksperimen pendukung yang
terpisah dari aplikasi utama.

## Peta singkat

| Folder | Apa isinya |
|---|---|
| [`mesin/`](mesin/README.md) | **Aplikasi utama** — generator soal, diagnosis otomatis, lembar cetak, laporan per anak. Sudah dipakai. Mulai dari sini. |
| [`spike/`](spike/README.md) | Eksperimen perekam goresan jari (Fase 0) — ortogonal dari `mesin/`, tidak bergantung padanya. |
| [`riset-pasar/`](riset-pasar/README.md) | Validasi kebutuhan & pemetaan kompetitor. Acuan keputusan produk, bukan kode. |
| [`produk/`](produk/README.md) | PRD, peta jalan, dan desain studi. Mulai dari README folder itu karena sebagian dokumen adalah keputusan historis, bukan roadmap aktif. |
| [`kurikulum/`](kurikulum/README.md) | Acuan: kurikulum OSN SD 2027 + instrumen tes. PDF, tidak ada kode. |
| [`latihan/`](latihan/README.md) | Lembar soal & penilaian untuk satu sesi konkret. Pola penamaan: `<tanggal>-<level>-<topik>-{SOAL,PENILAIAN}.{md,html,pdf}`. Lembar yang sudah diisi (`*-ISI.*`) di-gitignore. |
| [`docs/`](docs/README.md) | Catatan keputusan & diskusi internal. `plan/` masuk .gitignore. |

## Untuk siapa

- **Guru (pengguna aplikasi)** → [`mesin/README.md`](mesin/README.md)
- **Penjaga repo / kontributor** → mulai dari `CLAUDE.md`, lalu baca
  [`produk/README.md`](produk/README.md) untuk hierarki dokumen keputusan.

## Aturan privasi

Tidak ada data anak yang boleh masuk repo. Basis data, hash sandi, lembar
terisi, dan cache LLM semuanya masuk `.gitignore` **sebelum** ada datanya —
lihat komentar di `.gitignore` untuk alasannya.
