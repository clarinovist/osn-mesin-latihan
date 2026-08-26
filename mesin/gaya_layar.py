"""Gaya layar — CSS untuk lembar soal yang dibaca di browser/HP.

Dipecah dari cetak.py (Fase 3). CSS cetak (gaya_cetak.py) memikirkan
kertas A4 ber-satuan mm; CSS ini memikirkan layar sentuh:

  - satuan mm diganti rem/px — di layar, 22mm tidak bermakna apa-apa
  - kartu soal vertikal penuh, bukan padat A4
  - target sentuh minimum ~44px (pedoman aksesibilitas mobile)
  - tanpa @page, tanpa page-break — itu urusan gaya cetak

Lembar yang sama dirender dua kali dengan dua gaya: satu sumber, dua
tampilan. Struktur DOM-nya identik supaya test yang menjaga "berkas anak
tidak memuat kunci" cukup ditulis sekali.
"""

GAYA_LAYAR = """
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 16px; line-height: 1.55; color: #111; margin: 0;
  background: #f0f1f4;
}
.wrap { max-width: 46rem; margin: 0 auto; padding: 1rem 0.9rem 3rem; }
h1 {
  font-size: 1.35rem; margin: 0.2rem 0 0.9rem; color: #16213e;
}
.identitas {
  background: #fff; border: 1px solid #d5d8de; border-radius: 10px;
  padding: 0.8rem 1rem; margin-bottom: 1rem; font-size: 0.95rem;
}
.identitas span { display: block; padding: 0.45rem 0; }
.garis {
  display: inline-block; min-width: 9rem; min-height: 1.6em;
  vertical-align: bottom;
}
.garis.pendek { min-width: 6rem; }

.petunjuk {
  background: #eef3fb; border: 1px solid #c4d3ea; border-radius: 10px;
  padding: 0.9rem 1rem; margin-bottom: 1.2rem; font-size: 0.95rem;
}
.petunjuk p { margin: 0 0 0.6rem; }
.petunjuk p:last-child { margin-bottom: 0; }

.bagian {
  font-size: 1.05rem; font-weight: 700; color: #16213e;
  margin: 1.6rem 0 0.7rem; padding-bottom: 0.35rem;
  border-bottom: 2px solid #16213e;
}

.soal {
  background: #fff; border: 1px solid #d5d8de; border-radius: 12px;
  padding: 1rem; margin-bottom: 1rem;
}
.nomor {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 2rem; height: 2rem; font-weight: 700;
  border: 2px solid #16213e; border-radius: 50%;
  margin-right: 0.55rem; font-size: 0.95rem;
}
.teks { display: inline; }
.teks .deret { font-size: 1.25rem; letter-spacing: 0.03em; }
.tanya { margin-top: 0.6rem; }

.label { font-size: 0.85rem; color: #555; margin: 0.8rem 0 0.35rem; }
/* Di layar, kotak Caraku dibiarkan kosong polos: anak mengerjakan di
   kertas atau lewat kanvas coret (Fase 4). Garis panduan SVG-tile adalah
   urusan kertas — jangan disalin ke sini. */
.cara {
  border: 1.5px dashed #99a; border-radius: 8px;
  min-height: 96px; background: #fafafc;
}
.cara.kecil  { min-height: 96px; }
.cara.sedang { min-height: 120px; }
.cara.besar  { min-height: 150px; }

.restate {
  border-bottom: 1.5px solid #667; min-height: 2rem; margin-bottom: 0.3rem;
}
.jawab { margin-top: 0.8rem; font-size: 1.02rem; }
.isian {
  display: inline-block; min-width: 5.5rem; min-height: 2.2rem;
  border-bottom: 2px solid #333; vertical-align: bottom;
}
.isian.lebar { min-width: 8rem; }
.centang {
  margin-top: 0.7rem; font-size: 0.9rem; color: #444;
  display: flex; align-items: center; gap: 0.5rem;
  min-height: 44px; /* target sentuh */
}
.kotak {
  display: inline-block; width: 1.35rem; height: 1.35rem; flex: none;
  border: 2px solid #333; border-radius: 4px;
}
.bintang { font-weight: 700; color: #b8860b; }
.akhir {
  margin-top: 1.6rem; border-top: 2px solid #16213e; padding-top: 0.9rem;
  font-size: 0.95rem; background: #fff; border-radius: 0 0 10px 10px;
}
svg { display: block; margin: 0.6rem 0; max-width: 100%; height: auto; }

/* ── lembar penilaian (guru) ── */
.kunci-tabel { width: 100%; border-collapse: collapse; margin-top: 0.6rem; }
.kunci-tabel th, .kunci-tabel td {
  border: 1px solid #ccd; padding: 0.4rem 0.55rem; font-size: 0.9rem;
  text-align: left;
}
.kunci-tabel th { background: #eef; }
.kode {
  display: inline-block; min-width: 1.6rem; text-align: center;
  font-weight: 700; border: 1.5px solid #16213e; border-radius: 5px;
  padding: 0.1rem 0.3rem;
}
.kunci-nilai { font-size: 1.15rem; font-weight: 700; margin-top: 0.5rem; }
.rekap { width: 100%; border-collapse: collapse; margin-top: 1rem; }
.rekap th, .rekap td {
  border: 1px solid #333; padding: 0.65rem 0.55rem; font-size: 0.95rem;
}
.rekap th { background: #eef; }

@media print {
  /* Kalau user mencetak dari tampilan layar, jatuhkan ke perilaku cetak:
     satu sumber tetap menghasilkan kertas yang layak. */
  body { background: #fff; font-size: 10.5pt; }
  .wrap { max-width: none; padding: 0; }
  .soal, .identitas, .petunjuk { border-color: #000; border-radius: 0; }
  .soal { break-inside: avoid; }
  .bagian { break-after: avoid; }
}
"""
