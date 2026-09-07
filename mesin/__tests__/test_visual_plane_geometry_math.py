"""Luas aktual dari path SVG, bukan perhitungan pembanding yang terpisah."""
from __future__ import annotations
import math
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from plane_geometry_svg import render_geometri_datar

NS = {"s": "http://www.w3.org/2000/svg"}


def _luas_busur_path(teks):
    """Integral Green untuk path tertutup yang seluruh sisinya busur lingkaran."""
    awal = tuple(map(float, re.match(r"M ([^ ]+) ([^ ]+)", teks).groups()))
    luas = 0
    for raw in re.findall(r"A ([^A-Z]+)", teks):
        rx, ry, rotasi, besar, arah, x, y = map(float, raw.split())
        assert rx == ry and rotasi == 0 and besar == 0
        akhir = (x, y)
        dx, dy = x-awal[0], y-awal[1]
        jarak = math.hypot(dx, dy)
        assert 0 < jarak <= 2*rx
        tengah = ((x+awal[0])/2, (y+awal[1])/2)
        tinggi = math.sqrt(max(0, rx*rx-jarak*jarak/4))
        tanda = 1 if arah else -1
        cx = tengah[0] - tanda*dy/jarak*tinggi
        cy = tengah[1] + tanda*dx/jarak*tinggi
        a = math.atan2(awal[1]-cy, awal[0]-cx)
        b = math.atan2(y-cy, x-cx)
        delta = (b-a) % (2*math.pi) if arah else -((a-b) % (2*math.pi))
        luas += (cx*rx*(math.sin(b)-math.sin(a))
                 + cy*rx*(math.cos(a)-math.cos(b)) + rx*rx*delta)/2
        awal = akhir
    return abs(luas)


@pytest.mark.parametrize("r", (7, 14, 21, 28, 35))
def test_luas_path_arsiran_sesuai_komplemen_empat_pojok(r):
    akar = ET.fromstring(render_geometri_datar({"model": "arsiran_pojok", "r": r}, "arsir"))
    luar = akar.find('.//s:rect[@class="persegi-luar"]', NS)
    daerah = akar.find('.//s:path[@class="daerah-arsir-tengah"]', NS)
    sisi = float(luar.attrib["width"])
    luas_pixel = _luas_busur_path(daerah.attrib["d"])
    skala = sisi/(2*r)
    assert luas_pixel/(skala*skala) == pytest.approx((2*r)**2-math.pi*r*r, rel=1e-6)


@pytest.mark.parametrize("d1,d2", ((36,4), (40,6), (8,30)))
def test_label_diagonal_ketupat_memiliki_jarak_vertikal_aman(d1,d2):
    akar = ET.fromstring(render_geometri_datar({"model":"ketupat","d1":d1,"d2":d2},"uji"))
    label = [e for e in akar.findall('.//s:text',NS) if (e.text or '').endswith(' cm')]
    assert len(label) == 2
    assert abs(float(label[0].attrib['y'])-float(label[1].attrib['y'])) >= 22


@pytest.mark.parametrize("data", (
    {"model":"simetri_segitiga","ukuran":8,"satuan":"cm"},
    {"model":"trapesium","a":28,"b":6,"t":7},
    {"model":"trapesium","a":30,"b":4,"t":3},
    {"model":"trapesium","a":4,"b":30,"t":3},
))
def test_poligon_tetap_utuh_di_viewbox(data):
    akar = ET.fromstring(render_geometri_datar(data,"batas"))
    _,_,w,h = map(float,akar.attrib['viewBox'].split())
    for poligon in akar.findall('.//s:polygon',NS):
        titik = tuple(tuple(map(float,p.split(','))) for p in poligon.attrib['points'].split())
        assert all(2 <= x <= w-2 and 2 <= y <= h-2 for x,y in titik)
        if data['model'] == 'trapesium':
            skala=math.dist(titik[0],titik[1])/data['b']
            luas=abs(sum(titik[i][0]*titik[(i+1)%4][1]-titik[(i+1)%4][0]*titik[i][1] for i in range(4)))/2
            assert luas/skala**2 == pytest.approx((data['a']+data['b'])*data['t']/2, rel=1e-6)


def test_trapesium_sisi_atas_lebar_menghubungkan_kaki_tinggi_ke_alas():
    akar=ET.fromstring(render_geometri_datar({"model":"trapesium","a":28,"b":6,"t":7},"t"))
    assert akar.find('.//s:line[@class="perpanjangan-alas"]',NS) is not None


def test_luas_jalan_dari_dua_persegi_sesuai_data():
    for luar, dalam in ((18,10), (65,63), (120,100)):
        akar = ET.fromstring(render_geometri_datar({"model":"jalan","luar":luar,"dalam":dalam}, "jalan"))
        a = akar.find('.//s:rect[@class="jalan-luar"]',NS)
        b = akar.find('.//s:rect[@class="taman-dalam"]',NS)
        skala = float(a.attrib['width'])/luar
        luas = float(a.attrib['width'])*float(a.attrib['height']) - float(b.attrib['width'])*float(b.attrib['height'])
        assert luas/skala**2 == pytest.approx(luar**2-dalam**2, rel=1e-6)
        assert float(a.attrib['x'])+float(a.attrib['width'])/2 == pytest.approx(float(b.attrib['x'])+float(b.attrib['width'])/2)
        assert float(a.attrib['y'])+float(a.attrib['height'])/2 == pytest.approx(float(b.attrib['y'])+float(b.attrib['height'])/2)
