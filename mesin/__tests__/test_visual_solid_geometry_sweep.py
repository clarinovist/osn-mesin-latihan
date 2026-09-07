"""Sweep semua template ruang dan determinisme lintas proses."""
from __future__ import annotations
import os
import random
import re
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import topic_solid_geometry as g
from question_views import penyajian_dari_soal
from visual_contract import deserialisasi_penyajian, serialisasi_penyajian
from visual_renderer import render_pertanyaan


@pytest.mark.parametrize('level', ('P5', 'P6'))
def test_500_seed_setiap_template_aktif(level, monkeypatch):
    monkeypatch.setenv('OSN_VISUAL_KELUARGA', 'geometri-ruang')
    for tid in sorted(set(g.KOMPOSISI[level])):
        for seed in range(500):
            soal = replace(g.REGISTRI_TOPIK[tid](**g._parameter(tid, random.Random(seed), level)), level=level)
            p = penyajian_dari_soal(soal)
            html = render_pertanyaan(p, namespace=f'{tid}-{level}-{seed}')
            assert deserialisasi_penyajian(serialisasi_penyajian(p)) == p
            if tid == 'perbandingan_volume':
                assert p.descriptor is None and '<svg' not in html
                continue
            assert p.descriptor is not None
            gambar = re.search(r'<svg\b.*?</svg>', html, re.S)
            assert gambar is not None, (tid, seed)
            akar = ET.fromstring(gambar.group())
            assert not re.search(r'\b(?:NaN|Infinity)\b|<script|\bon\w+=|\bhref=', gambar.group())
            _, _, lebar, tinggi = map(float, akar.attrib['viewBox'].split())
            for e in akar.iter():
                if 'points' in e.attrib:
                    for titik in e.attrib['points'].split():
                        x, y = map(float, titik.split(','))
                        assert 0 <= x <= lebar and 0 <= y <= tinggi
            data = p.descriptor.data
            if data['model'].endswith('_balik'):
                label = ' '.join(e.text or '' for e in akar.iter() if e.tag.endswith('text'))
                assert '?' in label
                target = ('s' if data['model'] == 'kubus_balik' else 'p' if data['model'] == 'balok_balik'
                          else 'tinggi' if data['model'] == 'prisma_balik' else 't')
                assert target not in data


def test_determinisme_beda_pythonhashseed():
    kode = '''import hashlib,random
from question_views import penyajian_dari_soal
from visual_renderer import render_pertanyaan
from visual_contract import serialisasi_penyajian
import topic_solid_geometry as g
hasil=tuple(
 serialisasi_penyajian(p)+render_pertanyaan(p,namespace=f'{tid}-{seed}')
 for tid in sorted(g.REGISTRI_TOPIK) for seed in range(20)
 for p in (penyajian_dari_soal(g.REGISTRI_TOPIK[tid](**g._parameter(tid,random.Random(seed),'P6'))),))
print(hashlib.sha256(''.join(hasil).encode()).hexdigest())'''
    keluaran = tuple(subprocess.check_output([sys.executable, '-c', kode],
        cwd=Path(__file__).resolve().parent.parent, text=True,
        env={**os.environ, 'OSN_VISUAL_KELUARGA': 'geometri-ruang', 'PYTHONHASHSEED': str(seed)})
        for seed in (1, 976))
    assert keluaran[0] == keluaran[1]
