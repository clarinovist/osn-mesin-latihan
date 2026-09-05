"""Halaman landing publik — permukaan pertama pengunjung yang belum masuk.

Dibuka tanpa kredensial (200). Guru/murid yang sudah punya sesi diarahkan
ke /masuk. Konten marketing: apa yang dilakukan produk, untuk siapa, dan
rujukan kompetisi (OSN/SASMO). Data anak TIDAK pernah muncul di sini —
halaman ini statis, tidak membaca basis data sama sekali.

Brand dari design_tokens (sumber tunggal) — jangan hardcode nama di sini.

Sejak S8-S11 (1 Sep 2026): semua halaman publik diadopsi ke Stitch.
_halaman_publik lama dihapus (cleanup). Kontrak markup test dipertahankan.
"""
from __future__ import annotations

import html

import brand
import design_tokens as T
from teacher_style import SKRIP_MATA_SANDI, SKRIP_CEGAH_KIRIM_GANDA


def _font_link() -> str:
    """<link> Google Fonts CDN — dipakai semua halaman publik Stitch."""
    return (
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700'
        '&family=Plus+Jakarta+Sans:wght@400;600;700;800'
        '&family=Material+Symbols+Outlined&display=swap" rel="stylesheet">'
    )


def _halaman_publik_stitch(
    judul: str, isi: str, og: dict[str, str] | None = None
) -> bytes:
    """Kerangka halaman publik versi Stitch — GAYA_STITCH, body.st.

    Dipakai oleh halaman_daftar, halaman_kebijakan, halaman_lupa_sandi
    (S8-S10). Kontrak markup yang diuji test (a.brand href=/, tombol-putih
    href=/masuk, href=/masuk tepat 1) dipertahankan di markup isi.

    og = metadata share (WhatsApp/Facebook) untuk halaman yang memang
    dibagikan; None berarti favicon + manifest saja.
    """
    from style_stitch import gaya_stitch

    return f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(brand.judul(judul))}</title>
{brand.tag_kepala(og)}
{_font_link()}
<style>{gaya_stitch()}</style></head>
<body class="st"><div class="publik-badan-st">{isi}</div>
<script>{SKRIP_MATA_SANDI}</script><script>{SKRIP_CEGAH_KIRIM_GANDA}</script></body></html>""".encode()


def _topbar_publik_st() -> str:
    """Topbar publik Stitch: brand owl + nama (link /), tombol Masuk."""
    n = html.escape(T.NAMA_PRODUK)
    return (
        '<div class="publik-topbar-st">'
        f'<a class="brand" href="/">'
        f'{brand.mark("topbar")}'
        f'<span>{n}</span></a>'
        '<nav class="topbar-navigasi">'
        f'<a class="tombol-putih" href="/masuk">Masuk</a></nav></div>'
    )


def halaman_daftar(
    pesan: str = "", galat: bool = False, nama: str = ""
) -> bytes:
    """Form pendaftaran mandiri pengelola (orang tua / guru / les).

    pesan = teks feedback; galat=True membuatnya dirender sebagai galat.
    nama = nama yang diketik pengguna (dikembalikan supaya tidak mengetik ulang).
    """
    n = html.escape(T.NAMA_PRODUK)
    kotak = ""
    if pesan:
        kelas = "masuk-galat-st" if galat else "pesan-st"
        kotak = f'<div class="{kelas}">{html.escape(pesan)}</div>'

    isi = f"""
{_topbar_publik_st()}
<div class="publik-bungkus-st">
<section class="publik-kartu-st">
<h1 class="publik-judul-st">Daftar {n}</h1>
<p class="publik-sub-st">Buat akun orang tua — untuk orang tua yang menemani anak,
guru, atau les privat. Akun anak dibuat setelah ini, dari dalam aplikasi.</p>
{kotak}
<form class="masuk-form-st" method="post" action="/daftar">
  <div class="masuk-field-st">
    <label for="nama">Nama pengguna</label>
    <input type="text" id="nama" name="nama" autocomplete="username" required
     value="{html.escape(nama)}">
  </div>
  <div class="masuk-field-st">
    <label for="sandi">Kata sandi (minimal 8 karakter)</label>
    <input type="password" id="sandi" name="sandi" autocomplete="new-password" required minlength="8">
  </div>
  <p style="font-size:.9rem">
   <label class="koreksi-centang-st" style="font-weight:400">
    <input type="checkbox" name="setuju" value="1">
    <span>Saya orang tua/wali atau pendidik yang bertanggung jawab, dan saya
    menyetujui <a href="/kebijakan-privasi">Kebijakan Privasi</a>.</span>
   </label>
  </p>
  <button class="masuk-tombol-st" type="submit">
    <span class="material-symbols-outlined" style="font-size:1.1rem">person_add</span>
    Buat akun
  </button>
