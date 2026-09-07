"""Sweep seluruh cabang geometri, keamanan markup, dan determinisme."""
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

import question_views
import topic_plane_geometry as geometri
from visual_renderer import render_pertanyaan, ringkasan_pertanyaan


@pytest.mark.parametrize("level", ("P3", "P4", "P5", "P6"))
def test_semua_template_geometri_100_seed_menjaga_label_dan_svg(level, monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "geometri-datar")
    for tid in sorted(geometri.REGISTRI_TOPIK):
        for seed in range(100):
            parameter = geometri._parameter(tid, random.Random(seed), level)
            soal = replace(geometri.REGISTRI_TOPIK[tid](**parameter), level=level)
            penyajian = question_views.penyajian_dari_soal(soal)
            html = render_pertanyaan(penyajian, namespace=f"{tid}-{level}-{seed}")
            if tid == "perbandingan_ukuran":
                assert "<svg" not in html
                assert penyajian.teks_soal == soal.teks
                continue
            assert penyajian.descriptor is not None, (tid, seed)
            bagian = re.search(r"<svg\b.*?</svg>", html, flags=re.S)
            assert bagian is not None, (tid, seed)
            akar = ET.fromstring(bagian.group())
            label = " ".join(akar.itertext())
            assert not any(kata in html.lower() for kata in ("nan", "infinity", "malrule", "pembahasan"))
            assert all(not elemen.tag.endswith(("script", "foreignObject", "image")) for elemen in akar.iter())
            for elemen in akar.iter():
                assert all(not key.lower().startswith("on") for key in elemen.attrib)
                assert all(not key.endswith("href") for key in elemen.attrib)
            data = penyajian.descriptor.data
            if data["model"] == "ketupat_balik":
                assert set(data) == {"model", "L", "d1"}
                assert f"{soal.kunci} cm" not in [e.text for e in akar.iter() if e.tag.endswith("text")]
            if data["model"] in {"segitiga_sudut", "segitiga_luar", "sudut_pasangan"}:
                # Nilai sama boleh muncul sebagai sudut diketahui; target tetap ?.
                assert "?" in label
            assert ringkasan_pertanyaan(penyajian)


def test_50_svg_namespace_unik_dan_label_tidak_menjadi_markup(monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "geometri-datar")
    soal = geometri.luas_arsiran("persegi_titik_tengah", r=7)
    penyajian = question_views.penyajian_dari_soal(soal)
    semua = "".join(render_pertanyaan(penyajian, namespace=f'butir-{i}<"&') for i in range(50))
    identitas = re.findall(r'\bid="([^"]+)"', semua)
    assert identitas and len(identitas) == len(set(identitas))
    assert "<script" not in semua and 'onclick=' not in semua
    assert semua.count('<svg') == 50


def test_snapshot_dan_svg_identik_antar_pythonhashseed():
    skrip = '''import hashlib,random
from dataclasses import replace
import topic_plane_geometry as g
from question_views import penyajian_dari_soal
from visual_contract import serialisasi_penyajian
from visual_renderer import render_pertanyaan
hasil=[]
for tid in sorted(g.REGISTRI_TOPIK):
 for seed in range(10):
  s=replace(g.REGISTRI_TOPIK[tid](**g._parameter(tid,random.Random(seed),'P6')),level='P6')
  p=penyajian_dari_soal(s)
  hasil.extend((serialisasi_penyajian(p),render_pertanyaan(p,namespace=f'{tid}-{seed}')))
print(hashlib.sha256(''.join(hasil).encode()).hexdigest())'''
    lingkungan = {**os.environ, "OSN_VISUAL_KELUARGA": "geometri-datar"}
    keluaran = tuple(subprocess.check_output(
        [sys.executable, "-c", skrip],
        env={**lingkungan, "PYTHONHASHSEED": str(seed)},
        cwd=Path(__file__).resolve().parent.parent, text=True,
    ) for seed in (1, 971))
    assert keluaran[0] == keluaran[1]
