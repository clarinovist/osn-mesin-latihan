"""Halaman landing publik — permukaan pertama pengunjung yang belum masuk.

Dibuka tanpa kredensial (200). Guru/murid yang sudah punya sesi diarahkan
ke /masuk. Konten marketing: apa yang dilakukan produk, untuk siapa, dan
rujukan kompetisi (OSN/SASMO). Data anak TIDAK pernah muncul di sini —
halaman ini statis, tidak membaca basis data sama sekali.

Brand dari design_tokens (sumber tunggal) — jangan hardcode nama di sini.
"""
from __future__ import annotations

import html

import design_tokens as T
import ikon
from gaya_guru import GAYA_GURU as GAYA


def _halaman_publik(judul: str, isi: str) -> bytes:
    """Kerangka halaman publik — sama gaya _halaman web.py, tanpa data."""
    # Link yang berperan sebagai tombol CTA (selector button.* di CSS guru
    # tidak mengenai <a>). Style lokal, tidak menyentuh CSS bersama.
    gaya_cta = (
        "a.tombol-coral,a.tombol-putih{display:inline-block;padding:.6rem 1.2rem;"
        "border-radius:8px;text-decoration:none;font-weight:600;margin:.2rem .4rem .2rem 0}"
        f"a.tombol-coral{{background:{T.AKSEN_MURID_KORAL};color:{T.TEKS_PUTIH}}}"
        f"a.tombol-putih{{background:none;color:{T.STATUS_KUAT};border:1px solid {T.STATUS_KUAT}}}"
        "a.brand{text-decoration:none}"
    )
    return f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(judul)}</title><style>{GAYA}</style><style>{gaya_cta}</style></head>
<body><div class="bungkus">{isi}</div></body></html>""".encode()


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
        kelas = "pesan galat" if galat else "pesan tersimpan"
        kotak = f'<div class="{kelas}">{html.escape(pesan)}</div>'

    isi = f"""
<div class="topbar"><a class="brand" href="/">{n}</a>
<nav class="topbar-navigasi">
<a href="/masuk">Masuk</a></nav></div>

<section class="kartu" style="max-width:26rem;margin:2rem auto">
<h1>Daftar {n}</h1>
<p class="sub">Buat akun pengelola — untuk orang tua yang menemani anak,
guru, atau les privat. Akun anak dibuat setelah ini, dari dalam aplikasi.</p>
{kotak}
<form method="post" action="/daftar">
<label>Nama pengguna</label>
<input type="text" name="nama" autocomplete="username" required
 value="{html.escape(nama)}">
<label>Kata sandi (minimal 8 karakter)</label>
<input type="password" name="sandi" autocomplete="new-password" required minlength="8">
<p style="font-size:.9rem">
 <label style="display:flex;gap:.5rem;align-items:flex-start">
  <input type="checkbox" name="setuju" value="1" style="margin-top:.25rem">
  <span>Saya orang tua/wali atau pendidik yang bertanggung jawab, dan saya
  menyetujui <a href="/kebijakan-privasi">Kebijakan Privasi</a>.</span>
 </label>
</p>
<button type="submit" class="tombol-coral" style="width:100%">Buat akun</button>
</form>
</section>
"""
    return _halaman_publik(f"Daftar — {T.NAMA_PRODUK}", isi)


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
<div class="topbar"><a class="brand" href="/">{n}</a>
<nav class="topbar-navigasi"><a href="/masuk">Masuk</a></nav></div>

<section class="kartu" style="max-width:46rem;margin:2rem auto">
<h1>Kebijakan Privasi</h1>
<p class="sub">Ringkas dan jujur, tanpa bahasa hukum.
Terakhir diperbarui 30 Agustus 2026.</p>

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
memberimu akun.</p>
</section>
"""
    return _halaman_publik(f"Kebijakan Privasi — {T.NAMA_PRODUK}", isi)


def halaman_landing() -> bytes:
    n = html.escape(T.NAMA_PRODUK)
    tag = html.escape(T.TAGLINE)
    isi = f"""
<div class="topbar"><a class="brand" href="/">{n}</a>
<nav class="topbar-navigasi"><a href="/masuk">Masuk</a></nav></div>

<section class="kartu hero-landing">
  <img src="{ikon.OWL}" alt="" width="120" height="120">
  <h1>{n}</h1>
  <p class="sub">{tag}</p>
  <p>Anak berlatih matematika, menuliskan <b>caranya</b>, dan sistem
  menunjukkan letak kesalahannya — salah baca, salah konsep, salah hitung,
  atau salah tulis. Orang tua dan guru melihat peta belajarnya, bukan
  sekadar nilai.</p>
  <p><a class="tombol-coral" href="/daftar">Mulai — daftar sekarang</a></p>
</section>

<div class="grid-utama">
<section class="kartu">
  <h2>Untuk siapa</h2>
  <p><b>Orang tua</b> — temani anak belajar di rumah, lihat perkembangannya
  dari laporan mingguan.</p>
  <p><b>Guru &amp; les privat</b> — kelola banyak murid, beri latihan sesuai
  tingkat, dan ketahui topik mana yang perlu diulang.</p>
</section>

<section class="kartu">
  <h2>Cara kerja</h2>
  <ol>
    <li>Buat sesi latihan — pilih topik &amp; tingkat (P3–P6).</li>
    <li>Anak mengerjakan, lalu menuliskan caranya sendiri.</li>
    <li>Sistem mendiagnosis: jawaban benar, salah hitung, atau salah konsep
    — dan topik mana yang perlu diulang.</li>
  </ol>
</section>

<section class="kartu">
  <h2>Topik latihan</h2>
  <p>Pola bilangan, aritmetika dasar, geometri datar, kombinatorik — dengan
  soal yang dibuat otomatis sehingga tiap sesi berbeda dari sebelumnya.</p>
</section>

<section class="kartu">
  <h2>Ke arah kompetisi</h2>
  <p>Materi disusun mengikuti silabus OSN Matematika SD (Bilangan,
  Aritmatika, Geometri, Statistika &amp; Pengukuran, Kombinatorik) dan cocok
  juga untuk persiapan SASMO. Berlatih teratur di sini adalah fondasi kuat
  untuk olimpiade — tapi produk ini untuk semua anak yang ingin kuat
  matematika, bukan hanya calon peserta olimpiade.</p>
</section>
</div>

<footer class="sub" style="text-align:center;margin-top:1.5rem">
  <a href="/kebijakan-privasi">Kebijakan Privasi</a>
</footer>
"""
    return _halaman_publik(T.NAMA_PRODUK, isi)