</form>
</section>
</div>
"""
    return _halaman_publik_stitch(f"Daftar — {T.NAMA_PRODUK}", isi)


def halaman_kebijakan() -> bytes:
    """Kebijakan privasi publik — tujuan tiga tautan persetujuan
    (footer landing, checkbox /daftar, checkbox anak-baru di web.py).

    Statis: tidak membaca basis data sama sekali, identik untuk semua
    pengunjung. Isinya mengikuti perilaku aplikasi yang SEBENARNYA —
    termasuk pengiriman foto lembar ke layanan AI — bukan janji yang
    belum diimplementasi.
    """
    n = html.escape(T.NAMA_PRODUK)
    isi = f"""
{_topbar_publik_st()}
<div class="publik-bungkus-st">
<section class="publik-kartu-st lebar">
<h1>Kebijakan Privasi</h1>
<p class="publik-sub-st">Ringkas dan jujur, tanpa bahasa hukum.
Terakhir diperbarui 30 Agustus 2026.</p>

<div class="publik-isi-st">
<h2>Data yang dikumpulkan</h2>
<ul>
<li>Nama akun orang tua/guru dan kata sandinya (disimpan sebagai hash).</li>
<li>Nama panggilan anak dan kelas sekolahnya (kelas 3–6).</li>
<li>Hasil latihan: jawaban anak, kode diagnosis kesalahan
(K/B/H/E/T/N), dan catatan guru.</li>
<li>Foto lembar jawaban — hanya jika kamu mengunggahnya sebagai
lampiran.</li>
</ul>

<h2>Data anak</h2>
<p>Akun anak hanya bisa dibuat oleh orang tua/guru dari dalam aplikasi —
anak tidak pernah mendaftar sendiri. Anak hanya melihat sesi latihannya
sendiri di halaman murid; tidak ada obrolan atau kontak antar-anak.</p>

<h2>Layanan AI pihak ketiga</h2>
<p>Fitur <b>variasi cerita</b> mengirim kalimat soal (tanpa nama anak,
tanpa kunci jawaban) ke layanan AI untuk ditulis ulang menjadi soal
bercerita. Fitur <b>lampiran foto</b> mengirim foto lembar yang sudah
diisi anak ke layanan AI agar jawabannya bisa dibaca otomatis — foto itu
bisa memuat tulisan tangan anak. Selain dua fitur ini, tidak ada data
yang keluar dari server.</p>

<h2>Siapa yang bisa melihat</h2>
<ul>
<li>Data satu keluarga hanya terlihat oleh akun keluarga itu sendiri.</li>
<li>Akun pengelola server dapat membuka laporan untuk keperluan
dukungan, tetapi tidak bisa mengubah data anak.</li>
<li>Tidak ada pihak lain: tanpa iklan, tanpa pelacak, tanpa analitik.</li>
</ul>

<h2>Data yang tidak dikumpulkan</h2>
<ul>
<li>Tidak ada email, nomor telepon, atau alamat.</li>
<li>Tidak ada cookie pelacak atau analitik pihak ketiga.</li>
<li>Cukup tulis nama panggilan anak — jangan nama lengkap atau data
pribadi lainnya.</li>
</ul>

