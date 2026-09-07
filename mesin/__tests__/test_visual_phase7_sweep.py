"""Sweep pola lintas seed/level dan determinisme proses terpisah."""
import json
import math
import os
import random
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import replace
from pathlib import Path

import topics
from question_views import penyajian_dari_soal
from templates import REGISTRI
from visual_contract import serialisasi_penyajian
from visual_renderer import render_pertanyaan

NS = {"s": "http://www.w3.org/2000/svg"}


def test_pola_500_seed_per_level_dan_batas_koordinat(monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pola-bilangan")
    paket = topics.ambil("pola-bilangan")
    cakupan = frozenset()
    for lv, urutan in paket.komposisi.items():
        for tid in sorted(set(urutan) & {"korek_api", "titik_segitiga"}):
            for seed in range(500):
                p = paket.parameter_untuk(tid, random.Random(seed), lv)
                soal = replace(REGISTRI[tid](**p), level=lv)
                penyajian = penyajian_dari_soal(soal)
                badan = render_pertanyaan(penyajian, namespace=f"{lv}-{tid}-{seed}")
                akar = ET.fromstring(badan[badan.index("<svg"):badan.index("</svg>") + 6])
                _, _, lebar, tinggi = map(float, akar.attrib["viewBox"].split())
                for g in akar.findall("s:g", NS):
                    dx, dy = map(float, g.attrib["transform"].removeprefix("translate(").removesuffix(")").split())
                    for e in g:
                        for k, v in e.attrib.items():
                            if k in {"x", "x1", "x2", "cx", "y", "y1", "y2", "cy", "r"}:
                                assert math.isfinite(float(v))
                                if k != "r":
                                    horizontal = k in {"x", "x1", "x2", "cx"}
                                    assert 0 <= float(v) + (dx if horizontal else dy) <= (lebar if horizontal else tinggi)
                cakupan = cakupan | {(lv, tid)}
    harapan = {(lv, tid) for lv, urutan in paket.komposisi.items()
               for tid in set(urutan) & {"korek_api", "titik_segitiga"}}
    assert cakupan == harapan


def test_penyajian_identik_dua_proses():
    kode = '''import json
from topic_number_patterns import korek_api,titik_segitiga
from question_views import penyajian_dari_soal
from visual_contract import serialisasi_penyajian
from visual_renderer import render_pertanyaan
hasil=tuple((serialisasi_penyajian(p),render_pertanyaan(p,namespace=str(i)))
 for i,s in enumerate((korek_api(7,4,100),titik_segitiga(25)))
 for p in (penyajian_dari_soal(s),))
print(json.dumps(hasil))'''
    hasil = tuple(subprocess.check_output(
        [sys.executable, "-c", kode], cwd=Path(__file__).resolve().parent.parent,
        env={**os.environ, "PYTHONHASHSEED": str(seed), "OSN_VISUAL_KELUARGA": "pola-bilangan"},
        text=True) for seed in (1, 777))
    assert hasil[0] == hasil[1]
    assert len(json.loads(hasil[0])) == 2


def test_seluruh_generator_25_seed_setelah_integrasi_pola(monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pola-bilangan")
    pasangan = tuple((nama, lv, tid) for nama in topics.daftar_topik() if nama != "campuran"
                     for lv, urutan in topics.ambil(nama).komposisi.items() for tid in sorted(set(urutan)))
    assert pasangan and len(pasangan) == len(set(pasangan))
    for nama, lv, tid in pasangan:
        for seed in range(25):
            p = topics.ambil(nama).parameter_untuk(tid, random.Random(seed), lv)
            soal = replace(REGISTRI[tid](**p), level=lv)
            penyajian = penyajian_dari_soal(soal)
            assert render_pertanyaan(penyajian)
            assert serialisasi_penyajian(penyajian)
