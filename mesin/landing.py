"""Halaman landing publik — permukaan pertama pengunjung yang belum masuk.

Dibuka tanpa kredensial (200). Guru/murid yang sudah punya sesi diarahkan
ke /masuk. Konten marketing: apa yang dilakukan produk, untuk siapa, dan
rujukan kompetisi (OSN/SASMO). Data anak TIDAK pernah muncul di sini —
halaman ini statis, tidak membaca basis data sama sekali.

Brand dari design_tokens (sumber tunggal) — jangan hardcode nama di sini.

Sejak S8-S10 (1 Sep 2026): halaman publik diadopsi ke Stitch. Fungsi lama
_halaman_publik tetap (dipanggil fungsi Stitch yang bungkus-nya beda);
kontrak markup test (a.brand href=/, tombol-putih, href=/masuk tepat 1)
dipertahankan persis.
"""
from __future__ import annotations

import html

import design_tokens as T
import icons
from teacher_style import GAYA_GURU as GAYA, SKRIP_MATA_SANDI, SKRIP_CEGAH_KIRIM_GANDA


def _font_link() -> str:
    """<link> Google Fonts CDN — dipakai semua halaman publik Stitch."""
    return (
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700'
        '&family=Plus+Jakarta+Sans:wght@400;600;700;800'
        '&family=Material+Symbols+Outlined&display=swap" rel="stylesheet">'
    )


def _halaman_publik(judul: str, isi: str) -> bytes:
    """Kerangka halaman publik — sama gaya _halaman web.py, tanpa data."""
    # Link yang berperan sebagai tombol CTA (selector button.* di CSS guru
    # tidak mengenai <a>). Style lokal, tidak menyentuh CSS bersama.
    # Warna CTA memakai aksen teks-aman: putih di atas coral terang 2.8:1.
    gaya_cta = (
        "a.tombol-coral,a.tombol-putih{display:inline-block;padding:.6rem 1.2rem;"
        "border-radius:8px;text-decoration:none;font-weight:600;margin:.2rem .4rem .2rem 0}"
        f"a.tombol-coral{{background:{T.AKSEN_KORAL_TUA};color:{T.TEKS_PUTIH}}}"
        f"a.tombol-putih{{background:none;color:{T.AKSEN_TEAL_TUA};border:1px solid {T.AKSEN_TEAL_TUA}}}"
        f".topbar-navigasi a.tombol-putih:hover{{color:{T.AKSEN_MURID_UTAMA};"
        f"border-color:{T.AKSEN_MURID_UTAMA}}}"
        "a.brand{text-decoration:none}"
    )
    return f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(judul)}</title><style>{GAYA}</style><style>{gaya_cta}</style></head>
<body><div class="bungkus">{isi}</div><script>{SKRIP_MATA_SANDI}</script><script>{SKRIP_CEGAH_KIRIM_GANDA}</script></body></html>""".encode()


def _halaman_publik_stitch(judul: str, isi: str) -> bytes:
    """Kerangka halaman publik versi Stitch — GAYA_STITCH, body.st.

    Dipakai oleh halaman_daftar, halaman_kebijakan, halaman_lupa_sandi
    (S8-S10). Kontrak markup yang diuji test (a.brand href=/, tombol-putih
    href=/masuk, href=/masuk tepat 1) dipertahankan di markup isi.
    """
    from style_stitch import gaya_stitch

    return f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(judul)}</title>
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
        '<span class="material-symbols-outlined">school</span>'
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
<p class="publik-sub-st">Buat akun pengelola — untuk orang tua yang menemani anak,
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
<li>Nama panggilan anak dan tingkat sekolahnya (P3–P6).</li>
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
lebih besar (seluruh data keluarga), hubungi pengelola server yang
membermu akun.</p>
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
<li><b>Kamu orang tua/guru?</b> Hubungi pengelola aplikasi — orang yang
membuatkan akunmu — untuk menyetel ulang sandimu.</li>
</ul>
<p><a href="/masuk">Kembali ke halaman masuk</a></p>
</div>
</section>
</div>
"""
    return _halaman_publik_stitch(f"Lupa sandi? — {T.NAMA_PRODUK}", isi)


