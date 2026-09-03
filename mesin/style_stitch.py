"""Style Stitch — CSS bersama untuk adopsi desain Stitch (16 halaman).

Semua 16 halaman kini diadopsi ke Stitch (S1-S17 selesai 1 Sep 2026).
CSS lama (teacher_style.GAYA_GURU, student_pages.CSS_MURID) masih ada di
kode karena kelas-kelasnya dipakai oleh markup yang belum di-restyle
penuh (halaman guru memakai GAYA_GURU + GAYA_STITCH bersamaan lewat
_halaman(stitch=True)), dan beberapa test meng-assert isi GAYA_GURU.

Kelas dipisah dengan suffix "-st" agar tidak tabrakan dengan CSS lama yang
masih bertugas.
"""

import design_tokens as T

GAYA_STITCH = f"""
/* ── Font CDN (diizinkan 2026-09-01) — satu baris utuh; @import multi-baris
   memutus URL dan membuat font gagal dimuat tanpa jejak di konsol. ── */
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

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
  color: {T.WARNA_WORDMARK}; font-size: {T.LOGO_TOPBAR};
  display: inline-flex; align-items: center;
}}
/* Lambang brand: satu ukuran dari token, bukan angka lepas per stylesheet. */
.st-topbar .brand img {{ width: {T.LOGO_TOPBAR}; height: {T.LOGO_TOPBAR}; flex: none; }}
.st-topbar .brand .nama {{ color: {T.WARNA_WORDMARK}; font-size: 1.1rem; }}
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
/* Status review (1 Sep, feedback orang tua): "masih direview" dan
   "selesai" tidak boleh sama tampilannya — dulunya dua-duanya kelas
   .selesai, orang tua tidak bisa membedakan. */
.st-badge.review     {{
  background: #fff0d6; color: #815600;
  /* HP sempit: badge boleh pecah dua baris — min-content-nya tidak boleh
     memaksa kartu melebihi layar (temuan screenshot 390px 1 Sep). */
  white-space: normal; text-align: left; line-height: 1.3;
  max-width: 100%; overflow-wrap: anywhere;
}}
/* Ukuran terkendali di HP: inline-flex + min-content menang atas
   "max-width:100%" (pemegangnya sendiri tak terbatas). Klem eksplisit
   dari piksel screenshot 390px. */
@media (max-width: 36rem) {{
  .st-badge.review {{
    max-width: 9.5rem;
    font-size: .72rem; padding: .2rem .5rem;  /* muat di baris meta */
  }}
}}

/* Badge peran di topbar — dipakai _topbar_stitch lewat _badge_peran lama */
.badge-peran {{
  display: inline-flex; align-items: center;
  border-radius: {T.RADIUS_PIL};
  padding: 0.15rem 0.55rem;
  font-family: {T.FONT_HEADLINE};
  font-weight: 700; font-size: .72rem; letter-spacing: .02em;
}}
.badge-peran-admin {{ background: {T.BADGE_ADMIN_BG}; color: {T.BADGE_ADMIN_TEKS}; }}
.badge-peran-guru  {{ background: {T.BADGE_GURU_BG};  color: {T.BADGE_GURU_TEKS}; }}

/* Menu pengguna CSS-only di topbar */
.topbar-navigasi {{ display: flex; align-items: center; gap: {T.SP_3}; }}
.menu-pengguna {{ position: relative; }}
.menu-pengguna summary {{
  list-style: none; cursor: pointer; min-height: {T.TARGET_SENTUH};
  display: flex; align-items: center; padding: 0 {T.SP_2};
  font-family: {T.FONT_HEADLINE}; font-weight: 600; color: {T.TEKS_JUDUL};
  border-radius: {T.RADIUS_SEDANG};
}}
.menu-pengguna summary::-webkit-details-marker {{ display: none; }}
.menu-pengguna summary:hover {{ background: {T.LATAR_SEKUNDER_NETRAL}; }}
.menu-pengguna[open] summary {{ background: {T.LATAR_SEKUNDER_NETRAL}; }}
.menu-isi {{
  position: absolute; right: 0; top: calc(100% + 6px);
  background: {T.LATAR_KARTU}; border: 1px solid {T.BORDER_VARIAN};
  border-radius: {T.RADIUS_SEDANG}; min-width: 12rem; max-width: min(12rem, calc(100vw - 1.2rem));
  box-shadow: 0 8px 24px rgba(0,0,0,.10); padding: {T.SP_2};
  display: flex; flex-direction: column; gap: {T.SP_1}; z-index: 60;
}}
.menu-isi a, .menu-isi button {{
  display: block; width: 100%; text-align: left;
  padding: {T.SP_2} {T.SP_3}; border-radius: {T.RADIUS_KECIL};
  color: {T.TEKS_UTAMA}; text-decoration: none; background: none; border: 0;
  font: inherit; font-size: .92rem; cursor: pointer;
  min-height: {T.TARGET_SENTUH};
}}
.menu-isi a:hover, .menu-isi button:hover {{ background: {T.LATAR_SEKUNDER_LEMBUT}; }}
.menu-pisah {{ border-top: 1px solid {T.BORDER_VARIAN}; margin: {T.SP_1} 0; }}

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

/* Baris kartu (dipakai daftar sesi guru & murid di Stitch) */
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
  flex-wrap: wrap; /* 1 Sep: badge panjang mesti bisa pindah baris di HP */
  background: {T.LATAR_KARTU};
  border: 1px solid {T.BORDER_VARIAN};
  border-radius: {T.RADIUS_KARTU};
  padding: {T.SP_3} {T.SP_4};
  /* 1 Sep: tanpa guard ini, kartu melebar mengikuti min-content anak
     (badge panjang) → halaman menyamping di HP. max-width memaksa kartu
     tetap selebar konten; dengan wrap di bawah, badge pindah baris. */
  max-width: 100%;
}}
/* Pitas-vagasi 1 Sep: badge panjang ("Menunggu direview") + jumlah soal
   mengoverflow di HP 360-420px → halaman menyamping. min-width:0 pada
   anak fleksibel + wrap pada baris menjaga badge tetap di dalam layar.
   !important diperlukan: markup kartu memakai inline style="flex:none"
   yang tanpa ini menang atas media query.

   3 Sep: selector diubah dari `> span` ke `> *`. Kartu sesi GURU anaknya
   <div>, jadi aturan lama tidak pernah kena di /anak/<id> — kolom pertama
   menyusut jadi 76px dan judul sesi terlipat 3 baris. Semua anak kartu
   murid adalah <span>, jadi bagi mereka perubahan ini no-op. */
.st-kartu-baris > * {{ min-width: 0; }}
@media (max-width: 46rem) {{
  .st-kartu-baris {{ flex-wrap: wrap; }}
  .st-kartu-baris > *:nth-child(2) {{ flex: 1 1 10rem; }}
  /* pemegang badge jumlah + status boleh menyusut & pindah baris */
  .st-kartu-baris > *:nth-child(n+3) {{
    flex: 0 1 auto !important; margin-left: 0;
  }}
  /* HANYA kartu sesi guru: anak pertama ("Sesi #N · tanggal · topik") ambil
     baris penuh supaya tidak terjepit jadi 76px; angka & badge turun ke baris
     kedua. !important karena markup memakai inline style="flex:1".
     JANGAN digeneralkan ke .st-kartu-baris — anak pertama kartu MURID adalah
     ikon bulat 2.5rem yang justru harus tetap flex:none. */
  .kartu-sesi-guru > *:first-child {{ flex: 1 1 100% !important; }}
  .st-kartu-baris:not(.kartu-sesi-guru) > *:first-child {{ flex: none; }}
}}

/* 3 Sep: .daftar-anak sebelumnya HANYA ada di GAYA_GURU, yang tidak dimuat
   _halaman_stitch → grid+gap hilang dan kartu sesi dempet (terukur 1px).
   Versi di teacher_style.py dibiarkan: halaman non-stitch masih memakainya. */
.daftar-anak {{ display: grid; gap: {T.SP_3}; }}

/* ── Kartu sesi murid (3 Sep, feedback layout) ──
   Tiga masalah terukur di headless Chrome, akarnya satu markup:

   1. Badge "{{n}} soal" dulu ditulis DI DALAM kolom teks. Kolom itu
      flex-direction:column, jadi badge kena stretch: 271px di HP dan 617px
      di 1440px untuk konten yang lebar aslinya +-67px — terbaca orang tua
      sebagai "blok abu memanjang sampai habis" seolah progress bar.
   2. Kolom teks tak punya gap (computed `normal` = 0px) → tanggal, meta,
      dan badge dempet: "kayak agak bertumpuk".
   3. Karena (1), kartu hanya punya 2 anak flex sehingga aturan HP
      `.st-kartu-baris > *:nth-child(n+3)` di atas tidak pernah kena. */
.st-kartu-teks {{
  flex: 1; display: flex; flex-direction: column;
  gap: {T.SP_1};              /* akar keluhan "bertumpuk" */
  min-width: 0;
}}
/* Pill statis: lebar mengikuti isi, TIDAK memanjang. flex:none menahan
   shrink; align-self mencegah stretch kalau kartu jatuh ke mode wrap. */
.st-jumlah-soal {{
  flex: none; align-self: center; margin-left: auto;
  white-space: nowrap; font-size: 0.8rem;
}}
/* Bar progres hanya dipakai sesi yang SEDANG dikerjakan — saat pecahannya
   informatif. Sesi baru (0%) dan selesai (100%) tetap pill statis. */
.st-progres-soal {{
  flex: none; align-self: center; margin-left: auto;
  display: flex; flex-direction: column; gap: 0.2rem;
  width: 6.5rem;
}}
.st-progres-jalur {{
  display: block;
  height: 0.4rem; border-radius: {T.RADIUS_PIL};
  background: {T.LATAR_ELEVASI}; overflow: hidden;
}}
/* display:block WAJIB: penanda ini <span>, dan span inline mengabaikan
   width/height sepenuhnya — terukur 3 Sep, bar tampil kosong (0px) padahal
   style="width:30%" terpasang. Test HTML tidak menangkapnya; hanya render
   yang menangkap (CLAUDE.md §10). */
.st-progres-isi {{
  display: block;
  height: 100%; border-radius: {T.RADIUS_PIL};
  background: {T.AKSEN_MURID_UTAMA};
}}
.st-progres-label {{
  font-size: 0.7rem; color: {T.TEKS_VARIAN}; white-space: nowrap;
}}
@media (max-width: 46rem) {{
  /* Aturan HP `.st-kartu-baris > *:nth-child(n+3)` di atas memberi penanda
     `flex: 0 1 auto` + `margin-left: 0`, sehingga bar jatuh ke baris kedua
     dan menempel KIRI (terukur x=31, kartu memanjang 143→159px). Kembalikan
     dorongan ke kanan supaya bar tetap sebaris dengan kolom teks. */
  .st-jumlah-soal, .st-progres-soal {{ margin-left: auto !important; }}
  .st-progres-soal {{ width: 5.5rem; }}
}}

/* Sorot-baru — sisip baris yang baru dibuat */
tr.sorot-baru, div.sorot-baru {{
  background: {T.AKSEN_MURID_UTAMA}20;
  border-left: 4px solid {T.AKSEN_MURID_UTAMA};
}}

/* Meta info: tanggal, waktu */
.st-meta {{ color: {T.TEKS_SUBTLE}; font-size: .9rem; }}

/* Kanvas konten Stitch — _halaman_stitch dan seterusnya tidak lagi bergantung
   pada .bungkus milik teacher_style lama */
.bungkus-st {{ max-width: {T.LEBAR_KONTEN}; margin: 0 auto; padding: {T.SP_4} 0.9rem 3rem; }}

/* 3 Sep: blok lama ".strip-sesi / .mode-pilih / .mode-opsi" (versi strip satu
   baris) DIHAPUS dari sini — sisa refactor S6 yang tidak ikut dibersihkan.
   Bahayanya bukan sekadar duplikasi: ia membawa `align-items: flex-end`, dan
   blok S6 di bawah yang mengubah arah jadi kolom tidak me-reset properti itu,
   sehingga tiap anak yang tidak selebar penuh menempel ke tepi KANAN.
   Versi yang menang ada di bagian "Form buat sesi (S6)". */

/* ── Halaman /anak/<id> (3 Sep): dua kolom di desktop ──
   Mobile-first: bawaannya SATU kolom, jadi di HP tampilannya sama persis
   seperti sebelum blok ini ada. Grid dan pelebar kanvas baru hidup di
   >= 64rem, tempat halaman lama menyisakan ~350px kosong di kiri-kanan
   sambil memanjang 1698px ke bawah. */
.anak-grid {{ display: flex; flex-direction: column; gap: {T.SP_4}; }}
.anak-kolom-kanan {{ display: flex; flex-direction: column; gap: {T.SP_4}; }}

@media (min-width: 64rem) {{
  .bungkus-st.lebar {{ max-width: 72rem; }}
  .anak-grid {{
    display: grid;
    grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
    gap: {T.SP_5};
    align-items: start;
  }}
  /* Strip pertama di kolom kanan sudah punya jarak dari grid gap. */
  .anak-kolom-kanan > .strip-sesi:first-child {{ margin-top: 0; }}
}}


/* ── Kartu "Buat latihan" (3 Sep, Fase C): tab CSS-only ──
   Tiga form sebelumnya berdiri sebagai tiga kartu abu-abu berurutan; di
   kolom kanan itu berarti menggulir jauh untuk sampai ke form ketiga.
   Kini satu kartu dengan tab. TANPA JS: radio + :has(), sama seperti
   .mode-opsi:has(input:checked) yang sudah dipakai. */
.buat-latihan-st {{
  background: {T.LATAR_KARTU};
  border: 1px solid {T.BORDER_VARIAN};
  border-radius: {T.RADIUS_KARTU};
  padding: {T.SP_4};
}}
.buat-latihan-st > h2.st {{ margin: 0 0 {T.SP_3}; }}
/* Radio penggerak tab: disembunyikan dari mata, TETAP dapat difokus papan
   ketik (bukan display:none yang mencabutnya dari urutan tab). */
.tab-radio-st {{
  position: absolute; opacity: 0; width: 1px; height: 1px;
  margin: 0; pointer-events: none;
}}
.tab-bar-st {{
  display: flex; flex-wrap: wrap; gap: {T.SP_2};
  border-bottom: 1px solid {T.BORDER_VARIAN};
  margin-bottom: {T.SP_4};
}}
.tab-label-st {{
  display: inline-flex; align-items: center; gap: {T.SP_2};
  padding: {T.SP_2} {T.SP_3}; min-height: {T.TARGET_SENTUH};
  font-family: {T.FONT_HEADLINE}; font-weight: 600; font-size: .88rem;
  color: {T.TEKS_VARIAN}; cursor: pointer;
  border-bottom: 2px solid transparent; margin-bottom: -1px;
}}
.tab-label-st .material-symbols-outlined {{ font-size: 1.1rem; }}
.tab-label-st:hover {{ color: {T.TEKS_JUDUL}; }}
/* Strip di dalam panel sudah dibingkai kartu induk — buang bingkai gandanya. */
.panel-latihan-st > .strip-sesi {{
  margin-top: 0; padding: 0; background: none; border: 0;
}}

/* Penyembunyian panel HANYA kalau :has() didukung. Tanpa penjagaan ini,
   browser lama menyembunyikan panel dan tidak punya cara menampilkannya
   lagi — guru kehilangan tombol buat sesi sama sekali. Di sana semua panel
   tampil berurutan seperti sebelum Fase C: lebih panjang, tetap berfungsi. */
@supports selector(:has(*)) {{
  .panel-latihan-st {{ display: none; }}
  .buat-latihan-st:has(#tab-baru:checked) [data-panel="baru"],
  .buat-latihan-st:has(#tab-ulang:checked) [data-panel="ulang"],
  .buat-latihan-st:has(#tab-gabungan:checked) [data-panel="gabungan"] {{
    display: block;
  }}
  .buat-latihan-st:has(#tab-baru:checked) .tab-label-st[for="tab-baru"],
  .buat-latihan-st:has(#tab-ulang:checked) .tab-label-st[for="tab-ulang"],
  .buat-latihan-st:has(#tab-gabungan:checked) .tab-label-st[for="tab-gabungan"] {{
    color: {T.AKSEN_MURID_UTAMA}; border-bottom-color: {T.AKSEN_MURID_UTAMA};
  }}
}}
/* Fokus papan ketik harus terlihat: radio-nya kasat mata nol, jadi cincin
   fokus dipinjamkan ke labelnya. */
.tab-radio-st:focus-visible + .tab-bar-st .tab-label-st,
.buat-latihan-st:has(.tab-radio-st:focus-visible) .tab-bar-st {{
  outline: 2px solid {T.AKSEN_MURID_UTAMA}; outline-offset: 2px;
}}

/* ── Halaman kerja murid (/murid/kerjakan/<id>) — S4 adopsi Stitch ── */

/* Badan kerja: sticky topbar + timer, lalu konten utama, lalu save strip.  */
.kerja-badan-st {{ max-width: {T.LEBAR_KONTEN}; margin: 0 auto; padding: {T.SP_4} 0.9rem 5rem; min-height: 60vh; }}
.kerja-topbar-st {{
  background: {T.LATAR_SEKUNDER_LEMBUT};
  border-bottom: 1px solid {T.BORDER_VARIAN};
  height: {T.TARGET_SENTUH};
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 {T.SP_4};
  width: 100%; max-width: {T.LEBAR_KONTEN};
  margin: 0 auto; position: sticky; top: 0; z-index: 50;
  font-family: {T.FONT_HEADLINE};
}}
.kerja-topbar-st .brand {{ display: flex; align-items: center; gap: {T.SP_2}; }}
.kerja-topbar-st .brand .ik-owl {{
  width: {T.LOGO_TOPBAR}; height: {T.LOGO_TOPBAR}; flex: none;
  display: inline-flex; align-items: center;
}}
.kerja-topbar-st .brand .nama-osn {{ color: {T.WARNA_WORDMARK}; font-size: 1.1rem; font-weight: 800; }}
.kerja-topbar-st .cta-keluar {{
  font: inherit; color: {T.AKSEN_KORAL_TUA};
  background: none; border: 0; padding: {T.SP_2} {T.SP_4};
  font-weight: 700; min-height: {T.TARGET_SENTUH};
}}

.kerja-meta-st {{ font-size: .9rem; color: {T.TEKS_VARIAN}; margin: 0 0 {T.SP_4}; }}
.kerja-meta-st b {{ color: {T.TEKS_JUDUL}; font-family: {T.FONT_HEADLINE}; }}

.kerja-petunjuk-st {{
  background: {T.LATAR_SEKUNDER_LEMBUT};
  border: 1px solid {T.BORDER_VARIAN};
  border-radius: {T.RADIUS_KARTU};
  padding: {T.SP_3} {T.SP_4}; margin-bottom: {T.SP_5};
  font-size: .95rem; line-height: 1.55;
}}
.kerja-petunjuk-st .baris-petunjuk {{ display: flex; gap: {T.SP_3}; align-items: flex-start; }}
.kerja-petunjuk-st p {{ margin: 0 0 0.55rem; }}
.kerja-petunjuk-st p:last-child {{ margin-bottom: 0; }}

/* Timer strip per-sesi (Latihan Cepat). Sticky di bawah topbar, teal penuh.  */
.kerja-timer-st {{
  position: sticky; top: {T.TARGET_SENTUH}; z-index: 40;
  background: {T.AKSEN_MURID_UTAMA}; color: #fff;
  padding: {T.SP_2} {T.SP_4}; border-radius: {T.RADIUS_SEDANG};
  margin-bottom: {T.SP_5}; font-size: .98rem; font-weight: 600;
  text-align: center; display: flex; justify-content: center; align-items: center; gap: {T.SP_2};
}}
.kerja-timer-st b {{ font-size: 1.15rem; font-family: {T.FONT_HEADLINE}; }}
.kerja-timer-st.habis {{
  background: {T.LATAR_GALAT}; color: {T.TEKS_GALAT};
  border: 2px solid {T.BORDER_GALAT};
}}

/* Banner konfirmasi tersimpan. */
.kerja-tersimpan-st {{
  background: {T.LATAR_TERSIMPAN};
  border: 1px solid {T.BORDER_TERSIMPAN};
  color: {T.TEKS_TERSIMPAN};
  border-radius: {T.RADIUS_KARTU};
  padding: {T.SP_3} {T.SP_4}; margin: 0 0 {T.SP_4};
  display: flex; gap: {T.SP_3}; align-items: center;
  font-size: .98rem;
}}
.kerja-tersimpan-st .ikon {{
  background: {T.BORDER_TERSIMPAN}; color: #fff;
  border-radius: 50%; width: 24px; height: 24px;
  display: inline-flex; align-items: center; justify-content: center; font-weight: bold;
}}

/* Section heading bagian soal. */
.kerja-bagian-st {{
  font-family: {T.FONT_HEADLINE}; font-size: 1.05rem; font-weight: 700;
  color: {T.TEKS_JUDUL}; margin: {T.SP_5} 0 {T.SP_2};
  padding-bottom: .35rem; border-bottom: 2px solid {T.AKSEN_MURID_UTAMA};
}}
.kerja-catatan-bagian-st {{
  background: {T.LATAR_CATATAN}; border: 1px solid {T.BORDER_CATATAN};
  border-radius: {T.RADIUS_KECIL};
  padding: .55rem .8rem; margin: -.2rem 0 {T.SP_4}; font-size: .92rem;
}}

/* Kartu soal Stitch — primer. Nomor badge lingkaran teal menggantung di pojok. */
.kerja-soal-st {{
  background: {T.LATAR_KARTU}; border: 1px solid {T.BORDER_VARIAN};
  border-radius: {T.RADIUS_KARTU};
  padding: {T.SP_5} {T.SP_4} {T.SP_4}; margin-bottom: {T.SP_5};
  position: relative; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
}}
/* Nomor badge — di Stitch: lingkaran teal absolute -top-4 left-4. */
.kerja-nomor-st {{
  position: absolute; top: -0.85rem; left: {T.SP_3};
  width: 2.2rem; height: 2.2rem;
  background: {T.AKSEN_MURID_UTAMA}; color: {T.TEKS_PUTIH};
  border-radius: {T.RADIUS_BULAT}; border: 2px solid {T.LATAR_KARTU};
  display: inline-flex; align-items: center; justify-content: center;
  font-family: {T.FONT_HEADLINE}; font-weight: 700; font-size: .95rem;
  box-shadow: 0 2px 6px rgba(0,0,0,.18);
}}
.kerja-bintang-st {{ font-weight: 700; color: {T.AKSEN_MURID_AMBER}; margin-left: {T.SP_2}; }}

.kerja-teks-st {{ display: block; margin-top: {T.SP_2}; color: {T.TEKS_UTAMA}; }}
.kerja-tanya-st {{
  display: block; font-family: {T.FONT_HEADLINE}; font-size: 1.12rem; font-weight: 700;
  margin-top: {T.SP_3}; color: {T.TEKS_JUDUL}; line-height: 1.45;
}}

/* Label kecil (Caraku / restate). */
.kerja-label-st {{
  display: block; font-size: .85rem; color: {T.TEKS_VARIAN};
  margin: {T.SP_4} 0 {T.SP_2};
  display: flex; align-items: center; gap: {T.SP_1};
  font-family: {T.FONT_HEADLINE}; font-weight: 600;
}}

/* Restatement textarea. */
.kerja-restate-st {{
  width: 100%; min-height: 84px;
  border: 1.5px dashed #99a; border-radius: {T.RADIUS_KECIL};
  padding: .6rem; font-size: 1rem; font-family: inherit;
  background: {T.LATAR_SEKUNDER_LEMBUT};
}}
.kerja-restate-st:focus {{
  outline: none; border-color: {T.AKSEN_MURID_UTAMA}; border-style: solid;
  box-shadow: 0 0 0 3px rgba(15,163,163,0.18);
}}

/* Pilihan Caraku — pil 2-kolom; radio tersembunyi di dalam label yang tampil. */
.kerja-pill-grup-st {{
  display: grid; grid-template-columns: 1fr 1fr;
  gap: {T.SP_2}; margin-bottom: {T.SP_4};
}}
@media (max-width: 24rem) {{ .kerja-pill-grup-st {{ grid-template-columns: 1fr; }} }}
.kerja-pill-st {{
  display: flex; align-items: center; justify-content: center;
  border: 1.5px solid {T.BORDER_VARIAN}; border-radius: {T.RADIUS_PIL};
  padding: {T.SP_2} {T.SP_3}; min-height: {T.TARGET_SENTUH};
  background: {T.LATAR_KARTU}; cursor: pointer; font-size: .92rem;
  font-family: {T.FONT_HEADLINE}; font-weight: 500;
  text-align: center;
}}
.kerja-pill-st input {{ position: absolute; opacity: 0; pointer-events: none; }}
/* :has() — terpilih = teal solid penuh. */
.kerja-pill-st:has(input:checked) {{
  background: {T.AKSEN_MURID_UTAMA}; color: {T.TEKS_PUTIH};
  border-color: {T.AKSEN_MURID_UTAMA}; font-weight: 700;
}}
.kerja-pill-st:has(input:focus-visible) {{
  border-color: {T.AKSEN_MURID_UTAMA};
  box-shadow: 0 0 0 3px rgba(15,163,163,0.28);
}}
.kerja-pill-st:hover:not(:has(input:checked)) {{ background: {T.LATAR_SEKUNDER_LEMBUT}; }}

/* Textarea "tulis lebih jelas" opsional di Caraku. */
.kerja-cara-st {{
  width: 100%; min-height: 70px;
  border: 1px solid {T.BORDER_VARIAN}; border-radius: {T.RADIUS_SEDANG};
  padding: .6rem; font-size: 1rem; font-family: inherit;
  background: {T.LATAR_SEKUNDER_LEMBUT};
}}
.kerja-cara-st:focus {{
  outline: none; border-color: {T.AKSEN_MURID_UTAMA};
  box-shadow: 0 0 0 3px rgba(15,163,163,0.18);
}}

/* Baris Jawabanku: label + input besar, tekan tombol keyboard. */
.kerja-jawab-st {{
  display: flex; flex-direction: column; gap: {T.SP_2}; margin-top: {T.SP_4};
}}
.kerja-jawab-st .head-jawab {{
  display: flex; align-items: center; gap: {T.SP_2};
  font-family: {T.FONT_HEADLINE}; font-weight: 700; color: {T.TEKS_JUDUL};
  font-size: 1rem;
}}
.kerja-jawab-st .head-jawab .material-symbols-outlined {{ color: {T.AKSEN_MURID_UTAMA}; font-size: 1.15rem; }}
.kerja-jawab-st input[type=text] {{
  width: 100%; min-height: {T.TARGET_SENTUH};
  font-size: 1.15rem; font-family: inherit;
  text-align: center;
  border: 1.5px solid {T.BORDER_VARIAN};
  border-radius: {T.RADIUS_SEDANG}; padding: .55rem .7rem;
  background: {T.LATAR_KARTU};
}}
.kerja-jawab-st input[type=text]:focus {{
  outline: none; border-color: {T.AKSEN_MURID_UTAMA};
  box-shadow: 0 0 0 3px rgba(15,163,163,0.20);
}}

/* Centang "belum pernah lihat". */
.kerja-centang-st {{
  display: flex; align-items: center; gap: .5rem; margin-top: {T.SP_3};
  font-size: .92rem; color: {T.TEKS_VARIAN}; font-family: {T.FONT_HEADLINE};
}}
.kerja-centang-st input {{ width: 1.3rem; height: 1.3rem; flex: none; accent-color: {T.AKSEN_MURID_UTAMA}; }}

.catatan-soal-timer-st {{
  margin-top: .5rem; font-size: .85rem; color: {T.AKSEN_KORAL_TUA};
}}

/* Save strip sticky bawah. */
.kerja-simpan-strip-st {{
  position: sticky; bottom: 0; padding: {T.SP_3} 0 {T.SP_2};
  background: linear-gradient(to top, {T.LATAR_MURID} 70%, transparent);
}}
.kerja-simpan-strip-st button {{
  width: 100%; font-size: 1.1rem; padding: .95rem;
  background: {T.AKSEN_MURID_KORAL}; color: {T.TEKS_PUTIH};
  border: 0; border-radius: {T.RADIUS_PIL};
  font-family: {T.FONT_HEADLINE}; font-weight: 700; cursor: pointer;
  min-height: 48px;
  display: flex; align-items: center; justify-content: center; gap: {T.SP_2};
  box-shadow: 0 4px 12px rgba(255,107,91,.30);
}}
.kerja-simpan-strip-st button:hover {{ filter: brightness(1.06); }}
.kerja-simpan-strip-st button:disabled {{ opacity: .55; cursor: not-allowed; }}

/* Tombol sekunder Cetak/PDF + Sesi lain. */
.kerja-btn-sekunder-st {{
  font-family: {T.FONT_HEADLINE};
  background: {T.LATAR_SEKUNDER_NETRAL};
  color: {T.TEKS_JUDUL}; border: 1px solid {T.BORDER_VARIAN};
  border-radius: {T.RADIUS_SEDANG};
  padding: .55rem {T.SP_4}; font-weight: 600; font-size: .95rem;
  text-decoration: none; cursor: pointer;
  min-height: {T.TARGET_SENTUH};
  display: inline-flex; align-items: center; gap: {T.SP_1};
}}
.kerja-btn-sekunder-st:hover {{ background: {T.LATAR_ELEVASI}; }}

/* Kirim foto cara pengerjaan (anak yang mengerjakan di kertas).
   Sengaja terlihat sebagai jalur ALTERNATIF, bukan tombol utama: anak
   yang mengerjakan online tidak boleh merasa wajib memfoto. */
.kerja-foto-st {{
  background: {T.LATAR_KARTU_MURID};
  border: 1px dashed {T.AKSEN_MURID_UTAMA};
  border-radius: {T.RADIUS_KARTU};
  padding: {T.SP_4}; margin-top: {T.SP_4};
}}
.kerja-foto-kepala-st {{
  display: flex; align-items: center; gap: {T.SP_2};
  font-family: {T.FONT_HEADLINE}; color: {T.TEKS_JUDUL};
}}
.kerja-foto-kepala-st .material-symbols-outlined {{
  color: {T.AKSEN_MURID_UTAMA};
}}
.kerja-foto-sub-st {{
  color: {T.TEKS_SUBTLE}; font-size: .9rem; margin: {T.SP_2} 0 {T.SP_3};
}}
.kerja-foto-kabar-st {{
  background: {T.LATAR_TERSIMPAN}; border: 1px solid {T.BORDER_TERSIMPAN};
  color: {T.TEKS_TERSIMPAN}; border-radius: {T.RADIUS_SEDANG};
  padding: {T.SP_2} {T.SP_3}; margin: 0 0 {T.SP_3}; font-size: .92rem;
}}
.kerja-foto-jumlah-st {{
  color: {T.TEKS_SUBTLE}; font-size: .88rem; margin: 0 0 {T.SP_3};
}}
.kerja-foto-form-st {{
  display: flex; flex-wrap: wrap; gap: {T.SP_3}; align-items: center;
}}
/* Input file bawaan browser punya lebar intrinsik besar (nama berkas +
   tombol Choose File) dan TIDAK mengecil hanya dengan flex:1 — di HP 420px
   ia mendorong tombol kirim keluar layar (terbukti lewat screenshot
   headless). Paksa tiap anak jadi satu baris penuh: input dan tombol
   bertumpuk, tidak ada yang terpotong. */
.kerja-foto-form-st > * {{ flex: 1 0 100%; min-width: 0; max-width: 100%; }}
.kerja-foto-form-st input[type=file] {{
  font-size: .92rem; width: 100%;
}}
.kerja-foto-form-st button {{ width: 100%; justify-content: center; }}
@media (min-width: 34rem) {{
  /* Layar lebar: cukup ruang untuk sebaris. */
  .kerja-foto-form-st > * {{ flex: 0 1 auto; }}
  .kerja-foto-form-st input[type=file] {{ flex: 1 1 auto; }}
  .kerja-foto-form-st button {{ width: auto; }}
}}

/* Drill: kartu "ringan" — tetap punya kartu utuh, hilangkan pill Caraku.
   Pakai kelas modifier .kerja-soal-st.drill untuk menandakan. */
.kerja-soal-st.drill {{ padding-top: {T.SP_5}; }}

/* Cetak: halaman kerja harus cetak baik di A4. */
@media print {{
  body.st {{ background: #fff; font-size: {T.UKURAN_BADAN_CETAK}; }}
  .kerja-badan-st {{ max-width: none; padding: 0; }}
  .kerja-topbar-st, .kerja-simpan-strip-st, .hanya-layar {{ display: none; }}
  .kerja-soal-st {{ break-inside: avoid; box-shadow: none; border-color: #000; }}
  .kerja-bagian-st {{ break-after: avoid; }}
}}

/* Hormati preferensi gerak. */
@media (prefers-reduced-motion: reduce) {{
  * {{ transition-duration: .01ms !important; animation-duration: .01ms !important; animation-iteration-count: 1 !important; }}
}}

/* ── Form buat sesi (S6) — card radio mode + timer toggle ── */

/* Wrapper form di kartu siswa dashboard. */
.strip-sesi {{
  margin-top: {T.SP_4};
  padding: {T.SP_4};
  background: {T.LATAR_SEKUNDER_LEMBUT};
  border: 1px solid {T.BORDER_VARIAN};
  border-radius: {T.RADIUS_KARTU};
  display: flex; flex-direction: column; gap: {T.SP_4};
  /* 3 Sep: ditulis EKSPLISIT meski stretch itu nilai default. Sebelumnya ada
     blok .strip-sesi lain di atas dengan align-items:flex-end, dan blok kolom
     ini mewarisinya → label & select menempel ke tepi kanan (terukur x=866
     dan x=744, seharusnya 383). Baris ini yang menahannya kalau terulang. */
  align-items: stretch;
  flex-wrap: nowrap;
}}
.strip-sesi .strip-kolom {{ display: flex; flex-direction: column; gap: {T.SP_2}; min-width: 0; }}
/* Di desktop select melar selebar kartu (673px) dan lelah dipindai mata;
   22rem masih jauh di atas target sentuh saat di HP. */
.strip-sesi select.st-input {{ max-width: 22rem; }}
/* Tombol aksi di dalam strip: di HP ia melebihi lebar kartu karena
   padding tetap 1.5rem + label panjang ("Buat latihan ulang") dan
   terpotong di kanan (terbukti lewat screenshot headless 390px).
   Satu baris penuh di layar sempit, kembali auto di layar lebar. */
.strip-sesi .st-tombol-coral {{
  width: 100%; justify-content: center; padding: 0 {T.SP_4};
  display: inline-flex; align-items: center; gap: {T.SP_2};
}}
@media (min-width: 34rem) {{
  .strip-sesi .st-tombol-coral {{ width: auto; align-self: flex-start; }}
}}
.strip-sesi .strip-kolom > label {{
  font-family: {T.FONT_HEADLINE}; font-weight: 600; font-size: .82rem;
  color: {T.TEKS_VARIAN};
}}

/* Card radio mode (Diagnosa / Latihan Cepat) — bukan radio kecil. */
.mode-pilih {{ display: flex; flex-direction: column; gap: {T.SP_2}; }}
.mode-opsi {{
  display: flex; align-items: flex-start; gap: {T.SP_3};
  border: 1.5px solid {T.BORDER_VARIAN}; border-radius: {T.RADIUS_SEDANG};
  padding: {T.SP_3}; min-height: {T.TARGET_SENTUH};
  background: {T.LATAR_KARTU}; cursor: pointer;
  font-family: {T.FONT_HEADLINE}; font-weight: 600; font-size: .92rem;
  color: {T.TEKS_JUDUL};
}}
.mode-opsi input {{
  flex: none; width: 1.3rem; height: 1.3rem; margin-top: 0.15rem;
  accent-color: {T.AKSEN_MURID_UTAMA};
}}
.mode-opsi .mode-teks {{ display: flex; flex-direction: column; gap: 0.15rem; }}
.mode-opsi .mode-teks .mode-desk {{
  font-family: {T.FONT_BODY}; font-weight: 400; font-size: .82rem;
  color: {T.TEKS_VARIAN};
}}
.mode-opsi:has(input:checked) {{
  border-color: {T.AKSEN_MURID_UTAMA}; background: {T.LATAR_KARTU_SEKUNDER};
  box-shadow: 0 0 0 3px rgba(15,163,163,0.12);
}}

/* Blok timer — default hidden, tampil saat Latihan Cepat dipilih. */
.pengaturan-timer {{
  background: {T.LATAR_SEKUNDER_NETRAL};
  border: 1px solid {T.BORDER_VARIAN};
  border-radius: {T.RADIUS_SEDANG};
  padding: {T.SP_3};
  display: flex; flex-direction: column; gap: {T.SP_2};
}}
.pengaturan-timer > label {{
  font-family: {T.FONT_HEADLINE}; font-weight: 600; font-size: .82rem;
  color: {T.TEKS_VARIAN}; margin-bottom: {T.SP_1};
}}
.pengaturan-timer .mode-opsi {{
  min-height: 0; padding: {T.SP_2} {T.SP_3};
  font-weight: 500; font-size: .88rem;
}}
.pengaturan-timer input[type=number] {{
  width: 4.5rem; display: inline-block;
  font: inherit; font-size: 1rem; min-height: {T.TARGET_SENTUH};
  border-radius: {T.RADIUS_SEDANG}; border: 1px solid {T.BORDER_VARIAN};
  background: {T.LATAR_KARTU}; padding: 0 {T.SP_3};
}}

/* ── Halaman masuk /masuk (S7) — single column card ── */

.masuk-badan-st {{
  min-height: 100vh; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: {T.SP_5} {T.SP_4};
}}
.masuk-kartu-st {{
  width: 100%; max-width: 26rem;
  background: {T.LATAR_KARTU}; border: 1px solid {T.BORDER_VARIAN};
  border-radius: {T.RADIUS_KARTU};
  padding: {T.SP_6} {T.SP_5} {T.SP_5};
  box-shadow: 0 8px 24px rgba(0,0,0,.08);
  display: flex; flex-direction: column; gap: {T.SP_4};
}}
.masuk-brand-st {{
  display: flex; align-items: center; justify-content: center; gap: {T.SP_2};
  margin-bottom: {T.SP_2};
}}
.masuk-brand-st .ik-owl {{
  width: {T.LOGO_BADGE}; height: {T.LOGO_BADGE}; flex: none;
  display: inline-flex; align-items: center; justify-content: center;
}}
.masuk-brand-st .nama-brand {{
  font-family: {T.FONT_HEADLINE}; font-weight: 800; font-size: 1.5rem;
  color: {T.WARNA_WORDMARK}; letter-spacing: -0.02em;
}}
.masuk-judul-st {{
  font-family: {T.FONT_HEADLINE}; font-weight: 700; font-size: 1.2rem;
  color: {T.TEKS_JUDUL}; text-align: center; margin: 0;
}}
.masuk-sub-st {{
  font-family: {T.FONT_BODY}; font-size: .9rem; color: {T.TEKS_VARIAN};
  text-align: center; margin: 0 0 {T.SP_2};
}}

/* Galat / error flash. */
.masuk-galat-st {{
  background: {T.LATAR_GALAT}; border: 1px solid {T.BORDER_GALAT};
  color: {T.TEKS_GALAT}; border-radius: {T.RADIUS_SEDANG};
  padding: {T.SP_2} {T.SP_3}; font-size: .9rem; text-align: center;
}}

/* Form fields. */
.masuk-form-st {{ display: flex; flex-direction: column; gap: {T.SP_3}; }}
.masuk-field-st {{ display: flex; flex-direction: column; gap: {T.SP_1}; }}
.masuk-field-st label {{
  font-family: {T.FONT_HEADLINE}; font-weight: 600; font-size: .82rem;
  color: {T.TEKS_VARIAN};
}}
.masuk-field-st input {{
  font: inherit; font-size: 1rem; min-height: {T.TARGET_SENTUH};
  border-radius: {T.RADIUS_SEDANG}; border: 1px solid {T.BORDER_VARIAN};
  background: {T.LATAR_KARTU}; padding: 0 {T.SP_3}; width: 100%;
}}
.masuk-field-st input:focus {{
  border-color: {T.FOKUS_AKSEN}; outline: 0;
  box-shadow: 0 0 0 3px {T.AKSEN_MURID_UTAMA}55;
}}

.masuk-tombol-st {{
  width: 100%; font-size: 1.05rem; padding: .9rem;
  background: {T.AKSEN_MURID_KORAL}; color: {T.TEKS_PUTIH};
  border: 0; border-radius: {T.RADIUS_SEDANG};
  font-family: {T.FONT_HEADLINE}; font-weight: 700; cursor: pointer;
  min-height: 48px;
  display: flex; align-items: center; justify-content: center; gap: {T.SP_2};
  box-shadow: 0 4px 12px rgba(255,107,91,.25);
}}
.masuk-tombol-st:hover {{ filter: brightness(1.06); }}

.masuk-link-st {{
  text-align: center; font-size: .9rem; margin-top: {T.SP_2};
  font-family: {T.FONT_HEADLINE};
}}
.masuk-link-st a {{
  color: {T.AKSEN_MURID_UTAMA}; text-decoration: none; font-weight: 600;
}}
.masuk-link-st a:hover {{ text-decoration: underline; }}

/* ── Halaman publik (S8 daftar, S9 lupa-sandi, S10 kebijakan) ── */

.publik-badan-st {{
  min-height: 100vh; padding: {T.SP_5} {T.SP_4} 3rem;
}}
.publik-topbar-st {{
  background: {T.LATAR_SEKUNDER_LEMBUT}; border-bottom: 1px solid {T.BORDER_VARIAN};
  height: {T.TARGET_SENTUH}; display: flex; align-items: center;
  justify-content: space-between; padding: 0 {T.SP_4};
  width: 100%; max-width: {T.LEBAR_KONTEN}; margin: 0 auto;
  position: sticky; top: 0; z-index: 50; font-family: {T.FONT_HEADLINE};
}}
.publik-topbar-st .brand {{
  display: flex; align-items: center; gap: {T.SP_2}; text-decoration: none;
  font-weight: 800; font-size: 1.1rem; color: {T.WARNA_WORDMARK};
}}
.publik-topbar-st .brand img {{
  width: {T.LOGO_TOPBAR}; height: {T.LOGO_TOPBAR}; flex: none;
}}
.publik-topbar-st .tombol-putih {{
  font: inherit; color: {T.AKSEN_TEAL_TUA}; background: none;
  border: 1px solid {T.BORDER_VARIAN}; border-radius: {T.RADIUS_SEDANG};
  padding: {T.SP_2} {T.SP_4}; font-weight: 600; font-size: .9rem;
  text-decoration: none; min-height: {T.TARGET_SENTUH};
  display: inline-flex; align-items: center; gap: {T.SP_1};
}}
.publik-topbar-st .tombol-putih:hover {{
  border-color: {T.AKSEN_MURID_UTAMA}; color: {T.AKSEN_MURID_UTAMA};
}}

.publik-bungkus-st {{
  max-width: {T.LEBAR_KONTEN}; margin: 0 auto; padding: {T.SP_5} 0;
}}
.publik-kartu-st {{
  max-width: 28rem; margin: 0 auto;
  background: {T.LATAR_KARTU}; border: 1px solid {T.BORDER_VARIAN};
  border-radius: {T.RADIUS_KARTU}; padding: {T.SP_6} {T.SP_5} {T.SP_5};
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
  display: flex; flex-direction: column; gap: {T.SP_4};
}}
.publik-kartu-st.lebar {{
  max-width: {T.LEBAR_KONTEN};
}}
.publik-judul-st {{
  font-family: {T.FONT_HEADLINE}; font-weight: 800; font-size: 1.4rem;
  color: {T.TEKS_JUDUL}; margin: 0; letter-spacing: -0.01em;
}}
.publik-sub-st {{
  font-family: {T.FONT_BODY}; font-size: .9rem; color: {T.TEKS_VARIAN};
  margin: 0;
}}
.publik-isi-st {{
  font-family: {T.FONT_BODY}; font-size: .95rem; color: {T.TEKS_UTAMA};
  line-height: 1.6;
}}
.publik-isi-st h2 {{
  font-family: {T.FONT_HEADLINE}; font-weight: 700; font-size: 1.05rem;
  color: {T.TEKS_JUDUL}; margin: {T.SP_5} 0 {T.SP_2};
}}
.publik-isi-st ul, .publik-isi-st ol {{
  padding-left: 1.2rem; margin: {T.SP_2} 0;
}}
.publik-isi-st li {{ margin-bottom: 0.4rem; }}
.publik-isi-st a {{ color: {T.AKSEN_MURID_UTAMA}; }}

/* Tombol coral reusable di halaman publik. */
a.tombol-coral {{
  display: inline-block; padding: .7rem 1.4rem;
  border-radius: {T.RADIUS_SEDANG}; text-decoration: none; font-weight: 700;
  background: {T.AKSEN_MURID_KORAL}; color: {T.TEKS_PUTIH};
  font-family: {T.FONT_HEADLINE}; min-height: {T.TARGET_SENTUH};
  display: inline-flex; align-items: center; gap: {T.SP_2};
}}
a.tombol-coral:hover {{ filter: brightness(1.06); }}
/* Halaman hasil murid (/murid/hasil/<id>) — anak melihat letak salahnya.
   Warna status memakai palet murid yang sudah ada; tidak ada token baru. */
.hasil-ringkas-st {{
  display: flex; align-items: center; gap: {T.SP_4};
  background: {T.LATAR_KARTU_MURID}; border: 1px solid {T.BORDER_HALUS};
  border-radius: {T.RADIUS_KARTU}; padding: {T.SP_4}; margin-bottom: {T.SP_4};
}}
.hasil-skor-st {{
  font-family: {T.FONT_HEADLINE}; font-size: 2rem; font-weight: 800;
  color: {T.AKSEN_TEAL_TUA}; line-height: 1; flex: none;
}}
.hasil-skor-st span {{ font-size: 1.1rem; color: {T.TEKS_VARIAN}; }}
.hasil-pesan-st {{ font-size: .95rem; color: {T.TEKS_UTAMA}; }}
.hasil-soal-st {{
  background: {T.LATAR_KARTU_MURID}; border: 1px solid {T.BORDER_HALUS};
  border-left: 4px solid {T.BORDER_VARIAN};
  border-radius: {T.RADIUS_KARTU}; padding: {T.SP_4}; margin-bottom: {T.SP_3};
}}
.hasil-soal-st.benar {{ border-left-color: {T.AKSEN_MURID_UTAMA}; }}
.hasil-soal-st.salah {{ border-left-color: {T.AKSEN_MURID_KORAL}; }}
.hasil-kepala-st {{
  display: flex; align-items: center; gap: {T.SP_2}; margin-bottom: {T.SP_2};
  flex-wrap: wrap;
}}
.hasil-nomor-st {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 1.9rem; height: 1.9rem; border-radius: 50%; flex: none;
  background: {T.AKSEN_TEAL_TUA}; color: #fff; font-weight: 700;
}}
.hasil-teks-st {{ margin: 0 0 {T.SP_2}; font-size: .98rem; }}
.hasil-jawabku-st {{
  margin: 0 0 {T.SP_2}; font-size: .93rem; color: {T.TEKS_VARIAN};
}}
.hasil-langkah-st {{
  display: flex; gap: {T.SP_2}; align-items: flex-start;
  background: {T.LATAR_CATATAN}; border: 1px solid {T.BORDER_CATATAN};
  border-radius: {T.RADIUS_SEDANG}; padding: {T.SP_3}; font-size: .93rem;
}}
.hasil-langkah-st .material-symbols-outlined {{
  color: {T.AKSEN_MURID_AMBER}; flex: none; font-size: 1.15rem;
}}

/* Kartu rumus (poin c) — muncul di halaman hasil untuk konsep yang salah. */
.rumus-blok-st {{
  background: {T.LATAR_KARTU_MURID}; border: 1px solid {T.AKSEN_MURID_AMBER};
  border-radius: {T.RADIUS_KARTU}; padding: {T.SP_4}; margin-bottom: {T.SP_4};
}}
.rumus-kepala-st {{
  display: flex; align-items: center; gap: {T.SP_2}; margin-bottom: {T.SP_3};
  font-family: {T.FONT_HEADLINE}; color: {T.TEKS_JUDUL};
}}
.rumus-kepala-st .material-symbols-outlined {{
  color: {T.AKSEN_MURID_AMBER}; flex: none;
}}
.rumus-kartu-st {{
  border-left: 3px solid {T.AKSEN_MURID_AMBER};
  padding: {T.SP_2} 0 {T.SP_2} {T.SP_3}; margin-bottom: {T.SP_3};
}}
.rumus-kartu-st:last-child {{ margin-bottom: 0; }}
.rumus-judul-st {{
  font-family: {T.FONT_HEADLINE}; font-weight: 700; font-size: .95rem;
  color: {T.TEKS_JUDUL}; margin-bottom: .15rem;
}}
.rumus-inti-st {{ font-size: .93rem; }}
.rumus-contoh-st {{
  font-size: .88rem; color: {T.TEKS_VARIAN}; margin-top: .2rem;
}}

"""

