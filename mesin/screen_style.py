"""Gaya layar — CSS untuk lembar soal yang dibaca di browser/HP.

Dipecah dari worksheets.py (Fase 3). CSS cetak (print_style.py) memikirkan
kertas A4 ber-satuan mm; CSS ini memikirkan layar sentuh:

  - satuan mm diganti rem/px — di layar, 22mm tidak bermakna apa-apa
  - kartu soal vertikal penuh, bukan padat A4
  - target sentuh minimum ~44px (pedoman aksesibilitas mobile)
  - tanpa @page, tanpa page-break — itu urusan gaya cetak

Lembar yang sama dirender dua kali dengan dua gaya: satu sumber, dua
tampilan. Struktur DOM-nya identik supaya test yang menjaga "berkas anak
tidak memuat kunci" cukup ditulis sekali.

Nilai visual dipusatkan di design_tokens.py — ubah di sana, efek ke semua
permukaan.
"""

import design_tokens as T

GAYA_LAYAR = f"""
* {{ box-sizing: border-box; }}
html {{ -webkit-text-size-adjust: 100%; }}
body {{
  font-family: {T.FONT_LAYAR};
  font-size: {T.UKURAN_BADAN_LAYAR}; line-height: {T.LINE_HEIGHT}; color: {T.TEKS_UTAMA}; margin: 0;
  background: {T.LATAR_MURID};
}}
.wrap {{ max-width: {T.LEBAR_KONTEN}; margin: 0 auto; padding: {T.SP_4} 0.9rem 3rem; }}
h1 {{
  font-size: 1.35rem; margin: 0.2rem 0 0.9rem; color: {T.TEKS_JUDUL};
  display: flex; align-items: center; gap: 0.5rem;
}}
/* Header kartu-teal di mockup lembar; hanya dekoratif, tanpa fungsi. */
.mesin-banner {{
  display: flex; align-items: center; justify-content: space-between;
  background: {T.LATAR_KARTU_MURID}; border: 2px solid {T.AKSEN_MURID_UTAMA};
  border-radius: {T.RADIUS_KARTU}; padding: 0.55rem 0.9rem; margin-bottom: 0.7rem;
}}
.mesin-banner .nama-app {{ font-weight: 800; color: {T.AKSEN_TEAL_TUA}; }}
.mesin-banner .meta-sesi {{ font-size: 0.9rem; color: {T.TEKS_SUBTLE}; }}
.banner-kunci {{ border-color: {T.AKSEN_MURID_KORAL}; }}
.banner-kunci .nama-app {{ color: {T.AKSEN_KORAL_TUA}; }}
.kunci-headline {{
  background: {T.AKSEN_KORAL_TUA}; color: #fff; text-align: center;
  font-weight: 800; font-size: 1.2rem; letter-spacing: 0.04em;
  border-radius: {T.RADIUS_SEDANG}; padding: 0.6rem 1rem; margin-bottom: 0.8rem;
}}
.identitas {{
  background: {T.LATAR_KARTU_MURID}; border: 1px solid {T.BORDER_HALUS}; border-radius: {T.RADIUS_SEDANG};
  padding: 0.8rem 1rem; margin-bottom: 1rem; font-size: 0.95rem;
}}
.identitas span {{ display: block; padding: 0.45rem 0; }}
.garis {{
  display: inline-block; min-width: 9rem; min-height: 1.6em;
  vertical-align: bottom; border-bottom: 2px solid #333;
}}
.garis.pendek {{ min-width: 6rem; }}

.petunjuk {{
  background: {T.LATAR_KARTU_SEKUNDER}; border: 1px solid {T.BORDER_INTERAKTIF}; border-radius: {T.RADIUS_SEDANG};
  padding: 0.9rem 1rem; margin-bottom: 1.2rem; font-size: 0.95rem;
}}
.petunjuk p {{ margin: 0 0 0.6rem; }}
.petunjuk p:last-child {{ margin-bottom: 0; }}

.bagian {{
  font-size: 1.05rem; font-weight: 700; color: {T.TEKS_JUDUL};
  margin: 1.6rem 0 0.7rem; padding-bottom: 0.35rem;
  border-bottom: 2px solid {T.TEKS_JUDUL};
}}
.catatan-bagian {{
  background: {T.LATAR_CATATAN}; border: 1px solid {T.BORDER_CATATAN}; border-radius: {T.RADIUS_KECIL};
  padding: 0.55rem 0.8rem; margin: -0.2rem 0 0.8rem; font-size: 0.92rem;
}}

.soal {{
  background: {T.LATAR_KARTU_MURID}; border: 1px solid {T.BORDER_HALUS}; border-radius: {T.RADIUS_KARTU};
  padding: 1rem; margin-bottom: 1rem;
}}
.nomor {{
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 2rem; height: 2rem; font-weight: 700;
  background: {T.AKSEN_MURID_UTAMA}; color: #fff;
  border-radius: {T.RADIUS_BULAT}; margin-right: 0.55rem; font-size: 0.95rem;
}}
.teks {{ display: inline; }}
/* Dulu ".teks .deret" (keturunan) — tidak pernah cocok karena render.py
   menaruh kedua kelas di elemen yang SAMA, jadi deret tidak pernah
   diperbesar. */
.teks.deret {{ font-size: 1.25rem; letter-spacing: 0.03em; }}
/* Pertanyaan utama harus menonjol dari badan soal — dulu ukurannya sama,
   jadi anak kesulitan menemukan apa yang sebenarnya ditanya. */
.tanya {{ margin-top: 0.6rem; font-weight: 700; font-size: 1.06rem; }}

.label {{ font-size: 0.85rem; color: {T.TEKS_SUBTLE}; margin: 0.8rem 0 0.35rem; }}
/* Di layar, kotak Caraku dibiarkan kosong polos: anak mengerjakan di
   kertas atau lewat kanvas coret (Fase 4). Garis panduan SVG-tile adalah
   urusan kertas — jangan disalin ke sini. */
.cara {{
  border: 1.5px dashed #99a; border-radius: {T.RADIUS_KECIL};
  min-height: 96px; background: #fafafc;
}}
.cara.kecil  {{ min-height: 96px; }}
.cara.sedang {{ min-height: 120px; }}
.cara.besar  {{ min-height: 150px; }}

.restate {{
  border-bottom: 1.5px solid #667; min-height: 2rem; margin-bottom: 0.3rem;
}}
.jawab {{ margin-top: 0.8rem; font-size: 1.02rem; }}
.isian {{
  display: inline-block; min-width: 5.5rem; min-height: 2.2rem;
  border-bottom: 2px solid #333; vertical-align: bottom;
}}
.isian.lebar {{ min-width: 8rem; }}
.centang {{
  margin-top: 0.7rem; font-size: 0.9rem; color: #444;
  display: flex; align-items: center; gap: 0.5rem;
  min-height: {T.TARGET_SENTUH}; /* target sentuh */
}}
.kotak {{
  display: inline-block; width: 1.35rem; height: 1.35rem; flex: none;
  border: 2px solid #333; border-radius: 4px;
}}
.bintang {{ font-weight: 700; color: {T.AKSEN_MURID_AMBER}; }}
.akhir {{
  margin-top: 1.6rem; border-top: 2px solid {T.TEKS_JUDUL}; padding-top: 0.9rem;
  font-size: 0.95rem; background: {T.LATAR_KARTU_MURID}; border-radius: 0 0 {T.RADIUS_SEDANG} {T.RADIUS_SEDANG};
}}
svg {{ display: block; margin: 0.6rem 0; max-width: 100%; height: auto; }}

/* ── lembar penilaian (guru) ── */
.kunci-tabel {{ width: 100%; border-collapse: collapse; margin-top: 0.6rem; }}
.kunci-tabel th, .kunci-tabel td {{
  border: 1px solid {T.BORDER_HALUS}; padding: 0.4rem 0.55rem; font-size: 0.9rem;
  text-align: left;
}}
.kunci-tabel th {{ background: {T.LATAR_KARTU_SEKUNDER}; }}
.kode {{
  display: inline-block; min-width: 1.6rem; text-align: center;
  font-weight: 700; border: 1.5px solid {T.TEKS_JUDUL}; border-radius: 5px;
  padding: 0.1rem 0.3rem;
}}
.kunci-nilai {{ font-size: 1.15rem; font-weight: 700; margin-top: 0.5rem; }}
.rekap {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
.rekap th, .rekap td {{
  border: 1px solid {T.BORDER_HALUS}; padding: 0.65rem 0.55rem; font-size: 0.95rem;
}}
.rekap th {{ background: {T.LATAR_KARTU_SEKUNDER}; }}
.catatan-guru {{ font-size: 0.9rem; color: {T.TEKS_SUBTLE}; font-style: italic; }}
.meta-template {{ font-size: 0.8rem; color: {T.TEKS_SUBTLE}; }}

@media print {{
  /* Kalau user mencetak dari tampilan layar, jatuhkan ke perilaku cetak:
     satu sumber tetap menghasilkan kertas yang layak. */
  body {{ background: #fff; font-size: {T.UKURAN_BADAN_CETAK}; }}
  .wrap {{ max-width: none; padding: 0; }}
  .soal, .identitas, .petunjuk {{ border-color: #000; border-radius: 0; }}
  .soal {{ break-inside: avoid; }}
  .bagian {{ break-after: avoid; }}
}}
"""
