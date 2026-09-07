"""Invariant SVG dipulihkan dari koordinat, bukan label atau helper renderer."""
from __future__ import annotations
import importlib
import math
import re
import sys
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from solid_geometry_nets import opsi_jaring_v2


def render(data):
    modul = importlib.import_module('solid_geometry_svg')
    hasil = modul.render_geometri_ruang(data, 'fixture')
    return ET.fromstring(re.search(r'<svg\b.*?</svg>', hasil, re.S).group())


def elemen(akar, kelas):
    return tuple(e for e in akar.iter() if e.get('class') == kelas)


@pytest.mark.parametrize('bangun,sudut,rusuk', (
    ('kubus', 8, 12), ('balok', 8, 12), ('prisma_segitiga', 6, 9), ('limas_segiempat', 5, 8),
))
def test_rusuk_unik_dan_titik_sudut(bangun, sudut, rusuk):
    akar = render({'model': 'unsur', 'bangun': bangun, 'jumlah': 1})
    garis = elemen(akar, 'rusuk')
    ujung = tuple(tuple((float(g.get('x'+str(i))), float(g.get('y'+str(i))))
                        for i in (1, 2)) for g in garis)
    assert len(ujung) == rusuk
    assert len({frozenset(g) for g in ujung}) == rusuk
    derajat = Counter(t for ruas in ujung for t in ruas)
    assert len(derajat) == sudut
    assert sorted(derajat.values()) == ([3]*4+[4] if bangun == 'limas_segiempat' else [3]*sudut)
    assert any(g.get('stroke-dasharray') for g in garis)


def luas(p):
    return abs(sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1]
                   for i in range(len(p))))/2


@pytest.mark.parametrize('n', range(3, 11))
def test_grid_kubus_dicat_memiliki_3_muka_n_kuadrat(n):
    akar = render({'model': 'kubus_dicat', 'n': n, 'jumlah': 3})
    sel = elemen(akar, 'sel-kubus')
    assert len(sel) == 3*n*n
    poligon = tuple(tuple(tuple(map(float, titik.split(',')))
                         for titik in e.get('points').split()) for e in sel)
    assert len(set(poligon)) == len(poligon)
    # Proyeksi isometrik rusuk satu kubus besar: 90 px pada setiap sumbu.
    satu_muka = 90**2 * math.sqrt(3)/2
    assert sum(luas(p) for p in poligon) == pytest.approx(3*satu_muka, rel=1e-5)
    assert max(luas(p) for p in poligon) == pytest.approx(satu_muka/n**2, rel=1e-5)
    assert '3 kubus' in ' '.join(akar.itertext())


def test_jaring_enam_kotak_per_opsi_dengan_posisi_asli():
    opsi = opsi_jaring_v2(2, (1, 0, 1, 2, 3))
    akar = render({'model': 'jaring', 'opsi': opsi})
    kelompok = elemen(akar, 'opsi-jaring')
    assert len(kelompok) == 5
    for grup, pola in zip(kelompok, opsi):
        kotak = elemen(grup, 'sel-jaring')
        assert len(kotak) == 6
        ukuran = float(kotak[0].get('width'))
        x0 = min(float(e.get('x')) for e in kotak)
        y0 = min(float(e.get('y')) for e in kotak)
        aktual = {(round((float(e.get('y'))-y0)/ukuran),
                   round((float(e.get('x'))-x0)/ukuran)) for e in kotak}
        r0, c0 = min(p[0] for p in pola), min(p[1] for p in pola)
        assert aktual == {(r-r0, c-c0) for r, c in pola}
        assert all(e.get('width') == e.get('height') for e in kotak)