# Bagian CSS khusus halaman koreksi sesi (S5). Dipisah agar modul tetap bisa
# diimpor utuh; dipanggil oleh halaman_sesi_stitch lewat gaya_stitch() + blok
# tambahan ini.
CSS_SESI = f"""
/* ── Halaman koreksi sesi guru /sesi/<id> — S5 adopsi Stitch ── */

.sesi-badan-st {{ max-width: {T.LEBAR_KONTEN}; margin: 0 auto; padding: {T.SP_4} 0.9rem 3rem; }}
.sesi-jejak-st {{ margin-bottom: {T.SP_3}; font-size:.9rem; }}
.sesi-jejak-st a {{ color: {T.AKSEN_MURID_UTAMA}; text-decoration: none; }}
.sesi-jejak-st a:hover {{ text-decoration: underline; }}

.sesi-judul-st {{
  font-family: {T.FONT_HEADLINE}; font-size: 1.5rem; font-weight: 800;
  color: {T.TEKS_JUDUL}; margin: 0 0 0.3rem; letter-spacing: -0.01em;
}}
.sesi-sub-st {{ font-size: .92rem; color: {T.TEKS_VARIAN}; margin: 0 0 {T.SP_1}; }}

/* Pill mode Latihan Cepat — class badge-mode dipertahankan supaya test drill
   tetap mengenalinya (marker kelas, bukan teks global). */
.badge-mode {{
  display: inline-block;
  font-family: {T.FONT_HEADLINE}; font-weight: 700; font-size: .72rem;
  background: {T.STATUS_LATIHAN_BG}; color: {T.STATUS_LATIHAN_TEKS};
  padding: 0.15rem 0.5rem; border-radius: {T.RADIUS_PIL};
  margin-left: 0.3rem; vertical-align: middle;
}}

/* Pesan flash (sukses setelah simpan). */
.pesan-st {{
  background: {T.LATAR_TERSIMPAN}; border: 1px solid {T.BORDER_TERSIMPAN};
  color: {T.TEKS_TERSIMPAN}; border-radius: {T.RADIUS_KARTU};
  padding: {T.SP_3} {T.SP_4}; margin: 0 0 {T.SP_4}; font-size: .95rem;
}}

/* Pil navigasi antar-alat sesi (Koreksi · Cetak & Cerita · Lampiran). */
.pil-sesi-st {{
  display: flex; gap: {T.SP_2}; flex-wrap: wrap;
  margin: 0 0 {T.SP_4};
  border-bottom: 1px solid {T.BORDER_VARIAN}; padding-bottom: {T.SP_2};
}}
.pil-sesi-st a {{
  font-family: {T.FONT_HEADLINE}; font-weight: 600; font-size: .88rem;
  color: {T.TEKS_VARIAN}; text-decoration: none;
  padding: {T.SP_2} {T.SP_3}; border-radius: {T.RADIUS_SEDANG};
  border: 1px solid transparent; min-height: {T.TARGET_SENTUH};
  display: inline-flex; align-items: center; gap: {T.SP_1};
}}
.pil-sesi-st a:hover {{ background: {T.LATAR_SEKUNDER_LEMBUT}; color: {T.TEKS_JUDUL}; }}
.pil-sesi-st a.aktif {{
  background: {T.LATAR_SEKUNDER_NETRAL}; color: {T.TEKS_JUDUL};
  border-color: {T.BORDER_VARIAN};
}}

/* Kartu soal koreksi — layout dua kolom (isi kiri, status kanan) di layar
   lebar; tumpuk vertikal di HP. */
.koreksi-kartu-st {{
  background: {T.LATAR_KARTU}; border: 1px solid {T.BORDER_VARIAN};
  border-radius: {T.RADIUS_KARTU}; padding: {T.SP_5} {T.SP_4} {T.SP_4};
  margin-bottom: {T.SP_5}; position: relative;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
  display: flex; flex-direction: column; gap: {T.SP_5};
}}
@media (min-width: 40rem) {{
  .koreksi-kartu-st {{ flex-direction: row; align-items: stretch; }}
  .koreksi-kartu-st .koreksi-isi-st {{ flex: 1; min-width: 0; }}
  .koreksi-kartu-st .koreksi-status-st {{ width: 6rem; flex: none;
    border-left: 1px solid {T.BORDER_VARIAN}; padding-left: {T.SP_4}; }}
}}
.koreksi-isi-st {{ display: flex; flex-direction: column; gap: {T.SP_4}; }}
.koreksi-isi-st.sudah {{ opacity: .85; }}

/* Nomor + template_id badge. */
.koreksi-kepala-st {{ display: flex; align-items: center; gap: {T.SP_3}; }}
.koreksi-nomor-st {{
  flex: none; width: 2rem; height: 2rem;
  background: {T.AKSEN_MURID_UTAMA}; color: {T.TEKS_PUTIH};
  border-radius: {T.RADIUS_BULAT}; border: 2px solid {T.LATAR_KARTU};
  display: inline-flex; align-items: center; justify-content: center;
  font-family: {T.FONT_HEADLINE}; font-weight: 700; font-size: .9rem;
  box-shadow: 0 2px 6px rgba(0,0,0,.18);
}}
.koreksi-tipe-st {{
  font-family: {T.FONT_HEADLINE}; font-size: .78rem; font-weight: 600;
  color: {T.TEKS_VARIAN}; background: {T.LATAR_SEKUNDER_NETRAL};
  padding: 0.15rem 0.5rem; border-radius: {T.RADIUS_PIL};
}}

.teks-soal-st {{ color: {T.TEKS_UTAMA}; line-height: 1.5; }}

.kunci-baris-st {{
  background: {T.LATAR_SEKUNDER_LEMBUT}; border: 1px solid {T.BORDER_VARIAN};
  border-radius: {T.RADIUS_SEDANG}; padding: {T.SP_2} {T.SP_3};
  font-size: .92rem;
}}
.kunci-baris-st .kunci-val {{
  font-family: {T.FONT_HEADLINE}; font-weight: 700; color: {T.TEKS_JUDUL};
  background: {T.LATAR_KARTU}; padding: 0.1rem 0.5rem;
  border-radius: {T.RADIUS_KECIL};
}}

/* Label kecil di kartu koreksi. */
.koreksi-label-st {{
  display: block; font-family: {T.FONT_HEADLINE}; font-weight: 600;
  font-size: .82rem; color: {T.TEKS_VARIAN}; margin: 0 0 {T.SP_2};
  display: flex; align-items: center; gap: {T.SP_1};
}}

/* Baris dua kolom: Jawaban anak | Kode (select). */
.koreksi-baris-st {{
  display: grid; grid-template-columns: 1fr;
  gap: {T.SP_3};
}}
@media (min-width: 30rem) {{
  .koreksi-baris-st {{ grid-template-columns: 1.4fr 1fr; }}
}}
.koreksi-input-st {{
  font: inherit; font-size: 1rem; min-height: {T.TARGET_SENTUH};
  border-radius: {T.RADIUS_SEDANG}; border: 1px solid {T.BORDER_VARIAN};
  background: {T.LATAR_KARTU}; padding: 0 {T.SP_3}; width: 100%;
}}
.koreksi-input-st:focus {{
  border-color: {T.FOKUS_AKSEN}; outline: 0;
  box-shadow: 0 0 0 3px {T.AKSEN_MURID_UTAMA}55;
}}
.koreksi-select-st {{
  font: inherit; font-size: .95rem; min-height: {T.TARGET_SENTUH};
  border-radius: {T.RADIUS_SEDANG}; border: 1px solid {T.BORDER_VARIAN};
  background: {T.LATAR_SEKUNDER_LEMBUT}; padding: 0 {T.SP_3}; width: 100%;
  cursor: pointer;
}}
.koreksi-select-st:focus {{
  border-color: {T.FOKUS_AKSEN}; outline: 0;
  box-shadow: 0 0 0 3px {T.AKSEN_MURID_UTAMA}55;
}}

.koreksi-textarea-st {{
  width: 100%; min-height: 70px;
  border: 1px solid {T.BORDER_VARIAN}; border-radius: {T.RADIUS_SEDANG};
  padding: .6rem; font-size: 1rem; font-family: inherit;
  background: {T.LATAR_SEKUNDER_LEMBUT};
}}
.koreksi-textarea-st:focus {{
  outline: none; border-color: {T.AKSEN_MURID_UTAMA};
  box-shadow: 0 0 0 3px rgba(15,163,163,0.18);
}}

.koreksi-centang-st {{
  display: flex; align-items: center; gap: .5rem;
  font-size: .9rem; color: {T.TEKS_VARIAN}; font-family: {T.FONT_HEADLINE};
}}
.koreksi-centang-st input {{ width: 1.3rem; height: 1.3rem; flex: none; accent-color: {T.AKSEN_MURID_UTAMA}; }}
.koreksi-centang-st label {{ margin: 0; cursor: pointer; }}

.usulan-st {{
  background: {T.LATAR_SEKUNDER_NETRAL}; border-left: 3px solid {T.AKSEN_MURID_UTAMA};
  border-radius: 0 {T.RADIUS_KECIL} {T.RADIUS_KECIL} 0;
  padding: {T.SP_2} {T.SP_3}; font-size: .9rem; color: {T.TEKS_VARIAN};
  margin-top: {T.SP_2};
}}
.usulan-st.ragu {{ border-left-color: {T.AKSEN_KORAL_TUA}; }}
.usulan-st b {{ color: {T.TEKS_JUDUL}; }}

/* Kolom status kanan (badge BENAR/?/K/H/E/T). */
.koreksi-status-st {{
  display: flex; align-items: center; justify-content: center;
  padding-top: {T.SP_3};
  border-top: 1px solid {T.BORDER_VARIAN};
  gap: {T.SP_2}; flex-direction: column;
}}
@media (min-width: 40rem) {{
  .koreksi-status-st {{ border-top: 0; border-left: 1px solid {T.BORDER_VARIAN}; padding-top: 0; }}
}}
.koreksi-bulat-st {{
  width: 3rem; height: 3rem; border-radius: {T.RADIUS_BULAT};
  display: inline-flex; align-items: center; justify-content: center;
  font-family: {T.FONT_HEADLINE}; font-weight: 800; font-size: 1.1rem;
  box-shadow: inset 0 1px 3px rgba(0,0,0,.08);
}}
/* Marker span.kode dipertahankan untuk test; di dalam bulat, warnanya
   mewarisi lingkaran supaya BENAR putih di atas teal, dst. */
.koreksi-bulat-st .kode {{ color: inherit; background: none; padding: 0; border: 0; font: inherit; }}
.koreksi-bulat-st.benar {{ background: {T.AKSEN_MURID_UTAMA}; color: {T.TEKS_PUTIH}; }}
.koreksi-bulat-st.N {{ background: {T.LATAR_ELEVASI}; color: {T.TEKS_VARIAN}; }}
.koreksi-bulat-st.K {{ background: {T.KODE_SALAH_KONSEP_BG}; color: {T.KODE_SALAH_KONSEP_TEKS}; }}
.koreksi-bulat-st.B {{ background: {T.KODE_SALAH_BACA_BG}; color: {T.KODE_SALAH_BACA_TEKS}; }}
.koreksi-bulat-st.H {{ background: {T.KODE_SALAH_HITUNG_BG}; color: {T.KODE_SALAH_HITUNG_TEKS}; }}
.koreksi-bulat-st.E {{ background: {T.KODE_SALAH_TULIS_BG}; color: {T.KODE_SALAH_TULIS_TEKS}; }}
.koreksi-bulat-st.T {{ background: {T.KODE_BELUM_LIAT_BG}; color: {T.KODE_BELUM_LIAT_TEKS}; }}
.koreksi-bulat-label-st {{ font-family: {T.FONT_HEADLINE}; font-weight: 600; font-size: .76rem; color: {T.TEKS_VARIAN}; text-align: center; }}

/* Simpan & diagnosis — tombol coral penuh. */
.koreksi-simpan-st {{
  position: sticky; bottom: 0; padding: {T.SP_3} 0 {T.SP_2};
  background: linear-gradient(to top, {T.LATAR_SEKUNDER_LEMBUT} 70%, transparent);
}}
.koreksi-simpan-st button {{
  width: 100%; font-size: 1.05rem; padding: .9rem;
  background: {T.AKSEN_MURID_KORAL}; color: {T.TEKS_PUTIH};
  border: 0; border-radius: {T.RADIUS_SEDANG};
  font-family: {T.FONT_HEADLINE}; font-weight: 700; cursor: pointer;
  min-height: 48px;
  display: flex; align-items: center; justify-content: center; gap: {T.SP_2};
  box-shadow: 0 4px 12px rgba(255,107,91,.25);
}}
.koreksi-simpan-st button:hover {{ filter: brightness(1.06); }}

/* Danger zone hapus sesi. */
.danger-zone-st {{
  margin-top: 1.2rem; border-top: 1px solid {T.BORDER_GALAT}; padding-top: .7rem;
}}
.danger-zone-st p.sub {{ margin: 0 0 .4rem; font-size: .85rem; color: {T.TEKS_VARIAN}; }}
.tombol-kecil-st {{
  font: inherit; font-family: {T.FONT_HEADLINE}; font-size: .85rem;
  background: {T.LATAR_GALAT}; color: {T.TEKS_GALAT};
  border: 1px solid {T.BORDER_GALAT}; border-radius: {T.RADIUS_SEDANG};
  padding: .5rem {T.SP_4}; cursor: pointer;
  min-height: {T.TARGET_SENTUH};
}}
.tombol-kecil-st:hover {{ filter: brightness(1.04); }}

/* Cetak. */
@media print {{
  .sesi-badan-st {{ max-width: none; padding: 0; }}
  .st-topbar, .koreksi-simpan-st, .pil-sesi-st, .danger-zone-st, .hanya-layar {{ display: none; }}
  .koreksi-kartu-st {{ break-inside: avoid; box-shadow: none; border-color: #000; flex-direction: column; }}
  .koreksi-status-st {{ border: 0; }}
}}
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
