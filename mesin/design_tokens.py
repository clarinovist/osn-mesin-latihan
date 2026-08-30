"""Design tokens — sumber tunggal untuk semua nilai visual aplikasi.

Dipakai oleh gaya_layar.py, gaya_cetak.py, gaya_guru.py, dan murid.py
(CSS_MURID). Tujuan: konsistensi antar-viewport (layar sentuh, cetak A4,
dashboard guru) tanpa duplikasi nilai. Ubah di sini, efek ke semua permukaan.

== Palet ==

Sejak restyle 29 Agu 2026 seluruh permukaan (guru, murid, lembar) memakai
SATU palet hangat dari mockup — cream #FFF8EE + teal #0FA3A3 + coral
#FF6B5B + amber #FFB020. Yang dulu disebut "palet INTI" (biru tua #16213e +
abu) kini hanya tersisa sebagai warna judul/teks (TEKS_JUDUL, BORDER_KUAT)
dan garis cetak; latar semua halaman adalah LATAR_MURID.

== Mockup ==

9 mockup UI/UX ada di ~/Documents/osn/desain-ui/:
  - murid-sesiku.png, murid-kerjakan.png (mobile portrait)
  - guru-masuk.png, guru-dashboard.png, guru-sesi.png, guru-laporan.png,
    guru-akun.png (desktop landscape)
  - guru-lembar-soal.png, guru-lembar-kunci.png (A4 portrait)

Script generator: desain-ui/gen_guru.py (gpt-image-2 via chenzk.top).

Permukaan guru diimplementasi di gaya_guru.py (5 halaman layar); lembar di
gaya_layar.py (browser) + gaya_cetak.py (kertas A4); murid di murid.py.
"""

# ─────────────────────────────────────────────────────────────────────
# Palet INTI (permukaan guru: dashboard, sesi, laporan, akun, cetak)
# ─────────────────────────────────────────────────────────────────────

# Latar
LATAR_INTI = "#f0f1f4"          # abu muda, badan halaman
LATAR_KARTU = "#fff"            # putih, kartu/soal
LATAR_KARTU_SEKUNDER = "#eef3fb"  # biru muda, petunjuk/kartu interaktif

# Teks & border
TEKS_UTAMA = "#111"             # hampir hitam, body
TEKS_JUDUL = "#16213e"          # biru tua, heading/judul/border
TEKS_SUBTLE = "#555"            # abu, label/meta
BORDER_HALUS = "#d5d8de"
BORDER_INTERAKTIF = "#c4d3ea"
BORDER_KUAT = "#16213e"

# Aksen sekunder (catatan, penanda)
LATAR_CATATAN = "#fff7e6"
BORDER_CATATAN = "#ecd9a8"
BINTANG = "#b8860b"             # challenge star (legacy gold)

# Konfirmasi positif
LATAR_TERSIMPAN = "#e8f6ec"
BORDER_TERSIMPAN = "#9ed4b0"
TEKS_TERSIMPAN = "#14532d"

# Teks kontras di atas aksen (butuh teks putih di atas teal/coral/amber)
TEKS_PUTIH = "#ffffff"

# Galat (pesan error) — netral merah lembut
LATAR_GALAT = "#fdecea"
BORDER_GALAT = "#f5b5ae"
TEKS_GALAT = "#93352b"

# Status Dashboard (mockup guru-laporan)
STATUS_KUAT = "#0FA3A3"          # teal
STATUS_LEMAH = "#FFB020"        # amber
STATUS_SALAH = "#FF6B5B"        # coral

# Badge peran topbar (multi-keluarga): Pengelola amber, Orang Tua teal —
# warna status yang sama supaya tetap satu rasa visual.
BADGE_ADMIN_BG = "#FFB020"
BADGE_ADMIN_TEKS = "#5b430a"
BADGE_GURU_BG = "#0FA3A3"
BADGE_GURU_TEKS = TEKS_PUTIH