def halaman_landing() -> bytes:
    n = html.escape(T.NAMA_PRODUK)
    tag = html.escape(T.TAGLINE)
    isi = f"""
<div class="publik-topbar-st"><a class="brand" href="/"><span class="material-symbols-outlined">school</span><span>{n}</span></a>
<nav class="topbar-navigasi"><a class="tombol-putih" href="/masuk">Masuk</a></nav></div>

<div class="publik-bungkus-st">
<section class="publik-kartu-st" style="text-align:center;align-items:center">
  <span class="material-symbols-outlined fill" style="font-size:5rem;color:{T.AKSEN_MURID_UTAMA}">pets</span>
  <h1 class="publik-judul-st" style="font-size:2rem">{n}</h1>
  <p class="publik-sub-st" style="font-size:1.05rem">{tag}</p>
  <p class="publik-isi-st">Anak berlatih matematika, menuliskan <b>caranya</b>, dan sistem
  menunjukkan letak kesalahannya — salah baca, salah konsep, salah hitung,
  atau salah tulis. Orang tua dan guru melihat peta belajarnya, bukan
  sekadar nilai.</p>
  <p style="margin-top:1rem"><a class="tombol-coral" href="/daftar">
  <span class="material-symbols-outlined" style="font-size:1.1rem">rocket_launch</span>
  Mulai — daftar sekarang</a></p>
</section>

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(18rem,1fr));gap:{T.SP_5};margin-top:{T.SP_5}">
<section class="publik-kartu-st">
  <h2 class="publik-judul-st" style="font-size:1.1rem">Untuk siapa</h2>
  <div class="publik-isi-st">
  <p><b>Orang tua</b> — temani anak belajar di rumah, lihat perkembangannya
  dari laporan mingguan.</p>
  <p><b>Guru &amp; les privat</b> — kelola banyak murid, beri latihan sesuai
  tingkat, dan ketahui topik mana yang perlu diulang.</p>
  </div>
</section>

<section class="publik-kartu-st">
  <h2 class="publik-judul-st" style="font-size:1.1rem">Cara kerja</h2>
  <div class="publik-isi-st">
  <ol>
    <li>Buat sesi latihan — pilih topik &amp; tingkat (P3–P6).</li>
    <li>Anak mengerjakan, lalu menuliskan caranya sendiri.</li>
    <li>Sistem mendiagnosis: jawaban benar, salah hitung, atau salah konsep
    — dan topik mana yang perlu diulang.</li>
  </ol>
  </div>
</section>

<section class="publik-kartu-st">
  <h2 class="publik-judul-st" style="font-size:1.1rem">Topik latihan</h2>
  <div class="publik-isi-st">
  <p>Pola bilangan, aritmetika dasar, geometri datar, kombinatorik — dengan
  soal yang dibuat otomatis sehingga tiap sesi berbeda dari sebelumnya.</p>
  </div>
</section>

<section class="publik-kartu-st">
  <h2 class="publik-judul-st" style="font-size:1.1rem">Ke arah kompetisi</h2>
  <div class="publik-isi-st">
  <p>Materi disusun mengikuti silabus OSN Matematika SD (Bilangan,
  Aritmatika, Geometri, Statistika &amp; Pengukuran, Kombinatorik) dan cocok
  juga untuk persiapan SASMO. Berlatih teratur di sini adalah fondasi kuat
  untuk olimpiade — tapi produk ini untuk semua anak yang ingin kuat
  matematika, bukan hanya calon peserta olimpiade.</p>
  </div>
</section>
</div>

<footer class="publik-sub-st" style="text-align:center;margin-top:2rem">
  <a href="/kebijakan-privasi">Kebijakan Privasi</a>
</footer>
</div>
"""
    return _halaman_publik_stitch(T.NAMA_PRODUK, isi)
