"""Kontrak validator dan proyektor visual geometri datar."""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path
from types import MappingProxyType

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import topic_plane_geometry as topik  # noqa: E402
from plane_geometry_visual_data import validasi_data  # noqa: E402
from topic_plane_geometry_visual import proyeksi_geometri_datar  # noqa: E402
from visual_contract import DescriptorVisual  # noqa: E402


DATA_SAH = {
    "sudut_pasangan": {"model": "sudut_pasangan", "total": 180, "diketahui": 65},
    "sudut_rasio": {"model": "sudut_rasio", "kali": 4},
    "segitiga_sudut": {"model": "segitiga_sudut", "a": 45, "b": 65},
    "segitiga_rasio": {"model": "segitiga_rasio", "p": 1, "q": 2, "r": 3},
    "segitiga_luar": {"model": "segitiga_luar", "a": 70, "b": 40},
    "persegi_panjang": {"model": "persegi_panjang", "p": 12, "l": 7},
    "persegi_panjang_balik": {"model": "persegi_panjang_balik", "p": 12, "K": 42},
    "segitiga_tinggi": {"model": "segitiga_tinggi", "a": 20, "t": 8, "s": 10},
    "jajargenjang": {"model": "jajargenjang", "a": 20, "t": 8, "s": 10},
    "trapesium": {"model": "trapesium", "a": 10, "b": 18, "t": 7},
    "ketupat": {"model": "ketupat", "d1": 12, "d2": 18},
    "ketupat_balik": {"model": "ketupat_balik", "L": 108, "d1": 12},
    "lingkaran": {"model": "lingkaran", "r": 14},
    "juring": {"model": "juring", "s": 90, "r": 14},
    "arsiran_pojok": {"model": "arsiran_pojok", "r": 14},
    "jalan": {"model": "jalan", "luar": 30, "dalam": 20},
    "kisi": {"model": "kisi", "p": 6, "l": 5, "satuan": "cm"},
    "simetri_persegi": {"model": "simetri_persegi", "ukuran": 8, "satuan": "cm"},
    "simetri_segitiga": {"model": "simetri_segitiga", "ukuran": 8, "satuan": "m"},
    "simetri_ketupat": {"model": "simetri_ketupat", "ukuran": 8, "satuan": "cm"},
    "simetri_persegi_panjang": {
        "model": "simetri_persegi_panjang", "ukuran": 8, "lebar": 4, "satuan": "m"
    },
}


@pytest.mark.parametrize("model,data", DATA_SAH.items())
def test_validator_menerima_setiap_model_dan_registrasi_kontrak(model, data):
    assert validasi_data(data) is None
    descriptor = DescriptorVisual("geometri_datar", 1, data)
    assert descriptor.data["model"] == model
    assert isinstance(descriptor.data, MappingProxyType)
    with pytest.raises(TypeError):
        descriptor.data["model"] = "jalan"


@pytest.mark.parametrize(
    "data",
    [
        {"model": "asing", "r": 7},
        {"model": True, "r": 7},
        {"model": "lingkaran", "r": True},
        {"model": "lingkaran", "r": math.inf},
        {"model": "lingkaran", "r": 7, "diameter": 14},
        {"model": "lingkaran"},
        {1: "lingkaran", "model": "lingkaran", "r": 7},
        {"model": "kisi", "p": 4, "l": 3, "satuan": "mm"},
    ],
)
def test_validator_menolak_model_tipe_field_dan_satuan_tidak_sah(data):
    with pytest.raises(ValueError):
        validasi_data(data)


@pytest.mark.parametrize(
    "data",
    [
        {"model": "sudut_pasangan", "total": 90, "diketahui": 90},
        {"model": "sudut_rasio", "kali": 6},
        {"model": "segitiga_sudut", "a": 100, "b": 80},
        {"model": "segitiga_rasio", "p": 3, "q": 2, "r": 1},
        {"model": "segitiga_luar", "a": 100, "b": 80},
        {"model": "persegi_panjang_balik", "p": 12, "K": 23},
        {"model": "segitiga_tinggi", "a": 20, "t": 10, "s": 10},
        {"model": "jajargenjang", "a": 20, "t": 10, "s": 9},
        {"model": "trapesium", "a": 10, "b": 10, "t": 7},
        {"model": "ketupat_balik", "L": 107, "d1": 12},
        {"model": "juring", "s": 360, "r": 14},
        {"model": "arsiran_pojok", "r": 8},
        {"model": "jalan", "luar": 20, "dalam": 30},
        {"model": "simetri_persegi_panjang", "ukuran": 8, "lebar": 8, "satuan": "cm"},
    ],
)
def test_validator_menolak_relasi_geometri_tidak_sah(data):
    with pytest.raises(ValueError):
        validasi_data(data)


