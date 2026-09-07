"""Primitif proyeksi ruang; setiap rusuk polyhedron digambar sekali."""
from __future__ import annotations
import math

import design_tokens as T
from plane_geometry_svg_primitives import angka, garis, teks


def _rusuk(titik, pasangan, tersembunyi):
    return ''.join(garis(*titik[a], *titik[b], kelas='rusuk', putus=(a, b) in tersembunyi)
                   for a, b in pasangan)


def kotak():
    asal, sumbu = T.RUANG_ASAL, T.RUANG_SUMBU
    koordinat = ((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
                 (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1))
    titik = tuple(tuple(asal[j]+sum(p[i]*sumbu[i][j] for i in range(3))
                        for j in range(2)) for p in koordinat)
    pasangan = ((0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6),
                (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7))
    return _rusuk(titik, pasangan, ((1, 2), (2, 3), (2, 6)))


def prisma():
    depan = T.RUANG_PRISMA
    dx, dy = T.RUANG_PRISMA_GESER
    titik = depan + tuple((x+dx, y+dy) for x, y in depan)
    pasangan = ((0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3),
                (0, 3), (1, 4), (2, 5))
    return _rusuk(titik, pasangan, ((3, 4), (5, 3), (0, 3)))


def limas():
    pasangan = ((0, 1), (1, 2), (2, 3), (3, 0), (0, 4), (1, 4), (2, 4), (3, 4))
    return _rusuk(T.RUANG_LIMAS, pasangan, ((2, 3), (3, 0), (3, 4)))


def _busur(x, y, rx, ry, arah, putus=False):
    dash = f' stroke-dasharray="{T.GEO_PUTUS}"' if putus else ''
    return (f'<path class="rusuk-lengkung" d="M {x-rx} {y} A {rx} {ry} 0 0 {arah} {x+rx} {y}" '
            f'fill="none" stroke="{T.TEKS_UTAMA}" stroke-width="{T.GEO_GARIS}"{dash}/>')


def lengkung(kerucut=False):
    x, y = T.RUANG_TABUNG_PUSAT
    rx, ry = T.RUANG_TABUNG_RADIUS
    bawah = y+T.RUANG_TABUNG_TINGGI
    alas = _busur(x, bawah, rx, ry, 0) + _busur(x, bawah, rx, ry, 1, True)
    if kerucut:
        a = T.RUANG_KERUCUT_PUNCAK
        return alas + garis(*a, x-rx, bawah, 'siluet') + garis(*a, x+rx, bawah, 'siluet')
    atas = (f'<ellipse class="rusuk-lengkung" cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" '
            f'fill="none" stroke="{T.TEKS_UTAMA}" stroke-width="{T.GEO_GARIS}"/>')
    return (atas + alas + garis(x-rx, y, x-rx, bawah, 'siluet')
            + garis(x+rx, y, x+rx, bawah, 'siluet'))


def _isometri(p):
    u = T.RUANG_GRID_RUSUK
    x, y, z = p
    a, b = T.RUANG_GRID_ASAL
    return a+(x-y)*u*math.sqrt(3)/2, b-(x+y)*u/2-z*u


def _sel_muka(n, muka, i, j):
    def koordinat(a, b):
        return (a, 0, b) if muka == 0 else (0, a, b) if muka == 1 else (a, b, 1)
    sudut = tuple(_isometri(koordinat(a/n, b/n))
                  for a, b in ((i, j), (i+1, j), (i+1, j+1), (i, j+1)))
    points = ' '.join(f'{angka(x)},{angka(y)}' for x, y in sudut)
    return (f'<polygon class="sel-kubus" points="{points}" fill="{T.LATAR_KARTU}" '
            f'stroke="{T.TEKS_UTAMA}" stroke-width="{T.GEO_GARIS_TIPIS}"/>')


def dicat(n, jumlah):
    isi = ''.join(_sel_muka(n, muka, i, j) for muka in range(3)
                  for i in range(n) for j in range(n))
    return isi + teks(*T.RUANG_LABEL_JUMLAH, f'Contoh 1 dari {jumlah} kubus besar', ukuran=T.GEO_FONT_CATATAN)


def jaring(opsi):
    return ''.join(_opsi_jaring(i, pola) for i, pola in enumerate(opsi))


def _opsi_jaring(i, pola):
    ukuran = T.RUANG_JARING_SEL
    pusat = T.RUANG_JARING_PUSAT[2 if i == 4 else i % 2]
    atas = T.RUANG_JARING_ATAS + (i//2)*T.RUANG_JARING_BARIS
    r0, c0 = min(r for r, c in pola), min(c for r, c in pola)
    lebar = (max(c for r, c in pola)-c0+1)*ukuran
    isi = teks(pusat, T.RUANG_JARING_LABEL+(i//2)*T.RUANG_JARING_BARIS, 'ABCDE'[i])
    isi += ''.join(
        f'<rect class="sel-jaring" x="{pusat-lebar/2+(c-c0)*ukuran}" y="{atas+(r-r0)*ukuran}" '
        f'width="{ukuran}" height="{ukuran}" fill="{T.LATAR_KARTU}" stroke="{T.TEKS_UTAMA}" '
        f'stroke-width="{T.GEO_GARIS}"/>' for r, c in pola)
    return '<g class="opsi-jaring">'+isi+'</g>'
