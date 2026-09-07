"""Soal geometri versi baru tidak memakai kunci bank atau snapshot lama."""
from __future__ import annotations

import json
import random
import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database
import question_views
import topic_solid_geometry as geometri
from diagnosis import setara
from templates import REGISTRI


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.delenv('OSN_VISUAL_KELUARGA', raising=False)
    jalur = tmp_path / 'ruang-riwayat.db'
    database.siapkan(jalur)
    return jalur


def _sesi(kon, siswa, soal):
    soal = replace(soal, level='P6')
    return database.buat_sesi_dari_urutan(
        kon, siswa, seed=42, urutan=(soal.template_id,),
        topik='geometri-ruang', level='P6', soal_terpilih=(soal,),
    )


def test_bank_kunci_dan_snapshot_lama_tidak_terganti(db):
    lama = geometri.volume_prisma_tabung('tabung_V', r=2, t=3)
    baru = geometri.volume_prisma_tabung('tabung_V', r=2, t=3, versi=2)
    assert lama.kunci == '37'
    assert baru.kunci == '37,68'
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, 'Fixture', pemilik='guru')
        sesi_lama = _sesi(kon, siswa, lama)
        sebelum = dict(database.isi_sesi(kon, sesi_lama)[0])
        sesi_baru = _sesi(kon, siswa, baru)
        setelah = dict(database.isi_sesi(kon, sesi_lama)[0])
        assert sebelum == setelah
        butir = database.isi_sesi(kon, sesi_baru)[0]
        assert butir['soal_id'] != sebelum['soal_id']
        assert butir['kunci'] == '37,68'
        assert setelah['kunci'] == '37'
        assert butir['fingerprint_matematis'] != sebelum['fingerprint_matematis']
        for baris in (sebelum, butir):
            hasil = question_views.soal_dari_baris(baris)
            assert hasil.kunci == baris['kunci']
            assert hasil.teks == baris['teks_soal']
        assert kon.execute('SELECT COUNT(*) FROM soal').fetchone()[0] == 2
    assert setara(baru.kunci, '37.68')


def test_baris_warisan_tanpa_snapshot_tetap_memakai_template_lama():
    soal = geometri.perbandingan_volume('cari_V_baru', k=2, s=3, V=3, V_baru=24)
    baris = {'template_id': soal.template_id,
             'parameter': json.dumps(soal.parameter), 'level': 'P6'}
    penyajian = question_views.penyajian_dari_baris(baris)
    assert penyajian.status_visual == 'warisan'
    assert penyajian.teks_soal == soal.teks
    assert question_views.soal_dari_baris(baris).kunci == '24'


@pytest.mark.parametrize('tid', ('jaring_jaring', 'perbandingan_volume'))
def test_generator_baru_memilih_versi2_dan_roundtrip(tid):
    for seed in range(50):
        parameter = geometri._parameter(tid, random.Random(seed), 'P6')
        assert parameter.get('versi') == 2
        soal = REGISTRI[tid](**parameter)
        pulih = REGISTRI[tid](**json.loads(json.dumps(soal.parameter)))
        assert soal.tanda_tangan == pulih.tanda_tangan
        assert soal.kunci == pulih.kunci
        assert soal.teks == pulih.teks
        assert soal.malrule == pulih.malrule
