# Lanjutan — mulai dari sini besok

Catatan singkat supaya tidak perlu membaca ulang seluruh Rencana Spike.
Diperbarui 19 Agustus 2026.

## Posisi sekarang

Hari 1–4 selesai. Hari 5 **belum**, tertahan di satu hal: perekam belum
pernah mendapat verdict `sehat`.

| Hari | Isi | Status |
|---|---|---|
| 1–2 | Kanvas tinta web + ekspor JSON | selesai |
| 3 | `render.py` (PNG + turunan waktu) + malrule Tahap A | selesai |
| 4 | `tinta_heuristik` (jalan) + `tinta_llm` (ditulis, **ditunda**) | selesai |
| 5 | Sesi sungguhan dengan anak | **tertahan** |
| 6–7 | Wawancara NEA, bandingkan, putuskan | belum |

## Yang sudah terbukti (jangan diuji ulang)

**Anak bisa menulis dengan jari.** Sesi 19 Agustus: 10/10 soal dikerjakan,
~6 menit, skor 5/10 benar. Tulisannya terbaca — soal 1 terbaca "36 : 4 = 9"
(langkahnya benar), soal 3 terbaca "1/4 + 3/5" (mengubah 0,25 jadi 1/4,
langkah yang cerdas). Kriteria berhenti Hari 1 **tidak terpicu**.

## Penghalang tunggal ke Hari 5

Sesi 19 Agustus dipakai di **Chrome Android**, dan di sana
`getCoalescedEvents` **tidak ada** (`coalesced_didukung: false`). Akibatnya
2884 event menghasilkan tepat 2884 titik — resolusi antar-frame hilang,
verdict `degradasi`.

Gerbang melarang membaca hasil apa pun atas data seperti itu:

> "Kalau angkanya ≈1,0, tabel di atas tidak berlaku — yang diuji bukan
> tesisnya melainkan perekam yang kehilangan resolusi antar-frame."

**Langkah berikutnya: ulangi di browser lain** (Firefox / Samsung Internet,
**bukan** Chrome) di HP yang sama. Kalau `periksa_sesi.py` menyebut `sehat`,
Hari 5 yang sungguhan boleh jalan dengan soal kalibrasi asli.

Kalau semua browser di HP itu memberi ≈1,0, barulah keputusan "web untuk
spike" perlu ditinjau ulang — dan itu temuan yang sah, bukan kegagalan.

## Perintah

```bash
cd ~/Documents/osn/spike

./.venv/bin/python bundel.py --soal=mudah   # -> latihan-mudah.html (uji alat)
./.venv/bin/python bundel.py                # -> latihan.html (kalibrasi asli)
./.venv/bin/python sajikan.py               # sajikan lewat WiFi, cetak alamatnya

# setelah berkas sesi dipindah ke ~/Downloads:
./.venv/bin/python periksa_sesi.py          # kesehatan alat DULU
./.venv/bin/python render.py '<sesi.json>'  # PNG + turunan.yaml
./.venv/bin/python diagnosa_sesi.py         # Tahap A + heuristik

bash test.sh                                # seluruh test, nol API
```

Alamat WiFi berubah tiap ganti jaringan — `sajikan.py` mencetak yang berlaku.

## Dua set soal

- `latihan.html` — 10 soal kalibrasi asli. Untuk sesi sungguhan.
- `latihan-mudah.html` — aritmetika dasar (`soal_mudah.json`). **Hanya untuk
  menguji alat**: tujuannya membuat anak banyak menulis, bukan mengukur
  kemampuan.

## Sinyal dari sesi 19 Agustus — simpan, jangan dibuang

Bukan "soal terlalu sulit", tapi topik tertentu ditinggalkan:

| Dikerjakan tekun | Ditinggalkan cepat |
|---|---|
| soal 4 persen — 44 goresan, 80s, benar | soal 2 pecahan — **0 goresan, 1 detik** |
| soal 1 urutan operasi — 41 goresan, benar | soal 6 KPK — 1 goresan, 8 detik |
| soal 13 satuan waktu — 38 goresan, benar | soal 10 volume — 2 goresan, 9 detik |
| soal 3 desimal — 31 goresan | soal 5 FPB — 6 goresan, 21 detik |

Yang dihindari: **FPB, KPK, volume, pecahan**. Nol goresan bukan "salah
hitung" — itu tidak tahu harus mulai dari mana. Berkas sesinya tetap berguna
sebagai pembanding meski angkanya tidak bisa dipakai untuk gerbang.

## Utang kecil yang belum dibayar

Pencocokan jawaban masih sensitif spasi: anak menulis `6 jam 25menit`, kunci
`6 jam 25 menit` — **benar tapi terhitung salah**. Kalau lolos ke Hari 6–7,
ini akan mencemari angka kecocokan. Perbaiki di `tahap_a.py` (`normalisasi()`)
sebelum menghitung gerbang.

## Batas yang tidak boleh dilanggar

- **Jangan push** tanpa perintah eksplisit.
- `tinta_llm.py` **ditunda** — mengirim tulisan tangan anak ke API pihak
  ketiga bertentangan dengan PRD §7.1. Dipalang `OSN_IZIN_KIRIM_DATA_ANAK=1`.
  Keputusan yang berlaku: ukur heuristik dulu; kalau ≥7/10 dengan nol
  false-K, LLM keluar dari lingkup v1 dan pertanyaan ini tidak pernah perlu
  dijawab.
- Data anak (`turunan/`, `kejadian/`, `cache_llm/`) gitignored — repo publik.
