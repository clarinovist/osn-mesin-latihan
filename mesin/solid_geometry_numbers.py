"""Aritmetika eksak dan validasi angka geometri ruang versi baru."""
from __future__ import annotations

import re
from fractions import Fraction

from templates import Malrule, saring_malrule


def bulat(nilai, nama, minimum=1, maksimum=1000):
    """Terima bilangan bulat dalam batas, bukan boolean."""
    if type(nilai) is not int or not minimum <= nilai <= maksimum:
        raise ValueError(f'{nama} wajib bilangan bulat {minimum}–{maksimum}')
    return nilai


def pecahan(nilai, nama):
    """Baca nilai JSON eksak; float/nonfinite/notasi bebas tidak diterima."""
    if type(nilai) is int:
        hasil = Fraction(nilai)
    elif isinstance(nilai, str) and re.fullmatch(r'[0-9]{1,10}(?:[,.][0-9]{1,4})?', nilai):
        hasil = Fraction(nilai.replace(',', '.'))
    else:
        raise ValueError(f'{nama} bukan angka desimal yang sah')
    if not 0 < hasil <= 10**9:
        raise ValueError(f'{nama} di luar batas')
    return hasil


def desimal(nilai):
    """Format eksak maksimal empat desimal, dengan koma tanpa nol ekor."""
    nilai = Fraction(nilai)
    for digit in range(5):
        kelipatan = nilai * 10**digit
        if kelipatan.denominator == 1:
            angka = kelipatan.numerator
            if digit == 0:
                return str(angka)
            tanda = '-' if angka < 0 else ''
            angka = abs(angka)
            return f'{tanda}{angka // 10**digit},{angka % 10**digit:0{digit}d}'
    raise ValueError('nilai tidak memiliki desimal berhingga yang didukung')


def angka_json(nilai):
    """Bilangan bulat tetap int, pecahan disimpan sebagai teks eksak."""
    nilai = Fraction(nilai)
    return nilai.numerator if nilai.denominator == 1 else desimal(nilai)


def pi_untuk(r):
    return Fraction(22, 7) if r % 7 == 0 else Fraction(314, 100)


def malrule_angka(kunci, kandidat, id_h):
    """H diprioritaskan agar benturan tidak membuang jalur hitung."""
    nilai = Fraction(kunci.replace(',', '.'))
    langkah = Fraction(1, 10) if nilai.denominator != 1 else Fraction(1)
    h = Malrule(id_h, desimal(nilai - langkah), 'H',
                'rumus sudah tepat, tetapi hasil hitung meleset')
    calon = (h,) + tuple(Malrule(ident, desimal(jawaban), 'K', alasan)
                         for ident, jawaban, alasan in kandidat)
    hasil = saring_malrule(kunci, list(calon))
    if not any(m.kode == 'K' for m in hasil):
        raise ValueError('parameter kehilangan jalur kesalahan konsep')
    return hasil
