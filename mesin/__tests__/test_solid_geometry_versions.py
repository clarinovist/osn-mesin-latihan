"""Oracle matematika dari fakta pertanyaan, bukan parameter jawaban."""
from __future__ import annotations
import json
import random
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import topic_solid_geometry as g


def angka(nilai):
    return F(str(nilai).replace(',', '.'))


@pytest.mark.parametrize('tid,varian,parameter,kunci', (
    ('volume_prisma_tabung', 'tabung_V', {'r': 2, 't': 3}, '37,68'),
    ('volume_prisma_tabung', 'tabung_balik', {'r': 2, 'V': '37,68'}, '3'),
    ('luas_permukaan', 'tabung_LP', {'r': 2, 't': 3}, '62,8'),
    ('luas_permukaan', 'tabung_cari_t', {'r': 2, 'LP': '62,8'}, '3'),
    ('perbandingan_volume', 'cari_V_baru', {'k': 2, 's': 3}, '8'),
    ('perbandingan_volume', 'cari_k', {'k': 2, 'V_baru': 8}, '2'),
    ('perbandingan_volume', 'balok_V_baru', {'k': 2, 's': 3}, '24'),
))
def test_kunci_versi2_dari_fakta(tid, varian, parameter, kunci):
    soal = g.REGISTRI_TOPIK[tid](varian, **parameter, versi=2)
    assert soal.kunci == kunci
    assert soal.parameter['versi'] == 2
    assert {'K', 'H'} <= {m.kode for m in soal.malrule}
    nilai = tuple(m.jawaban for m in soal.malrule)
    assert kunci not in nilai and len(nilai) == len(set(nilai))
    ulang = g.REGISTRI_TOPIK[tid](**json.loads(json.dumps(soal.parameter)))
    assert ulang == soal


@pytest.mark.parametrize('versi', (0, 3, True, '2', None))
def test_versi_tidak_dikenal_ditolak(versi):
    with pytest.raises(ValueError, match='versi'):
        g.volume_prisma_tabung('tabung_V', r=2, t=3, versi=versi)


@pytest.mark.parametrize('tid,varian,parameter', (
    ('volume_prisma_tabung', 'tabung_V', {'r': True, 't': 3}),
    ('volume_prisma_tabung', 'tabung_V', {'r': 0, 't': 3}),
    ('volume_prisma_tabung', 'tabung_balik', {'r': 2, 'V': 'nan'}),
    ('luas_permukaan', 'tabung_cari_t', {'r': 2, 'LP': 1}),
    ('perbandingan_volume', 'cari_k', {'k': 2, 'V_baru': 24}),
    ('perbandingan_volume', 'cari_V_baru', {'k': False, 's': 3}),
    ('volume_prisma_tabung', 'tabung_balik', {'r': 2, 'V': '37,68', 't': False}),
    ('perbandingan_volume', 'cari_V_baru', {'k': 2, 's': 3, 'V': 'rusak'}),
    ('perbandingan_volume', 'cari_V_baru', {'k': 2, 's': 3, 'V_baru': float('inf')}),
))
def test_fakta_invalid_ditolak(tid, varian, parameter):
    with pytest.raises(ValueError):
        g.REGISTRI_TOPIK[tid](varian, **parameter, versi=2)


@pytest.mark.parametrize('lv', ('P5', 'P6'))
def test_tabung_500_seed_eksak(lv):
    for tid in ('volume_prisma_tabung', 'luas_permukaan'):
        for seed in range(500):
            soal = g.REGISTRI_TOPIK[tid](**g._parameter(tid, random.Random(seed), lv))
            p = soal.parameter
            if not p['varian'].startswith('tabung'):
                continue
            assert p['versi'] == 2
            pi = F(22, 7) if p['r'] % 7 == 0 else F(314, 100)
            if p['varian'] == 'tabung_V':
                harapan = pi * p['r'] ** 2 * p['t']
            elif p['varian'] == 'tabung_balik':
                harapan = angka(p['V']) / (pi * p['r'] ** 2)
            elif p['varian'] == 'tabung_LP':
                harapan = 2 * pi * p['r'] * (p['r'] + p['t'])
            else:
                harapan = angka(p['LP']) / (2 * pi * p['r']) - p['r']
            assert angka(soal.kunci) == harapan, p


def test_perbandingan_500_seed_sesuai_pertanyaan():
    for seed in range(500):
        soal = g.perbandingan_volume(**g._parameter('perbandingan_volume', random.Random(seed), 'P6'))
        p = soal.parameter
        assert p['versi'] == 2
        if p['varian'] == 'cari_k':
            assert int(soal.kunci) ** 3 == p['V_baru']
        else:
            faktor = p['s'] if p['varian'] == 'balok_V_baru' else 1
            assert int(soal.kunci) == p['k'] ** 3 * faktor
