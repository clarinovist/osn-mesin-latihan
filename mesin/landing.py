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
    return f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(judul)}</title><style>{GAYA}</style></head>
<body><div class="bungkus">{isi}</div></body></html>""".encode()


def halaman_landing() -> bytes:
    n = html.escape(T.NAMA_PRODUK)
    tag = html.escape(T.TAGLINE)
    isi = f"""
<div class="topbar"><span class="brand">{n}</span>
<nav class="topbar-navigasi"><a href="/masuk">Masuk</a></nav></div>

<section class="kartu hero-landing">
  <img src="{ikon.OWL}" alt="" width="120" height="120">
  <h1>{n}</h1>
  <p class="sub">{tag}</p>
  <p>Anak berlatih matematika, menuliskan <b>caranya</b>, dan sistem
  menunjukkan letak kesalahannya — salah baca, salah konsep, salah hitung,
  atau salah tulis. Orang tua dan guru melihat peta belajarnya, bukan
  sekadar nilai.</p>
  <p><a class="tombol-coral" href="/daftar">Mulai — daftar sekarang</a>
     <a class="tombol-putih" href="/masuk">Sudah punya akun? Masuk</a></p>
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
  <a href="/kebijakan-privasi">Kebijakan Privasi</a> ·
  <a href="/masuk">Masuk</a>
</footer>
"""
    return _halaman_publik(T.NAMA_PRODUK, isi)
