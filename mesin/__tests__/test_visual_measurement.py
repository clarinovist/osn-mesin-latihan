"""Skema peta hanya memperlihatkan dua besaran yang diberikan."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import topic_measurement as topik
from question_views import penyajian_dari_soal
from visual_renderer import render_pertanyaan, ringkasan_pertanyaan
from visual_contract import DescriptorVisual


@pytest.mark.parametrize("varian,field,target", (
    ("cari_skala", {"varian", "peta", "sebenarnya"}, "250000"),
    ("cari_peta", {"varian", "skala", "sebenarnya"}, "18 cm"),
    ("cari_sebenarnya", {"varian", "skala", "peta"}, "45 km"),
))
def test_skala_menyaring_target(monkeypatch, varian, field, target):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pengukuran")
    soal = topik.skala_peta(varian, 45, 18, 250000, versi=2)
    hasil = penyajian_dari_soal(soal)
    assert hasil.mode_representasi == "skala_peta-v1"
    assert hasil.descriptor is not None
    assert set(hasil.descriptor.data) == field
    html = render_pertanyaan(hasil)
    assert "Tidak berskala" in html
    assert "?" in html
    assert target not in html + ringkasan_pertanyaan(hasil)
    assert "<svg" in html


def test_skala_warisan_tidak_diaktifkan(monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pengukuran")
    lama = topik.skala_peta("cari_sebenarnya", 107, 43, 250000)
    assert penyajian_dari_soal(lama).status_visual == "tanpa_visual"


@pytest.mark.parametrize("data", (
    {"varian": "cari_peta", "sebenarnya": 45, "skala": 250000, "peta": 18},
    {"varian": "cari_peta", "sebenarnya": -1, "skala": 250000},
    {"varian": "cari_peta", "sebenarnya": True, "skala": 250000},
    {"varian": "cari_peta", "sebenarnya": 45, "skala": 0},
    {"varian": [], "sebenarnya": 45, "skala": 250000},
))
def test_skala_descriptor_invalid_ditolak(data):
    with pytest.raises(ValueError):
        DescriptorVisual("skala_peta", 1, data)
