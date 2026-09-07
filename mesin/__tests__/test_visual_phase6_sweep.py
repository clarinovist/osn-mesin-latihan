"""Sweep generator dan determinisme lintas proses untuk tranche Fase 6."""
from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import topics
from templates import REGISTRI
from question_views import penyajian_dari_soal
from visual_contract import serialisasi_penyajian
from visual_renderer import render_pertanyaan


def test_seluruh_generator_25_seed_dan_render_dua_keluarga(monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pengukuran,kombinatorik")
    hitungan = ()
    for nama in topics.daftar_topik():
        if nama == "campuran":
            continue
        paket = topics.ambil(nama)
        for level, urutan in paket.komposisi.items():
            for tid in sorted(set(urutan)):
                for seed in range(25):
                    soal = REGISTRI[tid](**paket.parameter_untuk(tid, random.Random(seed), level))
                    if nama in ("pengukuran", "kombinatorik"):
                        penyajian = penyajian_dari_soal(soal)
                        html = render_pertanyaan(penyajian, namespace=f"{tid}-{level}-{seed}")
                        if tid in ("jam_selesai", "jalur_petak"):
                            assert penyajian.status_visual == "siap"
                            svg = ET.fromstring(html[html.index("<svg"):html.index("</svg>") + 6])
                            import math
                            numerik = {"x", "y", "x1", "x2", "y1", "y2", "cx", "cy", "r"}
                            assert all(math.isfinite(float(v)) for e in svg.iter()
                                       for k, v in e.attrib.items() if k in numerik)
                hitungan = (*hitungan, (nama, level, tid))
    assert len(hitungan) == len(set(hitungan))
    assert hitungan


def test_snapshot_dan_svg_deterministik_dua_proses():
    kode = '''import json,random,topics
from templates import REGISTRI
from question_views import penyajian_dari_soal
from visual_contract import serialisasi_penyajian
from visual_renderer import render_pertanyaan
hasil=[]
for nama,tid,level in (("pengukuran","jam_selesai","P4"),("kombinatorik","jalur_petak","P6"),("pengukuran","skala_peta","P5"),("pengukuran","jam_menit_detik","P4")):
 p=topics.ambil(nama).parameter_untuk(tid,random.Random(26),level)
 soal=REGISTRI[tid](**p); s=penyajian_dari_soal(soal)
 hasil.append([soal.tanda_tangan,serialisasi_penyajian(s),render_pertanyaan(s)])
print(json.dumps(hasil))'''
    hasil = tuple(subprocess.check_output(
        [sys.executable, "-c", kode], cwd=Path(__file__).resolve().parent.parent,
        env={**os.environ, "PYTHONHASHSEED": str(seed), "OSN_VISUAL_KELUARGA": "pengukuran,kombinatorik"},
        text=True) for seed in (1, 777))
    assert hasil[0] == hasil[1]
    assert len(json.loads(hasil[0])) == 4
