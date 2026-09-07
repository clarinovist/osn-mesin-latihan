"""Invariant SVG statistika dihitung dari geometri, bukan label hasil."""
from __future__ import annotations
import importlib.util
import math
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
NS = {'s': 'http://www.w3.org/2000/svg'}


def gambar(jenis, data, namespace='butir-1'):
    assert importlib.util.find_spec('statistics_svg'), 'renderer statistika belum ada'
    from statistics_svg import render_statistika
    return ET.fromstring(render_statistika(jenis, data, namespace))


def test_batang_berawal_nol_dan_tinggi_sesuai_skala_tanpa_label_nilai():
    akar = gambar('batang', dict(nama=['B1','B2','B3'], data=[7,13,21], varian='baca', i=1))
    batang = akar.findall('.//s:rect[@class="batang-data"]', NS)
    tick = akar.findall('.//s:text[@class="skala"]', NS)
    assert tick[0].text == '0'
    skala = (float(tick[0].get('y')) - float(tick[1].get('y'))) / int(tick[1].text)
    for b, nilai in zip(batang, [7,13,21]):
        assert float(b.get('height')) / skala == pytest.approx(nilai)
        assert float(b.get('y')) + float(b.get('height')) == pytest.approx(float(tick[0].get('y')) - 5)
    assert len(batang) == 3
    assert not akar.findall('.//s:text[@class="nilai-batang"]', NS)
    assert '13' not in [t.text for t in akar.findall('.//s:text', NS)]


@pytest.mark.parametrize('nilai', range(1,26))
def test_turus_jumlah_garis_dan_silang_per_lima(nilai):
    akar = gambar('turus', dict(nama=['A','B','C'], data=[nilai,1,2], varian='baca', i=0))
    baris = akar.findall('.//s:g[@class="baris-data"]', NS)[0]
    garis = baris.findall('.//s:line', NS)
    assert len(garis) == nilai
    assert sum(g.get('x1') != g.get('x2') for g in garis) == nilai // 5
    assert not baris.findall('.//s:text[@class="frekuensi"]', NS)


def test_piktogram_ikon_utuh_dan_legenda_berbeda_dari_data():
    akar = gambar('piktogram', dict(nama=['Senin','Selasa','Rabu'], gambar=[12,4,1], satuan=5, varian='total', i=0))
    baris = akar.findall('.//s:g[@class="baris-data"]', NS)
    assert [len(b.findall('.//s:circle', NS)) for b in baris] == [12,4,1]
    assert '1 gambar = 5 buah' in ''.join(akar.itertext())
    assert '85' not in ''.join(akar.itertext())


@pytest.mark.parametrize('sudut', [30,45,60,90,120,180,270])
def test_lingkaran_sudut_path_cocok_dan_target_sudut_tidak_berlabel(sudut):
    akar = gambar('lingkaran', dict(varian='cari_sudut', total=360, nilai=sudut))
    path = akar.find('.//s:path[@class="sektor-data"]', NS)
    bagian = path.get('d').split()
    cx, cy = map(float, bagian[1:3])
    sx, sy = map(float, bagian[4:6])
    ex, ey = map(float, bagian[-3:-1])
    radius = math.hypot(sx-cx, sy-cy)
    assert math.hypot(ex-cx, ey-cy) == pytest.approx(radius, abs=0.001)
    aktual = math.degrees(math.atan2(ex-cx, cy-ey)) % 360
    assert aktual == pytest.approx(sudut, abs=0.001)
    assert path.get('d').split()[10] == str(int(sudut > 180))
    teks = ''.join(akar.itertext())
    assert f'{sudut}°' not in teks
    assert '?' in teks


def test_nama_panjang_dibagi_baris_tanpa_mengubah_teks():
    nama = 'W' * 24
    akar = gambar('turus', dict(nama=[nama,'B','C'], data=[1,2,3], varian='jumlah', i=0))
    label = akar.findall('.//s:g[@class="baris-data"]', NS)[0].find('s:text', NS)
    assert label is not None
    assert len(label.findall('s:tspan', NS)) == 2
    assert ''.join(label.itertext()) == nama


def test_namespace_deterministik_unik_dan_tidak_menyisipkan_markup():
    data = dict(nama=['A','B','C'], data=[1,2,3], varian='jumlah', i=0)
    a = gambar('turus', data, '\" onload=buruk')
    b = gambar('turus', data, 'butir-2')
    ids = lambda akar: {e.get('id') for e in akar.iter() if e.get('id')}
    assert ids(a).isdisjoint(ids(b))
    assert not any(k.startswith('on') for e in a.iter() for k in e.attrib)
    assert ET.tostring(a) == ET.tostring(gambar('turus', data, '\" onload=buruk'))
