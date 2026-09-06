# Produk

Dokumen keputusan produk Jagomat. Folder ini memuat prinsip yang masih dipakai
serta artefak konsep awal yang mendahului aplikasi web sekarang.

## Hierarki sumber kebenaran saat ini

| Sumber | Peran |
|---|---|
| Kode dan test di `../mesin/` | Kebenaran perilaku yang sudah diimplementasikan |
| `../CLAUDE.md` | Palang arsitektur, privasi, pengujian, dan aturan kerja repo |
| [`Siklus Belajar Terpandu.md`](Siklus%20Belajar%20Terpandu.md) | **Sumber kebenaran produk untuk siklus aktif**—alur, bukti, fokus, intervensi, evaluasi, checkpoint |
| `PRD.md` | Prinsip pedagogis dan riwayat keputusan awal; arsitektur file/Android di dalamnya sudah superseded |
| `Rencana Produk - Peta Jalan.md` | Konsolidasi historis 14–18 Agustus, bukan urutan kerja aktif |
| `Rencana Spike - Coretan ke Diagnosis.md` | Rencana historis eksperimen goresan di `../spike/` |
| `Desain Studi Bukti v1.md` | Protokol studi yang baru boleh dijalankan setelah siklus terpandu tersedia |

Aturan membaca: klaim “sudah tersedia” harus dibuktikan dari kode/test atau
runtime produksi. Jika PRD/peta jalan lama berbeda dengan `CLAUDE.md`, kode,
atau plan siklus terbaru, sumber yang lebih baru itulah yang berlaku.

File `.md` adalah sumber; `.pdf`/`.html` di folder ini adalah ekspor historis
dan masuk `.gitignore`.
