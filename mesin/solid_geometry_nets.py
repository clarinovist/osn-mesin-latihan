"""Topologi jaring versi2; tabel warisan tidak diubah atau diindeks ulang."""
from __future__ import annotations

from templates import Malrule, Soal
from solid_geometry_numbers import bulat

# Urutan dibekukan dari enumerasi 35 hexomino bebas dan audit enam normal.
JARING_SAH = (
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (3, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (1, 3), (1, 4)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 3)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1), (3, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (3, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (3, 1), (3, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (1, 3), (2, 2)),
)
JARING_TIDAK_SAH = (
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 2), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1)),
)


def opsi_jaring_v2(pilihan_benar, urutan):
    """Proyeksikan lima susunan persegi tanpa menyertakan penanda kunci."""
    bulat(pilihan_benar, 'pilihan', 0, 4)
    if not isinstance(urutan, (tuple, list)) or len(urutan) != 5:
        raise ValueError('urutan jaring wajib berisi lima indeks')
    bulat(urutan[0], 'indeks pola', 0, len(JARING_SAH)-1)
    for indeks in urutan[1:]:
        bulat(indeks, 'indeks pengecoh', 0, len(JARING_TIDAK_SAH)-1)
    if len(set(urutan[1:])) != 4:
        raise ValueError('pengecoh jaring wajib berbeda')
    return tuple(JARING_SAH[urutan[0]] if i == pilihan_benar else
                 JARING_TIDAK_SAH[urutan[1 + (i if i < pilihan_benar else i-1)]]
                 for i in range(5))


def parameter_jaring_v2(rng):
    """Pemilihan pola memakai RNG eksplisit dengan urutan tabel stabil."""
    return {'pilihan_benar': rng.randrange(5),
            'urutan': [rng.randrange(len(JARING_SAH))] + rng.sample(range(len(JARING_TIDAK_SAH)), 4),
            'versi': 2}


def buat_jaring_v2(pilihan_benar, urutan):
    """Versi teks ekuivalen menyebut posisi sel tanpa bergantung spasi ASCII."""
    opsi = opsi_jaring_v2(pilihan_benar, urutan)
    daftar = tuple(f"{'ABCDE'[i]}. " + '; '.join(f'({r+1},{c+1})' for r, c in pola)
                   for i, pola in enumerate(opsi))
    teks = ('Setiap pasangan (baris,kolom) menunjukkan satu persegi pada kisi. '
            'Baris dihitung dari atas, kolom dari kiri; persegi bertetangga berbagi sisi.\n'
            + '\n'.join(daftar)
            + '\nSusunan manakah yang dapat dilipat menjadi kubus? Jawab A, B, C, D, atau E.')
    kunci = 'ABCDE'[pilihan_benar]
    salah = tuple(h for h in 'ABCDE' if h != kunci)
    aturan = (('jaring.kebalikan', 'B'), ('jaring.salah_1', 'K'),
              ('jaring.salah_2', 'K'), ('jaring.kurang_satu', 'H'))
    mal = tuple(Malrule(ident, huruf, kode, 'memilih susunan yang bertumpuk saat dilipat')
                for (ident, kode), huruf in zip(aturan, salah))
    return Soal('jaring_jaring', {'pilihan_benar': pilihan_benar, 'urutan': tuple(urutan), 'versi': 2},
                teks, kunci, mal, bagian='B',
                pembahasan=('Bayangkan satu persegi menjadi alas, lalu lipat persegi tetangganya. '
                            f'Pada pilihan {kunci}, keenam persegi menutup muka yang berbeda; '
                            'pilihan lain membuat persegi bertumpuk.'))
