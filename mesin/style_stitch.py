"""Style Stitch — CSS bersama untuk adopsi desain Stitch (16 halaman).

Ditulis berdiri sendiri supaya setiap halaman yang difase-in memakai ini dan
modul lama (teacher_style.GAYA_GURU, student_pages.CSS_MURID) TIDAK dihapus
sampai cleanup Fase akhir. Semua nilai rujuk design_tokens (T.*).

Kelas dipisah dengan suffix "-st" agar tidak tabrakan dengan CSS lama yang
masih bertugas di halaman yang belum difase-in.
"""

import design_tokens as T

GAYA_STITCH = f"""
/* ── Font CDN (diizinkan 2026-09-01) ──────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?'
  'family=Be+Vietnam+Pro:wght@400;600;700'
  '&family=Plus+Jakarta+Sans:wght@400;500;600;700;800'
  '&family=Material+Symbols+Outlined'
  '&display=swap');

* {{ box-sizing: border-box; }}
html {{ -webkit-text-size-adjust: 100%; }}
body.st {{
  font-family: {T.FONT_BODY};
  font-size: {T.UKURAN_BADAN_LAYAR};
  line-height: {T.LINE_HEIGHT};
  color: {T.TEKS_UTAMA};
  margin: 0;
  background: {T.LATAR_MURID};
}}

.material-symbols-outlined {{
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  font-family: 'Material Symbols Outlined', sans-serif;
  font-style: normal; font-weight: normal;
  display: inline-block; line-height: 1; letter-spacing: normal;
  text-transform: none; white-space: nowrap; word-wrap: normal;
  direction: ltr; -webkit-font-smoothing: antialiased;
}}
.material-symbols-outlined.fill {{
  font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}}

h1.st, h2.st, h3.st, .st-headline {{
  font-family: {T.FONT_HEADLINE};
  color: {T.TEKS_JUDUL};
}}
h1.st {{ font-size: 1.75rem; margin: 0.4rem 0; font-weight: 800; letter-spacing: -0.02em; }}
h2.st {{ font-size: 1.25rem; margin: 1rem 0 0.6rem; font-weight: 700; }}
h3.st {{ font-size: 1.05rem; margin: 0.4rem 0; font-weight: 700; }}

/* Topbar */
.st-topbar {{
  background: {T.LATAR_SEKUNDER_LEMBUT};
  border-bottom: 1px solid {T.BORDER_VARIAN};
  height: {T.TARGET_SENTUH};
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 {T.SP_4};
  width: 100%; max-width: {T.LEBAR_KONTEN};
  margin: 0 auto;
  position: sticky; top: 0; z-index: 50;
  font-family: {T.FONT_HEADLINE};
}}
.st-topbar .brand {{ display: flex; align-items: center; gap: {T.SP_2}; font-weight: 800; }}
.st-topbar .brand .owl {{
  color: {T.AKSEN_MURID_UTAMA}; font-size: 1.35rem;
  display: inline-flex; align-items: center;
}}
.st-topbar .brand .nama {{ color: {T.AKSEN_MURID_UTAMA}; font-size: 1.1rem; }}
.st-topbar .cta {{
  font: inherit; color: {T.AKSEN_MURID_KORAL};
  background: none; border: 0;
  padding: {T.SP_2} {T.SP_4}; font-weight: 700;
  min-height: {T.TARGET_SENTUH};
}}
.st-topbar .cta:hover {{ opacity: .9; }}

/* Kartu utama */
.st-kartu {{
  background: {T.LATAR_KARTU};
  border: 1px solid {T.BORDER_VARIAN};
  border-radius: {T.RADIUS_KARTU};
  padding: {T.SP_4};
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
}}
.st-kartu:hover {{
  border-color: {T.FOKUS_AKSEN};
  box-shadow: 0 2px 8px rgba(0,106,106,0.12);
}}

/* Banner sukses */
.st-banner-sukses {{
  background: {T.LATAR_TERSIMPAN};
  border: 1px solid {T.BORDER_TERSIMPAN};
  color: {T.TEKS_TERSIMPAN};
  border-radius: {T.RADIUS_KARTU};
  padding: {T.SP_3} {T.SP_4};
  display: flex; gap: {T.SP_3}; align-items: center;
  margin: 0 0 {T.SP_4};
}}
.st-banner-sukses .ikon {{
  background: {T.BORDER_TERSIMPAN};
  color: {T.TEKS_TERSIMPAN};
  border-radius: 50%; width: 24px; height: 24px;
  display: inline-flex; align-items: center; justify-content: center;
  font-weight: bold;
}}

/* Badge status mode */
.st-badge {{
  display: inline-flex; align-items: center; gap: {T.SP_1};
  border-radius: {T.RADIUS_PIL};
  padding: {T.SP_1} {T.SP_3};
  font-family: {T.FONT_HEADLINE};
  font-weight: 600; font-size: .78rem; letter-spacing: .01em;
}}
.st-badge.diagnostik {{ background: {T.STATUS_DIAGNOSTIK_BG}; color: {T.STATUS_DIAGNOSTIK_TEKS}; }}
.st-badge.latihan    {{ background: {T.STATUS_LATIHAN_BG};    color: {T.STATUS_LATIHAN_TEKS}; }}
.st-badge.baru       {{ background: {T.AKSEN_MURID_KORAL};    color: #fff; }}
.st-badge.selesai    {{ background: {T.LATAR_ELEVASI};        color: {T.TEKS_VARIAN}; }}

/* Input + tombol */
.st-input {{
  font: inherit; font-size: 1rem;
  min-height: {T.TARGET_SENTUH};
  border-radius: {T.RADIUS_SEDANG};
  border: 1px solid {T.BORDER_VARIAN};
  background: {T.LATAR_KARTU};
  padding: 0 {T.SP_3};
  width: 100%;
}}
.st-input:focus {{
  border-color: {T.FOKUS_AKSEN}; outline: 0;
  box-shadow: 0 0 0 3px {T.AKSEN_MURID_UTAMA}55; /* ring teal lembut */
}}
.st-tombol-coral {{
  font: inherit;
  background: {T.AKSEN_MURID_KORAL}; color: {T.TEKS_PUTIH};
  border: 0; border-radius: {T.RADIUS_SEDANG};
  min-height: {T.TARGET_SENTUH};
  padding: 0 {T.SP_5};
  font-weight: 700; cursor: pointer;
}}
.st-tombol-coral:hover {{ filter: brightness(1.06); }}

/* Baris kartu ( sesi / hasil / item list — dipakai dashboard, murid, dsb ) */
.st-kartu-baris {{
  display: flex; align-items: center; gap: {T.SP_4};
  background: {T.LATAR_KARTU};
  border: 1px solid {T.BORDER_VARIAN};
  border-radius: {T.RADIUS_KARTU};
  padding: {T.SP_3} {T.SP_4};
}}
/* Juga badge-keluarga untuk data — admin melihat siapa pemilik keluarga */
.badge-keluarga {{
  font-size: .7rem; font-weight:700;
  background: {T.BADGE_ADMIN_BG};
  color: {T.BADGE_ADMIN_TEKS};
  padding: .15rem .5rem; border-radius: {T.RADIUS_PIL}; margin-left: .25rem;
}}

/* Baris jadwal sesi (pasangan kekeluargaan untuk grid kel) */
.st-kartu-baris {{
  display: flex; align-items: center; gap: {T.SP_4};
  background: {T.LATAR_KARTU};
  border: 1px solid {T.BORDER_VARIAN};
  border-radius: {T.RADIUS_KARTU};
  padding: {T.SP_3} {T.SP_4};
}}

/* Sorot-baru — sisip baris yang baru dibuat */
tr.sorot-baru, div.sorot-baru {{
  background: {T.AKSEN_MURID_UTAMA}20;
  border-left: 4px solid {T.AKSEN_MURID_UTAMA};
}}

/* Meta info: tanggal, waktu */
.st-meta {{ color: {T.TEKS_SUBTLE}; font-size: .9rem; }}

/* Form "buat sesi" dalam satu baris */
.strip-sesi {{ display: flex; gap: {T.SP_3}; flex-wrap: wrap; align-items: flex-end; }}
.strip-sesi label {{ font-size: .9rem; color: {T.TEKS_SUBTLE}; display:block; margin-bottom: .25rem; }}
.mode-pilih {{ display: flex; gap: {T.SP_4}; }}
.mode-opsi {{ display: flex; align-items: center; gap: {T.SP_2}; cursor: pointer; font-size: .95rem; }}
"""


def gaya_stitch() -> str:
    """
    Kembalikan string CSS lengkap untuk halaman yang difase-in ke Stitch.
    Dipakai oleh fungsi render halaman versi '_baru' di file-file yang ada.
    """
    return GAYA_STITCH


if __name__ == "__main__":
    # quick lint: unmatched braces?
    css = GAYA_STITCH
    open_count = css.count("{") + css.count("{{") / 2
    close_count = css.count("}") + css.count("}}") / 2
    print("fstring-open:", css.count("{"), "output-open:", GAYA_STITCH.count("{"), "len:", len(GAYA_STITCH))