@pytest.mark.parametrize('data', (
    {'model': 'kubus_balik', 'besaran': 'volume', 'nilai': 64},
    {'model': 'balok_balik', 'l': 4, 't': 3, 'besaran': 'volume', 'nilai': 96},
    {'model': 'tabung_balik', 'r': 2, 'besaran': 'volume', 'nilai': '37,68'},
    {'model': 'prisma_balik', 'a': 8, 'tinggi_alas': 4, 'nilai': 48},
))
def test_dimensi_target_hanya_tanda_tanya(data):
    akar = render(data)
    label = tuple(e.text for e in akar.iter() if e.tag.endswith('text'))
    assert any('?' in t for t in label)
    assert all('kunci' not in t and 'malrule' not in t for t in akar.itertext())


def test_id_unik_dan_svg_tanpa_resource_eksternal():
    modul = importlib.import_module('solid_geometry_svg')
    hasil = ''.join(modul.render_geometri_ruang({'model': 'kubus', 's': 5}, f'n-{n}<"&')
                    for n in range(50))
    ids = re.findall(r'\bid="([^"]+)"', hasil)
    assert ids and len(ids) == len(set(ids))
    assert not re.search(r'<(?:script|image|foreignObject)|\bon\w+=|\bhref=', hasil)


@pytest.mark.parametrize('data', (
    {'model': 'kubus', 's': 5},
    {'model': 'kubus_dicat', 'n': 10, 'jumlah': 15},
    {'model': 'unsur', 'bangun': 'prisma_segitiga', 'jumlah': 30},
))
def test_catatan_skala_cukup_jauh_untuk_font_halaman(data):
    akar = render(data)
    label = tuple(e for e in akar.iter() if e.tag.endswith('text'))
    catatan = next(e for e in label if e.text == 'Tidak berskala')
    terendah = max(float(e.attrib['y']) for e in label if e is not catatan)
    assert float(catatan.attrib['y']) - terendah >= 24


def test_label_radius_di_atas_kurva_tabung():
    akar = render({'model': 'tabung', 'r': 18, 't': 4})
    elips = next(e for e in akar.iter() if e.tag.endswith('ellipse'))
    label = next(e for e in akar.iter() if (e.text or '').startswith('r = '))
    batas_atas = float(elips.attrib['cy']) - float(elips.attrib['ry'])
    assert float(label.attrib['y']) <= batas_atas - 6


def test_label_tinggi_prisma_di_kiri_bangun():
    akar = render({'model': 'prisma', 'a': 26, 'tinggi_alas': 18, 'tinggi': 20})
    label = next(e for e in akar.iter() if (e.text or '').startswith('h = '))
    # Sediakan setengah lebar teks hingga 40px plus jarak 8px dari sisi kiri.
    assert float(label.attrib['x']) + 40 + 8 <= 100


def test_label_balok_di_luar_rusuk():
    akar = render({'model': 'balok', 'p': 13, 'l': 18, 't': 10})
    label = tuple(e for e in akar.iter() if e.tag.endswith('text'))
    lebar = next(e for e in label if (e.text or '').startswith('l = '))
    tinggi = next(e for e in label if (e.text or '').startswith('t = '))
    assert float(lebar.attrib['x']) <= 60
    assert float(tinggi.attrib['x']) >= 300


def test_radius_berawal_di_pusat_elips_yang_ditandai():
    akar = render({'model': 'tabung', 'r': 25, 't': 4})
    elips = next(e for e in akar.iter() if e.tag.endswith('ellipse'))
    titik = elemen(akar, 'pusat-alas')
    assert len(titik) == 1
    garis = elemen(akar, 'jari-jari')[0]
    assert titik[0].attrib['cx'] == elips.attrib['cx'] == garis.attrib['x1']
    assert titik[0].attrib['cy'] == elips.attrib['cy'] == garis.attrib['y1']
    assert float(garis.attrib['x2']) - float(garis.attrib['x1']) == float(elips.attrib['rx'])
    busur = elemen(akar, 'rusuk-lengkung')
    for b in busur:
        if 'd' in b.attrib:
            ukuran = re.search(r'A ([\d.]+) ([\d.]+)', b.attrib['d'])
            assert ukuran is not None
            assert tuple(map(float, ukuran.groups())) == (float(elips.attrib['rx']), float(elips.attrib['ry']))