<h2>Penyimpanan &amp; penghapusan data</h2>
<p>Semua data tersimpan dalam satu basis data di server pengelola —
bukan layanan cloud pihak ketiga. Dari aplikasi, kamu bisa menghapus
sesi latihan dan akun login anak kapan saja. Untuk penghapusan yang
lebih besar (seluruh data keluarga), hubungi pengelola server lewat WA
{html.escape(T.WA_SUPPORT)} — sebutkan nama akunmu.</p>
</div>
</section>
</div>
"""
    return _halaman_publik_stitch(f"Kebijakan Privasi — {T.NAMA_PRODUK}", isi)


def halaman_lupa_sandi() -> bytes:
    """Panduan publik "Lupa sandi?" — murni teks, tanpa form apa pun.

    Aplikasi ini SENGAJA tidak menyimpan email/telepon, jadi reset mandiri
    via email mustahil: tidak ada jalur kirim-ulang sandi otomatis dan tidak
    boleh diarang seolah ada. Sandi hanya bisa disetel ulang oleh manusia
    yang tepat — guru/orang tua untuk murid, pengelola untuk orang tua.
    Halaman ini menunjukkan jalurnya supaya yang terkunci tidak buntu di
    halaman masuk.
    """
    n = html.escape(T.NAMA_PRODUK)
    isi = f"""
{_topbar_publik_st()}
<div class="publik-bungkus-st">
<section class="publik-kartu-st" style="max-width:30rem">
<h1 class="publik-judul-st">Lupa sandi?</h1>
<p class="publik-sub-st">Tidak apa-apa — sandimu bisa disetel ulang, hanya saja tidak
lewat email.</p>
<div class="publik-isi-st">
<p>Aplikasi ini tidak menyimpan email, jadi sandi tidak bisa dikirim
otomatis. Yang menyetel ulang adalah manusia yang tepat:</p>
<ul>
<li><b>Kamu murid?</b> Mintalah gurumu atau orang tuamu menyetel sandi
baru — dari halaman Akun, kartu "Akun latihan", tombol
"Setel sandi baru".</li>
<li><b>Kamu orang tua yang daftar sendiri di /daftar?</b> Hubungi WA
{html.escape(T.WA_SUPPORT)} — sebutkan nama akunmu — untuk disetel
ulang oleh pengelola.</li>
<li><b>Akunmu dibuatkan les/guru?</b> Minta ke mereka yang menyetel
ulang — sandimu terikat ke keluarga mereka.</li>
</ul>
<p><a href="/masuk">Kembali ke halaman masuk</a></p>
</div>
</section>
</div>
"""
    return _halaman_publik_stitch(f"Lupa sandi? — {T.NAMA_PRODUK}", isi)


def halaman_landing() -> bytes:
    """Landing publik — mengikuti mockup Stitch landing_page_desktop.

    Memakai kerangka .landing-*-st sendiri (container 75rem), BUKAN
    .publik-*-st yang diklem 46rem untuk form: klem itu membuat
    halaman tampil separo layar di laptop (keluhan 4 Sep 2026).

    Yang sengaja TIDAK disalin dari mockup: nama "Caraku" (pakai
    T.NAMA_PRODUK), logo dari URL asing (pakai brand.mark), Tailwind
    CDN (CSS manual + token), klaim "Tulis Tangan" (aplikasi tidak
    punya input tulis tangan — yang ada foto lembar + AI vision yang
    dikonfirmasi guru), klaim "gratis" (keputusan bisnis), dan tombol
    "Cek Jawaban" (kontrol mati di halaman publik).
    """
    n = html.escape(T.NAMA_PRODUK)
    tag = html.escape(T.TAGLINE)
    mark_topbar = brand.mark("topbar")
    mark_hero = brand.mark("badge")
    isi = f"""
<header class="landing-topbar-st"><div class="landing-topbar-isi-st">
<a class="brand" href="/">{mark_topbar}<span>{n}</span></a>
<nav class="topbar-navigasi"><a class="tombol-putih" href="/masuk">Masuk</a></nav>
</div></header>

<div class="landing-bungkus-st">
<section class="landing-hero-st">
<div class="landing-hero-teks-st">
  <div class="landing-merek-st">{mark_hero}<span>{n}</span></div>
  <h1 class="landing-judul-st">Latih. Tulis caramu. Ketahui letak salahmu.</h1>
  <p class="landing-tagline-st">{tag}</p>
  <p class="landing-sub-st">Anak berlatih matematika, menuliskan <b>caranya</b>, dan
  sistem menunjukkan letak kesalahannya — salah baca, salah konsep, salah
  hitung, atau salah tulis. Orang tua dan guru melihat peta belajarnya, bukan
  sekadar nilai.</p>
  <p class="landing-cta-baris-st"><a class="tombol-coral" href="/daftar">
  <span class="material-symbols-outlined" style="font-size:1.15rem">rocket_launch</span>
  Mulai — daftar sekarang</a></p>
</div>

<div class="landing-demo-st">
  <div class="landing-demo-kepala-st"><span>Soal 4/10</span><span>Contoh</span></div>
  <p class="landing-demo-soal-st">Berapa hasil dari 345 + 128?</p>
  <div class="landing-demo-cara-st">  345
