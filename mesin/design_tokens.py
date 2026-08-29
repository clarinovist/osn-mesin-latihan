"""Design tokens — sumber tunggal untuk semua nilai visual aplikasi.

Dipakai oleh gaya_layar.py, gaya_cetak.py, dan murid.py (CSS_MURID).
Tujuan: konsistensi antar-viewport (layar sentuh, cetak A4, dashboard guru)
tanpa duplikasi nilai. Ubah di sini, efek ke semua permukaan.

== Palet ==

Ada dua paet yang hidup berdampingan:

  1. Palet INTI (biru tua #16213e + abu #f0f1f4) — sudah dipakai sejak Fase 3
     untuk semua permukaan guru: dashboard, sesi, laporan, akun, lembar cetak.
     5 mockup guru (guru-*) memakai palet ini.

  2. Palet MURID (cream #FFF8EE + teal #0FA3A3 + coral #FF6B5B + amber #FFB020)
     — dari mockup murid (murid-*). Lebih ramah anak, lebih hangat.

Keduanya tidak menyatu karena guru dan murid punya konteks emosi berbeda:
guru butuh konsentrasi (biru tua, netral), murid butuh semangat (hangat, cerah).

== Mockup ==

9 mockup UI/UX ada di ~/Documents/osn/desain-ui/:
  - murid-sesiku.png, murid-kerjakan.png (mobile portrait)
  - guru-masuk.png, guru-dashboard.png, guru-sesi.png, guru-laporan.png,
    guru-akun.png (desktop landscape)
  - guru-lembar-soal.png, guru-lembar-kunci.png (A4 portrait)

Script generator: desain-ui/gen_guru.py (gpt-image-2 via chenzk.top).
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

# Status Dashboard (mockup guru-laporan)
STATUS_KUAT = "#0FA3A3"          # teal
STATUS_LEMAH = "#FFB020"        # amber
STATUS_SALAH = "#FF6B5B"        # coral

# ─────────────────────────────────────────────────────────────────────
# Palet MURID (permukaan murid: /murid, /murid/kerjakan)
# ─────────────────────────────────────────────────────────────────────

LATAR_MURID = "#FFF8EE"         # cream hangat
AKSEN_MURID_UTAMA = "#0FA3A3"   # teal — primary action, nomor badge
AKSEN_MURID_KORAL = "#FF6B5B"   # coral — tombol simpan, highlight baru
AKSEN_MURID_AMBER = "#FFB020"   # amber — star/challenge
LATAR_KARTU_MURID = "#fff"

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
