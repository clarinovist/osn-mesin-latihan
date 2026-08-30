"""Navigasi landing: satu pintu Masuk, brand = link beranda.

Kontrak:
1. /daftar: brand = anchor link ke /; nav hanya "Masuk"; tidak ada
   duplikat "Sudah punya akun? Masuk" di bawah form.
2. Homepage: nav hanya "Masuk"; hero single CTA; footer tanpa /masuk.
3. Kedua halaman: tepat 1 href="/masuk".
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import design_tokens as T  # noqa: E402
from landing import halaman_daftar, halaman_landing  # noqa: E402


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


def test_landing_tidak_ada_tombol_putih_masuk():
    h = _html(halaman_landing)
    assert 'tombol-putih" href="/masuk"' not in h


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
    assert 'class="tombol-putih"' not in h