+ 128
─────
  463</div>
  <div class="landing-demo-hasil-st">
    <p class="landing-demo-label-st">Letak salahnya</p>
    <div class="landing-kode-grup-st">
      <span class="landing-kode-st aktif">H · Salah hitung</span>
      <span class="landing-kode-st">K · Salah konsep</span>
      <span class="landing-kode-st">B · Salah baca</span>
    </div>
    <p class="landing-demo-catatan-st"><b>Caranya sudah benar</b> — susun
    bersusun, mulai dari satuan. Yang meleset di 5 + 8: hasilnya 13, tulis 3
    simpan 1. Jadi jawabannya 473, bukan 463.</p>
  </div>
</div>
</section>

<section class="landing-pill-baris-st">
  <span class="landing-pill-st">
  <span class="material-symbols-outlined" style="font-size:1.15rem">edit_document</span>
  Tulis caranya</span>
  <span class="landing-pill-st">
  <span class="material-symbols-outlined" style="font-size:1.15rem">query_stats</span>
  Peta belajar</span>
  <span class="landing-pill-st">
  <span class="material-symbols-outlined" style="font-size:1.15rem">mood</span>
  Tanpa tekanan</span>
</section>

<div class="landing-grid-st">
<section class="landing-kartu-st">
  <h2 class="landing-kartu-judul-st">
  <span class="material-symbols-outlined">groups</span>Untuk siapa</h2>
  <div class="landing-kartu-isi-st">
  <p><b>Orang tua</b> — temani anak belajar di rumah, lihat perkembangannya
  dari laporan mingguan.</p>
  <p><b>Guru &amp; les privat</b> — kelola banyak murid, beri latihan sesuai
  tingkat, dan ketahui topik mana yang perlu diulang.</p>
  </div>
</section>

<section class="landing-kartu-st">
  <h2 class="landing-kartu-judul-st">
  <span class="material-symbols-outlined">list_alt</span>Cara kerja</h2>
  <div class="landing-kartu-isi-st">
  <ol>
    <li>Buat sesi latihan — pilih topik &amp; kelas.</li>
    <li>Anak mengerjakan, lalu menuliskan caranya sendiri.</li>
    <li>Sistem mendiagnosis: jawaban benar, salah hitung, atau salah konsep
    — dan topik mana yang perlu diulang.</li>
  </ol>
  </div>
</section>

<section class="landing-kartu-st">
  <h2 class="landing-kartu-judul-st">
  <span class="material-symbols-outlined">functions</span>Topik latihan</h2>
  <div class="landing-kartu-isi-st">
  <p>Pola bilangan, aritmetika dasar, geometri datar, kombinatorik — dengan
  soal yang dibuat otomatis sehingga tiap sesi berbeda dari sebelumnya.</p>
  </div>
</section>

<section class="landing-kartu-st">
  <h2 class="landing-kartu-judul-st">
  <span class="material-symbols-outlined">emoji_events</span>Ke arah kompetisi</h2>
  <div class="landing-kartu-isi-st">
  <p>Materi disusun mengikuti silabus OSN Matematika SD (Bilangan,
  Aritmatika, Geometri, Statistika &amp; Pengukuran, Kombinatorik) dan cocok
  juga untuk persiapan SASMO. Berlatih teratur di sini adalah fondasi kuat
  untuk olimpiade — tapi produk ini untuk semua anak yang ingin kuat
  matematika, bukan hanya calon peserta olimpiade.</p>
  </div>
</section>
</div>

<section style="margin-bottom:3rem">
<h2 class="landing-contoh-judul-st">Contoh yang dilihat orang tua</h2>
<p class="landing-contoh-sub-st">Contoh tertulis — bukan data anak mana pun.</p>
<div class="landing-grid-st" style="margin-bottom:0">
<section class="landing-kartu-st">
  <div class="landing-contoh-kode-st">
  <span class="landing-contoh-dot-st" style="background:{T.STATUS_SALAH}"></span>
  K · Salah konsep</div>
  <div class="landing-kartu-isi-st">
  <p>2/3 + 3/4 dijawab <b>5/7</b> — pembilang dan penyebut dijumlahkan
  sendiri-sendiri, dan anak yakin caranya benar.</p>
  <div class="landing-resep-st"><b>Resep:</b> 4–6 minggu pakai benda nyata
  (kue/gelas air) sebelum kembali ke angka. Cek ulang tiap 3 hari dengan
  angka berbeda.</div>
  </div>
