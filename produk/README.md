# Produk

Spesifikasi & peta jalan produk diagnosis kesalahan matematika SD.

Berisi:

- **PRD** — spesifikasi arsitektur (malrule sebagai fungsi, status topik
  append-only, dua implementasi `tinta_heuristik`/`tinta_llm` diuji
  berdampingan, siklus `osn sync`, tanpa server/DB/internet).
- **Peta jalan** — urutan pengerjaan.
- **Rencana spike ke diagnosis** — bagaimana eksperimen perekam goresan
  (lihat [`../spike/`](../spike/)) menghubungkan diri ke produk.
- **Desain studi bukti v1** — protokol uji untuk membuktikan produk
  benar-benar bekerja di lapangan.

Dokumen hidup — yang menentukan *apa* yang harus dibuat, bukan *bagaimana*.
File .md adalah sumber; .pdf/.html di folder ini adalah ekspor dan masuk
.gitignore.
