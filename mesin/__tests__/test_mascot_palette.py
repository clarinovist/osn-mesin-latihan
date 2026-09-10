"""Regresi ekspor maskot: palet kecil tidak boleh menambahkan bintik warna."""
import importlib.util
from pathlib import Path
import random

import pytest


JALUR = Path(__file__).resolve().parents[2] / "scripts" / "mascot_palette.py"
SPESIFIKASI = importlib.util.spec_from_file_location("palet_maskot", JALUR)
palet_maskot = importlib.util.module_from_spec(SPESIFIKASI)
SPESIFIKASI.loader.exec_module(palet_maskot)


def _jarak(warna, calon):
    return sum((a - b) ** 2 for a, b in zip(warna, calon))


def _piksel_sintetis():
    """Bidang mulus krem/teal/coral, tepi antialias, dan campuran warna sintetis."""
    acak = random.Random(71)
    piksel = [(0, 0, 0, 0)] * 20
    for pusat in ((244, 237, 224), (24, 145, 150), (238, 96, 78), (27, 41, 67)):
        for _ in range(150):
            piksel.append(tuple(c + acak.randint(-7, 7) for c in pusat) + (255,))
    piksel += [tuple(acak.randrange(256) for _ in range(3)) + (acak.randrange(1, 256),)
               for _ in range(250)]
    return piksel


def test_setiap_piksel_memakai_warna_terdekat_bukan_kotak_median():
    """Bug lama memberi bintik meski warna yang lebih dekat ada di palet sama."""
    piksel = _piksel_sintetis()
    palet, indeks = palet_maskot.kuantisasi(piksel)
    for warna, i in zip(piksel, indeks):
        if warna[3]:
            assert _jarak(warna, palet[i]) == min(
                _jarak(warna, calon) for calon in palet[1:]
            ), "Pemetaan kotak median mengubah warna terlalu jauh"
        else:
            assert i == 0


def test_palet_deterministik_tanpa_dithering_dan_piksel_tidak_diubah():
    piksel = _piksel_sintetis()
    semula = list(piksel)
    hasil = palet_maskot.kuantisasi(piksel)
    assert hasil == palet_maskot.kuantisasi(piksel)
    assert piksel == semula
    palet, indeks = hasil
    assert len(palet) <= 32
    assert len(indeks) == len(piksel)
    peta = {}
    for warna, i in zip(piksel, indeks):
        assert 0 <= i < len(palet)
        assert peta.setdefault(warna, i) == i


@pytest.mark.parametrize("piksel", [[], [(255, 20, 10, 0)] * 3])
def test_seluruh_piksel_transparan(piksel):
    assert palet_maskot.kuantisasi(piksel) == ([(0, 0, 0, 0)], [0] * len(piksel))


def test_warna_sedikit_dan_alpha_tetap_persis():
    piksel = [(0, 0, 0, 0), (15, 163, 163, 255), (255, 248, 238, 255),
              (15, 163, 163, 128), (255, 107, 91, 255)] * 5
    palet, indeks = palet_maskot.kuantisasi(piksel)
    assert [palet[i] for i in indeks] == piksel
