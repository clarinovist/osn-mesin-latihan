"""Data visual ruang hanya membawa fakta, bukan dimensi hasil hitung."""
from __future__ import annotations
import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import topic_solid_geometry as g


CONTOH = (
    (g.volume_kubus_balok('kubus_cari_V', s=4), {'model': 'kubus', 's': 4}),
    (g.volume_kubus_balok('kubus_cari_s', s=4, V=64),
     {'model': 'kubus_balik', 'besaran': 'volume', 'nilai': 64}),
    (g.volume_kubus_balok('balok_cari_V', p=8, l=4, t=3),
     {'model': 'balok', 'p': 8, 'l': 4, 't': 3}),
    (g.volume_kubus_balok('balok_cari_p', p=8, l=4, t=3, V=96),
     {'model': 'balok_balik', 'l': 4, 't': 3, 'besaran': 'volume', 'nilai': 96}),
    (g.volume_prisma_tabung('prisma_V', a=8, t_segitiga=4, t_prisma=3),
     {'model': 'prisma', 'a': 8, 'tinggi_alas': 4, 'tinggi': 3}),
    (g.volume_prisma_tabung('prisma_balik', a=8, t_segitiga=4, V=48),
     {'model': 'prisma_balik', 'a': 8, 'tinggi_alas': 4, 'nilai': 48}),
    (g.volume_prisma_tabung('tabung_V', r=2, t=3, versi=2),
     {'model': 'tabung', 'r': 2, 't': 3}),
    (g.volume_prisma_tabung('tabung_balik', r=2, V='37,68', versi=2),
     {'model': 'tabung_balik', 'r': 2, 'besaran': 'volume', 'nilai': '37,68'}),
    (g.unsur_bangun('prisma_segitiga', 'rusuk_kali', 7),
     {'model': 'unsur', 'bangun': 'prisma_segitiga', 'jumlah': 7}),
    (g.kubus_dicat(5, 'dua_sisi_kali', 3),
     {'model': 'kubus_dicat', 'n': 5, 'jumlah': 3}),
)


@pytest.mark.parametrize('soal,data', CONTOH)
def test_proyeksi_hanya_fakta(soal, data):
    fungsi = importlib.import_module('topic_solid_geometry_visual').proyeksi_geometri_ruang
    teks, descriptor = fungsi(soal.template_id, soal.parameter)
    assert dict(descriptor.data) == data
    assert descriptor.jenis == 'geometri_ruang'
    assert teks and all(k not in teks.lower() for k in ('malrule', 'diagnosis', 'kunci'))


@pytest.mark.parametrize('data', (
    {'model': []}, {'model': 'asing'}, {'model': 'kubus', 's': True},
    {'model': 'kubus', 's': 0}, {'model': 'kubus', 's': float('inf')},
    {'model': 'kubus', 's': 4, 'kunci': 64}, {'model': 'kubus', 1: 3},
    {'model': 'unsur', 'bangun': '<script>', 'jumlah': 1},
    {'model': 'kubus_balik', 'besaran': 'volume', 'nilai': 'NaN'},
    {'model': 'kubus_balik', 'besaran': [], 'nilai': 64},
    {'model': 'jaring', 'opsi': ()},
))
def test_descriptor_invalid_ditolak(data):
    from visual_contract import DescriptorVisual
    with pytest.raises(ValueError):
        DescriptorVisual('geometri_ruang', 1, data)


def test_jaring_tidak_membawa_indeks_kunci():
    modul = importlib.import_module('topic_solid_geometry_visual')
    soal = g.jaring_jaring(2, (0, 0, 1, 2, 3), versi=2)
    _, d = modul.proyeksi_geometri_ruang(soal.template_id, soal.parameter)
    assert set(d.data) == {'model', 'opsi'}
    assert len(d.data['opsi']) == 5
    assert all(len(opsi) == 6 for opsi in d.data['opsi'])


def test_warisan_bermasalah_dan_perbandingan_tetap_teks():
    fungsi = importlib.import_module('topic_solid_geometry_visual').proyeksi_geometri_ruang
    for soal in (g.jaring_jaring(0, (0, 0, 1, 2, 3)),
                 g.volume_prisma_tabung('tabung_V', r=2, t=3),
                 g.perbandingan_volume('cari_V_baru', k=2, s=3, versi=2)):
        assert fungsi(soal.template_id, soal.parameter) is None


@pytest.mark.parametrize('tid,p', (([], {}), ('volume_kubus_balok', []),
    ('volume_kubus_balok', {'varian': 'kubus_cari_V'}),
    ('volume_kubus_balok', {'varian': 'kubus_cari_V', 's': 3, 'html': '<svg>'}),
    ('volume_kubus_balok', {'varian': []})))
def test_proyeksi_menolak_parameter_rusak(tid, p):
    fungsi = importlib.import_module('topic_solid_geometry_visual').proyeksi_geometri_ruang
    with pytest.raises(ValueError):
        fungsi(tid, p)
