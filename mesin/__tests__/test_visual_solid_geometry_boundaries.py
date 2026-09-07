"""Guard tambahan pada batas data sebelum snapshot disimpan."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from topic_solid_geometry_visual import proyeksi_geometri_ruang
from solid_geometry_nets import JARING_SAH, JARING_TIDAK_SAH
from solid_geometry_visual_data import validasi_data


@pytest.mark.parametrize('versi', (True, False, '2', 3))
@pytest.mark.parametrize('tid,p', (
    ('jaring_jaring', {'pilihan_benar': 0, 'urutan': (0, 0, 1, 2, 3)}),
    ('volume_prisma_tabung', {'varian': 'tabung_V', 'r': 2, 't': 3}),
))
def test_versi_visual_bukan_boolean_atau_asing(versi, tid, p):
    with pytest.raises(ValueError):
        proyeksi_geometri_ruang(tid, {**p, 'versi': versi})


def test_pertanyaan_dicat_tidak_menerima_akhiran_ganda():
    with pytest.raises(ValueError):
        proyeksi_geometri_ruang('kubus_dicat', {'n': 5, 'n_kubus': 2, 'tanya': 'dua_sisi_kali_kali'})


@pytest.mark.parametrize('opsi', (
    (JARING_SAH[0],)*5,
    (JARING_SAH[0], JARING_SAH[1], *JARING_TIDAK_SAH[:3]),
    JARING_TIDAK_SAH,
))
def test_jaring_snapshot_harus_punya_tepat_satu_opsi_sah(opsi):
    with pytest.raises(ValueError):
        validasi_data({'model': 'jaring', 'opsi': opsi})