# Kode diagnosis — warna pill di halaman sesi guru (mockup guru-sesi).
# Mengikuti STATUS_* supaya satu rasa: kuat=teal, lemah=amber, salah=coral.
KODE_BENAR_BG = "#e6f6ec"
KODE_BENAR_TEKS = "#157347"
KODE_SALAH_KONSEP_BG = "#fdecea"   # K
KODE_SALAH_KONSEP_TEKS = "#c2352b"
KODE_SALAH_BACA_BG = "#fdf3e0"     # B
KODE_SALAH_BACA_TEKS = "#a4700f"
KODE_SALAH_HITUNG_BG = "#e8f0fc"   # H
KODE_SALAH_HITUNG_TEKS = "#2c60ad"
KODE_SALAH_TULIS_BG = "#f0ecfb"    # E
KODE_SALAH_TULIS_TEKS = "#6a4bb0"
KODE_BELUM_LIAT_BG = "#eaf4ef"     # T
KODE_BELUM_LIAT_TEKS = "#3f7d57"
KODE_MENEBAK_BG = "#efeff1"        # N
KODE_MENEBAK_TEKS = "#5b5b63"

# Chart tren (mockup guru-laporan) — SVG
CHART_GRID = "#e2e6ef"
CHART_AXIS = "#8a91a3"

# ─────────────────────────────────────────────────────────────────────
# Palet MURID (permukaan murid: /murid, /murid/kerjakan)
# ─────────────────────────────────────────────────────────────────────

LATAR_MURID = "#FFF8EE"         # cream hangat
AKSEN_MURID_UTAMA = "#0FA3A3"   # teal — primary action, nomor badge
AKSEN_MURID_KORAL = "#FF6B5B"   # coral — tombol simpan, highlight baru
AKSEN_MURID_AMBER = "#FFB020"   # amber — star/challenge
LATAR_KARTU_MURID = "#fff"

# ─────────────────────────────────────────────────────────────────────
# Identitas produk — SUMBER TUNGGAL nama & tagline (launch publik).
# Ganti nama di sini, efek ke semua permukaan (landing, login, dashboard).
# ─────────────────────────────────────────────────────────────────────

NAMA_PRODUK = "Caraku"
TAGLINE = "Latih. Tulis caramu. Ketahui letak salahmu."

# ─────────────────────────────────────────────────────────────────────
# Tipografi
# ─────────────────────────────────────────────────────────────────────

FONT_LAYAR = (
    '-apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
)
FONT_CETAK = '"Helvetica Neue", Arial, sans-serif'

# Ukuran teks — skala modular 1.2x (lihat docs/design-system.md)
UKURAN_BADAN_LAYAR = "16px"
UKURAN_BADAN_CETAK = "10.5pt"
LINE_HEIGHT = "1.55"

# ─────────────────────────────────────────────────────────────────────
# Spacing — skala 4px base (lihat docs/design-system.md)
# ─────────────────────────────────────────────────────────────────────

SP_1 = "0.25rem"   # 4px
SP_2 = "0.5rem"    # 8px
SP_3 = "0.75rem"   # 12px
SP_4 = "1rem"      # 16px
SP_5 = "1.5rem"    # 24px
SP_6 = "2rem"      # 32px

# ─────────────────────────────────────────────────────────────────────
# Radius
# ─────────────────────────────────────────────────────────────────────

RADIUS_KARTU = "12px"
RADIUS_SEDANG = "10px"
RADIUS_KECIL = "8px"
RADIUS_PIL = "999px"       # pilihan cara, badge
RADIUS_BULAT = "50%"       # nomor badge

# ─────────────────────────────────────────────────────────────────────
# Touch target
# ─────────────────────────────────────────────────────────────────────

TARGET_SENTUH = "44px"     # pedoman aksesibilitas WCAG 2.5.5
LEBAR_KONTEN = "46rem"     # maksimum lebar konten layar
