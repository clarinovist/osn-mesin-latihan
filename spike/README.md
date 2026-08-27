# Spike — Perekam Goresan Jari (Fase 0)

Eksperimen untuk membuktikan asumsi alat sebelum produk dibangun:
**bukan** turunan dari [`../mesin/`](../mesin/), bukan *mock* produk, bukan
fondasi aplikasi.

## Apa yang dibuktikan

Apakah tulisan tangan anak bisa:

1. Direkam di peramban HP lewat sentuhan jari.
2. Dirender ke PNG yang cukup jelas untuk dibaca.
3. Dicocokkan dengan tabel malrule deterministik (Tahap A).
4. Didiagnosis dengan heuristik (Tahap B).

Status & posisi terkini: [`LANJUTAN.md`](LANJUTAN.md).

## Struktur

- `tahap_a.py` — pencocokan malrule deterministik dari `malrule.yaml`.
- `tinta_heuristik.py`, `tinta_llm.py` — dua pendekatan diagnosis diuji
  berdampingan (lihat [`../produk/PRD.md`](../produk/PRD.md)).
- `render.py`, `sajikan.py` — render sesi JSON ke PNG + server lokal
  untuk diuji dari HP lewat WiFi.
- `bundel.py` — menggabungkan `index.html` + `toSamples.js` jadi satu
  berkas (`latihan.html` — di-gitignore karena bisa dibangkitkan ulang).
- `index.html`, `toSamples.js` — frontend statis.
- `turunan/` — data turunan waktu (tidak di-track).
- `requirements.txt` — dependensi spike, terpisah dari `mesin/`.

## Orthogonal dari `mesin/`

Tidak ada import silang. Kalau `mesin/` dirombak, `spike/` tidak
terpengaruh — dan sebaliknya. Ini disengaja: produk yang lebih besar akan
mengambil *yang terbukti* dari spike, bukan *kode* spike.
