# Design System — OSN Mesin Latihan

Sumber tunggal untuk semua nilai visual aplikasi. Implementasi ada di
`mesin/design_tokens.py`; dokumen ini adalah referensi naratif.

Mockup UI/UX (9 halaman) ada di `desain-ui/`. Generator: `gen_guru.py`
(gpt-image-2 via chenzk.top).

## Dua palet, dua konteks

Aplikasi punya dua palet yang hidup berdampingan — bukan karena malas
menyatukan, tapi karena guru dan murid butuh emosi berbeda:

### Palet INTI (permukaan guru)

Dipakai di: dashboard, sesi, laporan, akun, lembar cetak (5 mockup guru).

| Token | Nilai | Konteks |
|-------|-------|---------|
| LATAR_INTI | #f0f1f4 | Badan halaman, abu muda netral |
| LATAR_KARTU | #fff | Kartu soal, identitas |
| LATAR_KARTU_SEKUNDER | #eef3fb | Petunjuk, kartu interaktif |
| TEKS_UTAMA | #111 | Body text |
| TEKS_JUDUL | #16213e | Heading, border, judul — biru tua |
| TEKS_SUBTLE | #555 | Label, meta |
| BORDER_HALUS | #d5d8de | Border kartu |
| BORDER_INTERAKTIF | #c4d3ea | Border petunjuk |
| LATAR_CATATAN | #fff7e6 | Catatan bagian |
| BORDER_CATATAN | #ecd9a8 | Border catatan |
| BINTANG | #b8860b | Challenge star (legacy gold) |

