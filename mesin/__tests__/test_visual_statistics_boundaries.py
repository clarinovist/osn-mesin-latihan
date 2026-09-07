"""Batas input tak tepercaya dan pemindahan fakta ke gambar."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from statistics_visual_data import validasi_data  # noqa: E402
from topic_statistics_visual import proyeksi_statistika  # noqa: E402


@pytest.mark.parametrize("varian", ([], {}, None))
def test_varian_bukan_teks_gagal_domain(varian):
    with pytest.raises(ValueError):
        validasi_data(
            "turus",
            {
                "nama": ["A", "B", "C"],
                "data": [1, 2, 3],
                "varian": varian,
                "i": 0,
            },
        )


@pytest.mark.parametrize("nama", ["A\u200b", "A\u202e", "A\x85", "\ud800"])
def test_kontrol_unicode_ditolak(nama):
    with pytest.raises(ValueError):
        validasi_data(
            "turus",
            {
                "nama": [nama, "B", "C"],
                "data": [1, 2, 3],
                "varian": "jumlah",
                "i": 0,
            },
        )

    with pytest.raises(ValueError, match="duplikat"):
        validasi_data(
            "turus",
            {
                "nama": ["A", " A ", "C"],
                "data": [1, 2, 3],
                "varian": "jumlah",
                "i": 0,
            },
        )


def test_kunci_nonstring_ditolak_sebelum_pengurutan_pesan_galat():
    with pytest.raises(ValueError):
        validasi_data(
            "turus",
            {
                1: 2,
                "asing": 3,
                "nama": ["A", "B", "C"],
                "data": [1, 2, 3],
                "varian": "jumlah",
                "i": 0,
            },
        )


def test_data_baca_lingkaran_dan_legenda_hanya_di_visual():
    teks, _ = proyeksi_statistika(
        "diagram_lingkaran",
        {"varian": "cari_sudut", "s": 90, "total": 120, "nilai": 30},
    )
    assert "30" not in teks
    assert "\n" in teks

    teks, _ = proyeksi_statistika(
        "piktogram",
        {
            "varian": "total",
            "gambar": [1, 2, 3],
            "nama": ["A", "B", "C"],
            "satuan": 20,
        },
    )
    assert "20" not in teks
    assert "\n" in teks


@pytest.mark.parametrize(
    ("template_id", "parameter"),
    (
        ([], {"varian": "jumlah", "data": [1, 2, 3]}),
        (
            "piktogram",
            {
                "varian": [],
                "gambar": [1, 2, 3],
                "nama": ["A", "B", "C"],
                "satuan": 2,
            },
        ),
    ),
)
def test_proyektor_menolak_template_dan_varian_nonteks_sebagai_domain(
    template_id, parameter
):
    with pytest.raises(ValueError):
        proyeksi_statistika(template_id, parameter)


def test_batang_menolak_panjang_data_sebelum_membaca_isinya():
    class DataTerlaluPendek(list):
        def __iter__(self):
            raise AssertionError("isi data tidak boleh dibaca sebelum batas panjang")

    with pytest.raises(ValueError, match="3..6"):
        proyeksi_statistika(
            "diagram_batang_garis",
            {"varian": "jumlah", "data": DataTerlaluPendek((1, 2))},
        )