def test_offset_tinggi_segitiga_boleh_melebihi_alas():
    assert validasi_data(
        {"model": "segitiga_tinggi", "a": 4, "t": 3, "s": 20}
    ) is None


@pytest.mark.parametrize(
    "template_id,parameter,model,field",
    [
        ("sudut_pelurus_berpenyiku", {"varian": "pelurus", "x": 65}, "sudut_pasangan", {"model", "total", "diketahui"}),
        ("sudut_pelurus_berpenyiku", {"varian": "tiga_kali", "kali": 4}, "sudut_rasio", {"model", "kali"}),
        ("jumlah_sudut_segitiga", {"varian": "dua_sudut", "a": 45, "b": 65}, "segitiga_sudut", {"model", "a", "b"}),
        ("jumlah_sudut_segitiga", {"varian": "perbandingan", "p": 1, "q": 2, "r": 3}, "segitiga_rasio", {"model", "p", "q", "r"}),
        ("sudut_luar_segitiga", {"a": 70, "b": 40}, "segitiga_luar", {"model", "a", "b"}),
        ("keliling_luas_datar", {"varian": "keliling", "p": 12, "l": 7}, "persegi_panjang", {"model", "p", "l"}),
        ("keliling_luas_datar", {"varian": "balik_luas", "p": 12, "K": 42}, "persegi_panjang_balik", {"model", "p", "K"}),
        ("luas_segitiga_jajargenjang", {"varian": "segitiga", "a": 20, "t": 8, "s": 10}, "segitiga_tinggi", {"model", "a", "t", "s"}),
        ("luas_segitiga_jajargenjang", {"varian": "jajargenjang", "a": 20, "t": 8, "s": 10}, "jajargenjang", {"model", "a", "t", "s"}),
        ("luas_segiempat_lain", {"varian": "trapesium", "a": 10, "b": 18, "t": 7}, "trapesium", {"model", "a", "b", "t"}),
        ("luas_segiempat_lain", {"varian": "ketupat_layang", "d1": 12, "d2": 18}, "ketupat", {"model", "d1", "d2"}),
        ("luas_segiempat_lain", {"varian": "balik_diagonal", "L": 108, "d1": 12}, "ketupat_balik", {"model", "L", "d1"}),
        ("lingkaran_keliling_luas", {"varian": "luas", "r": 14}, "lingkaran", {"model", "r"}),
        ("juring", {"varian": "luas_juring", "s": 90, "r": 14}, "juring", {"model", "s", "r"}),
        ("luas_arsiran", {"varian": "persegi_titik_tengah", "r": 14}, "arsiran_pojok", {"model", "r"}),
        ("luas_arsiran", {"varian": "jalan_pinggir", "luar": 30, "dalam": 20}, "jalan", {"model", "luar", "dalam"}),
        ("luas_kotak_satuan", {"p": 6, "l": 5, "satuan": "cm", "konteks": "ubin"}, "kisi", {"model", "p", "l", "satuan"}),
        ("simetri_bangun", {"bangun": "persegi", "ukuran": 8, "satuan": "cm", "warna": "merah", "lebar": None}, "simetri_persegi", {"model", "ukuran", "satuan"}),
        ("simetri_bangun", {"bangun": "segitiga_sama_sisi", "ukuran": 8, "satuan": "cm", "warna": None, "lebar": None}, "simetri_segitiga", {"model", "ukuran", "satuan"}),
        ("simetri_bangun", {"bangun": "belah_ketupat", "ukuran": 8, "satuan": "cm", "warna": "biru", "lebar": None}, "simetri_ketupat", {"model", "ukuran", "satuan"}),
        ("simetri_bangun", {"bangun": "persegi_panjang", "ukuran": 8, "satuan": "m", "warna": "hijau", "lebar": None}, "simetri_persegi_panjang", {"model", "ukuran", "lebar", "satuan"}),
    ],
)
def test_proyektor_memetakan_model_dengan_field_persis(template_id, parameter, model, field):
    hasil = proyeksi_geometri_datar(template_id, parameter)
    assert hasil is not None
    teks, descriptor = hasil
    assert teks
    assert descriptor.jenis == "geometri_datar"
    assert descriptor.versi == 1
    assert descriptor.data["model"] == model
    assert set(descriptor.data) == field


