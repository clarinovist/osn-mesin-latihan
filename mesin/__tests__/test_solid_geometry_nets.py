"""Uji lipatan jaring memakai orientasi muka yang independen."""
from __future__ import annotations
import importlib
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import topic_solid_geometry as g


def lipatan_sah(pola):
    titik = frozenset(tuple(p) for p in pola)
    if len(titik) != 6:
        return False
    neg = lambda v: tuple(-n for n in v)
    orientasi = {min(titik): ((1, 0, 0), (0, 1, 0), (0, 0, 1))}
    antrian = (min(titik),)
    while antrian:
        (r, c), *sisa = antrian
        u, v, n = orientasi[(r, c)]
        tetangga = (((r, c+1), (neg(n), v, u)),
                    ((r, c-1), (n, v, neg(u))),
                    ((r+1, c), (u, neg(n), v)),
                    ((r-1, c), (u, n, neg(v))))
        antrian = tuple(sisa)
        for p, bingkai in tetangga:
            if p not in titik:
                continue
            if p in orientasi and orientasi[p] != bingkai:
                return False
            if p not in orientasi:
                orientasi = {**orientasi, p: bingkai}
                antrian = antrian + (p,)
    return len(orientasi) == 6 and len({b[2] for b in orientasi.values()}) == 6


def kanonis(pola):
    bentuk = tuple(pola)
    calon = ()
    for balik in (1, -1):
        titik = tuple((r, c*balik) for r, c in bentuk)
        for _ in range(4):
            a, b = min(r for r, c in titik), min(c for r, c in titik)
            calon += (tuple(sorted((r-a, c-b) for r, c in titik)),)
            titik = tuple((c, -r) for r, c in titik)
    return min(calon)


def test_semua_jaring_v2_sah_dan_berbeda():
    modul = importlib.import_module('solid_geometry_nets')
    assert len(modul.JARING_SAH) == 11
    assert all(lipatan_sah(p) for p in modul.JARING_SAH)
    assert len({kanonis(p) for p in modul.JARING_SAH}) == 11
    assert all(not lipatan_sah(p) for p in modul.JARING_TIDAK_SAH)
    assert len({kanonis(p) for p in modul.JARING_TIDAK_SAH}) == len(modul.JARING_TIDAK_SAH)


def test_500_seed_tepat_satu_jawaban_sah():
    modul = importlib.import_module('solid_geometry_nets')
    for seed in range(500):
        parameter = g._parameter('jaring_jaring', random.Random(seed), 'P6')
        soal = g.jaring_jaring(**parameter)
        opsi = modul.opsi_jaring_v2(parameter['pilihan_benar'], parameter['urutan'])
        benar = tuple('ABCDE'[i] for i, pola in enumerate(opsi) if lipatan_sah(pola))
        assert benar == (soal.kunci,)
        assert len({kanonis(p) for p in opsi}) == 5
        assert soal.parameter['versi'] == 2
        assert {'B', 'K', 'H'} <= {m.kode for m in soal.malrule}


@pytest.mark.parametrize('pilihan,urutan', (
    (True, (0, 0, 1, 2, 3)), (5, (0, 0, 1, 2, 3)),
    (0, (11, 0, 1, 2, 3)), (0, (0, 0, 0, 2, 3)),
    (0, (0, 0, 1)), (0, '01234'), (0, (0, 0, 1, 2, False)),
))
def test_parameter_jaring_invalid(pilihan, urutan):
    modul = importlib.import_module('solid_geometry_nets')
    with pytest.raises(ValueError):
        modul.opsi_jaring_v2(pilihan, urutan)


def test_oracle_membedakan_salib_dan_persegi_panjang():
    assert lipatan_sah(((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1)))
    assert not lipatan_sah(tuple((r, c) for r in range(2) for c in range(3)))