</section>

<section class="landing-kartu-st">
  <div class="landing-contoh-kode-st">
  <span class="landing-contoh-dot-st" style="background:{T.STATUS_LEMAH}"></span>
  B · Salah baca soal</div>
  <div class="landing-kartu-isi-st">
  <p>Soal cerita kecepatan: angka yang ditanya tidak ditandai — anak
  menghitung hal yang salah.</p>
  <div class="landing-resep-st"><b>Resep:</b> bukan lubang matematika.
  Latihan pegang pensil, tandai yang ditanya, ucapkan ulang soal.
  Biasanya hilang 2–3 minggu.</div>
  </div>
</section>

<section class="landing-kartu-st">
  <div class="landing-contoh-kode-st">
  <span class="landing-contoh-dot-st" style="background:{T.STATUS_KUAT}"></span>
  H · Salah hitung</div>
  <div class="landing-kartu-isi-st">
  <p>Perkalian bersusun: caranya benar, angkanya meleset di langkah
  penjumlahan.</p>
  <div class="landing-resep-st"><b>Resep:</b> bukan materi baru. Wajib tulis
  langkah + periksa ulang — gejala terburu-buru, bukan tidak paham.</div>
  </div>
</section>
</div>
</section>

<section style="margin-bottom:3rem">
<h2 class="landing-contoh-judul-st">Ikut pilot</h2>
<p class="landing-contoh-sub-st">Dibuka untuk 10–20 keluarga pertama
(kelas 4–6). Syaratnya: minimal 6 sesi latihan, izin memakai data
anonim untuk bukti, dan testimoni di akhir. Tertarik? Daftar lewat
tombol di atas — gratis selama masa pilot.</p>
</section>

<section class="landing-faq-st">
<h2 class="landing-contoh-judul-st">Sering ditanya</h2>
<details><summary>Untuk kelas berapa?</summary>
<p>Kelas 3–6 SD. Kelas 4–5 paling cocok untuk pilot.</p></details>
<details><summary>Anak mengerjakan di HP atau kertas?</summary>
<p>Keduanya bisa: kerjakan langsung di HP lewat halaman murid, atau cetak
lembarnya, kerjakan di kertas, lalu kirim foto lembarnya.</p></details>
<details><summary>Apakah ini khusus olimpiade?</summary>
<p>Tidak. Materinya mengikuti silabus OSN/SASMO sebagai fondasi, tapi
tujuannya semua anak yang ingin kuat matematika — diagnosis salah
konsep vs salah hitung berguna untuk nilai harian juga.</p></details>
<details><summary>Setelah pilot gratis, lalu apa?</summary>
<p>Harga belum diputuskan. Peserta pilot ikut menentukan — yang jelas
tidak ada tagihan diam-diam selama masa pilot.</p></details>
<details><summary>Data anak disimpan di mana?</summary>
<p>Di server pengelola, bukan cloud pihak ketiga. Tanpa iklan, tanpa
pelacak. Cukup tulis nama panggilan anak — dan aplikasi tidak
menyimpan email atau nomor telepon siapa pun.</p></details>
<details><summary>Lupa sandi bagaimana?</summary>
<p>Tidak ada reset via email. Anak minta ke orang tua/gurunya; orang tua
yang daftar sendiri hubungi WA {html.escape(T.WA_SUPPORT)}
(sebutkan nama akunmu). Detailnya ada di halaman
<a href="/lupa-sandi">Lupa sandi</a>.</p></details>
</section>
</div>

<footer class="landing-footer-st"><div class="landing-footer-isi-st">
  <div><a href="/kebijakan-privasi">Kebijakan Privasi</a> ·
  <span>Butuh bantuan? WA {html.escape(T.WA_SUPPORT)}</span></div>
  <div>{n} — {tag}</div>
</div></footer>
"""
    return _halaman_publik_stitch(
        T.NAMA_PRODUK,
        isi,
        og={
            "judul": f"{T.NAMA_PRODUK} — {T.TAGLINE}",
            "deskripsi": (
                "Latihan matematika bergaya OSN/SASMO untuk anak SD. Anak "
                "menulis caranya, orang tua melihat di mana letak salahnya."
            ),
            "jalur": "/",
        },
    )
