"""Sweep proyeksi dan invariant diagram terhadap parameter serta kunci lama."""
from __future__ import annotations
import math
import random
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import topic_statistics as topik
from topic_statistics_visual import proyeksi_statistika
from statistics_svg import render_statistika
NS = {'s':'http://www.w3.org/2000/svg'}


@pytest.mark.parametrize('level', ['P3','P4','P5','P6'])
def test_statistika_500_seed_semua_template_visual(level):
    for tid in ('diagram_batang_garis','tabel_turus','piktogram','diagram_lingkaran'):
        for seed in range(500):
            soal = topik.REGISTRI_TOPIK[tid](**topik._parameter(tid,random.Random(seed),level))
            teks, desc = proyeksi_statistika(tid,soal.parameter)
            data = desc.data
            akar = ET.fromstring(render_statistika(desc.jenis,data,f'{level}-{tid}-{seed}'))
            assert teks and akar.tag.endswith('svg')
            assert not any(e.tag.endswith(('script','foreignObject','image')) for e in akar.iter())
            v = data['varian']
            i = data.get('i',0)
            if desc.jenis == 'batang':
                rect = akar.findall('.//s:rect[@class="batang-data"]',NS)
                tick = akar.findall('.//s:text[@class="skala"]',NS)
                skala = (float(tick[0].attrib['y'])-float(tick[1].attrib['y']))/int(tick[1].text)
                nilai = [round(float(r.attrib['height'])/skala) for r in rect]
                assert nilai == list(data['data'])
                hasil = nilai[i] if v=='baca' else sum(nilai) if v=='jumlah' else abs(nilai[i]-nilai[(i+1)%len(nilai)])
            elif desc.jenis in ('turus','piktogram'):
                baris = akar.findall('.//s:g[@class="baris-data"]',NS)
                tag = 'line' if desc.jenis=='turus' else 'circle'
                nilai = [len(b.findall('.//s:'+tag,NS)) for b in baris]
                assert nilai == list(data['data'] if tag=='line' else data['gambar'])
                if v=='terbanyak':
                    hasil = data['nama'][nilai.index(max(nilai))]
                else:
                    hasil = nilai[i] if v=='baca' else sum(nilai) if v in ('jumlah','total') else abs(nilai[i]-nilai[(i+1)%len(nilai)])
                    hasil *= data.get('satuan',1)
            else:
                d = akar.find('.//s:path[@class="sektor-data"]',NS).attrib['d'].split()
                cx,cy = map(float,d[1:3]); ex,ey = map(float,d[-3:-1])
                sudut = math.degrees(math.atan2(ex-cx,cy-ey))%360
                hasil = round(sudut*data['total']/360) if v=='cari_nilai' else round(sudut)
                if v=='cari_sudut':
                    assert set(data)=={'varian','total','nilai'}
                    assert f'{soal.kunci}°' not in ''.join(akar.itertext())
            assert str(hasil) == soal.kunci, (tid,level,seed)
