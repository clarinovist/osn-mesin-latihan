"""Primitif SVG murni untuk geometri datar."""
from __future__ import annotations

import html

import design_tokens as T


def angka(nilai):
    return f"{nilai:.6f}".rstrip("0").rstrip(".")


def teks(x, y, isi, kelas="", jangkar="middle", ukuran=None, **atribut):
    tambahan = "".join(
        f' {html.escape(str(k).replace("_", "-"), quote=True)}="{html.escape(str(v), quote=True)}"'
        for k, v in atribut.items()
    )
    return (
        f'<text x="{angka(x)}" y="{angka(y)}" class="{html.escape(kelas, quote=True)}" '
        f'text-anchor="{jangkar}" font-size="{ukuran or T.GEO_FONT}" '
        f'fill="{T.TEKS_UTAMA}"{tambahan}>{html.escape(str(isi))}</text>'
    )


def garis(x1, y1, x2, y2, kelas="", putus=False):
    dash = f' stroke-dasharray="{T.GEO_PUTUS}"' if putus else ""
    return (
        f'<line class="{kelas}" x1="{angka(x1)}" y1="{angka(y1)}" '
        f'x2="{angka(x2)}" y2="{angka(y2)}" stroke="{T.TEKS_UTAMA}" '
        f'stroke-width="{T.GEO_GARIS}"{dash}/>'
    )


def poligon(daftar, kelas="bangun", isi=None):
    points = " ".join(f"{angka(x)},{angka(y)}" for x, y in daftar)
    fill = isi or T.LATAR_KARTU
    return (
        f'<polygon class="{kelas}" points="{points}" fill="{fill}" '
        f'stroke="{T.TEKS_UTAMA}" stroke-width="{T.GEO_GARIS}"/>'
    )


def polyline(daftar, kelas="", putus=False):
    points = " ".join(f"{angka(x)},{angka(y)}" for x, y in daftar)
    dash = f' stroke-dasharray="{T.GEO_PUTUS}"' if putus else ""
    return (
        f'<polyline class="{kelas}" points="{points}" fill="none" '
        f'stroke="{T.TEKS_UTAMA}" stroke-width="{T.GEO_GARIS}"{dash}/>'
    )


def pola_arsir(ident):
    return (
        f'<defs><pattern id="{ident}-arsir" width="{T.GEO_ARSIR_JARAK}" '
        f'height="{T.GEO_ARSIR_JARAK}" patternUnits="userSpaceOnUse">'
        f'<path d="M 0 {T.GEO_ARSIR_JARAK} L {T.GEO_ARSIR_JARAK} 0" '
        f'stroke="{T.TEKS_SUBTLE}" stroke-width="{T.GEO_GARIS_TIPIS}"/>'
        f'</pattern></defs>'
    )


def label_tidak_berskala():
    return teks(
        T.GEO_LEBAR / 2,
        T.GEO_TINGGI - T.GEO_CATATAN_BAWAH,
        "Tidak berskala",
        "catatan-skala",
        ukuran=T.GEO_FONT_CATATAN,
    )


def siku(x, y, arah_x=1, arah_y=-1):
    n = T.GEO_TANDA_SIKU
    return polyline(
        ((x, y + arah_y * n), (x + arah_x * n, y + arah_y * n), (x + arah_x * n, y)),
        "tanda-siku",
    )
