"""Gaya layar guru — CSS untuk 5 halaman guru (dashboard, sesi, laporan, akun, masuk).

Dipecah dari web.py (restyle 29 Aug 2026). Mengikuti mockup guru (guru-*.png):
cream hangat #FFF8EE + teal #0FA3A3 + coral #FF6B5B + amber #FFB020 — palet
yang SAMA dengan permukaan murid. Keputusan desain (29 Aug): guru dan murid
berbagi palet hangat; yang membedakan hanyalah kepadatan data. Guru butuh
konsentrasi, jadi kartu tetap netral putih di atas cream, dengan biru tua
#16213e untuk judul — persis murid.

Nilai visual dipusatkan di design_tokens.py — ubah di sana, efek ke semua
permukaan. Jangan hardcode hex literal di sini; selalu rujuk T.NAMA_TOKEN.

Kelas yang didefinisikan di sini harus mencakup SEMUA kelas yang dipakai
halaman guru di web.py (.kartu, .soal-kartu, .kode, .usulan, table, ...)
supaya tidak ada gaya patah. Daftar dipetakan dari fungsi halaman_* di
web.py: halaman_utama, halaman_sesi, halaman_laporan, halaman_akun,
_halaman_masuk, _kartu_akun_murid, _tombol_cerita, _halaman.
"""

import design_tokens as T