def test_prompt_memindahkan_ukuran_ke_diagram_tanpa_membocorkan_target_turunan():
    teks, persegi = proyeksi_geometri_datar(
        "keliling_luas_datar", {"varian": "balik_luas", "p": 12, "K": 42}
    )
    assert "12" not in teks and "42" not in teks
    assert "lebar" not in persegi.data and "luas" not in persegi.data

    teks, ketupat = proyeksi_geometri_datar(
        "luas_segiempat_lain", {"varian": "balik_diagonal", "L": 108, "d1": 12}
    )
    assert "108" not in teks and "12" not in teks
    assert "d2" not in ketupat.data

    teks, juring = proyeksi_geometri_datar(
        "juring", {"varian": "keliling_juring", "s": 90, "r": 14}
    )
    assert "90" not in teks and "14" not in teks
    assert "22/7" in teks
    assert not {"busur", "keliling", "sudut_target"} & set(juring.data)


@pytest.mark.parametrize("varian", ("balik_pelurus", "balik_penyiku"))
def test_prompt_sudut_balik_merujuk_target_yang_ada(varian):
    teks, _ = proyeksi_geometri_datar(
        "sudut_pelurus_berpenyiku", {"varian": varian, "x": 35}
    )
    assert "sudut x" not in teks
    assert "belum diketahui" in teks


@pytest.mark.parametrize("bangun,nama", (
    ("persegi", "persegi"), ("persegi_panjang", "persegi panjang"),
    ("segitiga_sama_sisi", "segitiga sama sisi"), ("belah_ketupat", "belah ketupat"),
))
def test_prompt_simetri_mempertahankan_jenis_bangun(bangun, nama):
    soal = topik.simetri_bangun(bangun, 8, lebar=4 if bangun == "persegi_panjang" else None)
    teks, _ = proyeksi_geometri_datar(soal.template_id, soal.parameter)
    assert nama in teks.lower()
    assert "8" not in teks


def test_perbandingan_ukuran_tetap_teks_dan_template_lain_none():
    assert proyeksi_geometri_datar(
        "perbandingan_ukuran", {"varian": "luas", "k": 3, "ukuran": 20}
    ) is None
    assert proyeksi_geometri_datar("template_lain", {}) is None


@pytest.mark.parametrize(
    "template_id,parameter",
    [
        ("sudut_pelurus_berpenyiku", {"varian": "pelurus"}),
        ("jumlah_sudut_segitiga", {"varian": [], "a": 40, "b": 50}),
        ("luas_segiempat_lain", {"varian": "trapesium", "a": 10, "b": 18}),
        ("lingkaran_keliling_luas", {"varian": "luas", "r": 14, "diameter": 28}),
        ("luas_kotak_satuan", {"p": 4, "l": 3, "satuan": "cm"}),
        ("simetri_bangun", {"bangun": "persegi", "ukuran": 8, "satuan": "cm", "warna": "merah"}),
    ],
)
def test_proyektor_menolak_parameter_tidak_persis_sebagai_value_error(template_id, parameter):
    with pytest.raises(ValueError):
        proyeksi_geometri_datar(template_id, parameter)


@pytest.mark.parametrize("template_id,parameter", [(None, {}), ([], {}), ("juring", None), ("juring", [])])
def test_proyektor_menolak_tipe_input_sebelum_lookup(template_id, parameter):
    with pytest.raises(ValueError):
        proyeksi_geometri_datar(template_id, parameter)


TEMPLATE_VISUAL = tuple(
    template_id
    for template_id in topik.REGISTRI_TOPIK
    if template_id != "perbandingan_ukuran"
)


@pytest.mark.parametrize("level", ("P3", "P4", "P5", "P6"))
def test_sweep_100_seed_semua_template_geometri_datar(level):
    assert len(TEMPLATE_VISUAL) >= 11
    for template_id in TEMPLATE_VISUAL:
        for seed in range(100):
            parameter = topik._parameter(template_id, random.Random(seed), level)
            soal = topik.REGISTRI_TOPIK[template_id](**parameter)
            hasil = proyeksi_geometri_datar(template_id, soal.parameter)
            assert hasil is not None, (level, template_id, seed)
            teks, descriptor = hasil
            assert teks and descriptor.jenis == "geometri_datar"
            assert validasi_data(descriptor.data) is None
