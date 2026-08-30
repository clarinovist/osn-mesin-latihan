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
