"""Semua template memiliki keputusan cakupan, bukan fallback tak sengaja."""
import importlib.util
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import topics
from templates import REGISTRI
from question_views import penyajian_dari_soal
from visual_renderer import render_pertanyaan


def test_semua_template_fase6_punya_alasan_eksplisit():
    assert importlib.util.find_spec("phase6_visual_coverage") is not None
    from phase6_visual_coverage import CAKUPAN
    for nama in ("pengukuran", "kombinatorik"):
        paket = topics.ambil(nama)
        assert set(paket.templates) <= set(CAKUPAN)
        for tid in paket.templates:
            status, alasan = CAKUPAN[tid]
            assert status in {"visual", "teks"}
            assert len(alasan.split()) >= 8


@pytest.mark.parametrize("nama", ("pengukuran", "kombinatorik"))
def test_sweep_lima_ratus_seed_semua_level(nama, monkeypatch):
    from phase6_visual_coverage import CAKUPAN
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pengukuran,kombinatorik")
    paket = topics.ambil(nama)
    for level, urutan in paket.komposisi.items():
        for tid in sorted(set(urutan)):
            for seed in range(500):
                soal = REGISTRI[tid](**paket.parameter_untuk(tid, random.Random(seed), level))
                hasil = penyajian_dari_soal(soal)
                assert (hasil.status_visual == "siap") == (CAKUPAN[tid][0] == "visual"), (tid, level, seed)
                html = render_pertanyaan(hasil, namespace=f"{tid}-{level}-{seed}")
                assert ("<svg" in html) == (CAKUPAN[tid][0] == "visual")
