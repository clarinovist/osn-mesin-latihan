"""Skema leaf immutable untuk fakta visual geometri ruang."""
from __future__ import annotations
from collections.abc import Mapping
from types import MappingProxyType

from solid_geometry_numbers import bulat, pecahan
from solid_geometry_nets import JARING_SAH, JARING_TIDAK_SAH

BANGUN_VISUAL = frozenset(('kubus', 'balok', 'prisma_segitiga', 'tabung', 'limas_segiempat', 'kerucut'))
FIELD_MODEL = MappingProxyType({
    'kubus': frozenset(('s',)),
    'kubus_balik': frozenset(('besaran', 'nilai')),
    'balok': frozenset(('p', 'l', 't')),
    'balok_balik': frozenset(('l', 't', 'besaran', 'nilai')),
    'prisma': frozenset(('a', 'tinggi_alas', 'tinggi')),
    'prisma_balik': frozenset(('a', 'tinggi_alas', 'nilai')),
    'tabung': frozenset(('r', 't')),
    'tabung_balik': frozenset(('r', 'besaran', 'nilai')),
    'unsur': frozenset(('bangun', 'jumlah')),
    'kubus_dicat': frozenset(('n', 'jumlah')),
    'jaring': frozenset(('opsi',)),
})


def validasi_opsi(opsi):
    """Setiap opsi enam persegi unik dalam kisi kecil, tanpa metadata."""
    if not isinstance(opsi, (tuple, list)) or len(opsi) != 5:
        raise ValueError('jaring wajib mempunyai lima opsi')
    for pola in opsi:
        if not isinstance(pola, (tuple, list)) or len(pola) != 6:
            raise ValueError('setiap opsi wajib mempunyai enam sel')
        for titik in pola:
            if not isinstance(titik, (tuple, list)) or len(titik) != 2:
                raise ValueError('sel wajib berisi baris dan kolom')
            for nilai in titik:
                bulat(nilai, 'koordinat sel', 0, 4)
        if len({tuple(p) for p in pola}) != 6:
            raise ValueError('sel jaring tidak boleh bertumpuk')
    pola = tuple(tuple(tuple(p) for p in bentuk) for bentuk in opsi)
    if (len(set(pola)) != 5 or sum(p in JARING_SAH for p in pola) != 1
            or any(p not in JARING_SAH + JARING_TIDAK_SAH for p in pola)):
        raise ValueError('opsi jaring wajib berbeda dan tepat satu dapat dilipat')


def validasi_data(data):
    """Tolak semua field ekstra, target, bilangan rusak, dan model asing."""
    if not isinstance(data, Mapping) or any(not isinstance(k, str) for k in data):
        raise ValueError('data visual wajib mapping dengan kunci teks')
    model = data.get('model')
    if not isinstance(model, str) or model not in FIELD_MODEL:
        raise ValueError('model geometri ruang tidak didukung')
    if set(data) != FIELD_MODEL[model] | {'model'}:
        raise ValueError('field geometri ruang tidak tepat')
    for nama in FIELD_MODEL[model]:
        nilai = data[nama]
        if nama == 'besaran':
            if nilai not in ('volume', 'luas_permukaan'):
                raise ValueError('besaran tidak dikenal')
        elif nama == 'bangun':
            if not isinstance(nilai, str) or nilai not in BANGUN_VISUAL:
                raise ValueError('bangun tidak dikenal')
        elif nama == 'opsi':
            validasi_opsi(nilai)
        elif nama == 'nilai':
            pecahan(nilai, 'besaran diketahui')
        elif nama == 'n':
            bulat(nilai, nama, 3, 10)
        elif nama == 'jumlah':
            bulat(nilai, nama, 1, 30 if model == 'unsur' else 15)
        else:
            bulat(nilai, nama)