GAYA_GURU = f"""
* {{ box-sizing: border-box; }}
html {{ -webkit-text-size-adjust: 100%; }}
body {{
  font-family: {T.FONT_LAYAR};
  font-size: {T.UKURAN_BADAN_LAYAR}; line-height: {T.LINE_HEIGHT};
  color: {T.TEKS_UTAMA}; margin: 0; background: {T.LATAR_MURID};
}}
.bungkus {{ max-width: 960px; margin: 0 auto; padding: {T.SP_4} 0.9rem 3rem; }}
a {{ color: {T.AKSEN_MURID_UTAMA}; }}
h1 {{ font-size: 1.5rem; margin: 0.3rem 0 0.3rem; color: {T.TEKS_JUDUL}; }}
h2 {{ font-size: 1.15rem; margin: 1.4rem 0 0.6rem; color: {T.TEKS_JUDUL}; }}
.sub {{ color: {T.TEKS_SUBTLE}; font-size: .9rem; margin: 0 0 1.3rem; }}
.jejak {{ font-size: .88rem; margin: 0 0 0.8rem; color: {T.TEKS_SUBTLE}; }}
.jejak a {{ color: {T.TEKS_SUBTLE}; text-decoration: none; }}
.jejak a:hover {{ color: {T.AKSEN_MURID_UTAMA}; }}

/* ── Kartu ─────────────────────────────────────────────────────────── */
.kartu {{
  background: {T.LATAR_KARTU_MURID}; border: 1px solid {T.BORDER_HALUS};
  border-radius: {T.RADIUS_KARTU}; padding: 1rem 1.1rem; margin-bottom: 1rem;
  box-shadow: 0 1px 3px rgba(22,33,62,0.04);
}}
.kartu h2 {{ margin-top: 0; }}

/* ── Tombol ────────────────────────────────────────────────────────── */
button {{
  background: {T.AKSEN_MURID_UTAMA}; color: #fff; border: 0;
  border-radius: 9px; padding: .7rem 1.2rem; font-size: 1rem; cursor: pointer;
}}
button:hover {{ filter: brightness(0.94); }}
button.tombol-sekunder {{
  background: {T.LATAR_KARTU_SEKUNDER}; color: {T.TEKS_JUDUL};
  border: 1px solid {T.BORDER_INTERAKTIF};
}}
button.tombol-coral {{ background: {T.AKSEN_MURID_KORAL}; }}
button.tombol-amber {{
  background: #fff; color: {T.AKSEN_MURID_AMBER};
  border: 1.5px solid {T.AKSEN_MURID_AMBER};
}}
button.tombol-kecil {{ padding: .35rem .7rem; font-size: .82rem; border-radius: 6px; }}
button.tombol-putih {{
  background: #fff; color: {T.TEKS_JUDUL}; border: 1px solid {T.BORDER_KUAT};
}}
.btn {{
  display: inline-block; padding: .55rem 1rem; border-radius: 8px;
  font-size: .9rem; text-decoration: none; background: {T.LATAR_KARTU_SEKUNDER};
  color: {T.TEKS_JUDUL}; border: 1px solid {T.BORDER_INTERAKTIF};
}}
.btn.utama {{ background: {T.AKSEN_MURID_UTAMA}; color: #fff; border: 0; }}
.btn.coral {{ background: {T.AKSEN_MURID_KORAL}; color: #fff; border: 0; }}

/* ── Header halaman guru (mockup guru-dashboard) ───────────────────── */
.topbar {{
  display: flex; align-items: center; justify-content: space-between;
  gap: 1rem; padding: 0.6rem 0 0.2rem; margin-bottom: 0.4rem;
  border-bottom: 1px solid {T.BORDER_HALUS};
}}
.brand {{
  font-weight: 800; font-size: 1.15rem; color: {T.AKSEN_MURID_UTAMA};
  display: flex; align-items: center; gap: .55rem;
}}
.brand img {{ width: 34px; height: 34px; }}
.topbar-navigasi {{ display: flex; align-items: center; gap: .7rem; }}
.topbar-navigasi a {{ color: {T.TEKS_SUBTLE}; text-decoration: none; font-size: .9rem; }}
.topbar-navigasi a:hover {{ color: {T.AKSEN_MURID_UTAMA}; }}
.topbar-navigasi form {{ margin: 0; }}
.badge-peran {{
  display: inline-block; padding: .12rem .55rem; border-radius: {T.RADIUS_PIL};
  font-size: .7rem; font-weight: 700; letter-spacing: .02em;
  vertical-align: middle;
}}
.badge-peran-admin {{ background: {T.BADGE_ADMIN_BG}; color: {T.BADGE_ADMIN_TEKS}; }}
.badge-peran-guru {{ background: {T.BADGE_GURU_BG}; color: {T.BADGE_GURU_TEKS}; }}
.badge-keluarga {{
  display: inline-block; margin-left: .45rem; padding: .1rem .5rem;
  border-radius: {T.RADIUS_PIL}; font-size: .72rem; font-weight: 600;
  background: {T.LATAR_KARTU_SEKUNDER}; color: {T.TEKS_JUDUL};
  border: 1px solid {T.BORDER_INTERAKTIF};
}}

/* ── Menu pengguna dropdown (CSS-only) ────────────────────────────── */
.menu-pengguna {{ position: relative; }}
.menu-pengguna summary {{
  display: flex; align-items: center; gap: .4rem;
  padding: .35rem .7rem; border: 1px solid {T.BORDER_INTERAKTIF};
  border-radius: 8px; cursor: pointer; font-size: .9rem;
  color: {T.TEKS_JUDUL}; background: none; list-style: none;
}}
.menu-pengguna summary::-webkit-details-marker {{ display: none; }}
.menu-pengguna[open] summary {{ border-color: {T.AKSEN_MURID_UTAMA}; }}
.menu-isi {{
  position: absolute; right: 0; top: calc(100% + .4rem);
  background: {T.LATAR_KARTU_MURID}; border: 1px solid {T.BORDER_HALUS};
  border-radius: {T.RADIUS_KARTU};
  box-shadow: 0 8px 24px rgba(0,0,0,.08);
  min-width: 12rem; padding: .4rem; z-index: 20;
  display: flex; flex-direction: column;
}}
.menu-isi a, .menu-isi button {{
  display: block; width: 100%; text-align: left;
  padding: .45rem .6rem; border-radius: 6px; background: none; border: none;
  color: {T.TEKS_JUDUL}; text-decoration: none; font-size: .9rem;
  cursor: pointer; font-family: inherit;
}}
.menu-isi a:hover, .menu-isi button:hover {{ background: {T.LATAR_KARTU_SEKUNDER}; }}
.menu-pisah {{ border-top: 1px solid {T.BORDER_HALUS}; margin: .3rem 0; }}

/* ── Sidebar halaman /akun ────────────────────────────────────────── */
.layout-samping {{
  display: grid; grid-template-columns: 13rem 1fr;
  gap: 1.2rem; align-items: start;
}}
.nav-samping {{
  display: flex; flex-direction: column; gap: .25rem;
  position: sticky; top: 1rem;
}}
.nav-samping a {{
  padding: .5rem .7rem; border-radius: 8px; text-decoration: none;
  color: {T.TEKS_SUBTLE}; font-size: .92rem; border: 1px solid transparent;
}}
.nav-samping a.aktif {{
  color: {T.AKSEN_MURID_UTAMA}; border-color: {T.BORDER_HALUS};
  font-weight: 600; background: {T.LATAR_KARTU_SEKUNDER};
}}
@media (max-width: 46rem) {{
  .layout-samping {{ grid-template-columns: 1fr; }}
  .nav-samping {{ flex-direction: row; flex-wrap: wrap; position: static; }}
}}

/* ── Dashboard: kartu siswa side-by-side (mockup guru-dashboard) ───── */
.grid-utama {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
@media (max-width: 46rem) {{ .grid-utama {{ grid-template-columns: 1fr; }} }}
.kartu-siswa {{ margin-bottom: 0; }}
.siswa-kepala {{
  display: flex; align-items: center; justify-content: space-between;
  gap: .6rem; margin-bottom: .7rem;
}}
.siswa-kepala h2 {{ margin: 0; font-size: 1.15rem; }}
.badge-tingkat {{
  font-size: .78rem; font-weight: 700; color: {T.AKSEN_MURID_UTAMA};
  background: {T.LATAR_KARTU_SEKUNDER}; padding: .15rem .5rem;
  border-radius: {T.RADIUS_PIL}; margin-left: .3rem;
}}
.badge-mode {{
  font-size: .78rem; font-weight: 700; color: {T.AKSEN_MURID_KORAL};
  background: {T.LATAR_TERSIMPAN}; border: 1px solid {T.BORDER_TERSIMPAN};
  padding: .12rem .5rem; border-radius: {T.RADIUS_PIL}; white-space: nowrap;
}}
.siswa-kepala a {{ font-size: .85rem; white-space: nowrap; }}
.kosong-hint-guru {{
  border: 1.5px dashed {T.BORDER_HALUS}; text-align: center;
  color: {T.TEKS_SUBTLE}; font-size: 1rem; padding: 2.5rem;
}}

/* ── Tabel ─────────────────────────────────────────────────────────── */
table {{ width: 100%; border-collapse: collapse; background: #fff; }}
th, td {{
  border: 1px solid {T.BORDER_HALUS}; padding: .5rem .6rem; text-align: left;
  font-size: .88rem;
}}
th {{ background: {T.LATAR_KARTU_SEKUNDER}; color: {T.TEKS_JUDUL}; font-weight: 600; }}
.angka {{ text-align: right; font-variant-numeric: tabular-nums; }}
.kosong {{ color: {T.TEKS_SUBTLE}; font-style: italic; }}
.tipe {{ color: {T.TEKS_SUBTLE}; font-size: .82rem; }}
.tabel-wrap {{ overflow-x: auto; }}

/* ── Form ──────────────────────────────────────────────────────────── */
label {{ display: block; font-size: .84rem; color: {T.TEKS_SUBTLE}; margin: .55rem 0 .2rem; }}
input[type=text], input[type=password], textarea, select {{
  width: 100%; padding: .5rem .6rem; border: 1px solid {T.BORDER_HALUS};
  border-radius: {T.RADIUS_KECIL}; font-size: .95rem; font-family: inherit;
  background: #fff; color: {T.TEKS_UTAMA};
}}
input[type=text]:focus, input[type=password]:focus, textarea:focus, select:focus {{
  outline: none; border-color: {T.AKSEN_MURID_UTAMA};
  box-shadow: 0 0 0 2px rgba(15,163,163,0.12);
}}
textarea {{ min-height: 3.2rem; resize: vertical; }}
.baris {{ display: flex; gap: .8rem; flex-wrap: wrap; }}
.baris > * {{ flex: 1; min-width: 180px; }}

/* ── Pilihan mode & timer saat buat sesi (Latihan Cepat) ───────────── */
.mode-pilih {{ display: flex; flex-wrap: wrap; gap: .4rem 1rem; margin-top: .2rem; }}
.mode-opsi {{ display: flex; align-items: center; gap: .4rem; font-size: .88rem;
  color: {T.TEKS_UTAMA}; margin: 0; }}
.mode-opsi input {{ width: auto; margin: 0; }}
.pengaturan-timer {{
  border: 1.5px dashed {T.BORDER_HALUS}; border-radius: {T.RADIUS_KECIL};
  padding: .55rem .7rem; background: {T.LATAR_KARTU_MURID};
}}
.pengaturan-timer label {{ margin: .2rem 0; }}
.pengaturan-timer input[type=number] {{ padding: .3rem .45rem; }}

/* ── Halaman sesi: kartu soal (mockup guru-sesi) ───────────────────── */
.peta {{ margin-bottom: 1rem; }}
.soal-kartu {{ border-left: 4px solid {T.BORDER_HALUS}; }}
.soal-kartu.sudah {{ border-left-color: {T.STATUS_KUAT}; }}
.soal-kartu.perlu {{ border-left-color: {T.STATUS_LEMAH}; }}
.kartu-kepala {{
  display: flex; align-items: center; gap: .55rem; margin-bottom: .5rem;
}}
.nomor {{
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 2.1rem; height: 2.1rem; font-weight: 700; font-size: .95rem;
  background: {T.AKSEN_MURID_UTAMA}; color: #fff;
  border-radius: {T.RADIUS_BULAT};
}}
.teks-soal {{
  background: {T.LATAR_KARTU_SEKUNDER}; border: 1px solid {T.BORDER_INTERAKTIF};
  border-radius: {T.RADIUS_KECIL}; padding: .55rem .7rem; margin: .4rem 0;
  white-space: pre-wrap; font-size: .93rem;
}}
.kunci {{ font-weight: 700; color: {T.STATUS_LEMAH}; }}
.centang {{
  display: flex; align-items: center; gap: .45rem; margin-top: .55rem;
  font-size: .88rem; color: {T.TEKS_SUBTLE};
}}
.centang input {{ width: auto; }}
.usulan {{
  background: {T.LATAR_KARTU_SEKUNDER}; border: 1px solid {T.BORDER_INTERAKTIF};
  border-radius: 8px; padding: .5rem .6rem; margin-top: .55rem; font-size: .87rem;
}}
.usulan.ragu {{ background: {T.LATAR_CATATAN}; border-color: {T.BORDER_CATATAN}; }}

/* Kode pill (diagnosis) — warna per kode, lihat design_tokens */
.kode {{
  display: inline-block; min-width: 1.9rem; text-align: center;
  font-weight: 700; border-radius: {T.RADIUS_PIL}; padding: .18rem .5rem;
  font-size: .82rem;
}}
.kode.K {{ background: {T.KODE_SALAH_KONSEP_BG}; color: {T.KODE_SALAH_KONSEP_TEKS}; }}
.kode.B {{ background: {T.KODE_SALAH_BACA_BG}; color: {T.KODE_SALAH_BACA_TEKS}; }}
.kode.H {{ background: {T.KODE_SALAH_HITUNG_BG}; color: {T.KODE_SALAH_HITUNG_TEKS}; }}
.kode.E {{ background: {T.KODE_SALAH_TULIS_BG}; color: {T.KODE_SALAH_TULIS_TEKS}; }}
.kode.T {{ background: {T.KODE_BELUM_LIAT_BG}; color: {T.KODE_BELUM_LIAT_TEKS}; }}
.kode.N {{ background: {T.KODE_MENEBAK_BG}; color: {T.KODE_MENEBAK_TEKS}; }}
.kode.benar {{ background: {T.KODE_BENAR_BG}; color: {T.KODE_BENAR_TEKS}; }}

/* Tombol variasi cerita (LLM) — amber outline, sesuai mockup */
.kartu-variasi h2 {{ display: flex; align-items: center; gap: .5rem; }}

/* Sticky simpan bar */
.simpan-strip {{
  position: sticky; bottom: 0; padding: .8rem 0 .4rem;
  background: linear-gradient(to top, {T.LATAR_MURID} 70%, transparent);
}}
.simpan-strip button {{ width: 100%; font-size: 1.05rem; padding: .85rem; }}

/* ── Halaman laporan (mockup guru-laporan) ─────────────────────────── */
.kartu-stat {{
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;
  margin-bottom: 1.2rem;
}}
@media (max-width: 42rem) {{ .kartu-stat {{ grid-template-columns: 1fr; }} }}
.stat {{
  background: {T.LATAR_KARTU_MURID}; border: 1px solid {T.BORDER_HALUS};
  border-radius: {T.RADIUS_KARTU}; padding: 1rem; text-align: center;
  box-shadow: 0 1px 3px rgba(22,33,62,0.04);
}}
.stat .angka-besar {{
  font-size: 2rem; font-weight: 800; color: {T.AKSEN_MURID_UTAMA};
  line-height: 1.1;
}}
.stat .stat-label {{ color: {T.TEKS_SUBTLE}; font-size: .88rem; margin-top: .3rem; }}
.stat .stat-nilai-utama {{ font-size: 1.15rem; font-weight: 700; color: {T.TEKS_JUDUL}; }}

.layout-laporan {{ display: grid; grid-template-columns: 2fr 1fr; gap: 1rem; }}
@media (max-width: 46rem) {{ .layout-laporan {{ grid-template-columns: 1fr; }} }}
.chart-wrap {{ overflow-x: auto; }}
.chart-wrap svg {{ display: block; margin: 0 auto; max-width: 100%; }}

.diagnosis-lis {{ list-style: none; margin: 0; padding: 0; }}
.diagnosis-lis li {{
  display: flex; align-items: flex-start; gap: .65rem; padding: .6rem 0;
  border-bottom: 1px solid {T.BORDER_HALUS}; font-size: .92rem;
}}
.diagnosis-lis li:last-child {{ border-bottom: none; }}
.dot {{
  flex: none; width: .85rem; height: .85rem; border-radius: {T.RADIUS_BULAT};
  margin-top: .3rem;
}}
.dot.kuat {{ background: {T.STATUS_KUAT}; }}
.dot.lemah {{ background: {T.STATUS_LEMAH}; }}
.dot.salah {{ background: {T.STATUS_SALAH}; }}

/* ── Halaman akun (mockup guru-akun) ───────────────────────────────── */
.kartu-judul {{
  display: flex; align-items: center; gap: .6rem; margin: 0 0 .7rem;
}}
.ikon-kartu {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 2rem; height: 2rem; border-radius: {T.RADIUS_BULAT};
  background: {T.AKSEN_MURID_UTAMA}; color: #fff; font-size: 1rem;
}}
.ikon-kartu.amber {{ background: {T.AKSEN_MURID_AMBER}; }}
.baris-aksi {{ display: flex; align-items: center; gap: .3rem; }}
.tombol-hapus {{
  background: {T.KODE_SALAH_KONSEP_BG}; color: {T.KODE_SALAH_KONSEP_TEKS};
  border: 1px solid {T.KODE_SALAH_KONSEP_TEKS};
}}
.baris-form {{ display: flex; gap: .7rem; align-items: flex-end; flex-wrap: wrap; }}
.baris-form > div {{ flex: 1; min-width: 150px; }}
.status-ok {{ color: {T.STATUS_KUAT}; }}
.status-buruk {{ color: {T.STATUS_SALAH}; }}

/* ── Halaman masuk (mockup guru-masuk) ─────────────────────────────── */
.layout-masuk {{
  display: grid; grid-template-columns: 1fr 1fr; min-height: calc(100vh - 6rem);
  align-items: center; gap: 2rem; max-width: 860px; margin: 0 auto;
}}
@media (max-width: 46rem) {{ .layout-masuk {{ grid-template-columns: 1fr; min-height: auto; }} }}
.masuk-kiri {{ text-align: center; }}
.masuk-kiri img {{ width: 200px; height: 200px; max-width: 70vw; }}
.masuk-kiri h1 {{
  font-size: 1.8rem; margin: .4rem 0 0; color: {T.AKSEN_MURID_UTAMA};
}}
.masuk-kiri p {{ color: {T.TEKS_SUBTLE}; margin: .2rem 0 0; }}
.masuk-kanan {{ display: flex; justify-content: center; }}
.kartu-masuk {{
  width: 100%; max-width: 380px; padding: 1.6rem;
}}
.kartu-masuk .ikon-gembok {{
  display: block; margin: 0 auto .8rem; width: 44px; height: 44px;
}}
.kartu-masuk button {{ width: 100%; margin-top: .7rem; padding: .8rem; }}

/* ── Pesan (sukses/galat) ──────────────────────────────────────────── */
.pesan {{
  background: {T.LATAR_TERSIMPAN}; border: 1px solid {T.BORDER_TERSIMPAN};
  color: {T.TEKS_TERSIMPAN}; border-radius: {T.RADIUS_SEDANG};
  padding: .7rem .9rem; margin-bottom: 1rem; font-size: .93rem;
}}
.pesan.galat {{ background: {T.LATAR_GALAT}; border-color: {T.BORDER_GALAT}; color: {T.TEKS_GALAT}; }}
.pesan-terlarang {{ background: {T.LATAR_GALAT}; border-color: {T.BORDER_GALAT}; }}

/* Masuk yg gagal / 401 */
.masuk-luar {{
  background: {T.LATAR_MURID}; border: 1px solid {T.BORDER_HALUS};
  border-radius: {T.RADIUS_KARTU}; padding: 1.4rem; max-width: 440px;
  margin: 2rem auto; text-align: center;
}}

@media print {{
  body {{ background: #fff; }}
  .simpan-strip, .tombol-coral, .tombol-kecil {{ display: none; }}
}}
"""