Filosofi: biru tua (#16213e) sebagai warna otoritas — guru butuh konsentrasi,
bukan semangat. Netral, terbaca lama, tidak melelahkan mata.

### Palet MURID (permukaan murid)

Dipakai di: /murid, /murid/kerjakan (2 mockup murid).

| Token | Nilai | Konteks |
|-------|-------|---------|
| LATAR_MURID | #FFF8EE | Cream hangat — badan halaman |
| AKSEN_MURID_UTAMA | #0FA3A3 | Teal — primary action, nomor badge |
| AKSEN_MURID_KORAL | #FF6B5B | Coral — tombol simpan, highlight |
| AKSEN_MURID_AMBER | #FFB020 | Amber — star/challenge |
| LATAR_KARTU_MURID | #fff | Kartu soal murid |

Filosofi: hangat dan cerah untuk anak SD. Teal sebagai aksen utama (bukan
biru tua) karena lebih ramah dan menos intimidating. Coral untuk CTA simpan
supaya menonjol dari teal.

### Status (diagnosis)

Dari mockup guru-laporan, untuk diagram tren dan diagnosis.

| Token | Nilai | Status |
|-------|-------|--------|
| STATUS_KUAT | #0FA3A3 | Teal — kuat |
| STATUS_LEMAH | #FFB020 | Amber — lemah |
| STATUS_SALAH | #FF6B5B | Coral — salah konsep |

## Tipografi

| Token | Nilai | Konteks |
|-------|-------|---------|
| FONT_LAYAR | -apple-system, "Segoe UI", Roboto, ... | Semua permukaan layar |
| FONT_CETAK | "Helvetica Neue", Arial, sans-serif | Lembar cetak A4 |
| UKURAN_BADAN_LAYAR | 16px | Body text layar |
| UKURAN_BADAN_CETAK | 10.5pt | Body text cetak |
| LINE_HEIGHT | 1.55 | Spacing baris |

Tidak ada font custom/webfont — pakai system stack supaya tidak ada loading
delay dan konsisten di semua device. Rounded sans-serif (terlihat di mockup)
tercapai via system font di Apple/Windows.

## Spacing

Skala 4px base, ratio 1.5x:

| Token | rem | px | Penggunaan |
|-------|-----|----|------------|
| SP_1 | 0.25rem | 4px | Gap mini |
| SP_2 | 0.5rem | 8px | Padding dalam, gap |
| SP_3 | 0.75rem | 12px | Padding kartu |
| SP_4 | 1rem | 16px | Default padding, margin |
| SP_5 | 1.5rem | 24px | Margin section |
| SP_6 | 2rem | 32px | Margin besar |

## Radius

| Token | Nilai | Konteks |
|-------|-------|---------|
| RADIUS_KARTU | 12px | Kartu soal |
| RADIUS_SEDANG | 10px | Petunjuk, identitas |
| RADIUS_KECIL | 8px | Catatan, input |
| RADIUS_PIL | 999px | Pilihan cara, badge |
| RADIUS_BULAT | 50% | Nomor badge (lingkaran) |

## Touch target

| Token | Nilai | Sumber |
|-------|-------|--------|
| TARGET_SENTUH | 44px | WCAG 2.5.5 — minimum untuk layar sentuh |
| LEBAR_KONTEN | 46rem | Max-width konten layar |

## Komponen patterns

Dari 9 mockup, pattern yang berulang:

1. **Kartu** — kontainer dasar: background putih/cream, border halus,
   radius 12px, padding 1rem, shadow halus. Dipakai di soal, petunjuk,
   identitas, stat cards, session cards.

2. **Nomor badge** — lingkaran dengan angka, border 2px teal (murid) atau
   biru tua (guru). Min 2rem x 2rem.

3. **Pill / badge** — border-radius 999px, padding .55rem .9rem,
   min-height 44px (touch target). Dipakai di pilihan "Caraku", badge soal,
   badge status.

4. **Btn (primary)** — background teal/coral (murid) atau biru tua (guru),
   text putih, border-radius 9px, padding .7rem 1.2rem.

5. **Btn (secondary)** — background abu muda, text biru tua, border halus.

6. **Sticky simpan bar** — position sticky bottom, background warna latar,
   button full-width coral. Hanya di halaman kerja murid.

7. **Tabel** — border-collapse, th background #eef/#eee, td border halus.
   Dipakai di dashboard (sesi), lembar penilaian (kunci), rekap.

## Viewport

| Viewport | Halaman | Orientasi mockup |
|----------|---------|-----------------|
| Mobile portrait | /murid, /murid/kerjakan | 1024x1536 |
| Desktop landscape | /, /masuk, /sesi, /laporan, /akun | 1536x1024 |
| A4 portrait | /lembar, /lembar/penilaian | 1024x1536 |

Halaman murid adalah mobile-first — di desktop, layout sama tapi column
di-tengah (max-width 46rem). Tidak perlu layout desktop terpisah.

## Cara pakai tokens di kode

```python
import design_tokens as T

# CSS string pakai f-string, escape {} jadi {{ }}
CSS = f"""
.soal {{
  background: {T.LATAR_KARTU};
  border-radius: {T.RADIUS_KARTU};
}}
"""
```

Aturan:
- Ubah nilai visual di `design_tokens.py`, bukan di file CSS.
- Jangan hardcode hex literal di file CSS — selalu rujuk token.
- Token baru tambahkan ke `design_tokens.py` + catat di dokumen ini.

## Mockup reference

| File | Halaman | Viewport |
|------|---------|----------|
| murid-sesiku.png | /murid — daftar sesi | Mobile |
| murid-kerjakan.png | /murid/kerjakan — halaman kerja | Mobile |
| guru-masuk.png | /masuk — login | Desktop |
| guru-dashboard.png | / — dashboard utama | Desktop |
| guru-sesi.png | /sesi/<id> — detail sesi | Desktop |
| guru-laporan.png | /laporan/<id> — laporan + tren | Desktop |
| guru-akun.png | /akun — kelola akun & siswa | Desktop |
| guru-lembar-soal.png | /lembar/<id> — soal cetak | A4 |
| guru-lembar-kunci.png | /lembar/<id>/penilaian — kunci cetak | A4 |

## Workflow: halaman baru

1. Generate mockup via gpt-image-2 (lihat `desain-ui/gen_guru.py`).
2. Ekstrak nilai visual baru ke `design_tokens.py` (jika ada).
3. Implementasi HTML/CSS di file yang sesuai, rujuk tokens.
4. Tambahkan ke tabel mockup reference di dokumen ini.
5. Jalankan tests: `./.venv/bin/python -m pytest __tests__/ -q`.
