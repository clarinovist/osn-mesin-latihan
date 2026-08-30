"""Navigasi landing: satu pintu Masuk, brand = link beranda.

Kontrak:
1. /daftar: brand = anchor link ke /; nav hanya "Masuk"; tidak ada
   duplikat "Sudah punya akun? Masuk" di bawah form.
2. Homepage: nav hanya "Masuk" — sebagai tombol outline (tombol-putih),
   tetap kalah menonjol dari CTA coral; hero single CTA; footer tanpa /masuk.
3. Kedua halaman: tepat 1 href="/masuk".
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import design_tokens as T  # noqa: E402
import web  # noqa: E402
from landing import halaman_daftar, halaman_kebijakan, halaman_landing  # noqa: E402


def _html(func, *a, **kw) -> str:
    return func(*a, **kw).decode()


# ──────────────────── halaman_daftar ────────────────────

def test_daftar_brand_adalah_link_beranda():
    h = _html(halaman_daftar)
    assert '<a class="brand" href="/">' in h


def test_daftar_tidak_ada_beranda_di_nav():
    h = _html(halaman_daftar)
    assert ">Beranda</a>" not in h


def test_daftar_href_masuk_tepat_satu():
    h = _html(halaman_daftar)
    assert h.count('href="/masuk"') == 1


def test_daftar_tidak_ada_duplikat_bawah_form():
    h = _html(halaman_daftar)
    assert "Sudah punya akun?" not in h


# ──────────────────── halaman_landing ───────────────────

def test_landing_href_masuk_tepat_satu():
    h = _html(halaman_landing)
    assert h.count('href="/masuk"') == 1


def test_landing_masuk_tombol_outline_di_nav():
    """Dulu Masuk sengaja teks polos (single-CTA), tapi tampilannya
    seperti lupa didesain. Sekarang tombol outline — tetap kalah
    menonjol dari CTA coral."""
    h = _html(halaman_landing)
    assert '<a class="tombol-putih" href="/masuk">Masuk</a>' in h


def test_landing_footer_tanpa_masuk():
    h = _html(halaman_landing)
    footer_start = h.index("<footer")
    footer = h[footer_start:]
    assert 'href="/masuk"' not in footer


def test_landing_brand_adalah_link_beranda():
    h = _html(halaman_landing)
    assert '<a class="brand" href="/">' in h


def test_landing_hero_single_cta():
    h = _html(halaman_landing)
    assert "Mulai — daftar sekarang" in h
    # satu-satunya tombol-putih di halaman adalah "Masuk" di nav —
    # hero tetap punya CTA tunggal coral
    assert h.count('class="tombol-putih"') == 1


# ─────────────────── halaman_kebijakan ───────────────────

def test_kebijakan_tautan_sumber_aktif():
    """Tiga sumber menaut /kebijakan-privasi: footer landing, consent
    /daftar, dan consent anak-baru (web.py). Halaman tujuannya wajib ada."""
    assert 'href="/kebijakan-privasi"' in _html(halaman_landing)
    assert 'href="/kebijakan-privasi"' in _html(halaman_daftar)
    sumber = Path(web.__file__).read_text(encoding="utf-8")
    assert 'href="/kebijakan-privasi"' in sumber


def test_kebijakan_halaman_statis_lengkap():
    h = _html(halaman_kebijakan)
    assert "<h1>Kebijakan Privasi</h1>" in h
    assert '<a class="brand" href="/">' in h  # brand = link beranda
    assert h.count('href="/masuk"') == 1
    for bagian in ("Data yang dikumpulkan", "Data anak", "Siapa yang bisa melihat",
                   "Data yang tidak dikumpulkan", "penghapusan data"):
        assert bagian in h, f"bagian {bagian} hilang"


def test_kebijakan_sebut_laporan_pihak_ketiga():
    """Keterbukaan jujur: variasi cerita mengirim teks soal ke layanan AI."""
    h = _html(halaman_kebijakan)
    assert "layanan AI" in h
